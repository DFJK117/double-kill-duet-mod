# -*- coding: utf-8 -*-
"""
v11.28 based on v11.27 full package:
  Densify GOD+ saw (Dodge Mechanic) events.
  v11.27 had 44 saws per song at fixed 5600ms -> felt sparse.
  New: ~78 saws per song, interval 2400-4200ms oscillating (no clustering).
  Timing safety: each event = 700ms to impact + 600ms anim tail = 1300ms,
  so 2400ms minimum gap never overlaps. Dodge window (DK_Fun 1.0s) also safe.
  All 10 GOD+ charts (2 main + 8 editor aliases) get the SAME new schedule.
  Deploy 3 roots, repack full zip. JSON written UTF-8 NO BOM (v11.27 lesson).
"""
import os, zipfile, hashlib, json

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.27_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.28_GODplus_20261117.zip'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
GODP_FILES = [
    'data/double-kill/double-kill-god+.json',
    'data/double-kill-miku/double-kill-miku-god+.json',
    'data/double-kill-god+/double-kill-god+.json',
    'data/double-kill-god+/double-kill-god+-god+.json',
    'data/double-kill-god/double-kill-god-god+.json',
    'data/double-kill-hard/double-kill-hard-god+.json',
    'data/double-kill-miku-god+/double-kill-miku-god+.json',
    'data/double-kill-miku-god+/double-kill-miku-god+-god+.json',
    'data/double-kill-miku-god/double-kill-miku-god-god+.json',
    'data/double-kill-miku-hard/double-kill-miku-hard-god+.json',
]

# deterministic interval pattern (ms): oscillate 2400..4200, avoid 2 short in a row
PATTERN = [2800, 3600, 2500, 4100, 3000, 3800, 2600, 3400, 2900, 4200]
T_START, T_END = 38000, 278800

def make_schedule():
    times = []
    t = T_START
    i = 0
    while t <= T_END:
        times.append(float(t))
        t += PATTERN[i % len(PATTERN)]
        i += 1
    # avoid a saw landing too close to the very end
    if times and T_END - times[-1] < 1800:
        times.pop()
    return times

SCHED = make_schedule()
print('new saw schedule: count=%d | first=%d last=%d | avg gap=%.0fms' % (
      len(SCHED), SCHED[0], SCHED[-1],
      (SCHED[-1]-SCHED[0])/(len(SCHED)-1)))

def rebuild_chart(b):
    d = json.loads(b.decode('utf-8'))
    others = [e for e in d.get('events', [])
              if not (isinstance(e, list) and len(e) > 1
                      and isinstance(e[1], list) and len(e[1]) > 0
                      and isinstance(e[1][0], list) and e[1][0][0] == 'Dodge Mechanic')]
    new_dodge = [[t, [['Dodge Mechanic', 'left', '1']]] for t in SCHED]
    all_ev = others + new_dodge
    all_ev.sort(key=lambda e: e[0] if isinstance(e, list) and e else 0)
    d['events'] = all_ev
    return json.dumps(d, ensure_ascii=False, separators=(',', ':')).encode('utf-8')

# read replacements from BASE zip
z = zipfile.ZipFile(BASE)
repl = {}
for rel in GODP_FILES:
    key = 'DK_Duet/' + rel
    assert key in z.namelist(), ('missing in zip', key)
    repl[key] = rebuild_chart(z.read(key))
z.close()

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    z2 = zipfile.ZipFile(BASE)
    for item in z2.infolist():
        zo.writestr(item, repl.get(item.filename, z2.read(item.filename)))
    z2.close()
os.replace(tmp, OUT)

# deploy to 3 roots (main + aliases), UTF-8 no BOM
for root in ROOTS:
    for rel in GODP_FILES:
        p = os.path.join(root, rel.replace('/', os.sep))
        assert os.path.isfile(p), ('missing on disk', p)
        open(p, 'wb').write(repl['DK_Duet/' + rel])

# verify
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None, 'CRC fail'
bom = [n for n in zz.namelist() if n.endswith('.json') and zz.read(n).startswith(b'\xef\xbb\xbf')]
assert not bom, ('BOM remains', bom)
for key in repl:
    d = json.loads(zz.read(key).decode('utf-8'))
    dod = [e for e in d['events'] if e[1][0][0] == 'Dodge Mechanic']
    assert len(dod) == len(SCHED), (key, len(dod))
# drift check
zb = zipfile.ZipFile(BASE)
changed = [n for n in zb.namelist()
           if hashlib.md5(zb.read(n)).hexdigest() != hashlib.md5(zz.read(n)).hexdigest()]
assert sorted(changed) == sorted(repl.keys()), ('drift mismatch', changed)
zb.close(); zz.close()
print('OK md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest(),
      '| items', len(zipfile.ZipFile(OUT).namelist()),
      '| size', os.path.getsize(OUT),
      '| charts updated', len(repl), '| saws/song', len(SCHED))
