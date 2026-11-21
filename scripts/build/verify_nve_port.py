# -*- coding: utf-8 -*-
"""按 NVE 源码规则验证 content/DK_Duet 移植是否完整可加载。"""
import os, json, glob
from collections import Counter

GAME = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
MOD = os.path.join(GAME, 'content', 'DK_Duet')
SONGS = ['double-kill', 'double-kill-miku']
DIFFS = ['easy', 'normal', 'hard', 'old', 'infant', 'god', 'god+']
errs = []
oks = []


def jload(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def chk(cond, msg):
    (oks if cond else errs).append(msg)


# 1. mod 在 content/ 下
chk(os.path.isdir(os.path.join(GAME, 'content', 'DK_Duet')), 'mod 位于 content/DK_Duet (NVE MODS_DIRECTORY=content)')
chk(not os.path.exists(os.path.join(GAME, 'mods', 'DK_Duet')), '错误的 mods/DK_Duet 已移除')

# 2. modsList
ml = os.path.join(GAME, 'modsList.txt')
lines = [l.strip() for l in open(ml, encoding='utf-8-sig') if l.strip()] if os.path.isfile(ml) else []
chk('DK_Duet|1' in lines, 'modsList.txt 含 DK_Duet|1 (启用)')

# 3. meta
mp = os.path.join(MOD, 'meta.json')
chk(os.path.isfile(mp), 'meta.json 存在')
if os.path.isfile(mp):
    m = jload(mp)
    chk('name' in m, 'meta.json 有 name 字段')

# 4. weeks
wdir = os.path.join(MOD, 'data', 'weeks')
weeks = glob.glob(os.path.join(wdir, '*.json'))
chk(len(weeks) >= 2, 'data/weeks/ 有 %d 个 week' % len(weeks))
for wp in weeks:
    w = jload(wp)
    chk(isinstance(w.get('songs'), list), '%s songs 是数组' % os.path.basename(wp))
    chk(isinstance(w.get('difficulties'), list), '%s difficulties 是数组(NVE 要求)' % os.path.basename(wp))
    for e in w.get('songs', []):
        chk(len(e) >= 2, '%s song 项至少2元素' % os.path.basename(wp))
    for c in w.get('weekCharacters', []):
        if c:
            cp = os.path.join(MOD, 'data', 'characters', c + '.json')
            chk(os.path.isfile(cp), '%s 角色 %s 存在' % (os.path.basename(wp), c))

# 5. songs: charts + audio + meta
grand_notes = 0
for song in SONGS:
    sd = os.path.join(MOD, 'songs', song)
    chk(os.path.isdir(os.path.join(sd, 'charts')), '%s charts/ 存在' % song)
    chk(os.path.isdir(os.path.join(sd, 'audio')), '%s audio/ 存在' % song)
    chk(os.path.isfile(os.path.join(sd, 'meta.json')), '%s meta.json 存在' % song)
    for af in ['Inst.ogg', 'Voices.ogg']:
        ap = os.path.join(sd, 'audio', af)
        chk(os.path.isfile(ap), '%s audio/%s 存在' % (song, af))
    for diff in DIFFS:
        cp = os.path.join(sd, 'charts', diff + '.json')
        if not os.path.isfile(cp):
            errs.append('%s 缺 chart %s.json' % (song, diff))
            continue
        c = jload(cp)
        chk('song' in c and isinstance(c['song'], dict), '%s/%s 有 song 外壳' % (song, diff))
        s = c['song']
        chk(s.get('format') == 'nmv2', '%s/%s format=nmv2 (不会被判不兼容)' % (song, diff))
        notes = s.get('notes', [])
        n = sum(len(x.get('sectionNotes', [])) for x in notes)
        grand_notes += n
        # 轨道范围 0-7
        lanes = set(int(nn[1]) for sec in notes for nn in sec.get('sectionNotes', []))
        chk(not lanes or max(lanes) < 8, '%s/%s 轨道<8 (4P布局)' % (song, diff))
        # 角色引用
        for key in ['player1', 'player2', 'gfVersion']:
            v = s.get(key)
            if v:
                chp = os.path.join(MOD, 'data', 'characters', v + '.json')
                chk(os.path.isfile(chp), '%s/%s %s=%s 角色存在' % (song, diff, key, v))

# 6. 唱者分流: infant 与 old 逐段主导唱者一致(old 自身混唱段 69/175/177/178 除外)
def dom(seq):
    c = Counter(seq)
    return max(set(seq), key=lambda v: c[v]) if seq else None


def opp_seq(s):
    rows = []
    for sec in s['notes']:
        seq = []
        for n in sec.get('sectionNotes', []):
            if len(n) < 2 or int(n[1]) < 4:
                continue
            t = str(n[3]) if len(n) > 3 else ''
            if t in ('DK Trap', 'DK Warn'):
                continue
            seq.append({'Both Opponents Sing': 'B', 'Opponent 2 Sing': 'T'}.get(t, 'M'))
        rows.append(seq)
    return rows

MIX_SECTIONS = {69, 175, 177, 178}  # old 自身混唱段, 削谱无法逐音符复刻
for song in SONGS:
    base = os.path.join(MOD, 'songs', song, 'charts')
    op = os.path.join(base, 'old.json')
    ip = os.path.join(base, 'infant.json')
    if not (os.path.isfile(op) and os.path.isfile(ip)):
        continue
    o = opp_seq(jload(op)['song'])
    i = opp_seq(jload(ip)['song'])
    dev = [k for k in range(min(len(o), len(i)))
           if k not in MIX_SECTIONS and dom(o[k]) and dom(i[k]) and dom(o[k]) != dom(i[k])]
    chk(not dev, '%s infant 与 old 逐段唱者一致(除 old 混唱段), 差异段=%s' % (song, dev))

print('=' * 60)
print('PASS 检查项:', len(oks))
print('FAIL 检查项:', len(errs))
for e in errs[:40]:
    print('  ERR:', e)
if not errs:
    print('全部通过。总谱面音符:', grand_notes)
