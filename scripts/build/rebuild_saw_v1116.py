# -*- coding: utf-8 -*-
"""
v11.16: correct saw sound (based on v11.15)
  - THRUST plays QT official attack.ogg (sawblade whir / fly-by)  <-- the real saw sound
  - DEATH  keeps dkSawAttack = sawbladeHit (the "death" sound)   <-- only on real death
  - nothing else touched (rhythm / judge / baguette speed unchanged)
Idempotent: reads v11.15 zip as base, adds 1 ogg + replaces DK_Saw.lua.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.15_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.16_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
QATTACK = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/qt_psyched-up-edition_v22_0832a/assets/shared/sounds/hazard/attack.ogg'
P = 'DK_Duet/scripts/DK_Saw.lua'
WHIR = 'DK_Duet/sounds/dkSawWhir.ogg'

whir = open(QATTACK, 'rb').read()
z = zipfile.ZipFile(BASE)
lua = z.read(P).decode('utf-8')
assert 'v11.15' in lua

# thrust bell: replace death sound with whir
old = """            pcall(playSound, 'dkAlert3', 1)
            pcall(playSound, 'dkSawAttack', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
new = """            pcall(playSound, 'dkAlert3', 1)
            pcall(playSound, 'dkSawWhir', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)"""
assert lua.count(old) == 1
lua = lua.replace(old, new)
assert "playSound, 'dkSawAttack'" in lua   # death branch still there
lua = lua.replace('v11.15 - QT OFFICIAL (slow bag, robust death)',
                  'v11.16 - QT OFFICIAL (whir at thrust, hit at death)')
data = lua.encode('utf-8')

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        if item.filename == P:
            zo.writestr(item, data)
        else:
            zo.writestr(item, z.read(item.filename))
    zo.writestr(WHIR, whir)
z.close()
os.replace(tmp, OUT)

for root in ROOTS:
    open(os.path.join(root, 'scripts', 'DK_Saw.lua'), 'wb').write(data)
    open(os.path.join(root, 'sounds', 'dkSawWhir.ogg'), 'wb').write(whir)

zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
assert hashlib.md5(zz.read(WHIR)).hexdigest() == hashlib.md5(whir).hexdigest()
for root in ROOTS:
    assert hashlib.md5(open(os.path.join(root,'scripts','DK_Saw.lua'),'rb').read()).hexdigest() == hashlib.md5(data).hexdigest()
    assert hashlib.md5(open(os.path.join(root,'sounds','dkSawWhir.ogg'),'rb').read()).hexdigest() == hashlib.md5(whir).hexdigest()
print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
print('thrust whir:', lua.count("playSound, 'dkSawWhir'"), '| death hit:', lua.count("playSound, 'dkSawAttack'"))
