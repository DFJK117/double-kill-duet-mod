# -*- coding: utf-8 -*-
"""修正 v11.30 包里 infant 谱的 noteType：按同刻(时间)匹配，而非(时间,轨道)。

mods12 新版是 4P 原始轨道分配，DK hard 是 4P->2P 对调版，同刻音符轨道不同，
所以之前按(时间,轨道)匹配只配上 124 个。改为按时间匹配，把 DK hard 的
Opponent 2 Sing / Both Opponents Sing 标注全部继承过来。
"""
import json, os, io, zipfile, hashlib, collections

PKG = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.30_OldInfant_20261118.zip'
TMP = PKG + '.tmp'
SONGS = ['double-kill', 'double-kill-miku']

zin = zipfile.ZipFile(PKG, 'r')
entries = {i.filename: zin.read(i.filename) for i in zin.infolist()}
infos = {i.filename: i for i in zin.infolist()}
zin.close()

def tkey(n):
    try: return round(float(n[0]))
    except Exception: return None

for s in SONGS:
    base = f'DK_Duet/data/{s}/{s}'
    hard = json.loads(entries[base + '-old.json'].decode('utf-8-sig'))  # old=hard原样
    infant = json.loads(entries[base + '-infant.json'].decode('utf-8-sig'))
    # 建时间->noteType列表 索引（从 hard）
    idx = collections.defaultdict(list)
    for sec in hard['notes']:
        for n in sec.get('sectionNotes', []):
            if isinstance(n, list) and len(n) > 3 and tkey(n) is not None:
                idx[tkey(n)].append(str(n[3]))
    # 给 infant 同刻音符补 noteType：优先 Both/Opponent2
    fixed = 0
    for sec in infant['notes']:
        for n in sec.get('sectionNotes', []):
            if not isinstance(n, list) or len(n) < 2: continue
            k = tkey(n)
            cand = idx.get(k, [])
            special = [t for t in cand if t in ('Opponent 2 Sing', 'Both Opponents Sing')]
            if special:
                while len(n) <= 3: n.append('')
                # 取出现最多的特殊类型
                n[3] = collections.Counter(special).most_common(1)[0][0]
                fixed += 1
    entries[base + '-infant.json'] = json.dumps(infant, indent=1, ensure_ascii=False).encode('utf-8')
    types = collections.Counter()
    for sec in infant['notes']:
        for n in sec['sectionNotes']:
            if len(n) > 3: types[str(n[3])] += 1
    print(s, 'fixed', fixed, 'types', dict(types))

with zipfile.ZipFile(TMP, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in entries.items():
        zout.writestr(infos[name] if name in infos else name, data)
os.replace(TMP, PKG)
z = zipfile.ZipFile(PKG)
assert z.testzip() is None
print('FINAL', PKG, 'items', len(z.namelist()), 'size', os.path.getsize(PKG),
      'md5', hashlib.md5(open(PKG, 'rb').read()).hexdigest())
