# -*- coding: utf-8 -*-
"""
v11.19: clean death (based on v11.18)
  - remove the extra dkSawAttack death sound (game engine plays its own death sfx)
  - health -1 -> 0 (engine doDeathCheck uses health<=0 edge; -1 caused fake-death render)
  - remove dkSawDeathVerify timer (no longer needed, God.killPlayer uses plain health=0)
  - keep: deng deng ci bells, baguette slow, saw whir at thrust
Idempotent.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.18_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.19_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P = 'DK_Duet/scripts/DK_Saw.lua'

z = zipfile.ZipFile(BASE)
lua = z.read(P).decode('utf-8')

old = """            else
                pcall(playSound, 'dkSawAttack', 1)
                sp('health', -1)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
                pcall(runTimer, 'dkSawDeathVerify', 0.12)
            end"""
new = """            else
                sp('health', 0)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
            end"""
assert lua.count(old) == 1
lua = lua.replace(old, new)

old2 = """    elseif tag == 'dkSawDeathVerify' then
        local h = 1
        pcall(function() h = getProperty('health') end)
        if type(h) == 'number' and h > 0 then sp('health', -1) end
    elseif tag == 'dkSawCleanup' then"""
new2 = """    elseif tag == 'dkSawCleanup' then"""
assert lua.count(old2) == 1
lua = lua.replace(old2, new2)

import re
lua = re.sub(r'v11\.1[678][^\n]*', 'v11.19 - clean death (health=0, engine sfx)', lua, count=1)

data = lua.encode('utf-8')
assert "playSound, 'dkSawAttack'" not in lua
assert "sp('health', 0)" in lua and "sp('health', -1)" not in lua
assert 'dkSawDeathVerify' not in lua

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
for root in ROOTS:
    assert hashlib.md5(open(os.path.join(root,'scripts','DK_Saw.lua'),'rb').read()).hexdigest() == hashlib.md5(data).hexdigest()
print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
