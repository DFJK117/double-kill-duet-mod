# -*- coding: utf-8 -*-
"""
v11.17: identical bells (based on v11.16)
  - dkAlert2.ogg and dkAlert3.ogg := dkAlert1.ogg content (all 3 bells identical, first-bell tone)
  - saw whir at thrust, death hit unchanged (v11.16 behaviour kept)
  - Lua untouched
Idempotent.
"""
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.16_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.17_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']

z = zipfile.ZipFile(BASE)
bell = z.read('DK_Duet/sounds/dkAlert1.ogg')   # trimmed first bell from v11.14

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        data = z.read(item.filename)
        if item.filename in ('DK_Duet/sounds/dkAlert2.ogg', 'DK_Duet/sounds/dkAlert3.ogg'):
            data = bell
        zo.writestr(item, data)
z.close()
os.replace(tmp, OUT)

for root in ROOTS:
    for f in ('dkAlert1.ogg','dkAlert2.ogg','dkAlert3.ogg'):
        open(os.path.join(root,'sounds',f),'wb').write(bell)

zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
hs = [hashlib.md5(zz.read('DK_Duet/sounds/dkAlert%d.ogg'%i)).hexdigest() for i in (1,2,3)]
assert len(set(hs)) == 1, hs
for root in ROOTS:
    for f in ('dkAlert1.ogg','dkAlert2.ogg','dkAlert3.ogg'):
        assert hashlib.md5(open(os.path.join(root,'sounds',f),'rb').read()).hexdigest() == hs[0]
print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      'items', len(zz.namelist()), 'size', os.path.getsize(OUT), '| all bells', hs[0][:12])
