# -*- coding: utf-8 -*-
"""按 VS Impostor Legacy 1.1.2 (老 PE) 真实规则验证 DK_Duet 移植。"""
import os, json, sys

GAME = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
DEST = os.path.join(GAME, 'content', 'DK_Duet')
SONGS = ['double-kill-duo-momo', 'double-kill-duo-miku']
ok, fail = 0, 0


def chk(cond, msg):
    global ok, fail
    if cond:
        ok += 1
    else:
        fail += 1
        print('FAIL:', msg)


def jload(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


# 1. 位置
chk(os.path.isdir(DEST), 'content/DK_Duet 不存在')
chk(os.path.isfile(os.path.join(DEST, 'meta.json')), 'meta.json 缺失')

# 2. 每首歌结构
for s in SONGS:
    sd = os.path.join(DEST, 'songs', s)
    chk(os.path.isdir(sd), f'{s}: song 目录缺失')
    chk(os.path.isfile(os.path.join(sd, 'Inst.ogg')), f'{s}: 根目录 Inst.ogg 缺失')
    chk(os.path.isfile(os.path.join(sd, 'Voices.ogg')), f'{s}: 根目录 Voices.ogg 缺失')
    cp = os.path.join(sd, 'data', 'normal.json')
    chk(os.path.isfile(cp), f'{s}: data/normal.json 缺失')
    # 绝不能有 charts/ 或 audio/ (NVE 残留)
    chk(not os.path.isdir(os.path.join(sd, 'charts')), f'{s}: 残留 charts/ (引擎不认)')
    chk(not os.path.isdir(os.path.join(sd, 'audio')), f'{s}: 残留 audio/ (引擎不认)')
    if os.path.isfile(cp):
        d = jload(cp)
        song = d['song'] if isinstance(d.get('song'), dict) else d
        nnotes = sum(len(sec.get('sectionNotes', [])) for sec in song.get('notes', []))
        chk(nnotes > 2000, f'{s}: 音符数只有 {nnotes}')
        # note 轨道必须是 int (老 PE 要求), 且 0..7
        bad = 0
        for sec in song.get('notes', []):
            for n in sec.get('sectionNotes', []):
                if len(n) < 2 or not isinstance(n[1], int) or n[1] < 0 or n[1] > 7:
                    bad += 1
        chk(bad == 0, f'{s}: {bad} 个非法轨道音符')
        # noteType 分布
        from collections import Counter
        c = Counter(n[3] if len(n) > 3 else '' for sec in song.get('notes', []) for n in sec.get('sectionNotes', []))
        print(f'  {s}: notes={nnotes} noteTypes={dict(c)} player2={song.get("player2")} gf={song.get("gfVersion")}')

# 3. 不顶原版: 原版 double-kill 完整且未被覆盖
orig = os.path.join(GAME, 'assets', 'songs', 'double-kill')
chk(os.path.isfile(os.path.join(orig, 'Inst.ogg')), '原版 double-kill Inst.ogg 被动过')
chk(os.path.isfile(os.path.join(orig, 'data', 'normal.json')), '原版 double-kill 谱被动过')
chk(not os.path.isdir(os.path.join(DEST, 'songs', 'double-kill')),
    'mod 里仍有同名 double-kill 目录(会顶原版)')

# 4. week 老 PE 格式
wdir = os.path.join(DEST, 'data', 'weeks')
wfiles = [f for f in os.listdir(wdir) if f.endswith('.json')] if os.path.isdir(wdir) else []
chk(len(wfiles) >= 2, f'week 文件不足: {wfiles}')
for wf in wfiles:
    w = jload(os.path.join(wdir, wf))
    chk('section' in w, f'{wf}: 缺 section (老 PE 必需)')
    chk('weekCharacters' not in w, f'{wf}: 残留 NVE weekCharacters')
    chk('freeplayColor' not in w, f'{wf}: 残留 NVE freeplayColor')
    import re
    def fmt(path):
        p = re.sub(r'[~&\\;:<>#]', '-', path.replace(' ', '-'))
        p = re.sub(r'[\.,\'"%?!]', '', p)
        return p.lower().strip()
    for entry in w.get('songs', []):
        chk(len(entry) >= 4, f'{wf}: songs 条目不是老 PE 格式')
        if len(entry) >= 1:
            # 显示名 sanitize 后必须命中真实 song 目录
            slug = fmt(entry[0])
            chk(os.path.isdir(os.path.join(DEST, 'songs', slug)),
                f'{wf}: 显示名 "{entry[0]}" sanitize={slug} 无对应 song 目录')

# 5. 角色 / 舞台
for c in ['momo', 'miku', 'teto', 'bf']:
    chk(os.path.isfile(os.path.join(DEST, 'data', 'characters', c + '.json')), f'角色 {c}.json 缺失')
chk(os.path.isfile(os.path.join(DEST, 'data', 'stages', 'cargo.json')), 'stage cargo.json 缺失(平铺)')
chk(os.path.isfile(os.path.join(DEST, 'data', 'stages', 'cargo.hx')), 'stage cargo.hx 缺失(双对手切换脚本)')

# 6. modsList
ml = os.path.join(GAME, 'modsList.txt')
if os.path.isfile(ml):
    lines = open(ml, encoding='utf-8-sig').read().splitlines()
    chk('DK_Duet|1' in lines, 'modsList.txt 未启用 DK_Duet')

# 7. 图标引用: week 条目里的图标名能在 images/icons 找到
for wf in wfiles:
    w = jload(os.path.join(wdir, wf))
    for entry in w.get('songs', []):
        if len(entry) >= 2:
            icon = entry[1]
            chk(os.path.isfile(os.path.join(DEST, 'images', 'icons', 'icon-' + icon + '.png')),
                f'{wf}: 图标 icon-{icon}.png 缺失')

print(f'\n=== 结果: PASS {ok} / FAIL {fail} ===')
sys.exit(1 if fail else 0)
