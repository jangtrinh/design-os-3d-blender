# Review Rubric & Quantitative Gates (chưng cất từ img2threejs source, 260728)

## 1. Suitability rubric (Bước 0.1)

**PASS:** 1 vật thể rõ · chiếm đủ khung · silhouette mạnh · material chính nhìn thấy được · mặt khuất suy được (đối xứng) · xấp xỉ được bằng primitives.
**CONDITIONAL:** chỉ 1 góc nhìn nhưng vật đối xứng xoay · che khuất một phần nhưng khối chính rõ · organic nhưng user chấp nhận stylized · không đòi hỏi logo/text chính xác.
**REJECT:** vật thể mơ hồ · ảnh là scene không phải object · phần hình quan trọng bị che/mờ/crop · đòi độ chính xác chế tạo · vật chủ yếu là khói/chất lỏng/kính caustics/ren lưới (không có đường procedural).
Reject → `request-input` (xin thêm góc, ảnh nét hơn hoặc bản vẽ kích thước); nếu đã được chấp nhận giảm fidelity thì đổi cách dựng Blender-native. Không dùng external generation/retrieval làm fallback.

## 2. Complexity tier → targetMinDetails (spec gate định lượng)

| Tier | Min details trong inventory | Ví dụ |
|---|---|---|
| simple | 3 | cốc, hộp, bàn đơn giản |
| moderate | 6 | ghế văn phòng, đèn bàn |
| complex | 10 | xe đạp, loa vintage, máy ảnh |
| ultra | 16 | cơ khí nhiều chi tiết, súng, đồng hồ |

Scan theo `component-zones` (khi đã chia parts) hoặc `grid-3x3` (chưa chia). Mỗi detail ghi: region + kind + confidence (0-1) + **mapsTo** (component/material cụ thể). Detail chỉ mô tả bằng văn = gate FAIL. Không thổi phồng confidence để đủ số.

## 3. Detail taxonomy → kỹ thuật Blender

| Kind | Blender technique |
|---|---|
| gloss (vùng bóng) | roughness thấp 0.05-0.2 vùng đó (vertex group/texture mask); brushed metal → anisotropy |
| bevel (bo cạnh) | **Bevel modifier — geometry thật**, không normal map, nếu ảnh có đường highlight sắc dọc cạnh |
| fastener (ốc/rivet) | instancing: Array modifier / Geometry Nodes distribute — KHÔNG model từng con |
| linework | 3 kỹ thuật, chọn theo bằng chứng: khắc chìm → groove geometry; sơn vẽ → texture/decal; panel-line → AO seam tối màu không có độ sâu |
| seam | groove/ridge mảnh + AO tối trong khe |
| stain/wear | procedural texture override: dirtAmount, cavityBias (bẩn đọng khe → AO/pointiness mask), streak theo trọng lực, patinaColor |
| scratch/chip | roughness/normal perturbation cục bộ; chip đổi silhouette → boolean nhỏ |
| decal | texture vùng (UV project); chỉ thêm geometry nếu có độ dày |
| emissive | Emission shader + cân nhắc thêm light thật cạnh đó để hắt sáng |
| hole | Boolean — lỗ thật đổi topology, không phải mảng tối |
| groove/ridge | curve + profile hoặc displacement dọc path |

## 4. Vision review — cách chấm mỗi pass

- Mỗi pass chấm từ **1 comparison sheet duy nhất**; chọn ≤5 hệ trọng yếu của pass đó để soi (đừng soi tất cả mọi thứ mọi pass).
- Feature chia tier: `critical` (bắt buộc đạt) / `important` / `detail`.
- **Ngưỡng:** global score ≥ 0.7; mọi critical feature phải đạt ngưỡng riêng. Dưới → refine.
- Không chắc (điểm dao động khi tự chấm lại) → coi như "probe": nhìn thêm góc khác rồi mới verdict.

## 5. Fidelity scale (báo cáo trung thực)

0.2 placeholder thô · 0.4 silhouette nhận ra được · 0.6 khối macro/meso đúng, material yếu · 0.75 vật đọc đúng, chi tiết xấp xỉ · 0.85 procedural match tốt · 0.95 gần tham chiếu (thường cần nhiều góc ảnh). **Không tự nhận ≥0.9 từ 1 ảnh mơ hồ.**

## 6. Root-cause: refine-spec vs refine-code

**refine-spec khi:** thiếu/bịa component · sai họ primitive · sai tỉ lệ/hệ toạ độ từ gốc · material layer thiếu đặc tả · detail thiếu trong spec · bằng chứng ảnh mâu thuẫn spec.
**refine-code khi:** spec rõ nhưng geometry sai · material param chưa implement · mask/wear thiếu trong code · hierarchy/pivot lệch spec · render có artifact.
**request-input khi:** ảnh giấu hình quan trọng · material không suy được từ góc này · cần branding/text chính xác · fidelity đòi hỏi vượt khả năng 1 ảnh.
**stop khi:** đạt mục tiêu · user chấp nhận xấp xỉ · phần còn lại cần reference mới/modeling tay/route khác.

## 7. Bẫy đã được xác nhận (từ production log của họ)

1. **So pixel với ảnh chụp là vô nghĩa** — framing/background/lighting át hết fidelity (BMX faithful bị chấm reject 0.53). ĐỪNG cố pixel-match photo; chấm theo mục tiêu từng pass: silhouette đọc được? part có mặt? màu đúng tông?
2. **2D gate mù 3D realism** — silhouette khớp vẫn có thể là "bìa cứng": cạnh sắc lịm không taper, metal trông như nhựa. LUÔN render thêm **góc 3/4** trước khi báo done; sheet chính diện pass chưa phải là xong.
3. **Đừng suy feature từ tên gọi** — với vật thể có danh tính cụ thể (sản phẩm thật), xin ảnh chính diện + tên chính xác; đừng đoán cấu tạo từ mô tả.
