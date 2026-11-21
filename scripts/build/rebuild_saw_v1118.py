# -*- coding: utf-8 -*-
"""
v11.18: DENG DENG CI (based on v11.17)
  - bell 1 (deng), bell 2 (deng), 3rd slot = SAW WHIR only (ci), no 3rd bell
  - removed playSound dkAlert3 at thrust; kept dkSawWhir
  - death sound / timing / baguette unchanged
Idempotent.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.17_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.18_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P = 'DK_Duet/scripts/DK_Saw.lua'

z = zipfile.ZipFile(BASE)
lua = z.read(P).decode('utf-8')
assert 'v11.16' in lua or 'v11.17' in lua or 'OFFICIAL' in lua

old = """            pcall(playSound, 'dkAlert3', 1)
            pcall(playSound, 'dkSawWhir', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
new = """            pcall(playSound, 'dkSawWhir', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
assert lua.count(old) == 1
lua = lua.replace(old, new)
# update version tag (v11.17 kept the v11.16 header string)
import re
lua = re.sub(r'v11\.1[67][^\n]*', 'v11.18 - DENG DENG CI (bell bell saw, no 3rd bell)', lua, count=1)
data = lua.encode('utf-8')

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, data if item.filename == P else z.read(item.filename))
z.close()
os.replace(tmp, OUT)

for root in ROOTS:
    open(os.path.join(root, 'scripts', 'DK_Saw.lua'), 'wb').write(data)

zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
assert "playSound, 'dkAlert3'" not in lua
assert lua.count("playSound, 'dkSawWhir'") == 1
assert lua.count("playSound, 'dkSawAttack'") == 1
for root in ROOTS:
    assert hashlib.md5(open(os.path.join(root,'scripts','DK_Saw.lua'),'rb').read()).hexdigest() == hashlib.md5(data).hexdigest()
print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
print('bell1:', lua.count("playSound, 'dkAlert1'"), 'bell2:', lua.count("playSound, 'dkAlert2'"),
      'bell3:', lua.count("playSound, 'dkAlert3'"), 'whir:', lua.count("playSound, 'dkSawWhir'"))
