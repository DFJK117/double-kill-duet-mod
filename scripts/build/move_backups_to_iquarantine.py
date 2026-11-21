# -*- coding: utf-8 -*-
"""Move all backup/legacy dirs from E: to I: quarantine, keeping E: paths alive via junctions.
   Scripts that hardcode E:/UST_work/.../_backup_* keep working unchanged."""
import os, glob, shutil, subprocess

E = 'E:/UST_work'
DEST = 'I:/_trash_ust_work'
os.makedirs(DEST, exist_ok=True)

targets = []
targets += sorted(glob.glob(E + '/dk_miku/_backup_*'))
targets += sorted(glob.glob(E + '/dk_miku/_old_*'))
targets += sorted(glob.glob(E + '/_backup_*'))
targets += sorted(glob.glob(E + '/_archive_*'))

report = []
for src in targets:
    name = os.path.basename(src)
    # avoid collision: dk_miku/_backup_X vs E:/_backup_X share the name
    sub = 'dk_miku' if '/dk_miku/' in src.replace('\\', '/') else 'root'
    dst = os.path.join(DEST, sub, name)
    if os.path.islink(src) or (os.path.exists(src) and os.path.isjunction(src) if hasattr(os.path, 'isjunction') else False):
        report.append((name, 'SKIP already-link'))
        continue
    if os.path.exists(dst):
        report.append((name, 'SKIP dest-exists'))
        continue
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    try:
        shutil.move(src, dst)
        # create junction at the original E: path -> new I: location
        ps = ('New-Item -ItemType Junction -Path "%s" -Target "%s" | Out-Null'
              % (src.replace('/', '\\'), dst.replace('/', '\\')))
        r = subprocess.run(['powershell', '-NoProfile', '-NonInteractive', '-Command', ps],
                           capture_output=True, text=True)
        ok = os.path.exists(os.path.join(src, '.'))
        report.append((name, 'MOVED junction=' + str(ok) + (' rc=' + str(r.returncode) if r.returncode else '')))
    except Exception as e:
        report.append((name, 'FAIL ' + str(e)[:120]))

for name, status in report:
    print(name, '->', status)
print('total', len(report))
