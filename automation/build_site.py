"""Build public HTML and PDF from the current exported models and render gallery."""
from pathlib import Path
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import html
import io
import json
import os
import re
import shutil
import subprocess

from PIL import Image
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas
from build_viewer import ROOT, MARKER, read_asset, validate_glb


def sha(data):
    return hashlib.sha256(data).hexdigest()


def metadata():
    commit = os.environ.get('GITHUB_SHA') or subprocess.check_output(
        ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip()
    timestamp = int(subprocess.check_output(
        ['git', '-C', str(ROOT), 'show', '-s', '--format=%ct', commit], text=True).strip())
    handoff = (ROOT / 'HOUSE_HANDOFF_UK.md').read_text(encoding='utf-8')
    revision = re.search(r'чинна редакція\s+(\d+)', handoff, re.I).group(1)
    return {'source_commit': commit, 'source_date': datetime.fromtimestamp(timestamp, timezone.utc).isoformat(),
            'revision': int(revision)}


def make_pdf(output, views, image_paths, info, site_url):
    fonts = ROOT / 'web/fonts'
    pdfmetrics.registerFont(TTFont('House', str(fonts / 'DejaVuSans.ttf')))
    pdfmetrics.registerFont(TTFont('HouseBold', str(fonts / 'DejaVuSans-Bold.ttf')))
    width, height = landscape(A4)
    paper = colors.HexColor('#f6f2ea')
    ink = colors.HexColor('#302d28')
    muted = colors.HexColor('#766b5b')
    c = canvas.Canvas(str(output), pagesize=(width, height), pageCompression=1)
    c.setTitle('Будинок - альбом дизайну')
    c.setAuthor('House Design')
    c.setSubject(f"Редакція {info['revision']}, джерело {info['source_commit'][:8]}")

    def page_base(number):
        c.setFillColor(paper)
        c.rect(0, 0, width, height, fill=1, stroke=0)
        c.setFillColor(muted)
        c.setFont('House', 8)
        c.drawString(36, 22, f"Редакція {info['revision']}  /  {info['source_commit'][:8]}")
        c.drawRightString(width - 36, 22, f'{number:02d} / {len(views) + 1:02d}')

    page_base(1)
    c.bookmarkPage('contents')
    c.addOutlineEntry('Зміст', 'contents', level=0)
    c.setFillColor(ink)
    c.setFont('HouseBold', 31)
    c.drawString(36, height - 64, 'Будинок. Дизайн інтер’єру')
    c.setFont('House', 12)
    date = datetime.fromisoformat(info['source_date']).strftime('%d.%m.%Y')
    c.drawString(38, height - 91, f"Права секція  ·  редакція {info['revision']}  ·  {date}")
    c.setFillColor(muted)
    c.setFont('House', 10)
    c.drawString(38, height - 118, 'Плани поверхів і ракурси кімнат. Натисніть назву, щоб перейти до сторінки.')
    if len(views) > 60:
        raise ValueError('More than 60 views need a multi-page table of contents layout.')
    rows = (len(views) + 1) // 2
    spacing = min(18, 320 / max(1, rows - 1))
    for index, (key, title) in enumerate(views):
        column = index // rows
        row = index % rows
        x = 38 + column * 390
        y = height - 157 - row * spacing
        c.setFillColor(ink)
        c.setFont('House', 9)
        c.drawString(x, y, f'{index + 2:02d}  {title}')
        c.linkRect('', 'view_' + key, (x, y - 3, x + 370, y + 12), relative=0, thickness=0)
    c.setFont('House', 10)
    c.setFillColor(muted)
    c.drawString(38, 66, 'Інтерактивний 3D-перегляд:')
    c.setFillColor(ink)
    c.drawString(38, 48, site_url)
    c.linkURL(site_url, (36, 43, width - 36, 63), relative=0, thickness=0)
    c.showPage()
    for index, ((key, title), image_path) in enumerate(zip(views, image_paths), 2):
        page_base(index)
        c.bookmarkPage('view_' + key)
        c.addOutlineEntry(title, 'view_' + key, level=0)
        c.setFont('HouseBold', 16)
        c.setFillColor(ink)
        c.drawString(36, height - 45, title)
        with Image.open(image_path) as im:
            iw, ih = im.size
        max_width, max_height = width - 72, height - 106
        scale = min(max_width / iw, max_height / ih)
        w, h = iw * scale, ih * scale
        c.drawImage(ImageReader(str(image_path)), (width - w) / 2, 44 + (max_height - h) / 2,
                    width=w, height=h, preserveAspectRatio=True)
        c.setFont('House', 8)
        c.setFillColor(muted)
        c.drawCentredString(width / 2, 22, 'Зміст')
        c.linkRect('', 'contents', (width / 2 - 30, 17, width / 2 + 30, 32), relative=0, thickness=0)
        c.showPage()
    c.save()


def build(output, site_url):
    output.mkdir(parents=True, exist_ok=True)
    (output / 'models').mkdir(exist_ok=True)
    (output / 'photos').mkdir(exist_ok=True)
    info = metadata()
    data = {'models': {}, 'photos': []}
    for floor in (1, 2):
        path = ROOT / f'House_Browser_Viewer/House_Floor_{floor}.glb'
        raw = read_asset(path)
        validate_glb(raw, path)
        digest = sha(raw)
        parts = []
        for index, offset in enumerate(range(0, len(raw), 24 * 1024 * 1024)):
            name = f'models/floor-{floor}-{digest[:12]}-{index:02d}.gz'
            (output / name).write_bytes(gzip.compress(raw[offset:offset + 24 * 1024 * 1024], compresslevel=6, mtime=0))
            parts.append(name)
        data['models'][str(floor)] = {'parts': parts, 'bytes': len(raw), 'sha256': digest}
    views = json.loads((ROOT / 'House_Library_Design/data/gallery_views.json').read_text(encoding='utf-8'))
    image_paths = []
    for key, title in views:
        raw = read_asset(ROOT / 'House_Library_Design/previews' / f'{key}.png')
        stream = io.BytesIO()
        with Image.open(io.BytesIO(raw)) as im:
            im.convert('RGB').save(stream, 'JPEG', quality=92, optimize=True, progressive=True)
        content = stream.getvalue()
        name = f'photos/{key}-{sha(content)[:12]}.jpg'
        image_path = output / name
        image_path.write_bytes(content)
        image_paths.append(image_path)
        data['photos'].append({'title': title, 'url': name})
    template = (ROOT / 'House_Browser_Viewer/viewer_template.html').read_text(encoding='utf-8')
    old = 'ya[i]=await new Promise((e,t)=>s0.parse(o0(Gu.models[i]),"",n=>e(n.scene),t))'
    new = 'ya[i]=await window.loadHouseModel(i).then(b=>new Promise((e,t)=>s0.parse(b,"",n=>e(n.scene),t)))'
    if template.count(old) != 1:
        raise ValueError('Viewer model loader changed; review web integration before publication.')
    template = template.replace(old, new)
    old_image = 'src="data:${i.mime||\'image/jpeg\'};base64,${i.image}"'
    if template.count(old_image) != 1:
        raise ValueError('Viewer image markup changed; review web integration.')
    template = template.replace(old_image, 'src="${i.url}"')
    prefix = '<script>window.HOUSE_DATA=' + MARKER + ';</script>'
    loader = (ROOT / 'web/model_loader.js').read_text(encoding='utf-8')
    template = template.replace(prefix, prefix + '<script>' + loader + '</script>')
    template = template.replace(MARKER, json.dumps(data, ensure_ascii=False, separators=(',', ':')))
    links = '<a class="publish-link" href="house-design.pdf" target="_blank" rel="noopener">PDF-альбом кімнат</a>'
    links += '<a class="publish-link" href="credits.html" target="_blank" rel="noopener">Джерела моделей</a>'
    template = template.replace('</aside>', links + f'<p class="subtle">Редакція {info["revision"]} · {info["source_date"][:10]}</p></aside>')
    template = template.replace('</style>', '.publish-link{display:block;margin-top:12px;padding:10px 12px;border:1px solid #d8cfbf;border-radius:8px;background:#fffdf8;color:#40392e;text-decoration:none;text-align:center}</style>')
    (output / 'index.html').write_text(template, encoding='utf-8')
    make_pdf(output / 'house-design.pdf', views, image_paths, info, site_url)
    credits = (ROOT / 'House_Library_Design/ASSET_CREDITS.md').read_text(encoding='utf-8')
    (output / 'credits.html').write_text('<!doctype html><html lang="uk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Джерела моделей</title><style>body{max-width:1100px;margin:40px auto;padding:20px;font:15px system-ui;background:#f6f2ea;color:#302d28}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><a href="./">До будинку</a><h1>Джерела моделей і матеріалів</h1><pre>' + html.escape(credits) + '</pre></html>', encoding='utf-8')
    shutil.copyfile(ROOT / 'House_Browser_Viewer/THREE_LICENSE.txt', output / 'THREE_LICENSE.txt')
    (output / '.nojekyll').write_text('')
    info.update(floors=data['models'], photos=len(views), pdf_pages=len(views) + 1)
    (output / 'build-info.json').write_text(json.dumps(info, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(output), 'source_commit': info['source_commit'], 'photos': len(views),
                      'pdf_pages': len(views) + 1, 'total_mb': round(sum(p.stat().st_size for p in output.rglob('*') if p.is_file()) / 1e6, 1)}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / '.site-dist')
    parser.add_argument('--site-url', default='https://eyr1on.github.io/house-design/')
    args = parser.parse_args()
    build(args.output.resolve(), args.site_url)
