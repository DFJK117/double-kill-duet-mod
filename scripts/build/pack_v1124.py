# -*- coding: utf-8 -*-
"""v11.24: watermark per difficulty (GOD+ only) + fix momo hard cross-song.
Pack a full mod zip from the live game deploy dir, then verify 3 deploy sites
are byte-identical.ASCII-only Lua, UTF-8-BOM charts preserved.
"""
import os, zipfile, hashlib, json

G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
SITES = [G, 'E:/UST_work/dk_miku/DK_Dual', 'E:/UST_work/dk_miku/DK_Miku']
OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.24_GODplus_20261117.zip'
CHECKS = []
def ck(name, cond):
    CHECKS.append((name, bool(cond)))
def rb(rel, base=G):
    p = os.path.join(base, rel)
    return open(p, 'rb').read() if os.path.isfile(p) else b''

# 1) watermark Lua: GOD+ gating present, no hardcoded single WATER_TEXT
death = rb('scripts/DK_Death.lua').decode('ascii')
ck('death WATER_GODPLUS', "local WATER_GODPLUS = 'DFJK117  GOD+'" in death)
ck('death WATER_DEFAULT', "local WATER_DEFAULT = 'DFJK117'" in death)
ck('death isGodPlus idx2', "return idx == 2" in death)
ck('death setTextString', 'setTextString' in death)
ck('death ASCII', all(ord(c) < 128 for c in death))

# 2) momo hard not cross-song; miku hard still miku
mh = json.loads(rb('data/double-kill/double-kill-hard.json').decode('utf-8-sig'))
kh = json.loads(rb('data/double-kill-miku/double-kill-miku-hard.json').decode('utf-8-sig'))
ck('momo hard song', mh.get('song') == 'Double Kill')
ck('momo hard chars', mh.get('player1') == 'bf' and mh.get('player2') == 'momo')
ck('miku hard song', kh.get('song') == 'double-kill-miku')
ck('miku hard chars', kh.get('player1') == 'bf' and kh.get('player2') == 'miku')

# 3) all playable chart paths exist + parse + correct chars
for song, p1god, p2god in [('double-kill','bf-god','momo-god'),('double-kill-miku','bf-god','miku-god')]:
    for diff in ['hard','god','god+']:
        rel = 'data/%s/%s-%s.json' % (song, song, diff)
        raw = rb(rel)
        ck('chart exists '+os.path.basename(rel), len(raw) > 0)
        if not raw: continue
        try:
            d = json.loads(raw.decode('utf-8-sig'))
        except Exception:
            ck('chart parse '+os.path.basename(rel), False); continue
        notes = sum(len(s.get('sectionNotes', [])) for s in d.get('notes', []))
        ck('chart notes '+os.path.basename(rel), notes > 500)
        if diff in ('god','god+'):
            ck('chart god chars '+os.path.basename(rel), d.get('player1')==p1god and d.get('player2')==p2god)

# 4) week difficulties include GOD+
for f in ['dk-miku.json','dk-momo.json']:
    ck('week diffs '+f, b'"hard,GOD,GOD+"' in rb('weeks/'+f))

# 5) custom note types
for f in ['DK Trap.txt','DK Warn.txt']:
    ck('notetype '+f, len(rb('custom_notetypes/'+f)) > 0)

# 6) three deploy sites byte-identical
rel_check = ['scripts/DK_Death.lua',
             'data/double-kill/double-kill-hard.json',
             'data/double-kill/double-kill-god+.json',
             'data/double-kill-miku/double-kill-miku-god+.json',
             'weeks/dk-momo.json','weeks/dk-miku.json']
for rel in rel_check:
    hs = [hashlib.md5(rb(rel, s)).hexdigest() for s in SITES]
    ck('3-site md5 '+os.path.basename(rel), len(set(hs)) == 1)

# report before pack
fails = [n for n, ok in CHECKS if not ok]
print('CHECKS', len(CHECKS), 'FAIL', len(fails))
for n in fails: print('  FAIL:', n)
if fails:
    print('ABORT PACK'); raise SystemExit(1)

# 7) pack full zip (top level DK_Duet/)
if os.path.exists(OUT):
    os.rename(OUT, OUT + '.prev')
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
    for root, dirs, files in os.walk(G):
        dirs[:] = [d for d in dirs if d != '__pycache__']
        for fn in files:
            if fn.endswith('.bak') or '.bak_' in fn: continue
            fp = os.path.join(root, fn)
            rel = os.path.relpath(fp, G).replace(os.sep, '/')
            zf.write(fp, 'DK_Duet/' + rel)

with zipfile.ZipFile(OUT) as zf:
    bad = zf.testzip()
    names = zf.namelist()
print('ZIP', OUT)
print('  items', len(names), 'bytes', os.path.getsize(OUT))
print('  CRC', 'OK' if bad is None else 'BAD:'+bad)
print('  md5', hashlib.md5(open(OUT,'rb').read()).hexdigest())
print('  has death lua', 'DK_Duet/scripts/DK_Death.lua' in names)
print('  has momo god+', 'DK_Duet/data/double-kill/double-kill-god+.json' in names)
