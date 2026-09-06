---
name: blender-agent-core
description: Core discipline for ANY Blender/bpy work — contract-first, knowledge routing, execute-verify-refine loop with the AGENT_OK/AGENT_FAIL sentinel contract, numeric-first verification, production gate before delivery. Activate for every task that touches Blender, before any domain skill.
---

# Blender Agent Core

Skill này là ROUTER + quy trình. Kiến thức sâu nằm ở `knowledge/` — load đúng file cần, không recall từ trí nhớ. Luật vận hành gốc ở `AGENTS.md` (precedence: `.project-agent.md` > `AGENTS.md` > skill này). Bản `.agents/skills/` là nguồn; `.claude/skills/` là mirror phải đồng bộ.

## 0. Routing theo task
| Task | Nạp thêm |
|---|---|
| Part sẽ in/chế tạo, cần đúng kích thước/chuẩn | [Production contract](references/recipes.md#production-contract) → `specs/README.md` |
| Execute qua MCP/headless, đọc lỗi | [Explicit execution context](references/recipes.md#explicit-execution-context) |
| Có ảnh reference | Skill `blender-image-to-3d` |
| Khớp, hand, thao tác, animation task | [Articulated task](references/recipes.md#articulated-task) |
| Assembly/exploded view | [Assembly sequences](references/assembly-sequences.md) |
| Chịu tải, duty, cơ cấu hoạt động | [Mechanical evidence](references/recipes.md#mechanical-evidence) |
| Render batch, video, export | [Render delivery](references/recipes.md#render-delivery) |
| Turntable / product shot | `scripts/turntable-preview.py` + `knowledge/60-pipeline/product-viz-and-shots.md` |

Đọc [hard rules](references/hard-rules.md) mỗi session (ghi rõ ENFORCED vs MANUAL). Giao kết quả theo [revision-bound acceptance](references/recipes.md#revision-bound-acceptance).

## 1. Knowledge routing (bắt buộc)
Mở đầu mọi task Blender, đọc **3 file nền** nếu chưa trong context: `knowledge/00-foundations/blender-version-matrix.md`, `bpy-scripting-core.md`, `agent-workflow-loop.md`. Rồi `python3 scripts/blender-knowledge.py list` → `route <workflow-id>` để lấy reading pack (skill `blender-knowledge-workbench`); chỉ nạp phần cần. `knowledge/INDEX.md` là lookup on-demand, không phải must-read. `loads_with` là gợi ý một hop, không nạp đệ quy (một hop ≈ 40–50k token).

## 2. Loop (R1–R8 rút gọn — bản đầy đủ trong agent-workflow-loop.md)
1. **Contract trước** — spec.json cho part production; fidelity contract cho reference; thiếu số → `request-input`.
2. **Decompose** — scene graph → mỗi pass 1 file ≤ ~80 dòng, 1 mục đích.
3. **Assert mỗi bước** — pass kết thúc bằng `rt.emit_ok(step, **postconditions)`; postcondition phải FAIL nếu bước silently no-op; operator return phải `{'FINISHED'}`.
4. **Scaffold không phá** — `scaffold()` của lib đọc trước, chỉ ghi khi factory-default hoặc `force=True`; không reset scene đang làm.
5. **Screenshot có chủ đích** — ghi kỳ vọng + điều gì falsify TRƯỚC khi nhìn.
6. **2 fail cùng bước → đổi CLASS approach; 3 fail → `request-input`.**
7. **Checkpoint** (`checkpoint(tag)`) trước mọi op phá huỷ (boolean, apply, join).
8. **Biết ranh giới bàn giao** — weight paint tinh, facial rig, art direction: báo sớm.

## 3. Verify ladder (rẻ → đắt; số trả lời được thì không tốn ảnh)
```python
import sys; sys.path.insert(0, "<ROOT>/scripts")
import agent_runtime as rt; lib = rt.load_lib("<ROOT>/scripts/agent-verify-lib.py")
```
1. Số: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys — và postconditions trong `AGENT_OK`.
2. `framing(obj)` → `preview_render(engine="EEVEE"|"CYCLES")` (≈0.1–0.2 s ở 128–256px trên scene nhỏ, restore state) → `frame_stats()` (stdev < 0.01 = frame phẳng cần chẩn đoán).
3. Viewport screenshot (MCP) — composition, "có giống không".
4. Cycles preview thấp sample — material/lighting thật.
5. Comparison sheet (`scripts/make-comparison-sheet.sh`) — khi có ảnh reference.
6. Turntable (`scripts/turntable-preview.py`) — chống "bìa cứng".
7. **Part production:** `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0; đính report vào build. Gate chứng minh topology/kích thước/screen số — **không** chứng minh tải, fit thật, nhiệt.

Đo trên máy này: cold start 0.5 s, preview 256px ≈ 0.4–2 s. Verify rẻ; thứ tự ladder là theo giá trị thông tin, không phải chi phí.

## 4. Execution modes (check theo thứ tự)
1. **MCP tools** (addon Connected): `rt.run_file("/abs/pass.py")` — traceback đầy đủ trong `AGENT_FAIL`; namespace mỗi call mới, helper nạp lại bằng `rt.load_lib` (cache theo sha). Đọc scene read-only trước mutation.
2. **Socket bridge** khi MCP tool chưa nạp: `python3 scripts/blender-socket-client.py execute_code --file pass.py` (exit 0/1/2/3 theo sentinel; không cắt output).
3. **Headless** cho batch/fault-test/gate: `bash scripts/headless-run.sh pass.py` (`--factory-startup --disable-autoexec --python-exit-code 3`; exit theo sentinel). Sau mỗi pass cung cấp sheet/preview; xong build mở đúng file cho user.
Quy tắc chung: quyết định bằng **dòng cuối** `AGENT_OK`/`AGENT_FAIL`; timeout sau khi gửi mutation = unknown → đọc state trước khi gửi lại; một writer cho GUI.

## 5. Failure quick-map
| Triệu chứng | Đọc |
|---|---|
| `NameError` helper/`__file__` trong "executed successfully" | §4 — import trong payload, `rt.load_lib` |
| Assert STL/topology fail dù mesh nhìn đẹp | `production-gate.py` topology; 3d-printing.md §5 |
| Endpoint PASS, giữa chuyển động đè nhau | assembly-sequences.md; sweep theo frame |
| Render đen/phẳng | `framing()` + `frame_stats()`; `persistent_data=False`; lighting.md |
| KeyError socket/enum | version-matrix §renames — introspect `[s.name for s in node.inputs]` |
| Boolean nát mesh | modifiers.md §boolean-solver + checkpoint trước đó |
| Export vỡ ở engine khác | export-interchange.md + `verify_export()` (process riêng) |
