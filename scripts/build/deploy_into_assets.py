# -*- coding: utf-8 -*-
"""
把 DK_Duet 双人对唱以【纯新增文件】方式装进遗产版引擎必读的 assets/ 目录。
不动任何原版文件；旧的错误 content/DK_Duet mod 保留但不再依赖。
关键修复：
  1) 独立 stage cargo-duo-{momo,miku}.hx —— 复制原版 cargo.hx 的双人对唱分流,
     但去掉硬编码 changeIcon('double-kill'/'black'/'white')，换成对应角色图标。
  2) 谱面 stage 字段改指新 stage, song 显示名保持 Add-freeplay 命中。
"""
import os, json, shutil, sys

ROOT = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
PKG  = os.path.join(ROOT, 'content', 'DK_Duet')
A    = os.path.join(ROOT, 'assets')

def cp(src, dst, log):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    log.append((src, dst))

def cp_tree(src_dir, dst_dir, log, overwrite=False):
    for root, _, files in os.walk(src_dir):
        for f in files:
            s = os.path.join(root, f)
            d = os.path.join(dst_dir, os.path.relpath(s, src_dir))
            if os.path.exists(d) and not overwrite:
                continue
            cp(s, d, log)

log = []

# ---- 1. 两首歌 (音乐 + 谱面 + info) ------------------------------------
for slug in ['double-kill-duo-momo', 'double-kill-duo-miku']:
    sd = os.path.join(PKG, 'songs', slug)
    dd = os.path.join(A, 'songs', slug)
    for f in ['Inst.ogg', 'Voices.ogg', 'info.txt']:
        cp(os.path.join(sd, f), os.path.join(dd, f), log)
    # 谱面: 改 stage 字段 + 注入 noteType 事件兜底, 保证分流独立于外部事件
    chart_src = os.path.join(sd, 'data', 'normal.json')
    with open(chart_src, encoding='utf-8') as fh:
        chart = json.load(fh)
    song = chart['song']
    who = 'momo' if slug.endswith('momo') else 'miku'
    song['stage'] = f'cargo-duo-{who}'
    # song 显示名 -> 引擎由 week 显示名 sanitize 定位目录, 必须严格对应
    song['song'] = 'Double Kill Duo ' + ('Momo' if who == 'momo' else 'Miku')
    # format: 遗产版原版谱就是 nmv2, 显式补上避免解析分歧
    song['format'] = 'nmv2'
    os.makedirs(os.path.join(dd, 'data'), exist_ok=True)
    with open(os.path.join(dd, 'data', 'normal.json'), 'w', encoding='utf-8') as fh:
        json.dump(chart, fh, ensure_ascii=False, indent=2)

# ---- 2. 角色 json ------------------------------------------------------
for c in ['momo', 'miku', 'teto', 'momo-god', 'miku-god', 'teto-god',
          'bf-ic', 'bf-god', 'bf-defeat-normal', 'bf-defeat-normal-god']:
    s = os.path.join(PKG, 'data', 'characters', c + '.json')
    if os.path.isfile(s):
        cp(s, os.path.join(A, 'data', 'characters', c + '.json'), log)

# ---- 3. 角色图片 (momo/miku/teto 及 god, 不覆盖原版 bf) ----------------
for f in os.listdir(os.path.join(PKG, 'images', 'characters')):
    if f.lower().startswith('bf'):
        continue
    s = os.path.join(PKG, 'images', 'characters', f)
    d = os.path.join(A, 'images', 'characters', f)
    if os.path.isfile(s) and not os.path.exists(d):
        cp(s, d, log)
# cuphead bf 子目录只在缺失时补
cup_src = os.path.join(PKG, 'images', 'characters', 'cuphead')
cup_dst = os.path.join(A, 'images', 'characters', 'cuphead')
if os.path.isdir(cup_src):
    cp_tree(cup_src, cup_dst, log)

# ---- 4. 图标 -----------------------------------------------------------
icons_src = os.path.join(PKG, 'images', 'icons')
icons_dst = os.path.join(A, 'images', 'icons')
for f in os.listdir(icons_src):
    s = os.path.join(icons_src, f)
    d = os.path.join(icons_dst, f)
    if os.path.isfile(s) and not os.path.exists(d):
        cp(s, d, log)

# ---- 5. 菜单角色 / 难度图标 / storymenu --------------------------------
for sub in ['menucharacters', 'menudifficulties', 'storymenu']:
    ss = os.path.join(PKG, 'images', sub)
    ds = os.path.join(A, 'images', sub)
    if os.path.isdir(ss):
        cp_tree(ss, ds, log)

# ---- 6. stage 图片 (airship/double-kill/*, 原版已有则不覆盖) -----------
stg_src = os.path.join(PKG, 'images', 'stages', 'airship', 'double-kill')
stg_dst = os.path.join(A, 'images', 'stages', 'airship', 'double-kill')
if os.path.isdir(stg_src):
    cp_tree(stg_src, stg_dst, log)
# 其它 stage 散图 (dk_saw 等)
for f in os.listdir(os.path.join(PKG, 'images')):
    s = os.path.join(PKG, 'images', f)
    if os.path.isfile(s) and not os.path.exists(os.path.join(A, 'images', f)):
        cp(s, os.path.join(A, 'images', f), log)

# ---- 7. 自定义事件 / 音符类型 (原版缺的才补) --------------------------
for f in ['DK Surprise', 'Reactor Beep', 'Set Cams', 'Extra Cam Zoom']:
    s = os.path.join(PKG, 'data', 'events', f + '.txt')
    if os.path.isfile(s) and not os.path.exists(os.path.join(A, 'data', 'events', f + '.txt')):
        cp(s, os.path.join(A, 'data', 'events', f + '.txt'), log)
for f in ['DK Trap', 'DK Warn', 'Alt Animation', 'No Animation']:
    s = os.path.join(PKG, 'data', 'notetypes', f + '.txt')
    if os.path.isfile(s) and not os.path.exists(os.path.join(A, 'data', 'notetypes', f + '.txt')):
        cp(s, os.path.join(A, 'data', 'notetypes', f + '.txt'), log)

# ---- 8. 独立 stage: 修掉硬编码图标, 保留双人对唱分流 -------------------
with open(os.path.join(A, 'data', 'stages', 'cargo.hx'), encoding='utf-8') as fh:
    base_hx = fh.read()

def make_stage(who):
    """who in {momo,miku}. 主对手图标 / teto 图标 / 双人图标。"""
    main_icon = who                       # icon-momo / icon-miku
    teto_icon = 'teto-2026'               # icon-teto-2026
    duo_icon  = f'{who}-teto'             # icon-momo-teto / icon-miku-teto
    hx = base_hx
    # 原版 onEvent 'Both Opponents' 分支里硬编码三件套 -> 换成 duo 体系
    hx = hx.replace(
        "playHUD.iconP2.changeIcon(bothSing ? 'double-kill' : (twoSing ? 'black' : 'white'));",
        f"playHUD.iconP2.changeIcon(bothSing ? '{duo_icon}' : (twoSing ? '{teto_icon}' : '{main_icon}'));"
    )
    # refreshDoubleKillIcon 里硬编码 black/white -> 换成 teto/main
    hx = hx.replace(
        "playHUD.iconP2.changeIcon(twoSing ? 'black' : 'white');",
        f"playHUD.iconP2.changeIcon(twoSing ? '{teto_icon}' : '{main_icon}');"
    )
    # 顶部注释掉原版的时间偏移提醒(保留逻辑, 仅说明)
    return hx

STAGE_JSON = '''{
	"directory": "",
	"defaultZoom": 0.8,
	"isPixelStage": false,
	"hide_girlfriend": false,
	"boyfriend": [2550, 650],
	"girlfriend": [1550, 600],
	"opponent": [1250, 680],
	"flags": { "airship": true }
}
'''
for who in ['momo', 'miku']:
    with open(os.path.join(A, 'data', 'stages', f'cargo-duo-{who}.hx'), 'w', encoding='utf-8') as fh:
        fh.write(make_stage(who))
    with open(os.path.join(A, 'data', 'stages', f'cargo-duo-{who}.json'), 'w', encoding='utf-8') as fh:
        fh.write(STAGE_JSON)

# ---- 9. week: 让两首歌进 Story + Freeplay -----------------------------
def make_week(who):
    disp = 'Double Kill Duo ' + ('Momo' if who == 'momo' else 'Miku')
    icon = who + '-teto'
    return {
        "songs": [[disp, icon, [200, 180, 220], who, "DFJK117"]],
        "section": "story",
        "storyName": "Double Kill Duet",
        "weekBefore": "week3",
        "weekName": "DK Duet - " + ('Momo' if who == 'momo' else 'Miku'),
        "startUnlocked": True,
        "hideStoryMode": False,
        "hideFreeplay": False,
        "node": {"parent": "week3", "direction": "north" if who == 'momo' else "south"}
    }

for who in ['momo', 'miku']:
    with open(os.path.join(A, 'data', 'weeks', f'dk-duo-{who}.json'), 'w', encoding='utf-8') as fh:
        json.dump(make_week(who), fh, ensure_ascii=False, indent=2)

print(f'新增/更新文件数: {len(log)}')
for s, d in log[:40]:
    print('  ', os.path.relpath(d, A))
if len(log) > 40:
    print(f'   ... 另有 {len(log)-40} 个')
