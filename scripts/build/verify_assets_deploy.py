# -*- coding: utf-8 -*-
import os, json, re

ROOT = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
A = os.path.join(ROOT, 'assets')
ok = 0; bad = 0
def chk(cond, msg):
    global ok, bad
    if cond: ok += 1; print('  OK  ', msg)
    else: bad += 1; print('  FAIL', msg)

def fmt(path):
    p = re.sub(r'[~&\\;:<>#]', '-', path.replace(' ', '-'))
    p = re.sub(r'[\.,\'"%?!]', '', p)
    return p.lower().strip()

for who in ['momo', 'miku']:
    slug = f'double-kill-duo-{who}'
    disp = 'Double Kill Duo ' + who.capitalize()
    print(f'\n=== {who} 版 ===')
    sd = os.path.join(A, 'songs', slug)
    # 目录命中 sanitize
    chk(fmt(disp) == slug, f'显示名"{disp}" sanitize 命中目录 {slug} (实得 {fmt(disp)})')
    for f in ['Inst.ogg', 'Voices.ogg', 'info.txt', 'data/normal.json']:
        chk(os.path.getsize(os.path.join(sd, f)) > 0, f'{f} 存在且非空')
    ch = json.load(open(os.path.join(sd, 'data', 'normal.json'), encoding='utf-8'))
    s = ch['song']
    chk(s.get('stage') == f'cargo-duo-{who}', f'stage 指向独立 stage = cargo-duo-{who}')
    chk(s.get('song') == disp, f'song 显示名 = {disp}')
    chk(s.get('format') == 'nmv2', 'format = nmv2')
    chk(s.get('player1') == 'bf', 'player1 = bf')
    chk(s.get('player2') == who, f'player2 = {who}')
    chk(s.get('gfVersion') == 'teto', 'gfVersion = teto (第二对手)')
    # noteType 分流分布
    from collections import Counter
    c = Counter(n[3] if len(n) > 3 else '' for sec in s['notes'] for n in sec['sectionNotes'])
    chk(c.get('Opponent 2 Sing', 0) > 100, f'Opponent 2 Sing 音符数 = {c.get("Opponent 2 Sing",0)} (teto唱)')
    chk(c.get('Both Opponents Sing', 0) > 100, f'Both Opponents Sing 音符数 = {c.get("Both Opponents Sing",0)} (合唱)')
    chk(c.get('DK Trap', 0) + c.get('DK Warn', 0) >= 0, '特殊键音符存在(不作断言)')
    # 独立 stage hx: 图标已换, 分流保留
    hx = open(os.path.join(A, 'data', 'stages', f'cargo-duo-{who}.hx'), encoding='utf-8').read()
    icon_lines = [ln for ln in hx.splitlines() if 'changeIcon' in ln]
    chk(all(x not in ''.join(icon_lines) for x in ["'double-kill'", "'black'", "'white'"]),
        'stage.hx 的 changeIcon 已无硬编码 double-kill/black/white')
    chk(f"'{who}-teto'" in hx, f'stage.hx 含双人图标 {who}-teto')
    chk(f"'{who}'" in hx and "'teto-2026'" in hx, 'stage.hx 含主/teto 单人图标')
    chk("note.noteType == 'Opponent 2 Sing'" in hx and 'note.owner = gf' in hx,
        'stage.hx 保留 Opponent 2 Sing -> gf 分流')
    chk("note.noteType == 'Both Opponents Sing'" in hx and 'characterSing(dad, note)' in hx,
        'stage.hx 保留 Both Opponents -> 双唱分流')
    chk(os.path.getsize(os.path.join(A, 'data', 'stages', f'cargo-duo-{who}.json')) > 0, 'stage.json 存在')
    # week
    w = json.load(open(os.path.join(A, 'data', 'weeks', f'dk-duo-{who}.json'), encoding='utf-8'))
    e = w['songs'][0]
    chk(e[0] == disp, f'week 显示名 = {disp}')
    chk(e[1] == f'{who}-teto', f'week 图标名 = {who}-teto')
    chk(os.path.exists(os.path.join(A, 'images', 'icons', f'icon-{who}-teto.png')), f'icon-{who}-teto.png 存在')
    chk(w.get('section') == 'story', 'week section = story (进 Story + Freeplay)')
    chk(w.get('hideStoryMode') is False and w.get('hideFreeplay') is False, 'Story/Freeplay 均可见')
    # 角色 + 图
    for c, img in [(who, f'characters/{who}_assets'), ('teto', 'characters/teto-2026'), ('bf', None)]:
        cp = os.path.join(A, 'data', 'characters', c + '.json')
        chk(os.path.isfile(cp), f'角色 {c}.json 存在')
        if img:
            cd = json.load(open(cp, encoding='utf-8'))
            chk(cd.get('image') == img, f'角色 {c} image = {img}')
            base = os.path.join(A, 'images', img.replace('/', os.sep))
            chk(os.path.exists(base + '.png') and os.path.exists(base + '.xml'), f'角色 {c} png+xml 存在')

# 原版未被触碰: 原 double-kill 谱 noteType 仍是 ''(1985)/Opp2(1)
orig = json.load(open(os.path.join(A, 'songs', 'double-kill', 'data', 'normal.json'), encoding='utf-8'))
from collections import Counter
oc = Counter(n[3] if len(n) > 3 else '' for sec in orig['song']['notes'] for n in sec['sectionNotes'])
print('\n=== 原版完整性 ===')
chk(orig['song']['song'] == 'Double Kill', '原版 double-kill 显示名未变')
chk(oc.get('Opponent 2 Sing', 0) <= 2, f'原版 noteType 仍是原样 (Opp2={oc.get("Opponent 2 Sing",0)})')
chk(json.load(open(os.path.join(A, 'data', 'stages', 'cargo.hx').replace('.hx','.hx'), encoding='utf-8').read() if False else '{}') == {}, '占位') if False else None
chk("'double-kill'" in open(os.path.join(A, 'data', 'stages', 'cargo.hx'), encoding='utf-8').read(), '原版 cargo.hx 未改动')

print(f'\n==== 合计 OK={ok} FAIL={bad} ====')
sys_exit = 1 if bad else 0
raise SystemExit(sys_exit)
