"""Refresh or verify the checksum inventory for tracked house project files."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / 'House_Library_Design'
MANIFEST = PROJECT / 'data' / 'portable_manifest.json'
PREFIX = 'House_Library_Design/'


def current_entries():
    paths = subprocess.check_output(
        ['git', '-C', str(ROOT), 'ls-files', '--', PREFIX], text=True
    ).splitlines()
    entries = []
    for tracked in paths:
        relative = tracked.removeprefix(PREFIX)
        if relative == 'data/portable_manifest.json':
            continue
        path = PROJECT / relative
        if not path.is_file():
            raise FileNotFoundError(f'Tracked project file is missing: {path}')
        digest = hashlib.sha256()
        size = 0
        with path.open('rb') as stream:
            while chunk := stream.read(8 * 1024 * 1024):
                if size == 0 and chunk.startswith(b'version https://git-lfs.github.com/spec/v1'):
                    raise ValueError(f'LFS pointer instead of file: {path}. Run git lfs pull.')
                size += len(chunk)
                digest.update(chunk)
        entries.append({'path': relative, 'bytes': size, 'sha256': digest.hexdigest()})
    return entries


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='fail when the saved inventory is stale')
    args = parser.parse_args()
    expected = current_entries()
    if args.check:
        actual = json.loads(MANIFEST.read_text(encoding='utf-8'))
        if actual != expected:
            expected_by_path = {row['path']: row for row in expected}
            actual_by_path = {row['path']: row for row in actual}
            stale = sorted(path for path in actual_by_path.keys() | expected_by_path.keys()
                           if actual_by_path.get(path) != expected_by_path.get(path))
            raise SystemExit('Portable manifest is stale: ' + ', '.join(stale[:20]))
        print(f'Portable manifest verified: {len(expected)} tracked files.')
        return
    temporary = MANIFEST.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(expected, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(MANIFEST)
    print(f'Portable manifest refreshed: {len(expected)} tracked files.')


if __name__ == '__main__':
    main()
