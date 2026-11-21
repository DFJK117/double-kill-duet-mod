# -*- coding: utf-8 -*-
"""
v11.14: GOD+ saw fix
  - bells trimmed to 0.26s so 300ms gap does NOT overlap
  - GAP 600 -> 300 ms (one beat at 200 BPM)
  - sawblade sound plays on THRUST (3rd bell), not only on death
Idempotent: reads v11.13 zip as base, replaces only changed files.
"""
import os, io, zipfile, hashlib, subprocess, shutil

FF   = r'E:/UST_work/MIDIStudio_Project/tools/ffmpeg.exe'
BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.13_GODplus_20261116.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.14_GODplus_20261117.zip'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DUAL = r'E:/UST_work/dk_miku/DK_Dual'
MIKU = r'E:/UST_work/dk_miku/DK_Miku'
QT   = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/qt_psyched-up-edition_v22_0832a/assets/shared/sounds/hazard'
BAK  = r'I:/_trash_ust_work/saw_alert_original_20261117'
ROOTS = [GAME, DUAL, MIKU]

# ---- 1. trimmed bells from QT official sources ----
os.makedirs(BAK, exist_ok=True)
TRIM = {}
for n in (1, 2, 3):
    src = os.path.join(QT, {1:'alert.ogg', 2:'alertDouble.ogg', 3:'alertTriple.ogg'}[n])
    dst = os.path.join(BAK, 'dkAlert%d_trim.ogg' % n)
    subprocess.run([FF, '-y', '-hide_banner', '-loglevel', 'error', '-i', src,
                    '-t', '0.26', '-c:a', 'libvorbis', '-q:a', '6', dst], check=True)
    TRIM['sounds/dkAlert%d.ogg' % n] = open(dst, 'rb').read()
    print('trim', n, len(TRIM['sounds/dkAlert%d.ogg' % n]))

# ---- 2. patch DK_Saw.lua ----
z = zipfile.ZipFile(BASE)
sawpath = 'DK_Duet/scripts/DK_Saw.lua'
lua = z.read(sawpath).decode('utf-8')
assert 'local GAP = 600' in lua
lua = lua.replace('local GAP = 600', 'local GAP = 300')          # 1 beat @200BPM
lua = lua.replace('v11.13 - QT OFFICIAL', 'v11.14 - QT OFFICIAL')
# play sawblade sound at thrust (3rd bell)
old = """            pcall(playSound, 'dkAlert3', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
new = """            pcall(playSound, 'dkAlert3', 1)
            pcall(playSound, 'dkSawAttack', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
assert old in lua
lua = lua.replace(old, new)
# remove duplicate saw sound on death branch (already played at thrust)
old2 = """                pcall(playSound, 'dkSawAttack', 1)
                sp('health', 0)"""
new2 = """                sp('health', 0)"""
assert old2 in lua
lua = lua.replace(old2, new2)
lua = lua.encode('utf-8')
lua[-1:]  # noop

# ---- 3. rebuild zip from v11.13 base ----
changed = dict(TRIM)
changed[sawpath] = lua
tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        data = changed.get(item.filename, z.read(item.filename))
        zo.writestr(item, data)
z.close()
os.replace(tmp, OUT)
print('zip', OUT, len(changed), 'files changed')

# ---- 4. deploy to 3 roots ----
for root in ROOTS:
    for rel, data in changed.items():
        rel2 = rel[len('DK_Duet/'):] if rel.startswith('DK_Duet/') else rel
        p = os.path.join(root, rel2.replace('/', os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        open(p, 'wb').write(data)
    print('deployed', root)

# ---- 5. verify ----
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
for root in ROOTS:
    for rel, data in changed.items():
        rel2 = rel[len('DK_Duet/'):] if rel.startswith('DK_Duet/') else rel
        p = os.path.join(root, rel2.replace('/', os.sep))
        assert hashlib.md5(open(p, 'rb').read()).hexdigest() == hashlib.md5(data).hexdigest(), p
print('OK md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest(), 'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
