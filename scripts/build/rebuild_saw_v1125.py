# -*- coding: utf-8 -*-
"""
v11.25 based on v11.24 full package:
  1) DK_Saw.lua -> impact-instant judgement (ci+100ms, dodge locked at hit),
     baguette timeline OUT 100ms / HOLD 300ms / BACK 300ms, sineIn thrust.
     Fixes "dodge failed but not dead" (late SPACE no longer counts) and
     "delayed death" (judge moved from ci+900ms to ci+100ms).
  Charts/events untouched. Idempotent, deploys 3 roots, repacks full zip.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.24_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.25_GODplus_20261117.zip'
NEW_LUA = r'E:/UST_work/dk_miku/scripts/DK_Saw_v1125.lua'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P_SAW = 'DK_Duet/scripts/DK_Saw.lua'

lua_data = open(NEW_LUA, 'rb').read()

z = zipfile.ZipFile(BASE)
assert P_SAW in z.namelist(), 'DK_Saw.lua missing in base'
replace = {P_SAW: lua_data}

# repack full zip preserving all entries
tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, replace.get(item.filename, z.read(item.filename)))
z.close()
os.replace(tmp, OUT)

# deploy to 3 roots
for root in ROOTS:
    dst = os.path.join(root, 'scripts', 'DK_Saw.lua')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    open(dst, 'wb').write(lua_data)

# verify
zz = zipfile.ZipFile(OUT)
bad = zz.testzip()
assert bad is None, ('CRC fail', bad)
h = hashlib.md5(lua_data).hexdigest()
for root in ROOTS:
    dst = os.path.join(root, 'scripts', 'DK_Saw.lua')
    assert hashlib.md5(open(dst, 'rb').read()).hexdigest() == h, ('mismatch', root)
# verify no other content drifted vs base
zb = zipfile.ZipFile(BASE)
assert set(zb.namelist()) == set(zz.namelist()), 'item set changed'
drift = [n for n in zb.namelist() if hashlib.md5(zb.read(n)).hexdigest() != hashlib.md5(zz.read(n)).hexdigest()]
assert drift == [P_SAW], ('unexpected drift', drift)
zb.close(); zz.close()

print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      '| items', len(zz.namelist()) if False else len(os.listdir(os.path.dirname(OUT))),
      '| size', os.path.getsize(OUT), '| saw md5', h, '| drift', drift)
