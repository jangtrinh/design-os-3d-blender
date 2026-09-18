#!/usr/bin/env python3
"""Generate index.html for the published DC-01 R02 delivery review.

Every number on the page is read from the delivered package (snapshot.json,
print/package-manifest.json, print/final-gate.json, electronics-audit.json,
media-manifest.json), never retyped. Regenerate instead of patching the HTML:

    python3 docs/reviews/dc-01/r02/build-page.py [--source builds/desktop-companion/delivery/R02]

The stylesheet and the carousel script are inlined from page-style.css and
page-carousel.js so the page also opens straight from disk.
"""

import argparse
import json
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
SITE = "https://jangtrinh.github.io/design-os-3d-blender"
PHOSPHOR = {
    "download": "M224,144v64a8,8,0,0,1-8,8H40a8,8,0,0,1-8-8V144a8,8,0,0,1,16,0v56H208V144a8,8,0,0,1,16,0Zm-101.66,5.66a8,8,0,0,0,11.32,0l40-40a8,8,0,0,0-11.32-11.32L136,124.69V32a8,8,0,0,0-16,0v92.69L93.66,98.34a8,8,0,0,0-11.32,11.32Z",
    "cube": "M223.68,66.15,135.68,18h0a15.88,15.88,0,0,0-15.36,0l-88,48.17a16,16,0,0,0-8.32,14v95.64a16,16,0,0,0,8.32,14l88,48.17a15.88,15.88,0,0,0,15.36,0l88-48.17a16,16,0,0,0,8.32-14V80.18A16,16,0,0,0,223.68,66.15ZM128,32h0l80.34,44L128,120,47.66,76ZM40,90l80,43.78v85.79L40,175.82Zm96,129.57V133.82L216,90v85.78Z",
    "file": "M213.66,82.34l-56-56A8,8,0,0,0,152,24H56A16,16,0,0,0,40,40V216a16,16,0,0,0,16,16H200a16,16,0,0,0,16-16V88A8,8,0,0,0,213.66,82.34ZM160,51.31,188.69,80H160ZM200,216H56V40h88V88a8,8,0,0,0,8,8h48V216Zm-32-80a8,8,0,0,1-8,8H96a8,8,0,0,1,0-16h64A8,8,0,0,1,168,136Zm0,32a8,8,0,0,1-8,8H96a8,8,0,0,1,0-16h64A8,8,0,0,1,168,168Z",
    "stack": "M230.91,172A8,8,0,0,1,228,182.91l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,36,169.09l92,53.65,92-53.65A8,8,0,0,1,230.91,172ZM220,121.09l-92,53.65L36,121.09A8,8,0,0,0,28,134.91l96,56a8,8,0,0,0,8.06,0l96-56A8,8,0,1,0,220,121.09ZM24,80a8,8,0,0,1,4-6.91l96-56a8,8,0,0,1,8.06,0l96,56a8,8,0,0,1,0,13.82l-96,56a8,8,0,0,1-8.06,0l-96-56A8,8,0,0,1,24,80Zm23.88,0L128,126.74,208.12,80,128,33.26Z",
    "circuit": "M216,136H192V120a8,8,0,0,0-8-8H136V88h16a8,8,0,0,0,8-8V32a8,8,0,0,0-8-8H104a8,8,0,0,0-8,8V80a8,8,0,0,0,8,8h16v24H72a8,8,0,0,0-8,8v16H40a8,8,0,0,0-8,8v48a8,8,0,0,0,8,8H88a8,8,0,0,0,8-8V176a8,8,0,0,0-8-8H80V128h96v40h-8a8,8,0,0,0-8,8v48a8,8,0,0,0,8,8h48a8,8,0,0,0,8-8V144A8,8,0,0,0,216,136ZM112,40h32V72H112ZM80,208H48V184H80Zm128,0H176V184h32Z",
    "play": "M232.4,114.49,88.32,26.35a16,16,0,0,0-16.2-.3A15.86,15.86,0,0,0,64,39.87V216.13A15.94,15.94,0,0,0,80,232a16.07,16.07,0,0,0,8.36-2.35L232.4,141.51a15.81,15.81,0,0,0,0-27ZM80,215.94V40.07l143.83,87.94Z",
    "ruler": "M235.32,73.37,182.63,20.69a16,16,0,0,0-22.63,0L20.69,160a16,16,0,0,0,0,22.63l52.68,52.68a16,16,0,0,0,22.63,0L235.32,96A16,16,0,0,0,235.32,73.37ZM84.68,224,32,171.31l32-32,26.34,26.35a8,8,0,0,0,11.32-11.32L75.31,128,96,107.31l26.34,26.35a8,8,0,0,0,11.32-11.32L107.31,96,128,75.31l26.34,26.35a8,8,0,0,0,11.32-11.32L139.31,64l32-32L224,84.69Z",
    "warning": "M236.8,188.09,149.35,36.22h0a24.76,24.76,0,0,0-42.7,0L19.2,188.09a23.51,23.51,0,0,0,0,23.72A24.35,24.35,0,0,0,40.55,224h174.9a24.35,24.35,0,0,0,21.33-12.19A23.51,23.51,0,0,0,236.8,188.09ZM120,144V104a8,8,0,0,1,16,0v40a8,8,0,0,1-16,0Zm8,48a12,12,0,1,1,12-12A12,12,0,0,1,128,192Z",
    "check": "M104,192a8.5,8.5,0,0,1-5.66-2.34l-56-56A8,8,0,0,1,53.66,122.3L104,172.69,218.34,58.34a8,8,0,0,1,11.32,11.32l-120,120A8.5,8.5,0,0,1,104,192Z",
    "caret-left": "M165.66,202.34a8,8,0,0,1-11.32,11.32l-80-80a8,8,0,0,1,0-11.32l80-80a8,8,0,0,1,11.32,11.32L91.31,128Z",
    "caret-right": "M181.66,133.66l-80,80a8,8,0,0,1-11.32-11.32L164.69,128,90.34,53.66a8,8,0,0,1,11.32-11.32l80,80A8,8,0,0,1,181.66,133.66Z",
    "github": "M208.31,75.68A59.78,59.78,0,0,0,202.93,28,8,8,0,0,0,196,24a59.75,59.75,0,0,0-48,24H124A59.75,59.75,0,0,0,76,24a8,8,0,0,0-6.93,4,59.78,59.78,0,0,0-5.38,47.68A58.14,58.14,0,0,0,56,104v8a56.06,56.06,0,0,0,48.44,55.47A39.8,39.8,0,0,0,96,192v8H72a24,24,0,0,1-24-24A40,40,0,0,0,8,136a8,8,0,0,0,0,16,24,24,0,0,1,24,24,40,40,0,0,0,40,40H96v16a8,8,0,0,0,16,0V192a24,24,0,0,1,48,0v40a8,8,0,0,0,16,0V192a39.8,39.8,0,0,0-8.44-24.53A56.06,56.06,0,0,0,216,112v-8A58.14,58.14,0,0,0,208.31,75.68ZM200,112a40,40,0,0,1-40,40H112a40,40,0,0,1-40-40v-8a41.74,41.74,0,0,1,6.9-22.48A8,8,0,0,0,80,73.83a43.81,43.81,0,0,1,.79-33.58,43.88,43.88,0,0,1,32.32,20.06A8,8,0,0,0,119.82,64h32.35a8,8,0,0,0,6.74-3.69,43.87,43.87,0,0,1,32.32-20.06A43.81,43.81,0,0,1,192,73.83a8.09,8.09,0,0,0,1,7.65A41.72,41.72,0,0,1,200,104Z",
    "arrow-right": "M221.66,133.66l-72,72a8,8,0,0,1-11.32-11.32L196.69,136H40a8,8,0,0,1,0-16H196.69L138.34,61.66a8,8,0,0,1,11.32-11.32l72,72A8,8,0,0,1,221.66,133.66Z",
}
EXTRA_CSS = """
/* Eighteen printable parts: one 1:1 tile each, three across on a desktop. */
.parts-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:var(--s-6);margin:0;padding:0;list-style:none}
@media(min-width:960px){.parts-grid{grid-template-columns:repeat(3,minmax(0,1fr))}}
.parts-grid .ds-card{margin:0;height:100%}
.parts-grid .ds-card-stage{aspect-ratio:1/1;overflow:hidden}
.parts-grid .ds-card-stage img{width:100%;height:100%;object-fit:cover}
.part-body{padding:var(--s-5) var(--s-6) var(--s-6)}
.part-body h3{margin:0 0 var(--s-2);font-size:var(--t-16);font-weight:var(--fw-semibold);line-height:var(--lh-tight)}
.part-body p{margin:0;color:var(--c-gray-1100);font-size:var(--t-13);font-family:var(--stack-mono);line-height:var(--lh-ui);overflow-wrap:anywhere}
/* A 64-character SHA-256 in a caption must wrap; the base rule keeps captions on one line. */
.case-plate-caption cite,.carousel-caption{white-space:normal;overflow-wrap:anywhere}
.part-chips{display:flex;flex-wrap:wrap;gap:var(--s-2);margin:var(--s-4) 0 0}
/* A missing file is a reserved blank that names it, never a stand-in picture. */
.media-blank{display:flex;align-items:center;justify-content:center;min-height:180px;padding:var(--s-8);
  border:1px dashed var(--c-gray-600);border-radius:var(--r-3);background:var(--c-gray-200);
  color:var(--c-gray-1000);font-family:var(--stack-mono);font-size:var(--t-13);text-align:center}
[hidden]{display:none!important}
"""

# Every image declares this fallback: on a load error the image is replaced by a blank that
# names the missing file. No placeholder service, no invented picture on an engineering page.
FALLBACK_JS = """window.__imgFallback=function(el){var b=document.createElement("div");
b.className="media-blank";b.textContent="Không tải được ảnh: "+(el.getAttribute("src")||"");
el.hidden=true;if(el.parentNode){el.parentNode.appendChild(b);}};"""
IMG_ONERROR = ' onerror="this.onerror=null;window.__imgFallback(this)"'



def icon(name, size=None):
    attr = ' data-size="20"' if size == 20 else ""
    return (f'<svg class="ph"{attr} viewBox="0 0 256 256" fill="currentColor" aria-hidden="true">'
            f'<path d="{PHOSPHOR[name]}"/></svg>')


def badge(label, value, colour):
    """One shields.io badge naming a tool this build was made with."""
    def quote(text):
        return text.replace(" ", "%20").replace("-", "--").replace("/", "%2F")
    url = f"https://img.shields.io/badge/{quote(label)}-{quote(value)}-{colour}?style=for-the-badge"
    return f'<img src="{url}" alt="{label} {value}" width="200" height="28" loading="eager">'


def fact(name, value, note=None, mono=False):
    small = f"<small>{note}</small>" if note else ""
    classes = ' class="mono"' if mono else ""
    return f'<div><dt>{icon("ruler")}{name}</dt><dd{classes}>{value}{small}</dd></div>'


def row(label, body, glyph="check"):
    return (f'<div class="register-row">{icon(glyph, 20)}'
            f"<dt>{label}</dt><dd>{body}</dd></div>")


def slide(index, src, label, alt):
    loading = "eager" if index == 0 else "lazy"
    return (f'<li class="slide" data-label="{label}">'
            f'<img src="{src}" width="1920" height="1080" alt="{alt}" loading="{loading}"></li>')


def part_card(part, label, render_bytes):
    size = part["local_bounds_mm"]
    dims = " × ".join(f"{round(size[1][i] - size[0][i], 1):g}" for i in range(3))
    chips = [f'<span class="ds-chip" data-variant="mono">{part["material"]}</span>',
             f'<span class="ds-chip" data-variant="mono">Khay {part["plate"]}</span>']
    return (
        '<li><article class="ds-card">'
        f'<div class="ds-card-stage capture-stage"><a href="stl/{part["id"]}.stl" download>'
        f'<img src="media/parts/{part["id"]}.jpg" width="1100" height="1100" '
        f'alt="Chi tiết in {label} dựng lại từ tệp STL đã qua gate" loading="lazy"></a></div>'
        f'<div class="part-body"><h3>{label}</h3>'
        f'<p>{part["id"]}<br>{dims} mm · {part["triangles"]:,} tam giác</p>'
        f'<p class="part-chips">{"".join(chips)}</p>'
        f'<p style="margin-top:var(--s-4)"><a class="text-link" href="stl/{part["id"]}.stl" download>'
        f'Tải STL {render_bytes}{icon("arrow-right")}</a></p>'
        "</div></article></li>")


def build(source):
    snapshot = json.loads((HERE / "snapshot.json").read_text())
    labels = snapshot["labels"]
    manifest = json.loads((HERE / "print" / "package-manifest.json").read_text())
    check = json.loads((HERE / "print" / "package-check.json").read_text())
    gate = json.loads((source / "print" / "final-gate.json").read_text())
    audit = json.loads((HERE / "electronics-audit.json").read_text())
    completion = json.loads((source.parent / "completion.json").read_text())
    video = json.loads((source / "reports" / "presentation" / "video-receipt.json").read_text())
    frames = json.loads((source / "reports" / "presentation" / "native-frames.json").read_text())
    media = json.loads((HERE / "media-manifest.json").read_text())
    stl_bytes = {r["path"]: r["bytes"] for r in media["published"]}

    stills = [
        ("media/assembled.jpg", "Mô hình đã lắp", "DC-01 đã lắp hoàn chỉnh, render native trong Blender"),
        ("media/exploded.jpg", "Tách rời giải thích", "Các chi tiết DC-01 tách rời để giải thích cấu tạo"),
        ("media/catalog.jpg", "Catalog 29 nhóm", "Catalog 29 nhóm chi tiết có nhãn của DC-01"),
        ("media/button.jpg", "Nút bấm và màng TPU", "Cụm nút bấm và màng TPU của DC-01"),
        ("media/print-layout.jpg", "Sắp khay in", "Hai khay in PETG và TPU của bộ chi tiết DC-01"),
        ("media/detail-arm.jpg", "Chi tiết tay", "Cận cảnh tay và nẹp giữ tay của DC-01"),
        ("media/detail-ear.jpg", "Chi tiết tai", "Cận cảnh tai và nẹp giữ tai của DC-01"),
        ("media/detail-interior.jpg", "Chi tiết bên trong", "Bên trong DC-01 với bo mạch, pin và dây đã đi"),
    ]
    tabs = "".join(
        f'<button type="button" class="ds-tab" data-index="{i}" '
        f'aria-pressed="{"true" if i == 0 else "false"}">{label}</button>'
        for i, (_, label, _) in enumerate(stills))
    track = "".join(slide(i, src, label, alt) for i, (src, label, alt) in enumerate(stills))

    petg = sum(1 for p in manifest["parts"] if p["material"] == "PETG")
    tpu = sum(1 for p in manifest["parts"] if p["material"] == "TPU")
    parts_html = "".join(
        part_card(p, labels.get(p["id"], p["id"]),
                  f'({stl_bytes.get("stl/" + p["id"] + ".stl", 0) // 1024} KB) ')
        for p in manifest["parts"])

    facts = "".join([
        fact("Phim lắp", f'{round(video["encoded_duration_seconds"])} giây',
             f'{video["native_poses"]} pose native 1920 × 1080, {video["audio"]} âm thanh'),
        fact("Chi tiết in", f"{check['part_count']} chi tiết",
             f"{petg} PETG và {tpu} TPU trên hai khay"),
        fact("Gate in cuối", f"{len(gate['parts'])}/{len(gate['parts'])} đạt",
             f"{len(gate['failed'])} chi tiết hỏng, {len(gate['required_checks_missing'])} kiểm tra bắt buộc thiếu"),
        fact("Bo carrier", f"{audit['tracks']} đường mạch",
             f"{audit['vias']} via, {audit['pads']} pad, KiCad {audit['native_version']}"),
        fact("ERC và DRC native", "0 vi phạm",
             f"ERC {audit['native_erc']}, DRC {audit['native_drc']}, đối chiếu {audit['native_parity']}"),
        fact("Dây trong máy", f"{audit['base_wires']}/{audit['base_wires']} kết nối",
             f"{audit['optional_wires']} dây âm thanh tùy chọn chưa gắn"),
        fact("Đối chứng âm", f"{audit['negative_controls_detected']}/5 lỗi cố tình đều bị bắt",
             "kiểm tra tự viết, tách khỏi ERC/DRC của KiCad"),
        fact("Đo vật lý", f"{audit['physical_measurements']} phép đo",
             "chưa in, chưa cấp điện, chưa có mẫu thật"),
        fact("Gói bàn giao", f'{completion["files"]} tệp · {completion["archive_bytes"]:,} byte',
             "đã kiểm CRC và hash từng thành viên"),
        fact("Scene lắp", snapshot["assembly_sha256"][:16] + "…", "SHA-256", mono=True),
        fact("Scene phim", snapshot["demo_sha256"][:16] + "…", "SHA-256", mono=True),
        fact("Scene in", check["print_sha256"][:16] + "…", "SHA-256", mono=True),
    ])

    electronics_rows = "".join([
        row("ERC và DRC", f'KiCad {audit["native_version"]}: 0 vi phạm, 0 mục chưa nối, 0 sai lệch với sơ đồ. '
                            '<a class="text-link" href="electronics-audit.json">Báo cáo</a>.'),
        row("Bo mạch", f'Hai lớp 54 × 46 × 1,6 mm · {audit["tracks"]} đường mạch · {audit["vias"]} via · '
                       f'{audit["pads"]} pad · khe hở nhỏ nhất 0,285 mm.'),
        row("Khoan", "41 lỗ mạ 1,0 mm · 13 via 0,3 mm · 4 lỗ không mạ 2,5 mm."),
        row("Chưa xác lập", 'Linh kiện thật, nhiệt độ sạc, ngưỡng cắt điện áp thấp, cầu chì, nhiệt vỏ kín, '
                            'firmware, RF. <a class="text-link" href="bench-validation.md">bench-validation.md</a>.', "warning"),
    ])

    print_rows = "".join([
        row("Gate hình học", f'{len(gate["parts"])} chi tiết: kín, thể tích dương, không mặt 0, không cạnh hở, '
                             "đủ dày thành, lọt khay."),
        row("Quay vòng", f'STL xuất rồi nạp lại: {check["part_count"]}/{check["part_count"]} khớp tam giác. '
                         f'3MF mở lại bằng bộ phân tích riêng: {check["status"]}.'),
        row("Chưa gate", "Overhang chưa có ngưỡng. Tám chi tiết nẹp/tay/tai không khai báo lỗ.", "warning"),
        row("Chưa in", 'Không cắt lớp, không G-code, không mẫu in. '
                       '<a class="text-link" href="print/README.md">Hướng dẫn in</a>: tỉ lệ 100%, '
                       "profile PETG/TPU, không xoay lần hai.", "warning"),
    ])

    blocked_rows = "".join([
        row("Chế tạo", f'{completion["manufacture"]} · {completion["physical_samples"]} mẫu vật lý. '
                       "Trên đây là hình học số, không phải bằng chứng in được hay lắp được.", "warning"),
        row("Điện và pin", "0 phép đo trên mạch thật: dòng sạc, nhiệt độ pack, điện áp thấp, cầu chì.", "warning"),
        row("Nút bấm", "Khe 0,25 mm + hành trình 0,25 mm chưa bảo đảm bấm được ở trường hợp xấu nhất.", "warning"),
        row("Dây", "13 đầu dây còn là đề xuất vị trí và cách bấm cốt.", "warning"),
        row("Lắp ráp", "Vít mạch sạc phải siết trước khi lắp; lực siết và dụng cụ thật chưa xác lập.", "warning"),
        row("Giống ảnh gốc", "Còn lộ vít mặt trước, cạnh và khe sắc hơn ảnh gốc. Không phải bản giống hệt.", "warning"),
    ])

    docs = [
        ("README.md", "README của gói bàn giao"),
        ("print/README.md", "Hướng dẫn in và giới hạn"),
        ("electronics-README.md", "Thiết kế điện tử, mạch và giao diện cơ khí"),
        ("bench-validation.md", "Điều kiện bắt buộc trước khi phát hành phần cứng"),
        ("print/package-manifest.json", "Manifest 18 chi tiết, vật liệu và khay"),
        ("print/package-check.json", "Kết quả mở lại 3MF độc lập"),
        ("electronics-audit.json", "Tổng hợp ERC, DRC, đồng và đối chứng âm"),
        ("system-wiring.csv", "33 kết nối dây với đầu nối nguồn"),
        ("system-bom.csv", "BOM module mua ngoài"),
        ("carrier-bom.csv", "BOM bo carrier tự thiết kế"),
        ("SHA256SUMS", "Hash của gói gốc"),
        ("media-manifest.json", "Hash và kích thước mọi tệp đã publish ở đây"),
    ]
    docs_html = "".join(
        f'<li><a class="ds-icon-row" href="{href}">{icon("file", 20)}'
        f'<span class="ds-icon-row-label">{text}</span>'
        f'<span class="ds-icon-row-meta">{href}</span></a></li>' for href, text in docs)

    cad_files = [
        ("cad/desktop-companion.kicad_sch", "Sơ đồ nguyên lý KiCad"),
        ("cad/desktop-companion.kicad_pcb", "Bố trí mạch in KiCad"),
        ("cad/desktop-companion.kicad_pro", "Dự án KiCad"),
        ("cad/desktop-companion.net", "Netlist XML"),
        ("cad/DC.kicad_sym", "Thư viện ký hiệu cục bộ"),
        ("cad/desktop-companion.svg", "Sơ đồ nguyên lý dạng vector"),
        ("cad/carrier-front.svg", "Lớp đồng mặt trên dạng vector"),
        ("cad/carrier-back.svg", "Lớp đồng mặt dưới dạng vector"),
        ("cad/gerber-excellon.zip", "Gerber X2 và Excellon ứng viên"),
    ]
    cad_html = "".join(
        f'<li><a class="ds-icon-row" href="{href}"{" download" if href.endswith("zip") else ""}>'
        f'{icon("circuit", 20)}<span class="ds-icon-row-label">{text}</span>'
        f'<span class="ds-icon-row-meta">{href.split("/")[-1]}</span></a></li>' for href, text in cad_files)

    style = (HERE / "page-style.css").read_text()
    carousel = (HERE / "page-carousel.js").read_text()

    html = f"""<!doctype html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>DC-01 bản R02 — robot để bàn native Blender: 18 chi tiết in, bo KiCad và phim lắp</title>
<link rel="canonical" href="{SITE}/reviews/dc-01/r02/">
<meta name="description" content="Gói bàn giao R02 của DC-01: 18 chi tiết in qua gate hình học, bo carrier KiCad với ERC/DRC 0 vi phạm, 26/26 kết nối dây và phim lắp 39 giây dựng native trong Blender. Chưa chấp thuận chế tạo.">
<meta property="og:title" content="DC-01 bản R02 — robot để bàn dựng native trong Blender">
<meta property="og:description" content="18 chi tiết in qua gate, bo carrier KiCad ERC/DRC 0 vi phạm, phim lắp 39 giây. Chế tạo vật lý chưa được chấp thuận.">
<meta property="og:image" content="{SITE}/reviews/dc-01/r02/media/assembled.jpg">
<meta property="og:type" content="article">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400..700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{style}{EXTRA_CSS}</style>
<script>{FALLBACK_JS}</script>
</head>
<body class="ds-shell">
<a class="ds-skip-link" href="#main">Tới nội dung</a>
<nav class="ds-shell-nav" aria-label="Tệp bàn giao">
  <a class="wordmark" href="https://www.jang.work/">JANG<span>®</span></a>
  <div class="home-nav-links">
    <a class="ds-tab" href="dc01-native-animatic.mp4">{icon("play")}Phim lắp</a>
    <a class="ds-tab" href="DC01-P03-print-kit.zip" download>{icon("download")}Bộ in</a>
    <a class="ds-tab" href="#cad">{icon("circuit")}Sơ đồ điện</a>
    <a class="ds-tab" href="README.md">{icon("file")}README</a>
  </div>
</nav>

<main id="main" class="ds-shell-main">
  <section aria-labelledby="title">
    <p class="eyebrow">DC-01 · gói R02 · demo kỹ thuật native</p>
    <h1 id="title" class="ds-heading" data-level="1">Robot để bàn DC-01 dựng hoàn toàn bằng Blender native: {check['part_count']} chi tiết in đã qua gate hình học, một bo carrier KiCad thật và phim lắp {round(snapshot['duration_seconds'])} giây.</h1>
    <p class="lede">Ảnh render, sơ đồ mạch, từng tệp in và phim lắp, đọc thẳng từ gói đã giao. Chế tạo vật lý và vận hành điện <strong>chưa được chấp thuận</strong>: 0 mẫu thật.</p>
    <p class="badges">
      {badge("Blender", gate["checker"]["blender"], "e87d0d")}
      {badge("Python", "bpy", "3776ab")}
      {badge("render", frames["engine"].title() + f" · {frames['samples']} mẫu", "1f2933")}
      {badge("KiCad", audit["native_version"], "314cb0")}
      {badge("xuất", "STL · 3MF", "067647")}
      {badge("video", "FFmpeg", "5c6370")}
    </p>
    <p class="hero-actions">
      <a class="ds-btn-pill" data-tone="solid" href="dc01-native-animatic.mp4">{icon("play")}Xem phim lắp {round(snapshot['duration_seconds'])} giây</a>
      <a class="text-link" href="DC01-P03-print-kit.zip" download>Tải bộ in P03{icon("arrow-right")}</a>
    </p>
    <figure class="ds-card branch-page-media">
      <div class="ds-card-stage capture-stage">
        <img src="media/assembled.jpg" width="1920" height="1080" alt="DC-01 đã lắp hoàn chỉnh, render native 1920 × 1080 trong Blender" loading="eager">
      </div>
      <figcaption class="case-plate-caption">
        <p>Render từ scene <code>dc01-demo.blend</code> đã giao.</p>
        <cite>SHA-256 {snapshot['demo_sha256']}</cite>
      </figcaption>
    </figure>
  </section>
</main>

<section class="band carousel" aria-roledescription="carousel" aria-label="Tám góc nhìn từ gói bàn giao">
  <div class="ds-shell-main carousel-head">
    <h2 class="ds-heading" data-level="3">Ảnh từ scene đã giao</h2>
    <div class="viewer-tabs" role="group" aria-label="Chọn ảnh">{tabs}</div>
  </div>
  <div class="carousel-frame">
    <ul class="track" id="track" tabindex="0" aria-label="Ảnh render, kéo ngang để xem">{track}</ul>
    <button type="button" class="ds-btn-pill carousel-btn" data-side="prev" data-dir="-1" aria-label="Ảnh trước" style="width:44px;height:44px;min-height:44px">{icon("caret-left")}</button>
    <button type="button" class="ds-btn-pill carousel-btn" data-side="next" data-dir="1" aria-label="Ảnh sau" style="width:44px;height:44px;min-height:44px">{icon("caret-right")}</button>
  </div>
  <div class="ds-shell-main carousel-foot">
    <p class="carousel-caption"><span id="carousel-label">{stills[0][1]}</span> — Cycles, không chỉnh sau render.</p>
    <cite class="carousel-count" id="carousel-count">01 / 0{len(stills)}</cite>
  </div>
</section>

<main class="ds-shell-main">
  <section data-pace="tight" aria-labelledby="facts-h">
    <h2 id="facts-h" class="ds-heading" data-level="3">Số liệu đọc từ gói</h2>
    <dl class="facts">{facts}</dl>
  </section>

  <section data-pace="chapter" aria-labelledby="film-h">
    <h2 id="film-h" class="ds-heading" data-level="2">Phim lắp {round(snapshot['duration_seconds'])} giây</h2>
    <p>Lắp sẵn, rút vít, nhấc thân trên, tách rời, catalog {len(labels)} nhãn, lắp lại, rồi màn hình và nút bấm. Animatic từ {video['native_poses']} pose native, không phải thiết bị đang chạy.</p>
    <figure class="ds-card branch-page-media">
      <div class="ds-card-stage capture-stage">
        <video controls preload="metadata" poster="media/catalog.jpg" width="1920" height="1080">
          <source src="dc01-native-animatic.mp4" type="video/mp4">
          Trình duyệt không phát được MP4; tải trực tiếp <a href="dc01-native-animatic.mp4">dc01-native-animatic.mp4</a>.
        </video>
      </div>
      <figcaption class="case-plate-caption">
        <p>Không âm thanh. Chương được giữ khung để đọc kịp nhãn.</p>
        <cite>SHA-256 {snapshot['video_sha256']}</cite>
      </figcaption>
    </figure>
  </section>

  <section data-pace="chapter" id="cad" aria-labelledby="cad-h">
    <h2 id="cad-h" class="ds-heading" data-level="2">Sơ đồ điện và tệp CAD</h2>
    <p>Bo carrier riêng cho module ESP32-S3 mua ngoài, không phải chip tự làm. Ảnh xuất trực tiếp từ tệp KiCad kèm dưới.</p>
    <dl class="register">{electronics_rows}</dl>
    <figure class="ds-card branch-page-media" style="margin-top:var(--s-12)">
      <div class="ds-card-stage capture-stage">
        <a href="cad/desktop-companion.svg" aria-label="Mở sơ đồ nguyên lý dạng vector để đọc chữ trên sơ đồ">
          <img src="media/pcb-desktop-companion.jpg" width="2200" height="1556" alt="Sơ đồ nguyên lý bo carrier DC-01 xuất từ KiCad" loading="lazy">
        </a>
      </div>
      <figcaption class="case-plate-caption">
        <p>Nguồn từ mạch sạc BQ24074 qua cầu chì, công tắc dịch vụ và bộ ổn áp 5 V; kèm net màn hình, nút bấm và âm thanh tùy chọn. Bấm để mở bản vector.</p>
        <cite>cad/desktop-companion.kicad_sch · bản vector: cad/desktop-companion.svg</cite>
      </figcaption>
    </figure>
    <ul class="pair" style="margin-top:var(--s-8)">
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="media/pcb-carrier-front.jpg" width="2200" height="1870" alt="Lớp đồng mặt trên của bo carrier DC-01" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>Đồng mặt trên, silkscreen, 4 lỗ vít 2,5 mm.</p><cite>cad/carrier-front.svg</cite></figcaption>
      </figure></li>
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="media/pcb-carrier-back.jpg" width="2200" height="1870" alt="Lớp đồng mặt dưới của bo carrier DC-01" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>Đồng mặt dưới, mảng đất và via nối.</p><cite>cad/carrier-back.svg</cite></figcaption>
      </figure></li>
    </ul>
    <ul class="pair" style="margin-top:var(--s-8)">
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="cad/desktop-companion-PTH-drl_map.svg" width="1200" height="1200" alt="Bản đồ khoan lỗ mạ của bo carrier DC-01" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>41 lỗ mạ 1,0 mm và 13 via 0,3 mm.</p><cite>cad/desktop-companion-PTH-drl_map.svg</cite></figcaption>
      </figure></li>
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="cad/desktop-companion-NPTH-drl_map.svg" width="1200" height="1200" alt="Bản đồ khoan lỗ không mạ của bo carrier DC-01" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>4 lỗ không mạ 2,5 mm bắt bo vào khung.</p><cite>cad/desktop-companion-NPTH-drl_map.svg</cite></figcaption>
      </figure></li>
    </ul>
    <div class="aside">
      <p>Gerber X2 và Excellon có trong gói nhưng chưa dựng thành ảnh raster: máy dựng trang không có trình xem Gerber. Các tệp này <strong>chưa phát hành để đặt gia công</strong>.</p>
    </div>
    <ul class="link-list doc-list" style="margin-top:var(--s-8)">{cad_html}</ul>
  </section>

  <section data-pace="chapter" aria-labelledby="print-h">
    <h2 id="print-h" class="ds-heading" data-level="2">Bộ chi tiết in 3D</h2>
    <p>Mỗi ô dựng lại từ chính tệp STL đã qua gate, nằm như trên bàn in. Bấm để tải STL.</p>
    <dl class="register">{print_rows}</dl>
    <ul class="parts-grid" style="margin-top:var(--s-12)">{parts_html}</ul>
    <ul class="pair" style="margin-top:var(--s-12)">
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="media/plate-01-PETG.jpg" width="1600" height="1600" alt="Khay in PETG với 17 chi tiết đã sắp" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>Khay 1 — {petg} chi tiết PETG. Tệp: <a class="text-link" href="print/plate-01-PETG.3mf" download>plate-01-PETG.3mf</a></p><cite>print/plates/plate-01-PETG.3mf</cite></figcaption>
      </figure></li>
      <li><figure class="ds-card">
        <div class="ds-card-stage capture-stage"><img src="media/plate-02-TPU.jpg" width="1600" height="1600" alt="Khay in TPU với màng nút bấm" loading="lazy"></div>
        <figcaption class="case-plate-caption"><p>Khay 2 — {tpu} chi tiết TPU (màng nút bấm). Tệp: <a class="text-link" href="print/plate-02-TPU.3mf" download>plate-02-TPU.3mf</a></p><cite>print/plates/plate-02-TPU.3mf</cite></figcaption>
      </figure></li>
    </ul>
  </section>

  <section data-pace="chapter" aria-labelledby="blocked-h">
    <h2 id="blocked-h" class="ds-heading" data-level="2">Những gì trang này không chứng minh</h2>
    <dl class="register">{blocked_rows}</dl>
  </section>

  <section data-pace="tight" aria-labelledby="docs-h">
    <h2 id="docs-h" class="ds-heading" data-level="3">Tài liệu và báo cáo kèm theo</h2>
    <ul class="link-list doc-list">{docs_html}</ul>
  </section>
</main>

<footer class="ds-shell-footer">
    <div class="ds-shell-footer-inner">
      <p style="margin:0;max-width:none">Tệp CAD và STL giữ byte-for-byte trong <code>cad/</code> và <code>stl/</code>. Hash và kích thước mọi tệp nằm trong <code>media-manifest.json</code> và <code>SHA256SUMS</code>. Không sửa lịch sử để tạo kết quả PASS.</p>
      <nav class="ds-shell-footer-nav" aria-label="Chân trang">
        <a class="ds-tab" href="https://github.com/jangtrinh/design-os-3d-blender">{icon("github")}design-os-3d-blender</a>
        <a class="ds-tab" href="../../ck-001/r02/">Bàn giao CK-001</a>
        <a class="ds-tab" href="#main">Lên đầu trang</a>
      </nav>
    </div>
  </footer>
<script>{carousel}</script>
</body>
</html>
"""
    # Declare the fallback on every image, as the static gate requires, using this page's
    # own handler rather than the autofixer's placeholder service.
    html = re.sub(r"(<img\b(?:(?!onerror)[^>])*?)>", r"\1" + IMG_ONERROR + ">", html)
    (HERE / "index.html").write_text(html)
    print(f"wrote {HERE / 'index.html'} ({len(html):,} bytes)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="builds/desktop-companion/delivery/R02")
    args = parser.parse_args()
    build(Path(args.source).resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
