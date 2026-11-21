# v11.22: add no-postfix BASE charts so Chart Editor can open GOD+ songs.
# Base chart content = god+ chart (so editor opens straight into GOD+ notes).
# Based on v11.21 full zip, idempotent.
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.21_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.22_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']

z = zipfile.ZipFile(BASE)

# base chart entries -> source god+ chart entries
add = {}
for song in ['double-kill', 'double-kill-miku']:
    src = 'DK_Duet/data/%s/%s-god+.json' % (song, song)
    dst = 'DK_Duet/data/%s/%s.json' % (song, song)
    add[dst] = z.read(src)
    print('base chart:', dst, '<=', src, len(add[dst]), 'B')

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, z.read(item.filename))
    for name, data in add.items():
        zo.writestr(name, data)
os.replace(tmp, OUT)

# deploy to all three roots
for root in ROOTS:
    for rel, data in add.items():
        dst = os.path.join(root, rel.split('/', 1)[1].replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)

# verify
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
for rel, data in add.items():
    assert hashlib.md5(zz.read(rel)).hexdigest() == hashlib.md5(data).hexdigest()
    for root in ROOTS:
        p = os.path.join(root, rel.split('/', 1)[1].replace('/', os.sep))
        assert hashlib.md5(open(p, 'rb').read()).hexdigest() == hashlib.md5(data).hexdigest(), (root, rel)

print('OK items', len(zz.namelist()))
print('OK md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
print('OK size', os.path.getsize(OUT))
