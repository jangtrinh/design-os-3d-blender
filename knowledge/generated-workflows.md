# Generated Blender workflow playbook

Generated from catalog-config.json. Edit the config, then prepare/publish again.
Routing reviews are static source assessments, not API, physics or hardware certification.
Read only the workflow and conditional topic relevant to the task. Core owns execution.

## native-hard-surface

Dựng từ ảnh, silhouette, topology và body bo mềm bằng Blender-native.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/10-modeling/modeling-topology.md` — read-verify; SHA256 `1b24a3089c56d919a90b1717ce805592229479c03a3db9bc73697e3d4ddc3608`
- `knowledge/10-modeling/modifiers.md` — read-verify; SHA256 `88f4e06ffc4d5b9f74db1d00f2c0a95cee35cbe28a8248ab12b19dbf8f6a1ff1`

### Steps

- Lập fidelity contract và scene graph từ ảnh/đo đạc.
- Blockout theo tỷ lệ và camera trước khi bo mép.
- Dựng surface liên tục, tách bộ phận thật, rồi mới thêm detail.
- So reference và góc khuất sau từng pass; chuyển verdict về core.

### Gates

- Landmark và kích thước có sai số được khai báo.
- Không có phần critical chỉ tồn tại dưới dạng mô tả.
- Topology/transforms đạt predicate của đối tượng.
- Xem sheet cùng camera và ảnh 3/4; không dùng score tự chấm để hứa đúng 100%.

### Limitations

- Ảnh không xác định chính xác mặt khuất.
- Ví dụ drone có giả định riêng; không chạy builder vào scene hiện tại.

### Topic: python-adapter-review

When: Khi muốn reuse thư viện bpy boilerplate thay vì viết helper mới.

- `knowledge/00-foundations/python-agent-boilerplates.md` — read-verify; SHA256 `17ab56b12a636bbddab1c0bb4c0f954db77ef04e0f856b1b3449a91be4a17685`
  Caution: Registry claims verified, operator-free and standards-compliant behavior not established by actual modules. Static audits found missing bearing bores, sag, gear root/helical features, X-joint limits and physical thin-film optics; examples often test counts only. Bibliography is not certification; read module-specific cautions.
- `scripts/boilerplates/bp_core.py` — inspect-adapt; SHA256 `24716d4a714d7dceb25b7e039a51a3ab3ff69b5328ac21118f07ffb8390ca9fd`
  Caution: clean_scene deletes global objects; mode errors swallowed; named data removal can affect other users. Evaluated mesh cleanup handle is lost; substring socket resolution is ambiguous.
- `scripts/boilerplates/run_all_boilerplate_tests.py` — inspect-adapt; SHA256 `bce4755c515b1b9028e8a52c7c8d84eb86e6155e1a578e58db6424dee30e3f9f`
  Caution: PASS = last-line AGENT_OK from the sentinel shim, not a magic string. --list prints the generated registry. A module PASS proves it runs and asserts its own postconditions, not standards-correct constants.

**Steps**

- Chọn đúng module và đọc source thực; phân biệt snippet trong tài liệu với implementation.
- Khai báo input/scene ownership, units, effects và output; tạo candidate riêng.

**Gates**

- Kiểm API/runtime và assertions theo hành vi task, không dựa vào header verified.
- Đo actual geometry/state và xem output; giữ source gốc cho rollback.

**Limitations**

- clean_scene và thay node group/mesh có thể phá scene khác; không tự chạy vì được index.
- Knowledge routing không chứng nhận mass/inertia, bone roll hoặc physics.

## native-product-visualization

Vật liệu nhựa nhám, studio, camera và hình sản phẩm polish.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/20-shading/materials-pbr.md` — read-verify; SHA256 `e455cc41465700c56266f5d9652adae920972e941644b27085b2982ab3fa8705`
- `knowledge/30-lighting-render/lighting.md` — read-verify; SHA256 `f2b8db7610f1793524b248c9442b0f1a6951dfe5015faa35d35168eadedd894f`
- `knowledge/60-pipeline/product-viz-and-shots.md` — read-verify; SHA256 `0ae55d706fd7496ee8bf802784938a97cbb5e4383939b27c09d47e1f48a85f35`

### Steps

- Chốt mục tiêu shot, nền, texture scale và độ nhám bằng reference.
- Kiểm tra normals và bevel trước khi sửa shader.
- Introspect node sockets; dùng neutral/grazing light để tách lỗi hình và vật liệu.
- Render diagnostic cùng aspect rồi hoàn thiện shot.

### Gates

- Framing toàn bộ phần chuyển động hoặc object trong camera.
- Ánh sáng grazing không lộ shading defect hoặc surface rời.
- Xem material ở neutral và hero view.

### Limitations

- Shader đẹp không chứng minh bề mặt in thực tế.
- Turntable/preview helpers thay đổi scene; dùng bản candidate/process riêng.

### Topic: opaque-micro-surfaces

When: Khi nhựa/kim loại sai phản xạ hoặc cần grain/imperfection có kích thước thật.

- `research/blender-advanced-materials-shading/01-OPENPBR-PRINCIPLED-BSDF-SURFACE.md` — read-verify; SHA256 `7d05fab6bb6ed95d4201618835091fbbc0522dab79320c7ae0b0d78e4332fc46`
  Caution: Fac/Factor migration conflicts with sibling snippets; Principled/OpenPBR equivalence is unverified. Introspect sockets; avoid deprecated use_nodes.
- `research/blender-advanced-materials-shading/04-PROCEDURAL-MICRO-SURFACE-IMPERFECTIONS.md` — read-verify; SHA256 `e41d624f3506ba398bab369df5770050e4e52f0d708e860966a08a685b27fc2a`
  Caution: Snippet uses 3D Object Noise rather than the described triplanar blending. Bump unit/presets are not calibrated physical thickness.
- `scripts/boilerplates/bp_materials_pbr.py` — inspect-adapt; SHA256 `8b143fdc2ad121976ad8f5e555f648b4e49b6a3d9265ea5fdf9d25da2846e2cd`
  Caution: Named material deletion affects global data; missing sockets silently ignored; data.materials assignment can affect shared mesh users. No actual rendered self-test.
- `scripts/boilerplates/materials_shading/bp_mat_metals.py` — inspect-adapt; SHA256 `c8ec6e3e66989bac62cc2a22c02c902666a8368ed77145c938aaac04de6775e9`
  Caution: Missing sockets silently skipped; unknown preset becomes aluminum. Deletes same-name material. Two-node test does not verify values, links, tangent orientation or physical reflectance; Optional annotation unresolved.

**Steps**

- Tách metallic/IOR/roughness; chốt unit và scale texture.
- Chọn roughness, bump hay geometry theo chi tiết nhìn thấy.

**Gates**

- Introspect socket, material output và giá trị hữu hạn.
- So crop neutral/grazing: không seam, grain quá lớn hoặc normal lỗi.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: subsurface-optics

When: Khi vật liệu mỏng/dày cần truyền tán xạ như silicone, sáp hoặc da.

- `research/blender-advanced-materials-shading/02-SUBSURFACE-SCATTERING-RANDOM-WALK.md` — read-verify; SHA256 `5c5a282cf39829e75795c0cea0b1e82b090dd87539b5e2d6e02b0aabc74d269f`
  Caution: Absolute fidelity, dual-layer model and hardcoded Random Walk enum are unverified; radius ratios and dimensional scale need distinction.

**Steps**

- Chốt kích thước mesh, thickness và scale/radius tương đối.
- Kiểm enum thuật toán trên runtime trước dựng material.

**Gates**

- Bounds đúng unit; scale/radius được khai báo và hữu hạn.
- So backlit thin/thick views với reference, không lấy preset làm ngưỡng pass.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: thin-film-optics

When: Khi brief cần màu giao thoa đổi theo góc nhìn hoặc lớp phủ mỏng.

- `research/blender-advanced-materials-shading/03-THIN-FILM-INTERFERENCE-IRIDESCENCE.md` — read-verify; SHA256 `c3d776a5e078722e4ffabe65a173f91fe0378e633becd5f2129a64f77814b07f`
  Caution: Example connects Generated gradient to Coat Tint; it has no thickness/view-angle interference model. Spatial tint is not thin-film evidence.
- `scripts/boilerplates/materials_shading/bp_mat_thinfilm.py` — inspect-adapt; SHA256 `8d1870e3b0e47a3a09d7b26b8559f3764d63aee199b6ee29b8106d88cfb62e67`
  Caution: Facing-to-Base-Color ramp produces stylized angle coloration, not claimed Airy/thickness optics. Four stops despite five-stop comment; deletes material. Node count is not optical verification.

**Steps**

- Phân biệt tint theo vị trí và interference theo góc.
- Xác nhận thickness/IOR sockets hoặc mô hình thực sự dùng.

**Gates**

- Ghi đơn vị thickness và thông số IOR.
- So ít nhất hai camera/light angles; gradient cố định không chứng minh thin film.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: fiber-fabric-surfaces

When: Chỉ khi hair/fur, velvet, satin hoặc hướng weave nhìn rõ trong shot.

- `research/blender-advanced-materials-shading/05-PHYSICAL-HAIR-FABRIC-SHADING.md` — read-verify; SHA256 `83846c13bd7c1938d3616f0eb7c4a27bd86e7da6808402b8f589f5a9a31f9c7a`
  Caution: TRT bounce descriptions conflict; anisotropy/tangent node and shader enum claims need runtime inspection.

**Steps**

- Chọn strand shader hay surface sheen/anisotropy.
- Chốt tangent/UV và kích thước sợi trước chỉnh màu.

**Gates**

- Shader/enum/output/tangent hợp lệ.
- Xem hướng highlight, silhouette và frame liên tiếp để phát hiện crawling.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

## native-animation-rigging

Khớp, hand, pick/place tự nhiên, biên độ và explode/reassemble.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/40-animation/rigging-armature.md` — read-verify; SHA256 `dd5b6f0feebbfb0d58ae1aed6963261ed8e5f09e96f16ece6e031b8b88671889`
- `knowledge/40-animation/animation-fcurves.md` — read-verify; SHA256 `1d0bc0a7456fb7dc092737f0d8f92b4aecc6d954061ace4fc6e07b9feaa9df81`
- `knowledge/70-cad-precision-robotics/robotics-urdf-mechanisms.md` — read-verify; SHA256 `dbd386d203b4e9f109a874f873fada6fd12aaab46016e04ed948d8e25f95174e`
  Caution: Static audit: named hull block decimates only; inertia block formats values; diagonal positivity is incomplete. Verify frame conventions independently.
- `knowledge/60-pipeline/scene-organization.md` — read-verify; SHA256 `7ca6183bbf3160eb85aae0c7d2843c3fe8ca4c0ad5eccf80f56a3890aa8ca10a`

### Steps

- Chốt joint frame, limit, TCP, hand interface và sơ đồ cha-con.
- Định nghĩa task bằng tiếp cận → gắp → nhấc → chuyển → nhả; tách explode thành sequence lắp ráp.
- Blockout motion và pose biên; chuyển hand phải giữ continuity ở frame gắn/nhả.
- Screen contact theo phạm vi khai báo và xem animatic trước polish/render.

### Gates

- Joint axes/limits và hierarchy đúng trong local/world space.
- Không có bước nhảy transform ở grasp/release.
- Biên độ, dựng thẳng, thao tác phía sau và quay trục có frame evidence khi được yêu cầu.
- Đúng trình tự tháo fastener → rút phần, lắp lại khôi phục transform.
- Xem clip theo thời gian; ảnh pose không thay thế review chuyển động.

### Limitations

- Contact library hiện lấy mẫu raw rigid surfaces, không chứng minh continuous collision hay lực.
- Animation scripted attachment không chứng minh servo chịu tải.
- Ví dụ create-task-scene có mesh dùng chung; copy mesh trước khi sửa geometry.

### Topic: rig-spaces-ik-mechanisms

When: Khi cần armature scripting, IK/pole, piston, gear hoặc cable.

- `research/blender-rigging-skeleton-skinning/01-ARMATURE-MATRICES-BONE-TRANSFORMS.md` — read-verify; SHA256 `2ac1d81d4f2ed9f922406bd4baa6f63975a3f7e413b1ddf56b3801c1c43e93a0`
  Caution: Roll helper lacks zero-length/parallel guards; simplified hierarchy product is not a general evaluated constraint/inheritance transform.
- `research/blender-rigging-skeleton-skinning/02-INVERSE-KINEMATICS-SOLVERS-MATHEMATICS.md` — read-verify; SHA256 `ac3e18104c8ded749a2c9da37fd01194f743fc716edf449360ad016e7368fe29`
  Caution: Claimed exact pole calibration does not read rest-axis/roll and lacks straight/coincident guards; example uses a fixed pole angle.
- `research/blender-rigging-skeleton-skinning/04-PROCEDURAL-MECHANICAL-CHARACTER-RIGGING.md` — read-verify; SHA256 `3abab897422d4863c1459564e05c7045e58bd4465609e13c4be8ac51da6e8dad`
  Caution: Mutually constrained piston targets risk a dependency cycle; driver expression is not contact/load proof and spaces/axes need explicit validation.
- `scripts/generate-procedural-rig.py` — inspect-adapt; SHA256 `2f77cb8f2da4017204e0b6b107248b579e9ac8a51a4f5f11991228cf27e7ab32`
  Caution: Callable builder deletes all bpy.data objects. Fixed pole angle; no claimed exact calibration, pose sweep, mesh/limits/load/visual validation.
- `scripts/boilerplates/bp_rigging.py` — inspect-adapt; SHA256 `6978e0ef90b15f73881915785706c2e9f2a7fcd07c4c5974037a8f25efc46090`
  Caution: calculate_deterministic_roll always returns 0.0. Operator context is not restored, missing parents ignored, control bones remain deforming. No IK calibration.

**Steps**

- Chốt world/rest/pose spaces, axes, hierarchy và motion envelope.
- Guard bone zero/parallel reference; hiệu chỉnh pole theo evaluated pose.
- Tách anchor khỏi constrained parts; ghi stroke/ratio/space.

**Gates**

- Đo pivot và IK endpoint errors theo tolerance task.
- Kiểm alignment/stroke/ratio ở pose biên và attachment events.
- Xem sweep qua thẳng/đứng/gập; motion không chứng minh tải servo.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Adapter xóa mọi object khi gọi hàm dựng; chỉ inspect/adapt trong candidate riêng.

### Topic: skinning-modular-rigs

When: Khi mesh biến dạng, twist limbs hoặc dùng Rigify đã cài và được chọn.

- `research/blender-rigging-skeleton-skinning/03-DUAL-QUATERNION-SKINNING-LBS.md` — read-verify; SHA256 `fb2d01f4293bbf3c383009522ac757fee1fb43a50e3a3d6105ba93a6a58b381c`
  Caution: Unconditional volume-preservation claims conflict with bulging discussion. DQ property and weight normalization behavior need runtime/group-role checks.
- `research/blender-rigging-skeleton-skinning/05-RIGIFY-MODULAR-RIGGING-PIPELINE.md` — read-verify; SHA256 `41d49fef80d6ca98fd3dabc48e3b3b373edc4190be16d1815c98c36b271ac796`
  Caution: WGT taxonomy and ORG-hand matrix_world statement are unverified/inconsistent with pose-space guidance; preexisting rig name can be mistaken for output.

**Steps**

- So LBS/preserve-volume/helper bones với cùng poses.
- Phân biệt deform groups và masks; giữ metarig và xác định rig mới theo provenance.

**Gates**

- Weights hữu hạn, nonnegative; thiếu weight/sum sai bị phát hiện.
- Đo displacement khi IK/FK switch; xem bulging, sections và penetration.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Không tự cài extension; object tên rig và operator success chưa đủ.

### Topic: animation-curves-drivers

When: Khi cần tạo keyframes, driver hoặc turntable từ helper Python.

- `scripts/boilerplates/bp_animation.py` — inspect-adapt; SHA256 `55df506beb0fa0584968ce053e0a1f8c2915c14d19236b6c369aae5c4c1915cd`
  Caution: Indexed assignment is not general RNA array/path handling. Matching curves across all action slots/preexisting keys may be edited. Turntable has no Cycles loop; driver setup clears state.

**Steps**

- Xác định object/action/slot và RNA path được phép sửa; giữ animation cũ ngoài phạm vi.
- Adapt helper cho path/index thực tế; chỉ tạo driver trên property đã chọn.

**Gates**

- Đo giá trị tại keyframe và giữa keyframes, kiểm tra đúng action slot và không đổi curve ngoài scope.
- Kiểm tra endpoint/seam của loop và xem playback; một midpoint pass không chứng minh toàn chu kỳ.

**Limitations**

- Helper hiện tại có thể đổi nhiều action slots và xóa driver state; không chạy trực tiếp vào animation đang dùng.
- Self-test hiện có chỉ kiểm tra một midpoint, chưa chứng nhận loop hoặc chuyển động tự nhiên.

### Topic: robot-joint-frame-adapter

When: Khi reuse helper armature robot sáu khớp.

- `scripts/boilerplates/rigging_kinematics/bp_rig_robot_arm.py` — inspect-adapt; SHA256 `2ab750a637d9b7668cf0f6dcde63785b8f4cb109ecb820ec876cbe14f9a07651`
  Caution: X-axis joint limits unconfigured; local frames not aligned/verified against mechanical axes. Deletes named rig and mutates active mode/context. Six bones do not prove 6-DOF kinematics or limit behavior.

**Steps**

- Khai báo joint frames, hierarchy, rotation axes và limits theo cơ cấu thực.
- Align bone frames, khóa đúng các trục và cấu hình cả X/Y/Z trong candidate.

**Gates**

- Kiểm allowed/locked axes mọi joint; đối chiếu FK endpoint tại các pose có kết quả biết trước.
- Sweep giới hạn, đo attachment/clearance và xem chuyển động; count bones không thay kinematics.

**Limitations**

- Helper bỏ sót X-axis limits và chưa ánh xạ bone frames thành trục cơ khí.
- Chuyển động demo không chứng minh tải, torque, nhiệt hoặc chế tạo được.

### Topic: assembly-collision-staging

When: Khi quay phim lắp ráp/explode hoặc phát hiện các phần chờ lắp và đường bay đè lên nhau.

- `research/robotics-precision-cad/13-ROBOT-ARM-PIPELINE-LESSONS-LEARNED.md` — read-verify; SHA256 `22e2d4f0635550f1cedf9017c707e0bc116723cdac98b4c9ff7b08ebb29efb76`
  Caution: Lines39/46 unmeasured<1ms and universal0.20mm3 are not acceptance evidence; source-level units/evaluated geometry matter. Lines57-71 fixed120mm and perfectly jerk-free are overclaims: quintic third derivative endpoints=60. Lines82-94 collapsing unused cable points does not preserve length. Lines100-113 weights/packing are historical candidates, not general calibrated optimum; pair exclusions need named phase-bound justification. Actual Arm uses frame-sampled LINEAR F-curves: smooth quintic sample values do not establish a continuous C2 Blender trajectory.
- `scripts/boilerplates/cad_mechanics/bp_assembly_collision_audit.py` — inspect-adapt; SHA256 `e7af4179f5ff43404dbbbc791c688f01a93040e6c8d00b0ee8cd76a88aa433ad`
  Caution: Lines76-99 boolean copies raw mesh, ignores evaluated modifiers and scene scale_length; runtime reproduced false zero versus5999.95mm3 modifier clash and1e9 unit error. BVH cannot detect contained solids (0pairs with1000mm3). Lines147-149 total_steps=2 divides by zero; lines207-222 accepts oversize parts. No obstacle input or collision-free proof;0.20mm3 and zero-jerk claims are not universal.
- `.agents/skills/blender-agent-core/references/assembly-sequences.md` — read; SHA256 `9488f39087d6e1f3d5827ec03cc571b95979247ccac162a212df0b367c97aef7`

**Steps**

- Tạo unit manifest và dependency graph theo receiver, internal parts, retention, wires rồi covers.
- Tính staging riêng và kiểm world/projected gap; không chỉ kiểm pose cuối.
- Kiểm cả arrival và seat qua thời gian; chọn waypoint/axis từ geometry và chỉ miễn trừ named mate đúng phase.
- Xem animatic ngắn ở đoạn lỗi, cơ cấu tương tự và endpoint camera trước full render.

**Gates**

- Negative controls phải phát hiện waiting clash, clear-wait/blocked-transit, wrong phase exemption và solid containment.
- Kiểm evaluated modifiers và scene units; báo riêng surface flags, solid predicate và phạm vi sample.
- Camera giữ đúng chủ ý; quintic samples/LINEAR F-curves không được mô tả là zero jerk hoặc controller dynamics.

**Limitations**

- 120mm lift,0.20mm³ và tuyên bố tốc độ là case/unverified values, không là chuẩn chung.
- Audit adapter bỏ qua modifiers/scale trong Boolean; same-future-link blanket exclusions có thể giấu lỗi.
- Mating với actuator-visual và media PASS không giải quyết cơ khí, hardware/tool access hoặc tải.

## polymer-functional-print

In FDM nhựa, fit, inserts, tháo lắp, độ bền và vật liệu.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/60-pipeline/3d-printing.md` — read-verify; SHA256 `4bce69b0a198c8406475bf230fe66a35cbad19752bba22aa8ce24ad66e6d0eda`
- `knowledge/70-cad-precision-robotics/polymer-3dprinting-cad.md` — read-verify; SHA256 `eab55760bfe566860b330463a65a8802b1dd569354d05e85ce96e5af3febd69d`
  Caution: Static audit: bottom semicircle spans90deg; chamfer example creates cylinder; wall test is bbox. Verify actual geometry before reuse.
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`

### Steps

- Chốt printer/nozzle/vật liệu/orientation, kích thước và interfaces.
- Tách chi tiết theo đường lắp và access dụng cụ; chọn vít/insert theo drawing thật.
- Thiết kế coupon fit và phần chịu tải với dữ liệu vật liệu theo hướng in.
- Export candidate đúng unit và kiểm tra chính file xuất trước physical trial.

### Gates

- Manifold, scale và local wall thực sự được đo.
- Vít âm có chiều sâu, chiều dài ăn ren và tool access kiểm chứng.
- Clearance/fit xác nhận bằng coupon, không chỉ bbox.
- Tải/nhiệt/creep và sai lệch in có evidence trước release.

### Limitations

- Mesh pass hoặc hình đẹp không đủ gọi printing-ready chịu lực.
- Helper tolerances hiện chỉ overhang/bbox; không có local-wall hay clearance test.
- Research là synthesis chưa được chứng nhận; kiểm tra datasheet/standard hiện hành khi dùng số.

### Topic: advanced-deposition-process

When: Khi high-flow, nonplanar hoặc LSAM được yêu cầu; chọn đúng nhánh.

- `research/polymer-additive-manufacturing-advanced/01-POLYMER-EXTRUSION-RHEOLOGY-HOTENDS.md` — read-verify; SHA256 `1be0673cd2e35dae58d243c1c2ef0a5ae84cebcd2367ed1d2d3896cb3a4ab13e`
  Caution: Pressure-advance example mixes displacement with seconds*acceleration; resolve quantity/units before control or firmware use.
- `research/polymer-additive-manufacturing-advanced/03-NON-PLANAR-SLICING-STRESS-ALIGNMENT.md` — read-verify; SHA256 `ad6b19112a6f25f67bd8c129a58cbf5571f1dfdaa42c5435dac64aa8e5aadeb7`
  Caution: Streamline loop never advances current_vert, repeatedly appending the same next point; no field read, reprojection or collision solver.
- `research/polymer-additive-manufacturing-advanced/05-LARGE-FORMAT-LSAM-PELLET-PRINTING.md` — read-verify; SHA256 `8458936f98c3796d58ae45cf9eab428952c532a197d069b085f9f7a0d059d0b5`
  Caution: No usable tmax calibration; total strain energy compared to fracture toughness without crack geometry/area; stock allowances unqualified.

**Steps**

- Chốt hardware envelope/flow/thermal hoặc toolpath/finishing constraints.

**Gates**

- Kiểm path có tiến triển và toolhead envelope; calibration/coupon thật.
- Không xuất G-code hay điều khiển máy chỉ từ research.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: polymer-selection

When: Khi chưa chốt vật liệu hoặc cần đánh giá isotropy/temperature limits.

- `research/3d-printing-polymer-engineering/01-POLYMER-MATERIALS-TAXONOMY.md` — read-verify; SHA256 `593b87a33135aa9734fb6e80857794eee902a539cc3a16a2c487fbd43483de57`
  Caution: Source has conflicting PETG crystallinity labels and absolute carbon-fiber warping claim; bibliography is not verification.

**Steps**

- Dùng taxonomy để đặt câu hỏi; chọn grade/process từ datasheet và coupon.

**Gates**

- Không dùng kết luận PETG/carbon-fiber tuyệt đối; dữ liệu phải cùng process/orientation.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: print-boss-cutouts

When: Khi dựng boss heat-set insert hoặc lỗ tự đỡ cho FDM.

- `scripts/boilerplates/dfam_3dprint/bp_insert_boss.py` — inspect-adapt; SHA256 `0bb053452708229c3a3a7f85e53a20eb32b28b3865d30f9d7b33ee045e87992b`
  Caution: 8-degree taper/minimum-wall claims not implemented; separate pillar/cutter are not assembled; unknown size falls back to M3.
- `scripts/boilerplates/dfam_3dprint/bp_teardrop_holes.py` — inspect-adapt; SHA256 `9e2919971fb179490cae5b3b8344b5a28b01c3abc97e30a65907e4c81691c219`
  Caution: Parameterized cutter lacks input guards and print validation; face count cannot establish self-support or retained bore dimensions.

**Steps**

- Chọn insert drawing, material/process/build orientation và coupon fit.
- Dựng boss với cutter thực, kiểm taper theo chiều sâu và trục lỗ trước export.

**Gates**

- Đo hole/taper/minimum local wall sau subtraction, không lấy parameter name làm bằng chứng.
- In coupon kiểm fit/insertion/pull-out hoặc support/bore retention theo chức năng.

**Limitations**

- Helper chưa ghép pillar/cutter; taper và wall claims không được enforce.
- Self-support phụ thuộc process/orientation; face count không đủ.

### Topic: plate-nesting-screen

When: Khi dùng heuristic orientation và guillotine packing để xếp các part lên plate.

- `research/robotics-precision-cad/13-ROBOT-ARM-PIPELINE-LESSONS-LEARNED.md` — read-verify; SHA256 `22e2d4f0635550f1cedf9017c707e0bc116723cdac98b4c9ff7b08ebb29efb76`
  Caution: Lines39/46 unmeasured<1ms and universal0.20mm3 are not acceptance evidence; source-level units/evaluated geometry matter. Lines57-71 fixed120mm and perfectly jerk-free are overclaims: quintic third derivative endpoints=60. Lines82-94 collapsing unused cable points does not preserve length. Lines100-113 weights/packing are historical candidates, not general calibrated optimum; pair exclusions need named phase-bound justification. Actual Arm uses frame-sampled LINEAR F-curves: smooth quintic sample values do not establish a continuous C2 Blender trajectory.
- `scripts/boilerplates/cad_mechanics/bp_assembly_collision_audit.py` — inspect-adapt; SHA256 `e7af4179f5ff43404dbbbc791c688f01a93040e6c8d00b0ee8cd76a88aa433ad`
  Caution: Lines76-99 boolean copies raw mesh, ignores evaluated modifiers and scene scale_length; runtime reproduced false zero versus5999.95mm3 modifier clash and1e9 unit error. BVH cannot detect contained solids (0pairs with1000mm3). Lines147-149 total_steps=2 divides by zero; lines207-222 accepts oversize parts. No obstacle input or collision-free proof;0.20mm3 and zero-jerk claims are not universal.

**Steps**

- Chọn vật liệu/process, đơn vị, bed usable area, margin và khoảng cách.
- Thử orientation theo support, tiếp xúc bed, trục tải/anisotropy và tính tháo support.
- Kiểm tất cả part sau packing bằng transform thực; từ chối part không vừa trước khi thêm plate.

**Gates**

- Oversize fixture phải bị từ chối; không nhận rectangle âm, part ra ngoài biên hoặc trùng/thiếu inventory.
- Re-import STL/slicer bằng đúng scale; heuristic score không thay đánh giá support và fit thực.

**Limitations**

- Packer hiện nhận oversize part khi mở plate mới; không dùng kết quả chưa kiểm làm print-ready.
- Các weights/margin trong source là ví dụ lịch sử, không có bằng chứng optimal/calibrated chung.

## precision-assembly-metrology

CAD chính xác, datum, dung sai chuỗi và tháo lắp.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/cad-precision-modeling.md` — read-verify; SHA256 `bc171eb925df0f536a5745c294496268eb8a31464c2044439d2a688051fc51f6`
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`

### Steps

- Chốt datum/unit và danh sách interface.
- Dùng drawing phần cứng thật để dựng nominal geometry.
- Tính tolerance stack với phân bố/giả định ghi rõ.
- Thiết kế đường lắp, access dụng cụ và phương pháp đo.

### Gates

- Drawing và mesh cùng unit/datum/revision.
- Vùng fit không dựa vào kích thước overall bbox.
- Có đo hoặc coupon cho kích thước critical.

### Limitations

- Blender mesh không tự cung cấp B-rep/GD&T hoặc tolerance solver.
- Inertia helper chưa áp object scale/scene scale; không dùng số trực tiếp khi transform khác identity.

### Topic: compliant-tendon-motion

When: Khi cần flexure, cable-driven hand hoặc remote actuation.

- `research/robotics-precision-cad/07-COMPLIANT-MECHANISMS-FLEXURES.md` — read-verify; SHA256 `6bb4eb0ab90270fc7a5d4b2c47691bd6d2e0a1abad02ad7890e2d9b3f90c2f27`
  Caution: Stiffness expression has suspect units; zero/infinite-life claims need material/duty evidence, not animation.
- `research/robotics-precision-cad/09-CABLE-TENDON-TRANSMISSIONS.md` — read-verify; SHA256 `3ce580cbbf877b2e96963a83e8d63cbb30cfe11eada9050d8f8d9b63ccdba0ec`
  Caution: Zero backlash/creep and universal pulley ratios unverified; actual cable, pretension, bend life and termination matter.
- `scripts/boilerplates/cad_mechanics/bp_flexures.py` — inspect-adapt; SHA256 `362939358115d1d70e38c2e452f5cdc4d4453947c21cb3344d5be5187a398f4e`
  Caution: BMesh flexure function returns uncut cube; object variant bakes booleans with implicit operation; compliance validity and web geometry ungated.
- `scripts/boilerplates/cad_mechanics/bp_springs.py` — inspect-adapt; SHA256 `2773e4640a6919adfaec02d0d272095c0baac78df59d4cc6a120e55d7386ea0b`
  Caution: Helix lacks ground ends; single washer only; axial versus normal thickness differs; no self-contact, load or fatigue gate.
- `scripts/boilerplates/dfam_3dprint/bp_snap_fits.py` — inspect-adapt; SHA256 `1af01f09b98946ed9da8068e55e75383caa62d0a36dfecaa2780998c3e7bc488`
  Caution: Taper formula differs from implementation; strain table is unverified; no mating/root-fillet/engagement check; polygon count only.

**Steps**

- Chốt travel/stiffness/parasitic motion, routing/pretension/tension-only constraints.

**Gates**

- Đo neck/strain, clearance qua envelope và bend/tension limits.
- Kiểm fatigue/creep/hysteresis theo vật liệu/duty thực.
- Đo neck/root/thickness, snap engagement và coil clearance; kiểm thực dưới process/duty phù hợp.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Geometry demo có thể thiếu notch, mating part hoặc ground ends; face count không chứng nhận compliant performance.

### Topic: precision-material-tessellation

When: Khi bore/tolerance/finish/heat-treatment cần budget định lượng.

- `research/robotics-precision-cad/04-CAD-VS-POLY-BLENDER-BRIDGE.md` — read-verify; SHA256 `c2aec3777fa475e9d3e285c4b18bcc86ca918f3bf78dcc03f1ea19fa8860fe49`
  Caution: Radial sagitta is not directly a diameter/H7 budget; STEP does not by itself supply GD&T. No CAD addon activation follows.
- `research/mechanical-engineering-foundations/03-MATERIALS-METALLURGY-HEAT-TREATMENT.md` — read-verify; SHA256 `73724dbe3b68749c29462f8093f84a183dc5fc8df897ecdbff16cc2a8a648f13`
  Caution: Grade/process dependence incomplete; zero-distortion/uniform-thickness/zero-dimension-change statements are not unconditional process guarantees.
- `scripts/boilerplates/bp_cad_robotics.py` — inspect-adapt; SHA256 `f4cefba47a6540da6fd19de46eb9cee9998c3065d9f974a2dcde69498435b566`
  Caution: Advertised inertia tensor is not computed/returned. Mass uses local evaluated coordinates without object/scene scale or validity guards. Counterbore concatenates capped cylinders, not a boolean union. Hull ignores modifiers.

**Steps**

- Tách nominal dimensions, tessellation error, process allowance và material grade.

**Gates**

- Phân biệt radial/diametral error, unit và export mesh.
- Đối chiếu grade/temper/finish với drawing/data có nguồn.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Không suy GD&T từ STEP export hoặc tự cài CAD addon.

### Topic: hardware-interface-geometry

When: Khi dùng helper ổ bi, nut/washer, keyway hoặc gland làm interface cơ khí.

- `scripts/boilerplates/cad_mechanics/bp_ball_bearing.py` — inspect-adapt; SHA256 `8383db28f846246672060a6ea553a3314bc9525d7115b2cdabb08cb203b99b4d`
  Caution: Inner/outer rings are overlapping solid cylinders; bores/raceways absent; demo checks ball face count only.
- `scripts/boilerplates/cad_mechanics/bp_fasteners_iso.py` — inspect-adapt; SHA256 `ad3513d1e7e4d031db513de349827e8e4a78bc8233b4ec3d7f59ec851adb6613`
  Caution: Only nut/washer exist; nut bore is hexagonal and unthreaded; unknown size silently becomes M6; face-count checks only.
- `scripts/boilerplates/cad_mechanics/bp_oring_glands.py` — inspect-adapt; SHA256 `75bd44c7c57fd6757e4227f669abb368f3a877fd44607fe29c1efbf5f22e9dbf`
  Caution: Static face gland only; claimed squeeze/fill limits not enforced; no seal-performance or geometry checks.
- `scripts/boilerplates/cad_mechanics/bp_shaft_couplings.py` — inspect-adapt; SHA256 `ffb7d0044c8413a575b80e09470b2e8a9a4adfd2261d516179dc42de93853fe6`
  Caution: Box/cylinder composites are not unioned; range fallback can silently choose wrong key; no spline/coupling or fit verification.

**Steps**

- Chọn drawing phần cứng cụ thể, đơn vị và dung sai; từ chối fallback kích thước âm thầm.
- Dựng/cắt đủ lỗ, rãnh và mặt tiếp xúc trong candidate; kiểm evaluated mesh sau union.

**Gates**

- Đo bore/raceway/keyway và fit ở section; không chấp nhận solid cylinder thay ring.
- Kiểm đúng local dimensions, squeeze/fill và topology; xác minh lực/mòn/seal bằng dữ liệu hoặc thử thực riêng.

**Limitations**

- Tên tiêu chuẩn trong header và số mặt không chứng minh tương thích phần cứng.
- Một số helper hiện thiếu bores/raceways/threads hoặc boolean union; chưa dùng làm chi tiết sản xuất trực tiếp.

### Topic: industrial-connector-panel-packaging

When: Khi dựng connector, panel cutout, terminal và khoảng thao tác ở hộp điều khiển.

- `knowledge/70-cad-precision-robotics/industrial-connectors-wire-harness.md` — read-verify; SHA256 `8835efc6e74d6ba2c45d0a0f0b2fc9b75e3b10d39a2af967511598b6a74fae1c`
  Caution: Lines36-49/154-158 present universal flats, bend and EMC spacing; treat as unverified task-specific inputs. Lines109-130 accept min_bend_radius but never use it; no curvature/strain-relief enforcement. Dimensions and connector coding require selected part drawings.
- `research/industrial-wiring-harness-packaging/01-INDUSTRIAL-BUS-PHYSICAL-LAYERS-PINOUTS.md` — read-verify; SHA256 `0de4f110d19f68c8b2fa83b1942970b058878e86f220e6aea2874fb11028d593`
  Caution: Lines51-60 collapse protocols/speeds/pinouts; A/B labels and terminal numbering require selected endpoint pin-view verification. Line73 says A>B while schematic pulls B high. HART loop resistance shares a table column with cable characteristic impedance. Lines153-159 mating/standoff envelopes are not universal dimensions.
- `research/industrial-wiring-harness-packaging/02-CONNECTOR-DIMENSIONAL-STANDARDS-PANEL-CUTOUTS.md` — read-verify; SHA256 `9bfd07b3b14ff26bc4ce263638dd428616117fb211398719b2c844e9284140b7`
  Caution: Lines80-82 RJ45 bayonet dimensions conflict with robotics source12; line131 DT04-4P dimensions conflict with extended boilerplate. Lines139-146 pitch alone does not establish terminal ratings, cutout or access. Choose actual housing/contact/terminal revision and drawings before machining.
- `scripts/boilerplates/cad_mechanics/bp_connectors_wiring.py` — inspect-adapt; SHA256 `c562ffea81232edf20bb2236280cc06dc96f955f8796e2ac5be368e527850ce2`
  Caution: Lines132-157 saddle is a solid8vertex cube: slot_width/slot_height unused. Lines160-186 AUTO Bezier does not enforce curvature, arc length or strain relief and leaves end caps disabled; runtime accepted0.370mm bend radius for7mm cable. D-cut default dimensions/manifold smoke passed; standard/fit claim still unverified.
- `scripts/boilerplates/cad_mechanics/bp_connectors_extended.py` — inspect-adapt; SHA256 `e6799635a8f6275cb8ecd5aeea4c3192ca99720f3e315bcf801f134f79650a8e`
  Caution: Lines142-189 thread_size changes name only; panel_thickness ignored, no real thread/membrane/vent. Runtime3disconnected solids. DT04 cutter shape differs from source02 and own documented tab size. EMC/IP compliance claims are unverified; cutter defaults require selected supplier drawing plus boolean/section checks.

**Steps**

- Chốt mã connector/contact, pin-view, giao thức, cáp và drawing cụ thể; ghi chỗ nguồn mâu thuẫn.
- Inspect/adapt cutter trong scene riêng; đo section, chiều dày panel, mặt gá và tool approach.
- Khai báo pin-to-pin wire list, terminal/crimp và khoảng lắp tháo.

**Gates**

- Thay tham số phải đổi đúng hình học; kiểm kích thước, topology và Boolean thật sau cắt.
- D-cut smoke không thay fit coupon; chiều pin và drawing phiên bản phải khớp phần cứng được chọn.

**Limitations**

- Bảng pinout/kích thước là synthesis chưa kiểm định; không lấy pitch hoặc tên ISO làm bảo đảm tương thích.
- Saddle hiện là cube không có slot; vent thiếu thread/membrane và bỏ qua tham số; cần sửa adapter trước sản xuất.

### Topic: enclosure-sealing-emc-harness

When: Khi packaging hộp điều khiển cần sealing, nhiệt, shield hoặc tài liệu harness.

- `research/industrial-wiring-harness-packaging/04-INGRESS-PROTECTION-SEALING-THERMAL-RELIEF.md` — read-verify; SHA256 `64e62ff9b34de40a3bee4a3f1adfaa5664b2ea58e673147af981762135390d44`
  Caution: Lines63-64 bolt pitch heuristic is not seal qualification. Lines87-89 use cold-temperature denominator while naming cooling vacuum, without matching initial-pressure reference. Lines96/117 universal membrane mandate and WEP values are unverified. IP rating requires assembled-product test, not CAD vent geometry.
- `research/industrial-wiring-harness-packaging/05-EMC-GROUNDING-SHIELDING-HARNESS-MANUFACTURING.md` — read-verify; SHA256 `0187d9f805ba6d158e2e475df576dfa7c692abe33d7088e1d4e85e537b9c7124`
  Caution: Production Architecture Specification label is not certification. Shield transfer impedance, universal segregation/crimp/pull-force and heat-shrink IP claims are unverified. Separation categories conflict with KB/source12. Pin-to-pin wire list must identify actual contact, wire, terminal/crimp tool and drawing revisions; formboard arc length does not prove strain relief.
- `scripts/boilerplates/cad_mechanics/bp_connectors_extended.py` — inspect-adapt; SHA256 `e6799635a8f6275cb8ecd5aeea4c3192ca99720f3e315bcf801f134f79650a8e`
  Caution: Lines142-189 thread_size changes name only; panel_thickness ignored, no real thread/membrane/vent. Runtime3disconnected solids. DT04 cutter shape differs from source02 and own documented tab size. EMC/IP compliance claims are unverified; cutter defaults require selected supplier drawing plus boolean/section checks.

**Steps**

- Tách yêu cầu môi trường thực khỏi ví dụ công nghiệp; chọn seal/vent theo đúng phần cứng.
- Khai báo reference pressure/temperature và mô hình; kiểm tính nhất quán đơn vị và giả định.
- Lập wire list, route, shield termination, crimp/tool và kiểm tra lắp ráp.

**Gates**

- Kiểm section/gland/mating và luồng thoát nhiệt thực; mô hình vent phải có đặc tính được yêu cầu.
- Không công bố IP/EMC từ mesh: cần phương pháp thử và dữ liệu phù hợp cho cụm đã lắp.

**Limitations**

- Các ngưỡng bolt spacing, membrane, EMC spacing và pull force trong nguồn chưa được xác nhận cho target.
- Boilerplate vent bỏ qua kích thước ren/panel; hình thức kín hoặc gọn không xác nhận chức năng.

## mechanisms-transmissions

Bánh răng, giảm tốc, trục/ổ, tải giữ lâu và truyền động.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/gears-transmission-modeling.md` — read-verify; SHA256 `1975a92284d94b2b84cf09707c7594935f3bde34bf448b6624efb37a415dbe86`
  Caution: Static audit: root radius and tolerance arguments unused; root fillets not constructed.
- `knowledge/70-cad-precision-robotics/fasteners-seals-mechanics.md` — read-verify; SHA256 `870ac87843291f7991ff38c0d804fff817d743fac5e123b2c4ad667da68dfaa0`
- `knowledge/70-cad-precision-robotics/cad-precision-modeling.md` — read-verify; SHA256 `bc171eb925df0f536a5745c294496268eb8a31464c2044439d2a688051fc51f6`

### Steps

- Chốt tải, reach, duty, tốc độ, hiệu suất và actuator envelope.
- Tính worst-case moment gồm link, hand, payload; phân biệt continuous với stall torque.
- Dựng reduction, bearings, fastener và cable space theo interface thật.
- Kiểm backlash/va chạm/cường độ/nhiệt rồi xác nhận bằng bench test.

### Gates

- Mass/CoM/inertia gắn unit và geometry revision.
- Mô-men liên tục có margin theo yêu cầu, không lấy stall rating làm giữ lâu.
- Gear profile/root/contact và bearing load được kiểm tra theo drawing/calculation.
- Giữ trạng thái BLOCKED khi thông số actuator hoặc test thực còn thiếu.

### Limitations

- Gear KB snippet chưa có root fillet như mô tả; tolerance tham số chưa thực hiện.
- Arm 250 g giữ nhiều phút đang BLOCKED; không chuyển sang PASS từ animation.

### Topic: contact-wear-sealing

When: Khi có wear/leakage/bearing/bushing/seal duty được yêu cầu.

- `research/advanced-tribology-contact-mechanics/01-HERTZIAN-CONTACT-STRESS.md` — read-verify; SHA256 `345be386539b7a407d38d5759f2cf363530b59ac69f86d5f69b837baebafc0c2`
  Caution: Source mixes subsurface depth values across line/point contact; resolve regime and equations before calculation.
- `research/advanced-tribology-contact-mechanics/02-TRIBOLOGY-LUBRICATION-STRIBECK.md` — read-verify; SHA256 `38b7690b920d9c43be0c88082e2b77fcd8a515424044318a14f7e4c59a460496`
  Caution: Quantity called dimensionless reduces to length with declared units; zero-wear and360deg purge prescriptions are not general rules.
- `research/polymer-additive-manufacturing-advanced/04-POLYMER-TRIBOLOGY-GEARS-BUSHINGS.md` — read-verify; SHA256 `e39d9245c95345dc96524d23523f7df90f4ea7b4e14852bb4030f5191a7589ca`
  Caution: PV/process tables and resistance units require source data; flash-temperature expression contains undefined Wbt.
- `research/mechanical-engineering-foundations/04-FLUID-POWER-SEALS-O-RINGS.md` — read-verify; SHA256 `34d279fbc34d937346a4ed6f509aba7e267c80e69094eba6dfa42a26a058f175`
  Caution: Fraction/percent notation changes; verify selected gland, seal, fluid, temperature and tolerance against actual drawing.

**Steps**

- Ghi material pair, contact regime, load/speed/finish/lubrication/seal duty.

**Gates**

- Kiểm đơn vị/phương trình đúng contact regime và data phần cứng.
- Đo local fit; wear/temperature/leak thử thực trước performance claim.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: cycloid-profile-kinematics

When: Chỉ khi cycloidal reduction đã được chọn.

- `research/advanced-tribology-contact-mechanics/03-CYCLOIDAL-SPEED-REDUCERS-MATHEMATICS.md` — read-verify; SHA256 `ccbc9d27cd6404d81249e90b47d522b9180bc8f57c79642b814d4a94b19e481d`
  Caution: Cusping/undercut criterion and universal coefficient range lack derivation; K1<1 alone is not manufacturability proof.
- `scripts/generate-cycloid-drive.py` — inspect-adapt; SHA256 `1364eb417d11e4a4a189864b1a0bc126ed5cf56dc7ded9e8484bf828edd018e8`
  Caution: main deletes all objects; fixed profile sampling, incomplete drive/housing and no ratio/contact/manifold checks. Raw count/success text is not acceptance.

**Steps**

- Chốt pins/lobes/eccentricity/phase/output holes/bearings.
- Dựng candidate riêng; adapter chỉ là nguồn tham khảo.

**Gates**

- Kiểm profile convergence, self-intersection, bores/walls trên evaluated mesh.
- Sweep vòng input theo contract; kiểm clearance và output ratio.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Generator xóa scene, không tạo toàn bộ drive hay tự chứng minh ratio/manufacture.

### Topic: actuator-duty-thermal

When: Khi payload, giữ lâu hoặc chu kỳ lặp quyết định actuator.

- `research/advanced-tribology-contact-mechanics/04-ACTUATOR-INERTIA-MATCHING-THERMAL.md` — read-verify; SHA256 `8cfcba1b7133177b918f05c264e91ba79aeef71b7a43c32919b384d96a76b5da`
  Caution: Optimal ratio equation needs dimensional review; stated Cth*Rth gives25–300seconds, not5–15minutes. Pulse/peak-current envelope unvalidated.

**Steps**

- Lập torque/speed trajectory, mass/inertia revision và mô hình điện/nhiệt.

**Gates**

- Kiểm đơn vị, nguồn motor/driver, continuous và peak limits riêng.
- Kiểm thermal response bằng duty thử thực trước loaded-hold claim.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: parametric-gear-profile

When: Khi dựng spur gear từ profile involute bằng BMesh.

- `scripts/boilerplates/cad_mechanics/bp_involute_gear.py` — inspect-adapt; SHA256 `5af44abbd8678d9e1a5e1eea10153a1fa06c5029c4a1637bdb9753104ae2ade4`
  Caution: Deletes same-name object/shared mesh; no helical/root-fillet implementation; flank phase/root geometry need validation; face count is not gear correctness.

**Steps**

- Chốt module, số răng, pressure angle, backlash và chiều rộng theo tải/drawing.
- Kiểm công thức flank/pitch/root; tạo mesh candidate trước khi gắn vào truyền động.

**Gates**

- Đo pitch tooth thickness và sai số profile ở nhiều sample counts; kiểm root, bore, manifold/self-intersection.
- Sweep cặp bánh răng; đo ratio/interference/clearance; kiểm tải và vật liệu riêng.

**Limitations**

- Không có helical/root fillet như header; geometry sample chưa chứng minh gear đúng.

## robotics-links-simulation

Robot links, URDF, coordinate frames, collision và inertia.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/70-cad-precision-robotics/robotics-urdf-mechanisms.md` — read-verify; SHA256 `dbd386d203b4e9f109a874f873fada6fd12aaab46016e04ed948d8e25f95174e`
  Caution: Static audit: named hull block decimates only; inertia block formats values; diagonal positivity is incomplete. Verify frame conventions independently.
- `knowledge/40-animation/rigging-armature.md` — read-verify; SHA256 `dd5b6f0feebbfb0d58ae1aed6963261ed8e5f09e96f16ece6e031b8b88671889`
- `knowledge/60-pipeline/export-interchange.md` — read-verify; SHA256 `54a6aba3dcdb747009017f27b30d874ac5453f4d137d4ec6186b036c37d23c0c`

### Steps

- Chốt hệ tọa độ từng link/joint và đơn vị SI ở boundary export.
- Tách visual, collision, physical properties; kiểm mass/CoM/inertia bằng phương pháp đã validate.
- Export articulation và import vào target simulator.
- So pose/pivot/limit, collision shape và physical response với kỳ vọng.

### Gates

- Không áp rotation cố định chỉ từ tên phần mềm; verify basis vector và forward axis.
- Collision shape được kiểm lồi/đơn giản thật, decimation không chứng minh convex.
- Inertia tensor đối xứng và positive definite bằng eigenvalues hoặc principal minors.
- Round-trip đúng link hierarchy, scale, limits; simulator test được lưu.

### Limitations

- Snippet URDF hiện format inertia truyền vào, không tính inertia.
- Collision và tensor snippets trong KB chưa đủ predicate cần thiết.
- Không chạy/install simulator chỉ vì đọc research.

### Topic: dynamic-harness-routing

When: Khi đi dây từ controller qua khớp chuyển động hoặc thiết kế carrier/drag chain.

- `knowledge/70-cad-precision-robotics/industrial-connectors-wire-harness.md` — read-verify; SHA256 `8835efc6e74d6ba2c45d0a0f0b2fc9b75e3b10d39a2af967511598b6a74fae1c`
  Caution: Lines36-49/154-158 present universal flats, bend and EMC spacing; treat as unverified task-specific inputs. Lines109-130 accept min_bend_radius but never use it; no curvature/strain-relief enforcement. Dimensions and connector coding require selected part drawings.
- `research/industrial-wiring-harness-packaging/03-CABLE-MECHANICS-FLEX-LIFE-DRAG-CHAINS.md` — read-verify; SHA256 `9505da833fe0db557b3385b4c94251829a5e5926ce37c86ed8987d98049256c6`
  Caution: Lines23-26 conductor class is not cycle-life qualification; generic radius, torsion/free-length and20-50N retraction values are unverified for target hardware. Chain neutral-axis layout, cable length/bend/torsion and endpoint strain relief require per-pose checks; no physical life proof.
- `research/robotics-precision-cad/12-INDUSTRIAL-WIRING-CONNECTORS-HARNESS-ROUTING.md` — read-verify; SHA256 `6ac53feff1fdfe7a1f10cb7e12875c130f24ecfb966357f6c80a6ca74754ed04`
  Caution: Generic cutout offsets, connector dimensions, EMC categories and breather mandate are unverified; source02 differs for RJ45 bayonet dimensions and source01 differs for PROFIBUS termination. Do not infer suitable terminal/contact selection from protocol or pitch; verify selected part and cable specification.
- `scripts/boilerplates/cad_mechanics/bp_cable_dragchain.py` — inspect-adapt; SHA256 `d1a95bc9acd1f7473c037a5716cb53dd9214ea38c865cb25c4489e972c79d978`
  Caution: Lines34-35 silently cap bend radius below own required minimum; negative dimensions yield negative link count. Lines71-76 production socket/stop claims exceed construction: runtime9disconnected primitive solids, no sockets/stops/union. Assembly poses are visual candidates; rated cable radius/torsion, link interference, fastening and endpoint strain relief unverified.

**Steps**

- Chốt endpoint, cáp thực, connector, giới hạn uốn/xoắn và chiều dài tự do.
- Dựng route theo từng joint pose; tính chiều dài, curvature và khoảng tránh cơ cấu.
- Thiết kế retention/strain relief; kiểm link socket, stop và fastening trước khi gọi chain là hoạt động được.

**Gates**

- Từ chối input âm và silent radius cap; đo min radius/length/torsion tại pose biên với units rõ.
- Kiểm giao thoa chain và tính kết nối của từng link; kiểm thực với cáp/link đã chọn trước tuyên bố cycle life.

**Limitations**

- Curve reveal không bảo toàn chiều dài hoặc chứng minh đi dây thật.
- Boilerplate hiện tạo primitive rời và thiếu socket/stop; kiểu conductor không chứng nhận flex life.

## render-export-delivery

Video không phụ đề, render batch, encode và export/re-import.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/30-lighting-render/render-engines.md` — read-verify; SHA256 `a241aa51cbfffb4bd67aca186e5605e158049a88e2fac1d569de308fa44d8dfb`
- `knowledge/30-lighting-render/compositing-output.md` — read-verify; SHA256 `ce19c33464e1ea8ef58cc5c686406eb3d227272c4cc1feb98a4c361e1c42f2ab`
- `knowledge/60-pipeline/export-interchange.md` — read-verify; SHA256 `54a6aba3dcdb747009017f27b30d874ac5453f4d137d4ec6186b036c37d23c0c`

### Steps

- Chốt source hash, camera, frame range, fps, aspect và yêu cầu overlay/audio.
- Đo render profile trên frame đại diện trong process riêng.
- Render raw frames với output/range riêng và kiểm đủ frame.
- Encode/decode hoặc export/re-import đúng artifact; xem cả nhịp chuyển động.

### Gates

- Python errors phải trả nonzero và có postcondition; shell exit 0 chưa đủ.
- Frame missing/corrupt/mixed revision bị loại trước encode.
- Duration/fps/resolution/range đúng brief; video không text khi user yêu cầu.
- Review đúng file đã hash; kỹ thuật và chất lượng visual ghi riêng.

### Limitations

- Headless wrapper chưa explicit Python-error exit; dùng CLI explicit theo core recipe.
- Ví dụ video chứa fixed arm path/24fps/720frames; phải chuyển contract theo task.
- Không resume dựa vào file tồn tại; stale-evidence enforcement E1–E5 còn backlog.

### Topic: renderer-diagnostics

When: Khi cần đo CPU/Metal, sampling hoặc so giới hạn renderer.

- `research/blender-rendering-deep-dive/01-PATH-TRACING-CYCLES-ARCHITECTURE.md` — read-verify; SHA256 `1ca697b7e8199900a9c8b6d070d63efa52b249878bfdc8f240038ddceb03c4de`
  Caution: GPU-only preset is not measured device selection; backend is not enabled by device assignment alone. Bounce/clamping no-bias and95% claims unverified.
- `research/blender-rendering-deep-dive/02-EEVEE-NEXT-REALTIME-RENDER-PIPELINE.md` — read-verify; SHA256 `44c0b09d2b7ecb81e4f72f83e9409234007ef6e884d504a444b7285ee1f2896b`
  Caution: Legacy engine identifier and universal Metal mandate conflict with current project runtime-introspection and measured CPU/Metal policy.
- `scripts/boilerplates/bp_render_camera.py` — inspect-adapt; SHA256 `a0462c9844057b058c04e855b47d26c21be2513adb242a74288e9b9ae20e90e2`
  Caution: GPU backend chosen by enumerating get_devices_for_type per backend (returns METAL on this Mac); never gates on the empty compute_device_type enum. Changes backend preferences and deletes named camera/lights in its self-test.

**Steps**

- Benchmark frame đại diện cùng resolution/source; lựa chọn device theo phép đo.
- Giữ Cycles batch theo policy; EEVEE chỉ khi capability được xác nhận.

**Gates**

- Engine/device thực sự enabled, timing và settings được ghi.
- So noise/detail và reflection artifacts; tốc độ không thay chất lượng.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Không thừa hưởng GPU/Metal-only hoặc bounce preset từ research.

### Topic: participating-media

When: Chỉ khi scene có haze/cloud/volume cần kiểm soát.

- `research/blender-rendering-deep-dive/03-VOLUMETRIC-SCATTERING-ATMOSPHERICS.md` — read-verify; SHA256 `3398c162a9916827d9f8cecf08f61be50dde18b4079a93242e14a05684d008ca`
  Caution: Universal zero-banding/integrator claim is not proven by stepping snippet; fixed100-unit cube/density is not scene-scale calibration.

**Steps**

- Chốt volume bounds, density và path-length assumptions.
- So baseline tắt atmosphere để tách exposure/material lỗi.

**Gates**

- Bounds/density hữu hạn và phù hợp scale.
- Xem banding, light shafts, transmission và khả năng đọc sản phẩm.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: color-denoise-delivery

When: Khi highlight/output colors hoặc temporal noise cần chẩn đoán.

- `research/blender-rendering-deep-dive/04-COLOR-MANAGEMENT-AGX-ACES.md` — read-verify; SHA256 `92ad6a1fe1eb4909477b6b9a90821f2aaba9f29b4718a0b40c453b846ea0a7b0`
  Caution: Hardcoded color/look/sequencer values omit an actual EXR output-space contract; sRGB and Rec709 transfer assumptions need qualification.
- `research/blender-rendering-deep-dive/05-DENOISING-OIDN-OPTIX-TEMPORAL.md` — read-verify; SHA256 `bfbe6228752fb87ad29ed1e75868cf2d3d5e63ceee83b1287b64703bc7a51da3`
  Caution: Snippet clears legacy scene compositor, assumes ViewLayer and pass sockets; conflicts with current KB. No real EXR setup or disocclusion rejection in shown blend.

**Steps**

- Chốt display/view/look/exposure và output encoding riêng.
- Giữ raw noisy evidence; kiểm guide passes trước nối denoiser.

**Gates**

- Introspect compositor/pass sockets; EXR contract có cấu hình thực.
- So raw/denoised crop và clip liên tiếp: không mất detail, ghost hoặc boiling.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Không xóa compositor hiện hữu hoặc dùng sample minimum làm bảo đảm.

### Topic: framing-export-contract

When: Khi tự căn camera hoặc xuất GLB/STL qua adapter.

- `scripts/boilerplates/pipeline_render/bp_export_pipeline.py` — inspect-adapt; SHA256 `f2499c0298d379263e2e8f2078d06ddbbfa6ca326a19e756c4b97290c0ce2ae1`
  Caution: Export operator FINISHED and file existence do not prove watertightness, units, contents or round-trip fidelity. Uses current selection/context and unvalidated output paths; self-test writes/deletes fixed /tmp filenames. Source citations are not export validation.
- `scripts/boilerplates/pipeline_render/bp_cam_autoframing.py` — inspect-adapt; SHA256 `78234a210fb236dcd25a08b9cd2faddca9c1976fd9f6cdb4deb200f13d2ce780`
  Caution: Only horizontal FOV/sensor_width considered; ignores render aspect, sensor fit, shift, clipping and orthographic cameras. Original bound_box may omit evaluated deformation. Reuses TRACK_TO and named target, assumes world values equal local location. Distance >2 test does not prove framing.

**Steps**

- Chốt object selection, evaluated bounds, camera type/aspect và output path của candidate.
- Adapt framing theo cả hai FOV; xuất với units và thuộc tính đúng contract.

**Gates**

- Chiếu evaluated bounds qua camera, kiểm cả X/Y, near/far clip tại mọi pose yêu cầu; xem ảnh render.
- Đọc lại artifact độc lập, kiểm object/count/bounds/units/materials theo format; STL cần topology và dung sai riêng.

**Limitations**

- FINISHED, file tồn tại hoặc camera distance không chứng minh output đúng.
- Helper có thể đổi target/constraint hiện hữu và ghi đường dẫn cố định; không chạy self-test trên scene sản xuất.

## native-procedural-simulation

Geometry Nodes, pattern, instances và simulation/caches bằng Blender-native.

### Base reading

- `knowledge/00-foundations/blender-version-matrix.md` — read-verify; SHA256 `db2d39bd3435f787a22a3fb8684415ecc51c87033e5e07d23aafb850eb81f96a`
- `knowledge/00-foundations/bpy-scripting-core.md` — read-verify; SHA256 `8bd924aae27b545232d3d8222152fe2160ff7f7cfeddd54ee1c7126487efcc5c`
- `knowledge/00-foundations/agent-workflow-loop.md` — read-verify; SHA256 `cc947502cc80a8c7b4e59d47462cc8a601636696b61bf1ab9bf3fa38310996a6`
- `knowledge/50-procedural/geometry-nodes.md` — read-verify; SHA256 `4e4dc95e1d559e39c4446d62b3a2b9ea6abbd85e35e461b25b15a2abf6c981a6`
  Caution: Vertex-count growth does not verify pure instancing, and fixed-topology simulation need not change vertex count. Check instance counts/transforms or expected simulation state; require topology growth only if the task specifies it.
- `knowledge/50-procedural/simulation-physics.md` — read-verify; SHA256 `eeb6afd6ebdb67b9743da7945d30891d46756145c4cfb4d99d780d33fe0abc00`
- `knowledge/10-modeling/modifiers.md` — read-verify; SHA256 `88f4e06ffc4d5b9f74db1d00f2c0a95cee35cbe28a8248ab12b19dbf8f6a1ff1`

### Steps

- Chốt procedural inputs, unit, seed, instance domain và output contract.
- Introspect node/socket/zone ở runtime; blockout graph nhỏ trước.
- Kiểm evaluated geometry/instance transforms và cache trên frame đại diện.
- Bake/render candidate riêng, xem kết quả nhiều frame.

### Gates

- Counts/attributes/instances đúng với input; thay input đổi output như spec.
- Kết quả evaluated và export không thiếu instances/modifiers.
- Cache gắn revision và frame range; replay candidate có kết quả đúng.
- Review visual và thời gian sau numeric checks.

### Limitations

- Simulation mesh không tự chứng minh vật liệu hoặc phần cứng thật.
- Physics cache và node API phụ thuộc runtime; không recall version.

### Topic: fields-parametric-solids

When: Khi field domains, attributes hoặc hình cơ khí tham số là mục tiêu.

- `research/blender-geometry-nodes-procedural/01-FIELDS-ARCHITECTURE-EVALUATION-MODEL.md` — read-verify; SHA256 `e067dbda62c98c67b8de34cb27377d9106a61e166d5c788fbd29f8566ce2dc99`
  Caution: Snippet clears node interface. Universal zero-memory/interpolation/persistence claims exceed evidence; test consumer domain and data type.
- `research/blender-geometry-nodes-procedural/02-PROCEDURAL-HARD-SURFACE-CAD-MODELING.md` — read-verify; SHA256 `1fa9d830e42ba72055c9affa9ff59b3acf2537d9d1721681d7e6e61af9d552f3`
  Caution: Pipe snippet lacks interior bore; Boolean index-remap/solver and unconditional robustness claims need runtime inspection.
- `scripts/generate-procedural-geonodes.py` — inspect-adapt; SHA256 `294e8ea053d503b169b622bd9bbc804b830f4ecb6161fa1efca9e5baec07e76d`
  Caution: main deletes all objects. Graph omits advertised four mounting holes/stress_zone; fixed cutter/boss do not cover input range. Attribute existence alone is not validation.
- `scripts/boilerplates/bp_geonodes.py` — inspect-adapt; SHA256 `769758b062e335afca97b87d871a6c4e5f78f8b67f2647669e28327eb8bf1021`
  Caution: Named node group deletion is global. Missing node group returns silently; input fallback unverified. Self-test checks nonempty geometry, not parameter behavior.
- `scripts/boilerplates/bp_bmesh_cad.py` — inspect-adapt; SHA256 `c68939cd8ecf5e31c0b0b577e14f7c742af3ace3debd6bd8f0e940161d327086`
  Caution: Named global data deletion and modifier baking replace mesh/clear stack. Manifold flags do not prove winding, self-intersection, dimensions or clearance.

**Steps**

- Chốt input ranges/units/schema/consumer domains.
- Introspect sockets rồi kiểm parameter matrix gồm biên.

**Gates**

- Đo evaluated dimensions, hole/component counts và topology.
- Kiểm attribute name/domain/type/distribution thực; xem sections và shading.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- Adapter thiếu bốn lỗ gá như header; main xóa toàn bộ object.

### Topic: simulation-repeat-budgets

When: Khi cần state qua frame, substeps, branching hoặc iterative solver.

- `research/blender-geometry-nodes-procedural/03-SIMULATION-ZONES-PHYSICS-SOLVERS.md` — read-verify; SHA256 `8959b378ecad521c39fe3fd915c6b65a655d04c84830314a61adad76136a07c0`
  Caution: Indefinite stability/fixed substep/cache guarantees unproven; boids formulas lack empty-neighborhood/coincident guards.
- `research/blender-geometry-nodes-procedural/04-REPEAT-ZONES-FRACTALS-RECURSION.md` — read-verify; SHA256 `ac7657d383102eec3294e8bc24af5d101ffdd7bf867e18c08c38c073e2a7adf1`
  Caution: 0.707 is mislabeled golden-ratio decay; fixed iteration/resource claims unverified. Position smoothing does not guarantee equilateral quads.
- `scripts/boilerplates/bp_physics.py` — inspect-adapt; SHA256 `310830e00597192f942742ea24a580ba26f1a04e65bf75c8a632fc523201ccea`
  Caution: World setup uses operators; linking a collection is assumed to create rigid_body immediately. Cache frame stepping lacks clear/bake/context restoration; isolate and verify actual world membership.

**Steps**

- Tách inter-frame simulation và intra-frame loop.
- Chốt timestep/state/seed/cache revision; xử lý empty/coincident neighborhoods.
- So hai timestep/substep candidates và dự toán growth trước chạy.

**Gates**

- Không NaN/Inf; count/time/memory trong budget task.
- Đo convergence/state residual và replay; không yêu cầu tăng vertex với fixed topology.
- Xem tunneling/stability/feature loss theo thời gian.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: sdf-feature-preservation

When: Khi chọn SDF boolean hoặc volume remesh cho candidate native.

- `research/blender-geometry-nodes-procedural/05-VOLUME-GRIDS-SDF-BOOLEANS.md` — read-verify; SHA256 `420beb9331f727a560f9e3fcab806dfc7d08e47c37405017e37db4879dd4d233`
  Caution: Named smooth subtraction has no smoothing parameter; guaranteed manifold/print-ready/half-wall preservation is not established.

**Steps**

- Phân biệt fog/distance grid/isovalue.
- Chọn voxel size theo feature và memory; giữ original.

**Gates**

- So topology, openings, local walls/clearance và deviation ở hai resolutions.
- Xem section và camera-matched sheet: không bịt lỗ/xóa vách.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.
- SDF không tự bảo đảm manifold/printing-ready hoặc giữ wall từ quy tắc half-wall.

### Topic: graded-lattice-reinforcement

When: Khi lattice hoặc reinforcement nhằm mục tiêu mass/stiffness cụ thể.

- `research/advanced-tribology-contact-mechanics/05-TOPOLOGY-OPTIMIZATION-LATTICES.md` — read-verify; SHA256 `e83faf7df5baa6639cdefeeb8484d463241f31e9bd2355f3134eb2a199a6f930`
  Caution: generate_gyroid_mesh only builds arrays/prints density; creates no Blender geometry or SIMP optimization. Field threshold is not physical wall thickness.
- `research/polymer-additive-manufacturing-advanced/02-CONTINUOUS-FIBER-COMPOSITES-CFRTP.md` — read-verify; SHA256 `6e4260f9be456a71959911ba1af3882f1c6b5868dca4edcb819050fd71ed2667`
  Caution: Quasi-isotropic in-plane layup does not justify zero directional weakness/warping claims for arbitrary through-thickness print behavior.

**Steps**

- Chốt cell size/local wall/boundary/load paths và fiber directions.

**Gates**

- Cần mesh thật, density/wall và resolution convergence; field preview không phải mesh.
- Kiểm orientation/boundary condition và physical stiffness riêng.

**Limitations**

- Nguồn research chưa chứng nhận API/số liệu; kiểm runtime và nguồn gốc theo yêu cầu task.

### Topic: procedural-component-adapters

When: Khi adapt graph cáp/tube hoặc flange có tham số.

- `scripts/boilerplates/geometry_nodes/bp_gn_cables.py` — inspect-adapt; SHA256 `5212fe937edc66bab7b449d0232199ae768b21cc4bd98325e447c433df97eee0`
  Caution: Sag input unused; graph generates a straight tube despite catenary header. Replaces named group and leaves test object. Nonempty mesh does not verify sag, dimensions, caps or clearance.
- `scripts/boilerplates/geometry_nodes/bp_gn_pipe_flange.py` — inspect-adapt; SHA256 `7e7ea9168e56dc6d4c677a548e3815d46786ca9845c479f3402b4fc3685991e1`
  Caution: Disc-minus-bore only; promised Hub Length, bolt pattern and ASME dimensional/class contract absent. Positional Boolean sockets need runtime inspection; replaces group; nonempty-mesh test only.

**Steps**

- Chốt component shape, input ranges và output measurements; không lấy header làm contract đã đạt.
- Inspect node/socket/interface thực; sửa feature còn thiếu trong candidate riêng.

**Gates**

- Đo endpoint/midpoint khi đổi Sag, đường kính, OD/bore/thickness và số lỗ theo component.
- Kiểm valid/invalid boundaries, caps/components/manifold và section/render; drawing thật mới xác định flange cần gì.

**Limitations**

- Cáp hiện không dùng Sag; flange chỉ có disc-minus-bore, chưa có hub/bolt pattern.
- Nonempty mesh không đủ chứng minh graph thực hiện input.

