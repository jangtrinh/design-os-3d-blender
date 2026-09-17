"""Headless contract tests for scripts/boilerplates/bp_geonodes.py on Blender 5.2."""

from __future__ import annotations

import importlib.util
import json
import math
from pathlib import Path
import sys
import unittest

import bpy


ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "boilerplates" / "bp_geonodes.py"
sys.path.insert(0, str(ROOT / "scripts"))
from agent_runtime import emit_ok


def load_geonodes_module():
    spec = importlib.util.spec_from_file_location("bp_geonodes_contract_target", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


geonodes = load_geonodes_module()
MEASUREMENTS = {}


class GeometryNodesContracts(unittest.TestCase):
    def setUp(self):
        self.collection = bpy.data.collections.new("gn-contract-fixture")
        bpy.context.scene.collection.children.link(self.collection)
        self.node_groups = []

    def tearDown(self):
        for obj in list(self.collection.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.data.collections.remove(self.collection)
        for tree in self.node_groups:
            if tree.name in bpy.data.node_groups and tree.users == 0:
                bpy.data.node_groups.remove(tree)

    def new_mesh_object(self, name: str) -> bpy.types.Object:
        mesh = bpy.data.meshes.new(name + "Mesh")
        obj = bpy.data.objects.new(name, mesh)
        self.collection.objects.link(obj)
        return obj

    def new_tree(self, name: str):
        tree, input_node, output_node = geonodes.create_geometry_node_tree(name)
        self.node_groups.append(tree)
        return tree, input_node, output_node

    def cylinder_fixture(self, name: str):
        obj = self.new_mesh_object(name + "Obj")
        tree, input_node, output_node = self.new_tree(name + "Tree")
        radius = geonodes.add_interface_socket(
            tree,
            "Radius",
            "INPUT",
            "NodeSocketFloat",
            default_value=0.025,
            min_value=0.001,
            max_value=0.5,
        )
        depth = geonodes.add_interface_socket(
            tree,
            "Depth",
            "INPUT",
            "NodeSocketFloat",
            default_value=0.080,
            min_value=0.001,
            max_value=1.0,
        )
        cylinder = geonodes.add_node(tree, "GeometryNodeMeshCylinder", location=(0, 0))
        cylinder.inputs["Vertices"].default_value = 32
        geonodes.connect(tree, input_node, radius.identifier, cylinder, "Radius")
        geonodes.connect(tree, input_node, depth.identifier, cylinder, "Depth")
        geonodes.connect(tree, cylinder, "Mesh", output_node, "Geometry")
        modifier = geonodes.assign_geonodes_modifier(obj, tree, name + "Modifier")
        return obj, tree, modifier, radius, depth

    def evaluated_dimensions(self, obj: bpy.types.Object):
        bpy.context.view_layer.update()
        graph = bpy.context.evaluated_depsgraph_get()
        owner = obj.evaluated_get(graph)
        mesh = owner.to_mesh()
        try:
            self.assertGreater(len(mesh.vertices), 0)
            xs = [vert.co.x for vert in mesh.vertices]
            ys = [vert.co.y for vert in mesh.vertices]
            zs = [vert.co.z for vert in mesh.vertices]
            return (
                max(xs) - min(xs),
                max(ys) - min(ys),
                max(zs) - min(zs),
            )
        finally:
            owner.to_mesh_clear()

    def test_identifier_and_unique_name_drive_evaluated_dimensions(self):
        obj, tree, modifier, radius, depth = self.cylinder_fixture("GNContractCylinder")
        self.assertTrue(tree.is_modifier)

        baseline = self.evaluated_dimensions(obj)
        self.assertAlmostEqual(baseline[0], 0.050, places=5)
        self.assertAlmostEqual(baseline[1], 0.050, places=5)
        self.assertAlmostEqual(baseline[2], 0.080, places=5)

        geonodes.set_modifier_input(modifier, radius.identifier, 0.050)
        geonodes.set_modifier_input(modifier, "Depth", 0.120)
        changed = self.evaluated_dimensions(obj)

        radius_entry = getattr(modifier.properties.inputs, radius.identifier)
        depth_entry = getattr(modifier.properties.inputs, depth.identifier)
        self.assertEqual(radius_entry.type, "VALUE")
        self.assertEqual(depth_entry.type, "VALUE")
        self.assertAlmostEqual(radius_entry.value, 0.050, places=7)
        self.assertAlmostEqual(depth_entry.value, 0.120, places=7)
        self.assertAlmostEqual(changed[0], 0.100, places=5)
        self.assertAlmostEqual(changed[1], 0.100, places=5)
        self.assertAlmostEqual(changed[2], 0.120, places=5)
        self.assertGreater(changed[0], baseline[0] * 1.9)
        self.assertGreater(changed[2], baseline[2] * 1.4)
        MEASUREMENTS["cylinder_m"] = {
            "baseline": [round(value, 6) for value in baseline],
            "changed": [round(value, 6) for value in changed],
        }

    def test_duplicate_name_is_ambiguous_but_identifier_is_stable(self):
        obj = self.new_mesh_object("GNContractAmbiguousObj")
        tree, _, _ = self.new_tree("GNContractAmbiguousTree")
        first = geonodes.add_interface_socket(
            tree, "Gain", "INPUT", "NodeSocketFloat", default_value=1.0, min_value=0.0, max_value=4.0
        )
        second = geonodes.add_interface_socket(
            tree, "Gain", "INPUT", "NodeSocketFloat", default_value=2.0, min_value=0.0, max_value=4.0
        )
        modifier = geonodes.assign_geonodes_modifier(obj, tree, "GNContractAmbiguousModifier")

        geonodes.set_modifier_input(modifier, first.identifier, 1.5)
        first_entry = getattr(modifier.properties.inputs, first.identifier)
        second_entry = getattr(modifier.properties.inputs, second.identifier)
        before = (first_entry.value, second_entry.value)
        self.assertEqual(before, (1.5, 2.0))

        with self.assertRaisesRegex(ValueError, "ambiguous"):
            geonodes.set_modifier_input(modifier, "Gain", 3.0)
        self.assertEqual((first_entry.value, second_entry.value), before)

    def test_invalid_type_and_range_fail_before_modifier_mutation(self):
        _, _, modifier, radius, _ = self.cylinder_fixture("GNContractValidation")
        entry = getattr(modifier.properties.inputs, radius.identifier)
        before = (entry.type, entry.value)

        with self.assertRaises(TypeError):
            geonodes.set_modifier_input(modifier, radius.identifier, "0.1")
        self.assertEqual((entry.type, entry.value), before)

        with self.assertRaises(ValueError):
            geonodes.set_modifier_input(modifier, radius.identifier, 0.0001)
        self.assertEqual((entry.type, entry.value), before)

        with self.assertRaises(ValueError):
            geonodes.set_modifier_input(modifier, radius.identifier, 0.75)
        self.assertEqual((entry.type, entry.value), before)

        for value in (math.nan, math.inf, -math.inf):
            with self.subTest(nonfinite=value):
                with self.assertRaisesRegex(ValueError, "finite"):
                    geonodes.set_modifier_input(modifier, radius.identifier, value)
                self.assertEqual((entry.type, entry.value), before)

    def test_vector_components_validate_before_modifier_mutation(self):
        obj = self.new_mesh_object("GNContractVectorObj")
        tree, _, _ = self.new_tree("GNContractVectorTree")
        vector = geonodes.add_interface_socket(
            tree,
            "Offset",
            "INPUT",
            "NodeSocketVector",
            default_value=(0.0, 0.0, 0.0),
            min_value=-1.0,
            max_value=1.0,
        )
        modifier = geonodes.assign_geonodes_modifier(obj, tree, "GNContractVectorModifier")
        entry = getattr(modifier.properties.inputs, vector.identifier)
        before = (entry.type, tuple(entry.value))

        with self.assertRaises(TypeError):
            geonodes.set_modifier_input(modifier, vector.identifier, (0.0, 0.0))
        self.assertEqual((entry.type, tuple(entry.value)), before)

        with self.assertRaises(TypeError):
            geonodes.set_modifier_input(modifier, vector.identifier, (0.0, "bad", 0.0))
        self.assertEqual((entry.type, tuple(entry.value)), before)

        with self.assertRaises(ValueError):
            geonodes.set_modifier_input(modifier, vector.identifier, (0.0, 1.5, 0.0))
        self.assertEqual((entry.type, tuple(entry.value)), before)

        geonodes.set_modifier_input(modifier, vector.identifier, (0.25, -0.5, 1.0))
        self.assertEqual(entry.type, "VALUE")
        self.assertEqual(tuple(entry.value), (0.25, -0.5, 1.0))

    def test_missing_tree_is_loud(self):
        obj = self.new_mesh_object("GNContractMissingTreeObj")
        modifier = obj.modifiers.new("GNContractMissingTreeModifier", "NODES")
        with self.assertRaisesRegex(ValueError, "node group"):
            geonodes.set_modifier_input(modifier, "Radius", 0.1)
        self.assertIsNone(modifier.node_group)

    def test_missing_socket_is_loud_and_does_not_mutate(self):
        _, _, modifier, radius, _ = self.cylinder_fixture("GNContractMissingSocket")
        entry = getattr(modifier.properties.inputs, radius.identifier)
        before = (entry.type, entry.value)

        with self.assertRaisesRegex(KeyError, "not found"):
            geonodes.set_modifier_input(modifier, "DoesNotExist", 0.1)

        self.assertEqual((entry.type, entry.value), before)

    def test_owned_node_group_is_not_deleted_on_same_name_rebuild(self):
        obj = self.new_mesh_object("GNContractOwnedObj")
        tree, _, _ = self.new_tree("GNContractOwnedTree")
        modifier = geonodes.assign_geonodes_modifier(obj, tree, "GNContractOwnedModifier")
        self.assertGreater(tree.users, 0)

        with self.assertRaisesRegex(RuntimeError, "in use"):
            geonodes.create_geometry_node_tree(tree.name)

        self.assertIs(modifier.node_group, tree)
        self.assertIs(bpy.data.node_groups.get(tree.name), tree)

    def test_zero_user_node_group_is_not_deleted_on_same_name_rebuild(self):
        tree = bpy.data.node_groups.new("GNContractZeroUserTree", "GeometryNodeTree")
        self.node_groups.append(tree)
        self.assertEqual(tree.users, 0)

        with self.assertRaisesRegex(RuntimeError, "zero users"):
            geonodes.create_geometry_node_tree(tree.name)

        self.assertIs(bpy.data.node_groups.get(tree.name), tree)
        self.assertEqual(tree.users, 0)

    def test_modifier_assignment_is_idempotent_and_name_safe(self):
        obj = self.new_mesh_object("GNContractModifierOwnerObj")
        tree, _, _ = self.new_tree("GNContractModifierOwnerTree")
        other_tree, _, _ = self.new_tree("GNContractModifierOtherTree")

        first = geonodes.assign_geonodes_modifier(obj, tree, "GNContractModifier")
        second = geonodes.assign_geonodes_modifier(obj, tree, "GNContractModifier")
        self.assertEqual(second.as_pointer(), first.as_pointer())
        self.assertEqual(len(obj.modifiers), 1)

        with self.assertRaisesRegex(RuntimeError, "refusing to replace"):
            geonodes.assign_geonodes_modifier(obj, other_tree, "GNContractModifier")
        self.assertEqual(len(obj.modifiers), 1)
        self.assertIs(first.node_group, tree)

        other_obj = self.new_mesh_object("GNContractModifierTypeObj")
        existing = other_obj.modifiers.new("GNContractModifier", "BEVEL")
        with self.assertRaisesRegex(RuntimeError, "type 'BEVEL'"):
            geonodes.assign_geonodes_modifier(other_obj, tree, "GNContractModifier")
        self.assertEqual(
            other_obj.modifiers.get("GNContractModifier").as_pointer(),
            existing.as_pointer(),
        )
        self.assertEqual(len(other_obj.modifiers), 1)


if __name__ == "__main__":
    assert bpy.app.background, "Run these fixtures in a disposable headless process"
    assert bpy.app.version >= (5, 2, 0), bpy.app.version_string
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(GeometryNodesContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    assert result.wasSuccessful(), "Geometry Nodes contract failures"
    emit_ok(
        "geonodes-contract",
        tests=result.testsRun,
        blender=bpy.app.version_string,
        build_hash=bpy.app.build_hash.decode(),
        measurements=MEASUREMENTS,
        manufacture="NOT_REQUESTED",
    )
