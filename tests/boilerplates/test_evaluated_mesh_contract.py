"""Native numerical fixtures; run with scripts/headless-run.sh, not host Python.

No render, external asset, source .blend or running GUI is involved. The tracking
proxy below forwards to real bpy objects so cleanup ownership can be observed
without dereferencing freed Blender memory.
"""
from pathlib import Path
import sys
import unittest

import bmesh
import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from agent_runtime import emit_ok
from agent_verify import framing, tri_count, world_bbox
from boilerplates.bp_core import evaluated_mesh


class MeshContracts(unittest.TestCase):
    def setUp(self):
        self.collection = bpy.data.collections.new('mesh-contract-fixture')
        bpy.context.scene.collection.children.link(self.collection)
        self.data = []
        self.frame = bpy.context.scene.frame_current

    def tearDown(self):
        for obj in list(self.collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(self.collection)
        for data in self.data:
            if isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
            else:
                bpy.data.cameras.remove(data)
        bpy.context.scene.frame_set(self.frame)

    def box(self):
        mesh = bpy.data.meshes.new('contract-box')
        self.data.append(mesh)
        bm = bmesh.new()
        try:
            bmesh.ops.create_cube(bm, size=2)
            bm.to_mesh(mesh)
        finally:
            bm.free()
        obj = bpy.data.objects.new('contract-box', mesh)
        self.collection.objects.link(obj)
        return obj

    def camera(self, kind='ORTHO'):
        data = bpy.data.cameras.new('contract-camera')
        self.data.append(data)
        data.type, data.ortho_scale = kind, 8
        data.clip_start, data.clip_end = 0.1, 20
        camera = bpy.data.objects.new('contract-camera', data)
        self.collection.objects.link(camera)
        camera.location = (0, 0, 10)
        return camera

    def test_modified_mesh_and_source_preservation(self):
        obj = self.box()
        modifier = obj.modifiers.new('two-cubes', 'ARRAY')
        modifier.count = 2
        modifier.relative_offset_displace = (1, 0, 0)
        obj.scale = (2, 3, 4)
        obj.location = (5, -2, 1)
        low, high = world_bbox(obj)
        self.assertEqual(tuple(low), (3, -5, -3))
        self.assertEqual(tuple(high), (11, 1, 5))
        self.assertEqual(tri_count(obj), 24)
        self.assertEqual(len(obj.data.vertices), 8)
        self.assertEqual(len(obj.modifiers), 1)
        self.assertEqual(tuple(obj.scale), (2, 3, 4))

    def test_cleanup_on_exact_evaluated_owner_and_exception(self):
        obj = self.box()
        graph = bpy.context.evaluated_depsgraph_get()
        owner = obj.evaluated_get(graph)
        calls = []

        class OwnerProxy:
            def to_mesh(self, **kwargs):
                calls.append('allocate')
                return owner.to_mesh(**kwargs)

            def to_mesh_clear(self):
                calls.append('clear-evaluated-owner')
                owner.to_mesh_clear()

        class InputProxy:
            name = obj.name

            def evaluated_get(self, supplied_graph):
                self.assert_graph = supplied_graph
                calls.append('evaluate')
                return OwnerProxy()

        for should_raise in (False, True):
            calls.clear()
            try:
                with evaluated_mesh(InputProxy(), graph) as (_, mesh):
                    self.assertEqual(len(mesh.vertices), 8)
                    if should_raise:
                        raise RuntimeError('intentional consumer failure')
            except RuntimeError as exc:
                self.assertTrue(should_raise)
                self.assertEqual(str(exc), 'intentional consumer failure')
            self.assertEqual(calls, ['evaluate', 'allocate', 'clear-evaluated-owner'])

    def test_empty_geometry_rejected_by_measurements(self):
        obj = self.box()
        obj.data.clear_geometry()
        self.assertEqual(tri_count(obj), 0)
        with self.assertRaisesRegex(ValueError, 'no evaluated mesh vertices'):
            world_bbox(obj)
        with self.assertRaisesRegex(ValueError, 'no evaluated mesh vertices'):
            framing(obj, self.camera())

    def test_constraints_are_evaluated_before_world_measurement(self):
        obj, target = self.box(), self.box()
        target.location = (7, 0, 0)
        constraint = obj.constraints.new('COPY_LOCATION')
        constraint.target = target
        low, high = world_bbox(obj)
        self.assertAlmostEqual(low.x, 6)
        self.assertAlmostEqual(high.x, 8)
        self.assertEqual(tuple(obj.location), (0, 0, 0))

    def test_camera_depth_rejects_false_xy_pass(self):
        obj, camera = self.box(), self.camera()
        row = framing(obj, camera)
        self.assertTrue(row['in_frame'])
        camera.data.clip_end = 8
        row = framing(obj, camera)
        self.assertTrue(row['in_image'])
        self.assertFalse(row['within_clip'])
        self.assertFalse(row['in_frame'])
        camera.data.clip_end, camera.data.clip_start = 20, 10
        self.assertFalse(framing(obj, camera)['in_frame'])
        camera.data.clip_start = 0.1
        camera.location.z = -10
        self.assertFalse(framing(obj, camera)['in_front'])

    def test_frustum_responds_to_modifier_and_camera_shift(self):
        obj, camera = self.box(), self.camera()
        self.assertTrue(framing(obj, camera)['in_frame'])
        modifier = obj.modifiers.new('outside-frame', 'ARRAY')
        modifier.count = 4
        self.assertFalse(framing(obj, camera)['in_frame'])
        modifier.show_viewport = False
        self.assertTrue(framing(obj, camera)['in_frame'])
        camera.data.shift_x = 2
        self.assertFalse(framing(obj, camera)['in_frame'])

    def test_perspective_and_invalid_camera(self):
        obj, camera = self.box(), self.camera('PERSP')
        self.assertTrue(framing(obj, camera)['in_frame'])
        with self.assertRaisesRegex(ValueError, 'camera object'):
            framing(obj, obj)
        camera.data.type = 'PANO'
        with self.assertRaisesRegex(ValueError, 'perspective and orthographic'):
            framing(obj, camera)

    def test_repeated_reads_do_not_allocate_persistent_data(self):
        obj = self.box()
        before = (len(bpy.data.objects), len(bpy.data.meshes))
        for _ in range(12):
            with evaluated_mesh(obj) as (owner, mesh):
                self.assertTrue(owner.is_evaluated)
                self.assertEqual(len(mesh.vertices), 8)
            self.assertEqual(tri_count(obj), 12)
        self.assertEqual(before, (len(bpy.data.objects), len(bpy.data.meshes)))


if __name__ == '__main__':
    assert bpy.app.background, 'Run these fixtures in a disposable headless process'
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(MeshContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), 'evaluated-mesh contract failures'
    emit_ok('evaluated-mesh-contract', tests=result.testsRun,
            blender=bpy.app.version_string,
            build_hash=bpy.app.build_hash.decode(), manufacture='NOT_REQUESTED')
