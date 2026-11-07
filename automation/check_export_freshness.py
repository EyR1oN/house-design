"""Reject automatic publication of model edits with no updated export or review image."""
import json
import os
from pathlib import Path
import subprocess

event_path = os.environ.get('GITHUB_EVENT_PATH')
if event_path and os.environ.get('GITHUB_EVENT_NAME') == 'push':
    event = json.loads(Path(event_path).read_text())
    before, after = event.get('before', ''), event.get('after', '')
    if before.strip('0') and after:
        paths = subprocess.check_output(['git', 'diff', '--name-only', before, after], text=True).splitlines()
        master_changed = 'House_Library_Design/House_Library_Design.blend' in paths
        review_changed = any(p in ['House_Browser_Viewer/House_Floor_1.glb', 'House_Browser_Viewer/House_Floor_2.glb']
                             or p.startswith('House_Library_Design/previews/') for p in paths)
        if master_changed and not review_changed:
            raise SystemExit('Master changed, but exports and render images did not. Export the changed floor and update relevant renders before publishing.')
print('Export freshness check passed.')
