"""Package the verified revision-B scene and native Full HD media, preserving r01."""
import argparse
import html
import json
import shutil
import struct
import zipfile
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from project import BUILD,ROOT,write,sha,spec_path,contract_path


def load(path):
    return json.loads(Path(path).read_text())


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--presentation',required=True)
    ap.add_argument('--verification',required=True)
    ap.add_argument('--media',required=True)
    ap.add_argument('--visual-review',required=True)
    ap.add_argument('--revision',default='r02')
    args=ap.parse_args()
    pres,verify,media,review=map(lambda p:Path(p).resolve(),
                              (args.presentation,args.verification,args.media,args.visual_review))
    assert all(p.is_relative_to(ROOT) and p.exists() for p in (pres,verify,media,review))
    def step(name):return verify/'steps'/name/'attempt-0001'
    gate=load(step('final-gate')/'final-gate.json')
    roundtrip=load(step('reopen')/'glb-roundtrip.json')
    inspection=load(step('inspect')/'fit-report.json')
    inventory=load(step('inspect')/'mesh-inventory.json')
    layout_checks=load(step('inspect')/'layout-checks.json')
    exported=load(step('export')/'export-settings.json')
    media_record=load(media/'media-manifest.json')
    source=pres/'keyboard.blend'; glb=step('export')/'keyboard.glb'; scene_sha=sha(source)
    assert roundtrip['pass'] and roundtrip['glb_sha256']==sha(glb)==exported['glb_sha256']
    assert not gate['failed'] and not gate['required_checks_missing']
    assert gate['inputs']['scene_sha256']==scene_sha==media_record['scene_sha256']==exported['blend_sha256']
    assert layout_checks['status']=='pass'
    assert inspection['interfaces']['key_stem']['key_material_stem_collision_indices']==[]
    assert inspection['interfaces']['wide_guides']['collision_free']
    assert inspection['interfaces']['encoder_dshaft']['matching_rotations_collision_free']
    video=media_record['video']; stream=video['probe']
    assert [stream['width'],stream['height']]==[1920,1080] and int(stream['nb_read_frames'])==96
    assert video['full_decode']=='pass'
    shots=sorted(media.glob('CK-001-*.png'))
    assert len(shots)==11,len(shots)
    for path in shots:
        with path.open('rb') as handle: header=handle.read(24)
        assert header[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',header[16:24])==(1920,1080),path
    destination=BUILD/'delivery'/args.revision
    destination.mkdir(parents=True,exist_ok=False)
    files={'CK-001-B.blend':source,'CK-001-B.glb':glb,
           'media/'+video['file']:media/video['file'],
           'reports/visual-review.md':review,'reports/media-manifest.json':media/'media-manifest.json',
           'reports/stills.json':media/'stills.json','reports/fit-report.json':step('inspect')/'fit-report.json',
           'reports/layout-checks.json':step('inspect')/'layout-checks.json',
           'reports/final-gate.json':step('final-gate')/'final-gate.json',
           'reports/glb-roundtrip.json':step('reopen')/'glb-roundtrip.json',
           'reports/motion-report.json':pres/'motion-report.json',
           'reports/export-settings.json':step('export')/'export-settings.json',
           'design/interfaces.json':BUILD/'interfaces.json','design/layout.json':BUILD/'layout.json',
           'design/spec.json':spec_path(),'design/dimensions-contract.json':contract_path(),
           'design/design-basis.md':BUILD/'scripts/design_basis.md'}
    for path in shots:files['media/'+path.name]=path
    for path in (step('final-gate')/'stl').iterdir():files['stl/'+path.name]=path
    records=[]
    for rel,origin in files.items():
        target=destination/rel; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copy2(origin,target)
        assert sha(target)==sha(origin)
        records.append({'file':rel,'sha256':sha(target),'bytes':target.stat().st_size,
                        'source':origin.relative_to(ROOT).as_posix()})
    names=[o['name'] for o in inventory['objects']]
    count=lambda prefix:sum(n.startswith(prefix) for n in names)
    bom=[{'family':family,'quantity':qty,'scope':scope} for family,qty,scope in [
        ('Keycaps with integral cross receivers',count('RK_KEY_'),'Digital prototype; source-guided stem dimensions, retention force not tested'),
        ('Custom dual spacebar guides',count('RK_GUIDE_SLEEVE_'),'Coaxial sliding pair, 3 mm sampled stroke; friction/rattle untested'),
        ('Slotted aluminum knobs with staged D receivers',count('RK_KNOB_'),'Nominal D engagement and interference checked; fit/axial retention require coupon'),
        ('PEC11R reference-envelope encoders',count('RK_ENCODER_BODY_'),'Manufacturer mechanical baseline; exact electrical suffix not selected'),
        ('Custom encoder carriers',count('RK_ENCODER_CARRIER_')-count('RK_ENCODER_CARRIER_SCREW_'),'19.6x15 mm carrier with modeled mounting hardware'),
        ('Bonded encoder risers',count('RK_ENCODER_RISER_'),'Explicit 0.08 mm adhesive bond; strength/creep untested'),
        ('Encoder daughterboards',count('RK_ENCODER_DAUGHTERBOARD_'),'Mechanical envelopes and contact holes; no fabricated circuit'),
        ('PCB supports',count('RK_PCB_SUPPORT_'),'Explicit chassis-to-board support contact planes'),
        ('USB daughterboard',1,'Supported board and connector shell; footprint/netlist not manufacturer-qualified'),
        ('Per-key RGB emitter envelopes',count('RK_RGB_KEY_'),'Native emitter geometry; electrical/thermal/light-output model unqualified'),
        ('Perimeter RGB emitter envelopes',count('RK_RGB_LED_'),'Native emitter geometry in the acrylic cavity'),
        ('Main mounting plate',1,'Actual key, knob and status apertures'),('PCB',1,'1.6 mm envelope with actual clearance windows; no copper/netlist'),
        ('Acrylic frame',1,'8 mm envelope; transmissive material, not a uniformly emissive shell'),
        ('Lower case',1,'4 mm envelope with internal floor and actual mounting bores'),('Silicone foot envelopes',count('RK_FOOT_'),'14x5x2 mm')]]
    write(destination/'BOM.json',{'revision':'B','families':bom,'scene_sha256':scene_sha})
    status={'revision':'B','scene_sha256':scene_sha,'glb_sha256':sha(glb),'native_meshes':len(names),
            'envelope_mm':[284,92,32],'keys':count('RK_KEY_'),'knobs':count('RK_KNOB_'),
            'native_render_pixels':[1920,1080],'stills':len(shots),'video_frames':96,'fps':24,
            'gate_families':len(gate['parts']),'roundtrip_frames':sorted(map(int,roundtrip['frames'])),
            'max_surface_error_mm':max(o['surface_max_error_mm'] for b in roundtrip['frames'].values() for o in b['objects']),
            'digital_interfaces':'checked within the declared sampled scope','manufacture':'PHYSICAL_QUALIFICATION_PENDING',
            'original_owner_reference_bytes':'UNAVAILABLE; generated marketing images excluded'}
    write(destination/'status.json',status)
    readme=f'''# CK-001 revision B

Open `review.html` for the native Full HD images and four-second video. All eleven
shareable PNG images and all 96 movie frames were rendered by Blender at 1920x1080.
No image-generation or upscaling path was used for these assets.

The editable scene is `CK-001-B.blend`; `CK-001-B.glb` contains the product and one
scene animation. Source scene SHA256: `{scene_sha}`. Product meshes: {len(names)}.

## Substantive changes

Keycaps now have integral cross receivers and a shorter visible shell. The spacebar
has two integral guide pins and matching sleeves. Knobs have actual staged D bores
and matching sourced encoder-shaft envelopes, a custom carrier and modeled clamp
hardware. Main PCB clearance windows now fit those parts; PCB and USB daughterboard
have explicit support/contact planes. RGB comes from native LED geometry through
transmissive acrylic. Legends are attached to the actual cap surfaces.

## Evidence

See `reports/fit-report.json` for actual stem/receiver insertion, full 3 mm travel
sampled every 0.5 mm, spacebar guides and five encoder pairs. Digital geometry gates
and fresh STL re-import cover {len(gate['parts'])} representative manufactured part
families. GLB was imported into a fresh Blender process and compared at frames1/7/60.
PNG dimensions and complete video decode were checked. Earlier failed runs remain
in the project and were not rewritten as successful runs.

## Specific physical work remaining

Print/machine the receiver and D-fit specimens with the intended material/process,
measure insertion and retention forces, guide friction/rattle and repeat-cycle fit.
Test the bonded encoder risers for torque and creep; the adhesive joint is modeled,
not strength-qualified. Select exact encoder electrical suffix, switch/socket and
USB-C/daughterboard footprints, then complete PCB netlist/routing/ESD/power/firmware
and physical electrical tests. The switch cover/receiver is a custom source-guided
prototype and is not certified interchangeable with a commercial KS-33 switch.

The original owner image files remain unavailable to the local reference-hash
workflow. Native feature review is separate from exact image-to-image certification.
Generated social images from the preceding chat are deliberately excluded.

The STL directory contains dimensioned prototype geometry, not an approved factory
manufacturing release. The original r01 package remains untouched.
'''
    (destination/'README.md').write_text(readme)
    buttons=''.join('<button data-src="media/'+html.escape(p.name)+'">'+html.escape(p.stem.removeprefix('CK-001-'))+'</button>' for p in shots)
    page='''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CK-001 / Revision B</title><style>
*{box-sizing:border-box}body{margin:0;background:#101216;color:#f2f3f6;font:16px/1.65 system-ui,sans-serif}main{max-width:1280px;margin:auto;padding:48px 28px}small{letter-spacing:.18em;color:#97a9b8}h1{font-size:44px;margin:8px 0}p{color:#b6c1cc}nav{display:flex;gap:8px;flex-wrap:wrap;margin:22px 0}button,a{font:inherit;color:inherit;border:1px solid #454b55;border-radius:7px;padding:8px 13px;background:transparent;text-decoration:none}button{cursor:pointer}button:hover,button:focus{background:#343d45}img,video{width:100%;display:block;border-radius:12px;background:#ddd}.meta{display:flex;gap:36px;flex-wrap:wrap;margin:22px 0}.meta b{display:block;font-size:24px}.meta span{font-size:13px;color:#a6b4c1}.note{border:1px solid #524e40;background:#24231e;border-radius:12px;padding:24px;margin-top:28px;color:#dfd3b6}h2{font-size:24px;margin-top:36px}footer{color:#8597a4;font-size:13px;margin-top:28px}@media(max-width:650px){main{padding:26px 16px}h1{font-size:32px}}</style><main>
<small>DESIGN OS / BLENDER NATIVE</small><h1>CK-001 / Revision B</h1><p>Ngàm chữ thập, trục D, giá đỡ encoder, dẫn hướng spacebar và kết cấu PCB/USB đã được dựng và kiểm tra trong model.</p>
<div class="meta"><div><b>1920 × 1080</b><span>11 ảnh và video render native</span></div><div><b>58 phím / 5 núm</b><span>284 × 92 × 32 mm</span></div><div><b>3 mm</b><span>Hành trình phím được kiểm tra theo mẫu</span></div></div>
<p><a href="CK-001-B.blend">Blender</a> <a href="CK-001-B.glb">GLB</a> <a href="README.md">Báo cáo</a> <a href="BOM.json">Danh mục chi tiết</a></p><nav>'''+buttons+'''</nav>
<img id="hero" src="media/CK-001-hero.png" alt="CK-001 revision B, render từ Blender"><h2>Chuyển động và cấu trúc</h2>
<video controls loop preload="metadata" poster="media/CK-001-exploded.png"><source src="media/CK-001-animation-FullHD.mp4" type="video/mp4"></video>
<section class="note"><strong>Kiểm chứng thiết kế số đã mở rộng; thử nghiệm sản phẩm thật vẫn còn.</strong><br>Ngàm và trục D đã có hình học lắp ghép. Lực giữ, độ rơ, độ bền keo và vật liệu cần thử trên mẫu thật. Mạch điện/firmware và khả năng thay thế đúng linh kiện thương mại chưa được chấp thuận. Các ảnh trên được render từ file Blender của bản B; không dùng ảnh sinh lại để thay thế sản phẩm.</section>
<footer>Mọi ảnh chia sẻ trong bộ này là Full HD native. Hash model, báo cáo và kết quả đọc lại GLB nằm trong thư mục reports. Bản r01 và lịch sử chạy lỗi được giữ nguyên.</footer></main><script>document.querySelectorAll('button[data-src]').forEach(b=>b.onclick=()=>document.querySelector('#hero').src=b.dataset.src)</script></html>'''
    (destination/'review.html').write_text(page)
    for rel in ('BOM.json','status.json','README.md','review.html'):
        path=destination/rel; records.append({'file':rel,'sha256':sha(path),'bytes':path.stat().st_size,'source':'generated from verified revision-B evidence'})
    write(destination/'manifest.json',{'files':records,'scene_sha256':scene_sha,'status':status})
    archive=BUILD/('CK-001-'+args.revision+'-FullHD.zip')
    with zipfile.ZipFile(archive,'x',compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(destination.rglob('*')):
            if path.is_file(): handle.write(path,'CK-001-B/'+path.relative_to(destination).as_posix())
    with zipfile.ZipFile(archive) as handle: assert handle.testzip() is None
    print(json.dumps({'delivery':str(destination),'archive':str(archive),'files':len(records),
                      'archive_bytes':archive.stat().st_size,'scene_sha256':scene_sha,'status':status}))

if __name__=='__main__':main()
