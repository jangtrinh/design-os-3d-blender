"""Package only source-matched, actually checked outputs; preserve every prior run."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import sys
import zipfile
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import ROOT,BUILD,write,sha


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--roundtrip-report',required=True)
    args=parser.parse_args()
    pres=BUILD/'runs/presentation-r02/steps/presentation/attempt-0001'
    verify=BUILD/'runs/verification-r02/steps'
    media=BUILD/'runs/media-r01/steps/media/attempt-0001'
    report=Path(args.roundtrip_report).resolve()
    assert report.is_relative_to(BUILD)
    roundtrip=json.loads(report.read_text())
    gate=json.loads((verify/'final-gate/attempt-0001/final-gate.json').read_text())
    settings=json.loads((verify/'export/attempt-0001/export-settings.json').read_text())
    movie=json.loads((media/'media-manifest.json').read_text())
    scene_sha=sha(pres/'keyboard.blend')
    glb=verify/'export/attempt-0001/keyboard.glb'
    assert roundtrip['pass'] and roundtrip['mesh_names_match'],'reimport must actually pass'
    assert roundtrip['glb_sha256']==sha(glb)==settings['glb_sha256']
    assert settings['blend_sha256']==gate['inputs']['scene_sha256']==movie['scene_sha256']==scene_sha
    assert not gate['failed'] and not gate['required_checks_missing']
    assert len(roundtrip['frames'])==3 and len(roundtrip['expected_mesh_names'])==496
    assert len(movie['frames'])==96 and movie['video']['full_decode']=='pass'
    destination=BUILD/'delivery/r01'
    destination.mkdir(parents=True,exist_ok=False)
    files={
        'CK-001.blend':pres/'keyboard.blend','CK-001.glb':glb,
        'CK-001-hero.png':media/'CK-001-hero.png',
        'CK-001-exploded.png':media/'CK-001-exploded.png',
        'CK-001-bottom.png':media/'CK-001-bottom.png',
        'CK-001-animatic.mp4':media/'CK-001-animatic.mp4',
        'details/keycaps.png':pres/'key-detail.png','details/rotary-knob.png':pres/'knob-detail.png',
        'details/top.png':pres/'top.png','reports/glb-roundtrip.json':report,
        'reports/final-gate.json':verify/'final-gate/attempt-0001/final-gate.json',
        'reports/layout-checks.json':verify/'inspect/attempt-0001/layout-checks.json',
        'reports/fit-report.json':verify/'inspect/attempt-0001/fit-report.json',
        'reports/motion-report.json':pres/'motion-report.json',
        'reports/media-manifest.json':media/'media-manifest.json',
        'reports/export-settings.json':verify/'export/attempt-0001/export-settings.json',
        'reports/visual-review.md':ROOT/'plans/260917-reference-keyboard/reports/final-visual-review.md',
        'design/layout.json':BUILD/'layout.json','design/spec.json':BUILD/'spec.json',
        'design/dimensions-contract.json':BUILD/'dimensions-contract.json',
        'design/design-basis.md':BUILD/'scripts/design_basis.md',
    }
    for path in (verify/'final-gate/attempt-0001/stl').iterdir(): files['stl/'+path.name]=path
    records=[]
    for relative,source in files.items():
        target=destination/relative
        target.parent.mkdir(parents=True,exist_ok=True)
        assert not target.exists()
        shutil.copy2(source,target)
        digest=sha(source)
        assert sha(target)==digest
        records.append({'file':relative,'sha256':digest,'bytes':target.stat().st_size,
                        'source':source.relative_to(ROOT).as_posix()})
    bom=[{'part':name,'quantity':qty,'qualification':scope} for name,qty,scope in [
        ('Keycaps 1U',57,'Digital shell geometry; stem receiver not qualified'),
        ('Wide keycap',1,'35 x 16.2 x 9.5 mm specimen; stabilizer/retention not qualified'),
        ('Slotted rotary knobs',5,'16 x 18 mm; circular 6 mm bore, D-flat/shaft fit not qualified'),
        ('Representative switch assemblies',58,'15.6 x 15.6 x 11 mm combined envelope; no electrical model'),
        ('Black mounting plate',1,'1.5 mm nominal, actual key and mounting apertures'),
        ('Representative PCB',1,'1.6 mm envelope; not a netlist/fabrication design'),
        ('RGB acrylic frame',1,'8 mm nominal; static baked color texture'),
        ('Lower chassis',1,'4 mm nominal envelope; digital geometry only'),
        ('Feet',4,'14 x 5 x 2 mm nominal'),('Spacers',4,'Generic hollow envelopes; threads not qualified'),
        ('Chassis screws',8,'M3 nominal shank envelopes'),('Hub screw details',4,'Visual details only'),
        ('USB-C envelope',1,'Appearance/placement only'),('Status indicator envelopes',3,'No electrical function')]]
    write(destination/'BOM.json',bom)
    maximum=max(row['surface_max_error_mm'] for block in roundtrip['frames'].values() for row in block['objects'])
    status={'scene_sha256':scene_sha,'glb_sha256':sha(glb),'native_meshes':496,'keys':58,'knobs':5,
            'envelope_mm':[284,92,32],'gate_part_families':7,'motion_frames':[1,96],'fps':24,
            'roundtrip_frames':[1,7,60],'surface_tolerance_mm':.05,'max_surface_error_mm':maximum,
            'media':'reviewed','motion':'sampled-pass','digital_geometry':'pass',
            'manufacture':'BLOCKED','original_reference_hash_review':'BLOCKED_REFERENCE_BYTES_UNAVAILABLE'}
    write(destination/'status.json',status)
    text=f'''# CK-001 native keyboard reconstruction

Open `review.html` for the images and four-second animatic. `CK-001.blend` is editable
in Blender 5.2. `CK-001.glb` contains the product, one merged 96-frame animation and
embedded RGB texture. The scene has 58 keys, 5 knobs and 496 product meshes.

## Verified digital scope

The overall modeled envelope is 284 x 92 x 32 mm. Form and final production gates
passed for seven representative part families, including fresh STL re-import.
Layout, 58 switch envelopes, sampled 0/0.5/1/1.5 mm key travel and 58 drivers were
checked. GLB re-import matches all 496 meshes at frames 1, 7 and 60 under 0.05 mm
surface/bounds criteria. Recorded maximum surface metric: {maximum:.8f} mm.
Video is 384 x 288, 24 fps, 96 decoded frames, four seconds. Hero/exploded images
are 1024 x 768; closeups and underside are verification views.

## Not a manufacturing release

Manufacture remains **BLOCKED**. Keycap stem receivers, the knob D-flat, selected
switch/socket/encoder hardware, screw engagement, PCB/netlist, electrical behavior,
material/process and physical fit/load/thermal trials are not qualified. STL files
are dimensioned digital specimens, not a validated printable functional keyboard kit.
The old blueprint's 41 mm side annotation conflicts with the later catalog's 32 mm;
the later envelope is the current design choice. The local knob neck and PCB rebate
are declared adaptations, not hidden dimensions measured from a photograph.

Independent review inspected actual images and saved geometry for visible features.
Original uploaded reference-image bytes were unavailable to the local tools, so the
formal native-review reference-hash packet remains blocked. No 100% likeness score
or authenticated independent-image certificate is claimed.

## Source and repeatability

The full editable project remains at `{BUILD}`. Native pipeline manifests and
append-only attempt journals are retained under that project. Use a new run directory
for a deliberate rebuild; never erase earlier failed attempts to force resumption.
The display package is self-contained for viewing; rebuild scripts use the main
repository's helpers and have not been relabeled as a standalone application.

The geometric gate exposed and fixed a real reusable bug: a 200 mm axial-ray limit
missed holes on a 284 mm plate. Checker 1.0.1 uses projected axis extents; all 28 gate
regressions pass. The build also exposed unused knob vertices, foreign-scene GLB
selection and a nearest-normal containment false positive. Original evidence is kept.

Scene SHA-256: `{scene_sha}`.
'''
    (destination/'README.md').write_text(text,encoding='utf-8')
    html='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>CK-001 | Native Blender review</title><style>
*{box-sizing:border-box}body{margin:0;background:#101216;color:#eef0f5;font:16px/1.6 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:44px 28px}header{display:flex;align-items:end;justify-content:space-between;gap:24px}small{letter-spacing:.16em;color:#a4afbf;font-size:12px}h1{font-size:40px;margin:6px 0;font-weight:650}p{color:#b7c0cf}a,button{color:inherit}a{padding:10px 16px;border:1px solid #454b56;border-radius:8px;text-decoration:none;display:inline-block}nav{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}button{font:inherit;border:1px solid #454b56;background:transparent;padding:9px 14px;border-radius:8px;cursor:pointer}button:focus,button:hover{background:#303640}figure{margin:0}figure img{width:100%;display:block;border-radius:14px;background:#d8d8d8}.meta{display:flex;gap:30px;flex-wrap:wrap;padding:24px 0}.meta strong{font-size:22px;display:block}.meta span{color:#9daabb;font-size:13px}.grid{display:grid;grid-template-columns:1fr 1fr;gap:24px;margin:24px 0}.grid img,video{width:100%;border-radius:12px}h2{font-size:22px}aside{padding:22px;border:1px solid #565346;border-radius:12px;background:#25231d;color:#ddcfaf}footer{margin-top:32px;font-size:13px;color:#8e9bad}@media(max-width:700px){header{display:block}h1{font-size:32px}.grid{grid-template-columns:1fr}main{padding:25px 18px}}
</style><main><header><div><small>DESIGN OS / BLENDER NATIVE</small><h1>CK-001</h1><p>Bàn phím tham chiếu, mô hình và kiểm chứng số.</p></div><div><a href="CK-001.blend">Blender</a> <a href="CK-001.glb">GLB</a> <a href="README.md">Báo cáo</a></div></header>
<div class="meta"><div><strong>284 × 92 × 32</strong><span>Kích thước mô hình, mm</span></div><div><strong>58 / 5</strong><span>Phím / núm xoay</span></div><div><strong>96 frames</strong><span>Animation, 24 fps</span></div><div><strong>7 nhóm chi tiết</strong><span>Gate hình học và STL đọc lại</span></div></div>
<nav><button onclick="show('CK-001-hero.png')">Tổng thể</button><button onclick="show('CK-001-exploded.png')">Tháo rời</button><button onclick="show('details/top.png')">Mặt trên</button><button onclick="show('CK-001-bottom.png')">Mặt dưới</button></nav>
<figure><img id="hero" src="CK-001-hero.png" alt="Mô hình bàn phím CK-001"></figure><h2>Chi tiết đã dựng</h2><div class="grid"><img src="details/keycaps.png" alt="Keycap và chữ trên phím"><img src="details/rotary-knob.png" alt="Rãnh thực trên núm xoay"></div>
<h2>Animatic đã kiểm tra</h2><video controls loop preload="metadata" poster="CK-001-exploded.png"><source src="CK-001-animatic.mp4" type="video/mp4"></video>
<p>File GLB đã được nhập lại và đối chiếu hình học, vị trí và chuyển động tại ba frame. Các báo cáo chi tiết nằm trong thư mục <code>reports</code>.</p>
<aside><strong>Chưa chấp thuận chế tạo.</strong> Kết quả trên là kiểm chứng tài sản số. Giao diện stem/keycap, trục D, phần cứng và mạch điện cụ thể, vật liệu và thử nghiệm thực vẫn chưa được xác minh. Ảnh tham chiếu gốc chưa có file local để khóa hash; không có chứng nhận độ giống tuyệt đối.</aside>
<footer>Source, các lần chạy thất bại, báo cáo và journal được giữ trong project. Không sửa lịch sử để tạo kết quả PASS.</footer></main><script>function show(path){document.getElementById('hero').src=path}</script></html>'''
    (destination/'review.html').write_text(html,encoding='utf-8')
    for relative in ('BOM.json','status.json','README.md','review.html'):
        path=destination/relative
        records.append({'file':relative,'sha256':sha(path),'bytes':path.stat().st_size,'source':'generated from checked evidence'})
    write(destination/'manifest.json',{'files':records,'scene_sha256':scene_sha,'status':status})
    archive=BUILD/'CK-001-review-r01.zip'
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(destination.rglob('*')):
            if path.is_file(): handle.write(path,'CK-001/'+path.relative_to(destination).as_posix())
    with zipfile.ZipFile(archive) as handle: assert handle.testzip() is None
    print(json.dumps({'delivery':str(destination),'archive':str(archive),'files':len(records),
                      'archive_bytes':archive.stat().st_size,'archive_sha256':sha(archive)}))


if __name__=='__main__': main()
