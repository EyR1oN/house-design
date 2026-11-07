from pathlib import Path
R=Path(__file__).resolve().parents[1]
for path in [R/'ASSET_CREDITS.md',R.parent/'House_Browser_Viewer/ASSET_CREDITS.md']:
 b=path.read_bytes();at=b.find(b'- Arlos Dining Table')
 if at>=0:
  try:b[at:].decode('utf8')
  except UnicodeDecodeError:path.write_bytes(b[:at]+b[at:].decode('cp1251').encode('utf8'))
print('CREDITS_UTF8_CHECKED')
