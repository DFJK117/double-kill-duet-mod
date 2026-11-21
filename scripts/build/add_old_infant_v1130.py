# -*- coding: utf-8 -*-
"""v11.30：hard 改名 old(内容不动)，新增 Infant(婴儿模式)难度 = mods12 新版 2800 谱。

- 基底 = v11.29 完整 zip（含用户新 FLS 人声），从 zip 读写，产物也是 zip。
- week difficulties: hard,GOD,GOD+ -> old,Infant,GOD,GOD+
- 两首曲 double-kill / double-kill-miku：
    - <song>-old.json  = 当前 <song>-hard.json 原样（内容一个字节不动）
    - <song>-infant.json = mods12 新版 4P 谱转成 DK 双人格式：
        轨道保留 mods12 原始分配(0-3 玩家/4-7 对手)，
        角色 player2=momo、gfVersion=teto，
        noteType 融合：从同刻 DK hard 谱继承 Opponent 2 Sing / Both Opponents Sing 标注。
- 难度图 old.png(灰白) / infant.png(浅蓝)。
- 幂等：可重复跑。
"""
import json, os, io, zipfile, hashlib
from PIL import Image, ImageDraw, ImageFont

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.29_GODplus_20261117.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.30_OldInfant_20261118.zip'
MODS12 = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods12/data/double-kill-harder.json'
FONT = r'C:/Windows/Fonts/arialbd.ttf'
SONGS = ['double-kill', 'double-kill-miku']
WEEKS = ['DK_Duet/weeks/dk-momo.json', 'DK_Duet/weeks/dk-miku.json']

def diff_png(text, fill, outline):
    font = ImageFont.truetype(FONT, 58)
    probe = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(probe)
    bb = d.textbbox((0, 0), text, font=font, stroke_width=3)
    w, h = bb[2] - bb[0] + 20, bb[3] - bb[1] + 16
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((10 - bb[0], 8 - bb[1]), text, font=font, fill=fill,
            stroke_width=3, stroke_fill=outline)
    buf = io.BytesIO(); im.save(buf, format='PNG')
    return buf.getvalue()

def note_key(n):
    # 用 (取整时间, 轨道) 做同刻匹配 key
    try: return (round(float(n[0])), int(n[1]))
    except Exception: return (None, None)

# ---- 读 mods12 新版 4P 谱 ----
m12 = json.load(open(MODS12, encoding='utf-8-sig'))['song']
print('mods12 song', m12['song'], 'notes secs', len(m12['notes']))

zin = zipfile.ZipFile(BASE, 'r')
entries = {i.filename: zin.read(i.filename) for i in zin.infolist()}
infos   = {i.filename: i for i in zin.infolist()}
zin.close()

# 1) week
for wf in WEEKS:
    d = json.loads(entries[wf].decode('utf-8-sig'))
    diffs = [x.strip() for x in (d.get('difficulties') or '').split(',') if x.strip()]
    diffs = [x for x in diffs if x.lower() != 'hard']
    for want in ('old', 'Infant'):
        if want not in diffs: diffs.append(want)
    # 保留 GOD/GOD+ 位置，顺序: old, Infant, GOD, GOD+
    order = ['old', 'Infant', 'GOD', 'GOD+']
    diffs = [x for x in order if x in diffs] + [x for x in diffs if x not in order]
    d['difficulties'] = ','.join(diffs)
    entries[wf] = json.dumps(d, indent=1, ensure_ascii=False).encode('utf-8')
    print(wf, '->', d['difficulties'])

# 2) 谱面
for s in SONGS:
    is_miku = (s == 'double-kill-miku')
    base = f'DK_Duet/data/{s}/{s}'
    # 2a) old = hard 原样
    hard_path = base + '-hard.json'
    hard_raw = entries[hard_path]
    entries[base + '-old.json'] = hard_raw
    hard = json.loads(hard_raw.decode('utf-8-sig'))

    # 2b) infant = mods12 新版谱融合 DK 双人标注
    infant = json.loads(json.dumps(hard))  # 深拷贝 hard 作为顶层结构模板
    # 元数据：保留 DK 的角色映射(bf/momo/teto)，只用 mods12 的段落/音符
    infant['player1'] = 'bf'
    infant['player2'] = 'momo' if not is_miku else 'teto'
    infant['gfVersion'] = 'teto' if not is_miku else 'miku'
    infant['stage'] = m12.get('stage', 'cargo')
    infant['song'] = 'double-kill-miku' if is_miku else 'Double Kill'
    infant['bpm'] = m12.get('bpm', 200)
    infant['speed'] = 3
    # 段落：用 mods12 原始分配，但补 sectionBeats（DK 结构有）
    infant['notes'] = []
    for i, sec in enumerate(m12['notes']):
        dk_sec = hard['notes'][i] if i < len(hard['notes']) else {}
        newnotes = []
        for n in sec.get('sectionNotes', []):
            if not isinstance(n, list) or len(n) < 2: continue
            nn = list(n)
            # noteType 从 DK hard 同刻音符继承
            k = note_key(n)
            if k != (None, None):
                for dn in dk_sec.get('sectionNotes', []):
                    if isinstance(dn, list) and note_key(dn) == k and len(dn) > 3:
                        while len(nn) <= 3: nn.append('')
                        nn[3] = dn[3]
                        break
            newnotes.append(nn)
        infant['notes'].append({
            'sectionNotes': newnotes,
            'lengthInSteps': sec.get('lengthInSteps', 16),
            'mustHitSection': bool(sec.get('mustHitSection')),
            'sectionBeats': dk_sec.get('sectionBeats', 4),
        })
    entries[base + '-infant.json'] = json.dumps(infant, indent=1, ensure_ascii=False).encode('utf-8')
    # 统计
    tot = sum(len(x['sectionNotes']) for x in infant['notes'])
    types = {}
    for sec in infant['notes']:
        for n in sec['sectionNotes']:
            if len(n) > 3: types[str(n[3])] = types.get(str(n[3]), 0) + 1
    print(s, 'old=hard原样', len(hard_raw), 'B; infant', tot, 'notes types', types)

# 3) 难度图：old=文字，infant=抠好的坐姿婴儿透明图
md = 'DK_Duet/images/menudifficulties/'
entries[md + 'old.png'] = diff_png('OLD', (200, 200, 200, 255), (20, 20, 20, 255))
INFANT_ICON = r'E:/UST_work/dk_miku/_godmode/infant_icon.png'
entries[md + 'infant.png'] = open(INFANT_ICON, 'rb').read()
print('difficulty pngs added; infant from', INFANT_ICON, len(entries[md + 'infant.png']), 'B')

# 4) 写 zip（保持原压缩方式，BOM-free）
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
    for name, data in entries.items():
        zout.writestr(infos[name] if name in infos else name, data)
z = zipfile.ZipFile(OUT)
bad = z.testzip()
assert bad is None, 'CRC ' + str(bad)
print('OUT', OUT)
print('items', len(z.namelist()), 'size', os.path.getsize(OUT),
      'CRC OK', 'md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
