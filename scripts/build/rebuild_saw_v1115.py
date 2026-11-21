# -*- coding: utf-8 -*-
"""
v11.15: slow baguette + ROBUST death + saw sound (based on v11.14)
  - baguette tween +300ms (visual only): out 0.13->0.43, timer 0.17->0.47, in 0.16->0.46
  - death: health=-1 + delayed verify (health=0 is fragile, can be overwritten)
  - saw hit sound plays BOTH at thrust (3rd bell) and at death
  - judge timing (AFTER_3RD=300) UNCHANGED so reaction window stays 300ms
Idempotent: reads v11.14 zip as base, replaces only DK_Saw.lua.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.14_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.15_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P = 'DK_Duet/scripts/DK_Saw.lua'

z = zipfile.ZipFile(BASE)
lua = z.read(P).decode('utf-8')
assert 'v11.14' in lua

def rep(old, new, cnt=1):
    global lua
    assert lua.count(old) == cnt, (old[:70], lua.count(old))
    lua = lua.replace(old, new)

# 1) baguette flight +300ms (visual only), judge timing untouched
rep("'dkBagOutX', BAG_TAG, BAG_X1, 0.13, 'expoOut'", "'dkBagOutX', BAG_TAG, BAG_X1, 0.43, 'expoOut'")
rep("'dkBagOutY', BAG_TAG, BAG_Y1, 0.13, 'expoOut'", "'dkBagOutY', BAG_TAG, BAG_Y1, 0.43, 'expoOut'")
rep("'dkBagBack', 0.17)", "'dkBagBack', 0.47)")
rep("'dkBagInX', BAG_TAG, BAG_X0, 0.16, 'expoIn'", "'dkBagInX', BAG_TAG, BAG_X0, 0.46, 'expoIn'")
rep("'dkBagInY', BAG_TAG, BAG_Y0, 0.16, 'expoIn'", "'dkBagInY', BAG_TAG, BAG_Y0, 0.46, 'expoIn'")

# 2) robust death: saw hit sound at death + health=-1 + verify timer
old = """            else
                sp('health', 0)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
            end"""
new = """            else
                pcall(playSound, 'dkSawAttack', 1)
                sp('health', -1)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
                pcall(runTimer, 'dkSawDeathVerify', 0.12)
            end"""
rep(old, new)

# 3) verify timer handler keeps health <= 0
old2 = """    elseif tag == 'dkSawCleanup' then
        hideAll()
    end"""
new2 = """    elseif tag == 'dkSawDeathVerify' then
        local h = 1
        pcall(function() h = getProperty('health') end)
        if type(h) == 'number' and h > 0 then sp('health', -1) end
    elseif tag == 'dkSawCleanup' then
        hideAll()
    end"""
rep(old2, new2)

rep('v11.14 - QT OFFICIAL', 'v11.15 - QT OFFICIAL (slow bag, robust death)')

data = lua.encode('utf-8')

# remove stale .tmp from aborted run
tmpold = OUT + '.tmp'
if os.path.exists(tmpold):
    os.replace(tmpold, tmpold + '.dead')

tmp = tmpold
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, data if item.filename == P else z.read(item.filename))
z.close()
os.replace(tmp, OUT)

for root in ROOTS:
    p = os.path.join(root, 'scripts', 'DK_Saw.lua')
    open(p, 'wb').write(data)
    assert hashlib.md5(open(p, 'rb').read()).hexdigest() == hashlib.md5(data).hexdigest()

zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
print('OK md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
print('health=-1:', "sp('health', -1)" in lua,
      '| saw at death:', lua.count("playSound, 'dkSawAttack'"), 'x',
      '| verify timer:', 'dkSawDeathVerify' in lua,
      '| bag 0.43:', "0.43, 'expoOut'" in lua)
