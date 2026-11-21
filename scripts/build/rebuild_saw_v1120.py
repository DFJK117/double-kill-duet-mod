# -*- coding: utf-8 -*-
"""
v11.20 based on v11.19 zip (full package, no incremental drift):
  1) DK_Saw.lua  -> new file: baguette 200ms out + 500ms hold(shake) + 200ms back,
                   judge moved from ci+300ms to ci+900ms (whole anim), a3 loop.
  2) DK_Fun.lua  -> DODGE_WINDOW 0.5 -> 1.0 (fairer dodge).
  3) both god+ charts -> Dodge Mechanic events 34 -> 44, evenly spread
                   (min gap ~5600ms, no 4.5s clustering).
Idempotent, deploys 3 roots, repacks full zip.
"""
import os, zipfile, hashlib, json, shutil

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.19_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.20_GODplus_20261117.zip'
NEW_LUA = r'E:/UST_work/dk_miku/scripts/DK_Saw_v1120.lua'
ROOTS = [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
         r'E:/UST_work/dk_miku/DK_Dual',
         r'E:/UST_work/dk_miku/DK_Miku']
P_SAW = 'DK_Duet/scripts/DK_Saw.lua'
P_FUN = 'DK_Duet/scripts/DK_Fun.lua'
SONGS = [('double-kill','double-kill-god+.json'), ('double-kill-miku','double-kill-miku-god+.json')]

lua_data = open(NEW_LUA,'rb').read()

z = zipfile.ZipFile(BASE)
names = z.namelist()

# --- 2) widen dodge window ---
fun = z.read(P_FUN).decode('utf-8')
assert fun.count('local DODGE_WINDOW = 0.5') == 1, 'DODGE_WINDOW pattern not found'
fun = fun.replace('local DODGE_WINDOW = 0.5', 'local DODGE_WINDOW = 1.0')
fun_data = fun.encode('utf-8')

# --- 3) respread dodge events: 44 events, even 5600ms, start 38000ms ---
# even spacing 5600ms across [38000, 38000+43*5600=278800] -> within song (282379ms)
NEW_TIMES = [38000 + i*5600 for i in range(44)]
assert NEW_TIMES[-1] < 282000
chart_data = {}
for song, fn in SONGS:
    p = 'DK_Duet/data/%s/%s' % (song, fn)
    raw = z.read(p).decode('utf-8-sig')
    j = json.loads(raw)
    # remove existing Dodge Mechanic / DK Saw events, keep everything else
    evs = j.get('events', [])
    kept = []
    for e in evs:
        is_dodge = False
        if isinstance(e, list) and len(e) > 1 and isinstance(e[1], list):
            for sub in e[1]:
                if isinstance(sub, list) and sub and str(sub[0]) in ('Dodge Mechanic','DK Saw'):
                    is_dodge = True
        if not is_dodge:
            kept.append(e)
    for t in NEW_TIMES:
        kept.append([float(t), [['Dodge Mechanic', 'left', '1']]])
    kept.sort(key=lambda e: float(e[0]) if isinstance(e, list) and e else 0)
    j['events'] = kept
    # keep utf-8-sig BOM like original
    chart_data[p] = json.dumps(j, ensure_ascii=False, separators=(',',':')).encode('utf-8-sig')
    print(song, 'dodge events ->', sum(1 for e in kept if isinstance(e,list) and len(e)>1 and isinstance(e[1],list) and any(isinstance(s,list) and s and str(s[0]) in ('Dodge Mechanic','DK Saw') for s in e[1])))

replace = {P_SAW: lua_data, P_FUN: fun_data}
replace.update(chart_data)

tmp = OUT + '.tmp'
with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zo:
    for item in z.infolist():
        zo.writestr(item, replace.get(item.filename, z.read(item.filename)))
z.close()
os.replace(tmp, OUT)

# --- deploy to 3 roots ---
for root in ROOTS:
    for rel, data in replace.items():
        dst = os.path.join(root, rel.split('/',1)[1].replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'wb').write(data)

# --- verify ---
zz = zipfile.ZipFile(OUT)
assert zz.testzip() is None
for rel, data in replace.items():
    h = hashlib.md5(data).hexdigest()
    for root in ROOTS:
        dst = os.path.join(root, rel.split('/',1)[1].replace('/', os.sep))
        assert hashlib.md5(open(dst,'rb').read()).hexdigest() == h, ('mismatch', root, rel)
# chart sanity
for song, fn in SONGS:
    j = json.loads(zz.read('DK_Duet/data/%s/%s' % (song, fn)).decode('utf-8-sig'))
    ts = sorted(float(e[0]) for e in j['events'] if isinstance(e,list) and len(e)>1 and isinstance(e[1],list) and any(isinstance(s,list) and s and str(s[0])=='Dodge Mechanic' for s in e[1]))
    gaps = [ts[i+1]-ts[i] for i in range(len(ts)-1)]
    print('verify', song, 'count', len(ts), 'min gap', int(min(gaps)), 'max gap', int(max(gaps)))

print('OK md5', hashlib.md5(open(OUT,'rb').read()).hexdigest(), 'items', len(zz.namelist()), 'size', os.path.getsize(OUT))
