"""Verify the generated public review bundle without starting a browser."""
from pathlib import Path
import argparse
import gzip
import hashlib
import json
import re
import sys
from pypdf import PdfReader


def verify(root):
    info = json.loads((root / 'build-info.json').read_text(encoding='utf-8'))
    page = (root / 'index.html').read_text(encoding='utf-8')
    marker = 'window.HOUSE_DATA='
    data, _ = json.JSONDecoder().raw_decode(page[page.index(marker) + len(marker):])
    for floor, item in data['models'].items():
        raw = b''.join(gzip.decompress((root / part).read_bytes()) for part in item['parts'])
        assert len(raw) == item['bytes'], f'Floor {floor} length mismatch'
        assert hashlib.sha256(raw).hexdigest() == item['sha256'], f'Floor {floor} hash mismatch'
        assert raw.startswith(b'glTF'), f'Floor {floor} invalid GLB'
    assert len(data['photos']) == info['photos']
    for photo in data['photos']:
        assert (root / photo['url']).exists(), photo['url']
    for link in re.findall(r'(?:href|src)="([^"<>]+)"', page):
        if link.startswith(('http:', 'https:', '#', 'data:', '${')):
            continue
        assert (root / link).exists(), link
    pdf = PdfReader(root / 'house-design.pdf')
    assert len(pdf.pages) == info['pdf_pages']
    assert 'Будинок' in pdf.pages[0].extract_text()
    assert 'window.CORNER_PANTRY=' in page
    assert '__HOUSE_DATA_JSON__' not in page
    assert 'window.loadHouseModel(i)' in page
    assert not list(root.rglob('*.blend')), 'Master must not be part of the published website'
    assert sum(p.stat().st_size for p in root.rglob('*') if p.is_file()) < 1_000_000_000
    print(json.dumps({'verified': True, 'floors': 2, 'photos': info['photos'], 'pdf_pages': len(pdf.pages),
                      'source_commit': info['source_commit']}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    verify(parser.parse_args().directory.resolve())
