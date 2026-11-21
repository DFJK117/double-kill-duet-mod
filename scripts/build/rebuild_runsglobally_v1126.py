# -*- coding: utf-8 -*-
"""
v11.26 based on v11.25 full package:
  1) DK_Duet/pack.json runsGlobally false -> true.
     Root cause of Freeplay "No Chart Found": modFolders() only searches
     currentModDirectory + getGlobalMods(). With runsGlobally=false DK_Duet
     was excluded from getGlobalMods(), so the detail panel could not resolve
     GOD/GOD+ charts when currentModDirectory was wrong/empty.
  2) weeks/dk-momo.json + dk-miku.json: songs entries had only 3 fields,
     missing song[3] (musican) and song[4] (charter) -> Freeplay showed N/A.
     Filled to standard 5 fields with 'DFJK117'.
  Everything else untouched. Idempotent, deploys 3 roots, repacks full zip.
"""
import os, zipfile, hashlib, json

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.25_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.26_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
CHANGED = ['DK_Duet/pack.json',
           'DK_Duet/weeks/dk-momo.json',
           'DK_Duet/weeks/dk-miku.json']

# build replacement contents from the already-deployed primary root
primary = ROOTS[0]
repl = {}
# pack.json: match on-disk bytes
repl['DK_Duet/pack.json'] = open(os.path.join(primary, 'pack.json'), 'rb').read()
for fn in ['dk-momo.json', 'dk-miku.json']:
    repl['DK_Duet/weeks/' + fn] = open(os.path.join(primary, 'weeks', fn), 'rb').read()

# sanity: pack has runsGlobally true, weeks have 5-field songs
assert json.loads(repl['DK_Duet/pack.json'].decode('utf-8-sig'))['runsGlobally'] is True
for fn in ['dk-momo.json', 'dk-miku.json']:
    d = json.loads(repl['DK_Duet/weeks/' + fn].decode('utf-8-sig'))
    assert len(d['songs'][0]) == 5, (fn, d['songs'][0])

z = zipfile.ZipFile(BASE)
for c in CHANGED:
    assert c in z.namelist(), ('missing in base', c)

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, repl.get(item.filename, z.read(item.filename)))
z.close()
os.replace(tmp, OUT)

# deploy replacement bytes to all 3 roots
for root in ROOTS:
    for c in CHANGED:
        sub = c[len('DK_Duet/'):]
        dst = os.path.join(root, sub.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(repl[c])

# verify
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None, 'CRC fail'
for root in ROOTS:
    for c in CHANGED:
        dst = os.path.join(root, c[len('DK_Duet/'):].replace('/', os.sep))
        assert hashlib.md5(open(dst, 'rb').read()).hexdigest() == hashlib.md5(repl[c]).hexdigest(), ('mismatch', root, c)
zb = zipfile.ZipFile(BASE)
assert set(zb.namelist()) == set(zz.namelist()), 'item set changed'
drift = [n for n in zb.namelist() if hashlib.md5(zb.read(n)).hexdigest() != hashlib.md5(zz.read(n)).hexdigest()]
assert sorted(drift) == sorted(CHANGED), ('unexpected drift', drift)
zb.close(); zz.close()

print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(),
      '| items', len(zipfile.ZipFile(OUT).namelist()),
      '| size', os.path.getsize(OUT), '| drift', sorted(drift))
