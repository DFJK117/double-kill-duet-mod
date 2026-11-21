# -*- coding: utf-8 -*-
"""
v11.27 based on v11.26 full package:
  ROOT CAUSE FIX (engine trace proof): "No Chart Found" was caused by UTF-8 BOM
  (0xEF 0xBB 0xBF = U+FEFF char 65279) at position 0 of chart JSON.
  Engine Json.parse rejects it: FreeplayState.hx "Invalid char 65279 at position 0".
  v11.22/v11.23 rebuild scripts wrote charts with utf-8-sig -> BOM.
  v11.21 (working) had NO BOM. Only hard/events.json had no BOM, which is why
  "only hard was readable".
  Fix: strip BOM from ALL json in the package. Deploy 3 roots, repack full zip.
"""
import os, zipfile, hashlib, json

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.26_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.27_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']

def strip_bom(b):
    return b[3:] if b.startswith(b'\xef\xbb\xbf') else b

z = zipfile.ZipFile(BASE)
repl = {}
for n in z.namelist():
    if n.endswith('.json'):
        b = strip_bom(z.read(n))
        repl[n] = b
z.close()

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    z2 = zipfile.ZipFile(BASE)
    for item in z2.infolist():
        zo.writestr(item, repl.get(item.filename, z2.read(item.filename)))
    z2.close()
os.replace(tmp, OUT)

# deploy: strip BOM from all json in 3 roots (idempotent)
for root in ROOTS:
    for dp,_,fs in os.walk(root):
        for f in fs:
            if f.endswith('.json'):
                p = os.path.join(dp, f)
                b = open(p, 'rb').read()
                nb = strip_bom(b)
                if nb != b:
                    open(p, 'wb').write(nb)

# verify
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None, 'CRC fail'
bom = [n for n in zz.namelist() if n.endswith('.json') and zz.read(n).startswith(b'\xef\xbb\xbf')]
assert not bom, ('BOM remains', bom)
parse_bad = []
for n in zz.namelist():
    if n.endswith('.json'):
        try: json.loads(zz.read(n).decode('utf-8'))
        except Exception as e: parse_bad.append((n, str(e)[:50]))
assert not parse_bad, ('parse fail', parse_bad)
# roots: no BOM in any json
root_bom = []
for root in ROOTS:
    for dp,_,fs in os.walk(root):
        for f in fs:
            if f.endswith('.json'):
                if open(os.path.join(dp,f),'rb').read().startswith(b'\xef\xbb\xbf'):
                    root_bom.append(os.path.join(dp,f))
assert not root_bom, ('root BOM', root_bom)
# drift: only json files changed that had BOM
zb = zipfile.ZipFile(BASE)
changed = [n for n in zb.namelist() if hashlib.md5(zb.read(n)).hexdigest() != hashlib.md5(zz.read(n)).hexdigest()]
assert all(n.endswith('.json') for n in changed), changed
zb.close(); zz.close()

print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      '| items', len(zipfile.ZipFile(OUT).namelist()),
      '| size', os.path.getsize(OUT),
      '| json debommed', len(changed), '| BOM remain 0 | parse bad 0')
