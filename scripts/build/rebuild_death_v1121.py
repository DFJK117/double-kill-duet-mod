# -*- coding: utf-8 -*-
"""
v11.21 based on v11.20 full zip:
  + scripts/DK_Death.lua : watermark "DFJK117 GOD+", Chinese death cause on top
                           of death animation (camOther upper-middle), key 1=+5s
  + fonts/dkCN.ttf       : 15KB subset Chinese font (setTextFont dkCN.ttf)
  ~ DK_God.lua           : killPlayer(cause) stamps dkDeathCause at 3 kill sites
  ~ DK_Saw.lua           : stamp dkDeathCause='saw' on failed dodge
Idempotent, 3 roots, full repack.
"""
import os, zipfile, hashlib, shutil

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.20_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.21_GODplus_20261117.zip'
DEATH_LUA = r'E:/UST_work/dk_miku/scripts/DK_Death_v1121.lua'
CN_FONT   = r'E:/UST_work/dk_miku/scripts/dkCN.ttf'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P_GOD = 'DK_Duet/scripts/DK_God.lua'
P_SAW = 'DK_Duet/scripts/DK_Saw.lua'
P_DEATH = 'DK_Duet/scripts/DK_Death.lua'
P_FONT  = 'DK_Duet/fonts/dkCN.ttf'

z = zipfile.ZipFile(BASE)

# ---- modify DK_God.lua ----
god = z.read(P_GOD).decode('utf-8')
# 1) signature + stamp inside killPlayer
old_sig = 'local function killPlayer()\n'
new_sig = 'local function killPlayer(cause)\n'
assert god.count(old_sig) == 1, 'killPlayer signature'
god = god.replace(old_sig, new_sig)
old_stamp = "    sp('health', 0)\n    sv('dkGodLastKill', killCount)\n"
new_stamp = "    sp('health', 0)\n    sv('dkGodLastKill', killCount)\n    sv('dkDeathCause', cause or 'miss')\n"
assert god.count(old_stamp) == 1, 'killPlayer stamp point'
god = god.replace(old_stamp, new_stamp)
# 2) three call sites (context-anchored)
a = "                    sv('dkGodOppWarnKills', oppWarnKillCount)\n                    killPlayer()"
b = "                    sv('dkGodOppWarnKills', oppWarnKillCount)\n                    killPlayer('opwarn')"
assert god.count(a) == 1, 'opwarn call'
god = god.replace(a, b)
a = "    if noteType == TRAP_TYPE and not botPlaying() then\n        killPlayer()\n    end"
b = "    if noteType == TRAP_TYPE and not botPlaying() then\n        killPlayer('trap')\n    end"
assert god.count(a) == 1, 'trap call'
god = god.replace(a, b)
a = "    if noteType == WARN_TYPE and not botPlaying() then\n        killPlayer()\n    end"
b = "    if noteType == WARN_TYPE and not botPlaying() then\n        killPlayer('warn')\n    end"
assert god.count(a) == 1, 'warn call'
god = god.replace(a, b)

# ---- modify DK_Saw.lua ----
saw = z.read(P_SAW).decode('utf-8')
a = "                else\n                    sp('health', 0)\n                    pcall(cameraFlash, 'game', 'FF2222', 0.4, true)"
b = "                else\n                    sp('health', 0)\n                    pcall(setVar, 'dkDeathCause', 'saw')\n                    pcall(cameraFlash, 'game', 'FF2222', 0.4, true)"
assert saw.count(a) == 1, 'saw death branch'
saw = saw.replace(a, b)

death_data = open(DEATH_LUA, 'rb').read()
font_data  = open(CN_FONT, 'rb').read()
replace = {
    P_GOD: god.encode('utf-8'),
    P_SAW: saw.encode('utf-8'),
}

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, replace.get(item.filename, z.read(item.filename)))
    # new files
    zo.writestr(P_DEATH, death_data)
    zo.writestr(P_FONT, font_data)
z.close()
os.replace(tmp, OUT)

# deploy to 3 roots
for root in ROOTS:
    for rel, data in list(replace.items()) + [(P_DEATH, death_data), (P_FONT, font_data)]:
        dst = os.path.join(root, rel.split('/',1)[1].replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)

# verify
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
all_files = dict(replace)
all_files[P_DEATH] = death_data
all_files[P_FONT] = font_data
for rel, data in all_files.items():
    h = hashlib.md5(data).hexdigest()
    assert hashlib.md5(zz.read(rel)).hexdigest() == h, ('zip mismatch', rel)
    for root in ROOTS:
        dst = os.path.join(root, rel.split('/',1)[1].replace('/', os.sep))
        assert hashlib.md5(open(dst,'rb').read()).hexdigest() == h, ('root mismatch', root, rel)

# lua compile all
from lupa import LuaRuntime
L = LuaRuntime(); bad = []
for n in zz.namelist():
    if n.endswith('.lua'):
        s = zz.read(n).decode('utf-8', errors='replace')
        r = L.eval('(function(s) local f,e=load(s) return {ok=(f~=nil),err=tostring(e)} end)(%r)' % s)
        if r['ok'] != True: bad.append((n, r['err']))
print('LUA compile bad:', bad if bad else 'NONE')
print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
