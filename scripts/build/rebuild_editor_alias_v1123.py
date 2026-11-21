# v11.23: exhaustive chart aliases so Chart Editor / Freeplay can open GOD+
# under ANY editor title text and ANY difficulty-list state.
# Root cause: Chart Editor loadJson(song) does
#   if Difficulty.getString() != 'Normal':
#       Song.loadFromJson(song + '-' + getString(), song)   -> data/<song>/<song>-<diff>.json
#   else:
#       Song.loadFromJson(song, song)                        -> data/<song>/<song>.json
# If the user types the FULL name (with difficulty suffix) in the title box,
# folder == that full name, so it looks for data/<fullname>/<fullname>[-<diff>].json
# which never existed. Generate every alias -> GOD+ content.
# Based on v11.22 full zip, idempotent. Dict-based: no duplicate zip entries.
import os, zipfile, hashlib

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.22_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.23_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']

z = zipfile.ZipFile(BASE)
# dict name -> bytes, seed from base zip (dedup automatically)
files = {}
for item in z.infolist():
    if not item.filename.endswith('/'):
        files[item.filename] = z.read(item.filename)

add = {}
for song in ['double-kill', 'double-kill-miku']:
    godp = files['DK_Duet/data/%s/%s-god+.json' % (song, song)]
    hard = files['DK_Duet/data/%s/%s-hard.json' % (song, song)]
    # base-name folder aliases the editor may request (real hard chart untouched)
    for alias in ['', '-easy', '-normal', '-god', '-god+']:
        add['DK_Duet/data/%s/%s%s.json' % (song, song, alias)] = godp
    # full-name folders (user typed "double-kill-god+" etc. in title box)
    for full in ['%s-god+' % song, '%s-god' % song, '%s-hard' % song]:
        for alias in ['', '-easy', '-normal', '-hard', '-god', '-god+']:
            add['DK_Duet/data/%s/%s%s.json' % (full, full, alias)] = godp

files.update(add)  # overwrite, never duplicate

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for name, data in files.items():
        zo.writestr(name, data)
os.replace(tmp, OUT)

for root in ROOTS:
    for rel, data in add.items():
        dst = os.path.join(root, rel.split('/', 1)[1].replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)

zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
names = zz.namelist()
assert len(names) == len(set(names)), 'DUPLICATE ENTRIES!'
for rel, data in add.items():
    assert hashlib.md5(zz.read(rel)).hexdigest() == hashlib.md5(data).hexdigest()
    for root in ROOTS:
        p = os.path.join(root, rel.split('/', 1)[1].replace('/', os.sep))
        assert hashlib.md5(open(p, 'rb').read()).hexdigest() == hashlib.md5(data).hexdigest(), (root, rel)

print('alias charts added:', len(add))
print('OK items', len(names))
print('OK md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
print('OK size', os.path.getsize(OUT))
