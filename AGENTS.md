# AGENTS.md — Blender AI Orchestration (file vận hành chính)

**Thứ tự ưu tiên khi mâu thuẫn:** `.project-agent.md` (identity + binding rules) > file này > `.agents/skills/*/SKILL.md` + references > `knowledge/` > `docs/` (tường thuật, không phải luật). `CLAUDE.md` chỉ import file này. Rule ghi `MANUAL` = kỷ luật controller, chưa có code enforce.

## Mission
`<ROOT>` trong file này = đường dẫn tuyệt đối của repo trên máy đang chạy (ví dụ local của Jang: `/Users/jang/Products/Blender`).

AI dựng 3D/animation/render trong Blender **5.2.0 LTS** (local = target KB) qua 2 đường:
- **Interactive:** MCP server `blender` → addon trong GUI (phải Connect). Tool dùng được: `execute_blender_code`, `get_object_info`, `get_viewport_screenshot`, `get_scene_info` (chỉ trả 10 object đầu — lấy danh sách đầy đủ bằng bpy). Các tool PolyHaven/Sketchfab/Hyper3D/Hunyuan/`set_texture` **bị cấm** bởi Native Asset Policy.
- **Headless:** `scripts/headless-run.sh <pass.py>` — process mới `--factory-startup`, dùng cho batch, render, fault-probe, gate.

Mục tiêu sản phẩm (Jang, 2026-09-06): **production level — in 3D được, đúng kích thước, đúng tiêu chuẩn.** Ảnh/video "nhìn đúng" không phải acceptance.

## Loop bắt buộc cho mọi task dựng cảnh
```
Contract → Plan (scene graph) → Code (pass files) → Critic → Execute → Verify → Verdict
```
0. **Contract trước khi vào chi tiết.** Part sẽ in/chế tạo → viết `builds/<slug>/spec.json` theo `specs/build-spec.schema.json` (kích thước ± dung sai, lỗ/boss, fastener theo chuẩn, vật liệu/process, hướng in, min wall, load case đã khai báo). Thiếu kích thước/payload/duty → verdict `request-input`, **không** dựng chi tiết. Có ảnh reference → fidelity contract (skill `blender-image-to-3d`). Lịch sử: mọi rebuild toàn bộ đều do spec đến sau khi đã detail.
1. **Plan:** scene graph — objects, hierarchy, vị trí, materials, camera, lights. Task dài → `plans/`.
2. **Code:** data API trước, `bpy.ops` là ngoại lệ (`knowledge/00-foundations/bpy-scripting-core.md`). Mỗi pass = 1 file `builds/<slug>/pass-NN-<muc-dich>.py` ≤ ~80 dòng, kết thúc bằng postcondition số qua `emit_ok`.
3. **Critic (tự soát):** import/`__file__` nằm trong payload (namespace MCP không persist)? tên socket/enum/operator đã introspect runtime? đơn vị (1 BU = 1 m, spec tính mm)? mutation trước assert? op phá huỷ → `checkpoint()` trước?
4. **Execute:**
   - MCP: `import sys; sys.path.insert(0, "<ROOT>/scripts"); import agent_runtime as rt; rt.run_file("/abs/builds/<slug>/pass-NN.py")`
   - Headless: `bash scripts/headless-run.sh builds/<slug>/pass-NN.py`
   - **Quyết định bằng dòng cuối stdout** `AGENT_OK {json}` / `AGENT_FAIL {json}`; "Code executed successfully" chỉ là transport. Exit code Blender sai cả hai chiều. Timeout sau khi đã gửi mutation → outcome unknown: đọc state trước khi gửi lại.
5. **Verify ladder (rẻ → đắt; số trả lời được thì không tốn ảnh):** (1) assert số: `assert_exists`, `tri_count`, `world_bbox`, `has_material`, fcurve keys → (2) `framing()` + `preview_render(engine="EEVEE"|"CYCLES")` + `frame_stats()` (≈0.2 s ở 256px trên scene nhỏ, cả hai engine chạy headless macOS; restore state) → (3) viewport screenshot **sau khi ghi kỳ vọng + điều gì falsify** → (4) Cycles preview thấp sample → (5) comparison sheet khi có reference → (6) turntable. Part production: `python3 scripts/production-gate.py --scene <blend> --spec <spec.json> --report <out.json>` exit 0 trước khi giao; đính report.
6. **Verdict (chọn đúng 1):** `continue` · `refine-spec` (gốc rễ ở spec — sửa spec trước) · `refine-code` · `request-input` · `stop` (= báo user, đổi hướng). 2 lần fail cùng bước → đổi **class** approach; 3 lần → `request-input`.

**Điểm quyết định của owner (MANUAL, bắt buộc):** blockout sheet trước khi detail; animatic ≤ 120 frame trước bất kỳ render > 120 frame; chỉ render dài sau khi owner đã thấy và chốt. Record: 2 lần render-rồi-bỏ (~26 phút, ~3.000 frame) xảy ra sau khi retro đã ghi rule này thành prose.

## Failure map (theo record thật, không phải lý thuyết)
| Triệu chứng | Nguyên nhân thường gặp | Làm gì |
|---|---|---|
| `NameError` trong "executed successfully" | helper/import từ call trước không còn | đặt import + `rt.load_lib()` trong payload |
| Assert hình học/STL fail dù mesh "đẹp" | degenerate faces, non-manifold sau boolean | `production-gate.py` topology + đọc lại STL |
| Endpoint PASS nhưng giữa chuyển động đè nhau | chỉ verify trạng thái cuối | sweep theo frame + animatic; `assembly-sequences.md` |
| Render đen/silhouette đen | persistent_data stale, camera trong wall, không light | `framing()`, `frame_stats()`, `persistent_data=False` |
| Render đúng nhưng owner từ chối | camera/nhịp/scope không có trong contract | `refine-spec`; hỏi trước, không render lại mù |
| `ModuleNotFoundError` (scipy/fitz) | Python của Blender ≠ host Python | `importlib.util.find_spec` trong preflight; code không phụ thuộc |
| MCP connection error | addon chưa Connect | báo user, không retry |

## Visual feedback cho user (BẮT BUỘC)
MCP live: user nhìn object mọc trong viewport. Headless: sau mỗi pass `open <sheet.png>`; build xong `open -a Blender <file.blend>`. Build > 2 phút → báo số pass + ước lượng thời gian trước.

## Giao hàng
README của build ghi trạng thái **riêng** cho media / motion / fit / manufacture; đính `gate-report.json`, hash input, frame range; geometry đổi → evidence cũ vô hiệu. Không suy ra tải/nhiệt/độ bền từ check số hoặc video; thiếu bằng chứng vật lý → manufacture **BLOCKED** ghi rõ.

## Bản đồ tài nguyên
| Cần | Đọc/dùng |
|---|---|
| Loop chi tiết, execution modes, verify ladder | `.agents/skills/blender-agent-core/SKILL.md` (+ `references/`) |
| Có ảnh reference | `.agents/skills/blender-image-to-3d/SKILL.md` |
| Reading pack theo task | `python3 scripts/blender-knowledge.py list` / `route <workflow-id>` (skill `blender-knowledge-workbench`) |
| 3 file KB nền (bắt buộc) | `knowledge/00-foundations/{blender-version-matrix,bpy-scripting-core,agent-workflow-loop}.md` |
| Spec/gate production | `specs/README.md`, `scripts/production-gate.py` |
| Sense organs trong bpy | `scripts/agent-verify-lib.py` (đọc-only an toàn; `preview_render` restore state; `verify_export` chạy process riêng) |
| Preview nhanh / so ảnh | `scripts/turntable-preview.py`, `scripts/make-comparison-sheet.sh` |
| Kiến trúc, backlog | `docs/system-architecture.md`, `docs/blender-workflow-improvement-backlog.md` |

Native Asset Policy, QRemeshify gate và các binding rule khác: `.project-agent.md` (không lặp lại ở đây).
