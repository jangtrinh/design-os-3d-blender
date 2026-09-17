"""Copy the actual C03/E02 engineering evidence into a new, checked local package."""
import html
import json
from pathlib import Path
import shutil
import socket
import struct
import sys
import zipfile

MFG = Path(__file__).resolve().parent
ROOT = MFG.parents[2]
sys.path.insert(0, str(MFG / 'qualification'))
from evidence_io import sha, load
from evidence_gate import validate_assessment


def main():
    assert str(ROOT.resolve()) == '/Users/jang/Products/design-os-3d-blender'
    assert socket.gethostname() == 'jangtrinhs-MacBook-Pro-2.local'
    destination = MFG / 'delivery/C03-E02'
    archive = MFG / 'CK-001-C03-E02-engineering.zip'
    assert not destination.exists() and not archive.exists()
    build = MFG / 'runs/mechanics-C03/steps/build/attempt-0001'
    gated = MFG / 'runs/gate-C03-final/steps/gate/attempt-0001'
    travel = MFG / 'runs/travel-C03/steps/travel/attempt-0001/maximum-travel.json'
    views = MFG / 'runs/C03-engineering-views'
    coupons = MFG / 'runs/coupons-C02/steps'
    scene = build / 'model.blend'
    scene_sha = sha(scene)
    gate, movement, view = load(gated / 'gate-report.json'), load(travel), load(views / 'view-manifest.json')
    assert gate['inputs']['scene_sha256'] == movement['scene_sha256'] == view['scene_sha256'] == scene_sha
    assert not gate['failed'] and not gate['required_checks_missing'] and movement['status'] == 'pass'
    assessment = load(MFG / 'qualification/C03/assessment.json')
    assert validate_assessment(ROOT, assessment)
    assert assessment['physical_records'] == 0 and assessment['status'] == 'INCOMPLETE_MANUFACTURING_EVIDENCE'
    freeze = load(MFG / 'electrical/freeze-E02-final.json')
    for name, digest in freeze['authoritative_files'].items():
        assert sha(MFG / 'electrical' / name) == digest, ('stale electrical source', name)
    assert freeze['headroom_truth']['guaranteed_headroom'] == 'NOT_ESTABLISHED'
    for directory in (gated, coupons / 'gate/attempt-0001'):
        receipt = load(directory / 'gate-report.json')
        assert not receipt['failed'] and not receipt['required_checks_missing']
        manifest = load(directory / 'stl/manifest.json')
        assert {p['id'] for p in manifest['parts']} == {p['id'] for p in receipt['parts']}
        for row in manifest['parts']:
            assert sha(directory / 'stl' / Path(row['file']).name) == row['sha256']

    sources = {}
    def add(path, relative=None):
        assert path.is_file() and path.resolve().is_relative_to(ROOT)
        key = relative or path.relative_to(MFG).as_posix()
        assert key not in sources and '..' not in Path(key).parts
        sources[key] = {'path': path, 'sha256': sha(path)}

    add(MFG / 'README.md')
    add(scene, 'CK-001-C03.blend')
    for dirname in ('mechanical', 'coupons', 'qualification'):
        for path in sorted((MFG / dirname).glob('*')):
            if path.is_file() and path.suffix in ('.py', '.json', '.md'):
                add(path)
    for path in sorted((MFG / 'qualification/C03').glob('*.json')):
        add(path)
    for name in freeze['authoritative_files']:
        add(MFG / 'electrical' / name)
    add(MFG / 'electrical/freeze-E02-final.json')
    for path in sorted((MFG / 'electrical/firmware').rglob('*')):
        if path.is_file() and '__pycache__' not in path.parts:
            key = path.relative_to(MFG).as_posix()
            if key not in sources:
                add(path)
    for name in ('firmware-host-test.json', 'arm-core-build.json'):
        add(MFG / 'electrical/history/E01-before-polarity-fix' / name,
            'electrical/inherited-E01/' + name)
    for folder in (gated, views, coupons / 'gate/attempt-0001', coupons / 'view/attempt-0001'):
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.suffix in ('.json', '.png', '.stl'):
                add(path)
    add(scene)
    add(build / 'changes.json')
    add(travel)
    add(coupons / 'build/attempt-0001/specimens.blend')
    for path in sorted((ROOT / 'plans/260917-keyboard-manufacturing/reports').glob('*.md')):
        add(path, 'reports/' + path.name)
    for name, digest in view['files'].items():
        path = views / name
        assert sha(path) == digest
        with path.open('rb') as handle:
            header = handle.read(24)
        assert struct.unpack('>II', header[16:24]) == (1920, 1080)

    status = {'mechanical_revision': 'C03', 'electrical_revision': 'E02',
              'scene_sha256': scene_sha, 'manufacture': 'BLOCKED',
              'digital_gate_families': len(gate['parts']), 'travel_keys': movement['keys_checked'],
              'travel_samples_mm': movement['samples_mm'], 'physical_records': 0,
              'required_physical_metrics': assessment['required_metrics'],
              'blocked_prerequisites': assessment['blocked_digital_prerequisites'],
              'electrical_logical_checks': freeze['validation']['logical_checks'],
              'electrical_negative_controls': freeze['validation']['negative_controls'],
              'guaranteed_rgb_headroom': 'NOT_ESTABLISHED',
              'scope': 'Engineering candidate, prototype specimens and evidence. No C03 animation, GLB or physical release.'}
    destination.mkdir(parents=True)
    records = []
    for relative, row in sorted(sources.items()):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(row['path'], target)
        assert sha(target) == row['sha256']
        records.append({'file': relative, 'sha256': row['sha256'], 'bytes': target.stat().st_size,
                        'source': row['path'].relative_to(ROOT).as_posix()})
    gallery = ''.join(f'<figure><img src="runs/C03-engineering-views/{file}" alt="{label}"><figcaption>{label}</figcaption></figure>'
                      for file, label in (('assembly-C03.png', 'Assembly geometry'), ('cap-C03.png', 'Full-stroke cap receiver'),
                                          ('collar-C03.png', 'Acrylic collar and chassis spacer')))
    document = '''<!doctype html><html lang="vi"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>CK-001 C03 / E02</title><style>body{margin:0;background:#15181d;color:#eceff4;font:16px/1.65 system-ui}main{max-width:1200px;margin:auto;padding:40px 24px}h1{font-size:36px}a{color:#c9ddff}figure{margin:28px 0}img{width:100%;border-radius:10px}figcaption{color:#b8c0ce}aside{padding:22px;background:#28251e;border:1px solid #645b45;border-radius:10px}code{overflow-wrap:anywhere}.links{display:flex;gap:24px;flex-wrap:wrap}</style>
<main><h1>CK-001 · C03 / E02</h1><p>12 nhóm chi tiết qua gate · 58 phím kiểm tra đến 3,2 mm · 37 kiểm tra điện logic và 7 phép thử lỗi.</p>
<div class="links"><a href="CK-001-C03.blend">Model Blender C03</a><a href="README.md">Báo cáo kỹ thuật</a><a href="electrical/logical-schematic.svg">Sơ đồ logic, chưa ERC</a><a href="qualification/BENCH-PROCEDURE.md">Quy trình thử mẫu</a><a href="status.json">Trạng thái và bằng chứng</a></div>
<p>Ba ảnh kỹ thuật được render trực tiếp ở 1920 × 1080 với vật liệu trung tính. Đây không phải bộ marketing, animation hay GLB mới.</p>''' + gallery + '''
<aside><strong>Chưa chấp thuận chế tạo.</strong><p>Chưa có phép đo vật lý nào trên 16 tiêu chí pilot. Giao diện switch thực, ERC, PCB DRC, firmware chạy trên thiết bị và quy trình lắp ráp/vật liệu vẫn mở. Điện áp dự phòng RGB chưa có giá trị bảo đảm.</p><p>STL đại diện và 16 mẫu thử dung sai phục vụ đánh giá mẫu. Mẫu số và kết quả unit test không phải vật phẩm đã chế tạo hoặc phép đo bench.</p></aside>
<p>Các đường dẫn nguồn trong báo cáo là lịch sử của project gốc. Source trong gói vẫn dùng helper của repository; gói này không tự nhận là một hệ thống rebuild độc lập. Media Revision B được giữ ở bộ bàn giao cũ và không đại diện C03.</p></main></html>'''
    (destination / 'review.html').write_text(document, encoding='utf-8')
    (destination / 'status.json').write_text(json.dumps(status, indent=2), encoding='utf-8')
    for name in ('review.html', 'status.json'):
        path = destination / name
        records.append({'file': name, 'sha256': sha(path), 'bytes': path.stat().st_size, 'source': 'generated from verified evidence'})
    (destination / 'manifest.json').write_text(json.dumps({'files': records, 'status': status}, indent=2))
    with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(destination.rglob('*')):
            if path.is_file():
                handle.write(path, 'CK-001-C03-E02/' + path.relative_to(destination).as_posix())
    with zipfile.ZipFile(archive) as handle:
        assert handle.testzip() is None
        assert len(handle.namelist()) == len(records) + 1
    print(json.dumps({'delivery': str(destination), 'archive': str(archive), 'files': len(records),
                      'archive_sha256': sha(archive), 'archive_bytes': archive.stat().st_size, 'manufacture': 'BLOCKED'}))


if __name__ == '__main__':
    main()
