#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DK_Duet Lua v7 —— 修 bf-ic 站位错误 + 摄像机远航（幂等，可重复运行）

问题（用户实测反馈「bf位置错误，摄像机去远航」）：
  v6 把玩家 BF 换成 Indie Cross v15 的 bf-ic 图集时，只换了 image/scale/offsets，
  却**照抄了 DK 原 BOYFRIEND 的 position[-12,342] / camera_position[0,0]**。
  而 Flixel 的落点由「图集首帧画布 + 动画 offset + scale」共同决定，换图集后
  这套常量全部失配：
      · origin 与命中框在 loadCharacterFile 时按 **图集首帧**（0BF attack, 775x200）锁定，
        命中框变成 1550x400 → getMidpoint() 右移 556px → 摄像机瞄空；
      · IC 的 idle 画布只有 218x204 且内容贴画布左上，图形整体比原版左移 406px、上移 109px。
  结果：BF 跑到画面左下，摄像机停在空地。

修法（几何反解，不猜）：
  以「DK 原版 BF（BOYFRIEND, scale1）」在 cargo 舞台的真实落点为基准，
  用 Flixel 5.9 的真实渲染矩阵复算，反解出 IC BF 的
      position        = [394.5, 455]     （idle 左缘对齐 2557、脚底对齐 1415）
      camera_position = [962.5, -95.5]   （camFollow 回到 (2517, 1029.5)）
  其余 offsets / scale / 动画表一律保留 IC 官方值不动。

校验：几何回归（idle 左缘/脚底/camFollow 与原版逐项比对）+ 全动画脚底线检查 +
      图集前缀命中 + 图集文件 md5 + 三处目录 md5 一致 + chart player1 + zip CRC。
"""

import io
import json
import os
import shutil
import sys
import zipfile
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calc_bf_ic_layout import Character, solve, idle_world, STAGE  # noqa: E402

GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
IC = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/Indie Cross v15'
ROOT = r'E:/UST_work/dk_miku'
SOURCES = [ROOT + '/DK_Dual', ROOT + '/DK_Miku']
BACKUP = ROOT + '/_backup_lua_v7_20261115'
BASELINE = ROOT + '/_backup_lua_v6_20261115/characters/bf.json'  # v6 之前的 DK 原版 BF
ZIP = ROOT + '/DK_Duet_Lua_v7_20261115.zip'
SONGS = ['double-kill', 'double-kill-miku']

IC_PNG = GAME + '/images/characters/cuphead/BoyFriend_ICCuphead.png'
IC_XML = GAME + '/images/characters/cuphead/BoyFriend_ICCuphead.xml'

FILES = [
    'scripts/BOTPLAY_Pro.lua',
    'scripts/DK_Fun.lua',
    'scripts/DK_Push.lua',
    'custom_events/DK Push.lua',
    'custom_events/DK Attack.lua',
    'characters/bf.json',
    'characters/bf-ic.json',
    'characters/momo.json',
    'characters/miku.json',
    'characters/bf-defeat-normal.json',
    'images/characters/cuphead/BoyFriend_ICCuphead.png',
    'images/characters/cuphead/BoyFriend_ICCuphead.xml',
]

CHECKS = []
WARNS = []


def ck(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  | ' + str(detail)) if detail != '' else ''))


def warn(name, detail=''):
    WARNS.append(name)
    print('  WARN  ' + name + (('  | ' + str(detail)) if detail != '' else ''))


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def load_json(p):
    return json.load(io.open(p, encoding='utf-8-sig'))


def save_json(p, obj):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')


def backup_once():
    os.makedirs(BACKUP, exist_ok=True)
    n = 0
    for rel in ['characters/bf.json', 'characters/bf-ic.json']:
        src, dst = os.path.join(GAME, rel), os.path.join(BACKUP, rel)
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print('[backup] %s  新增备份 %d 个' % (BACKUP, n))


# ---------------------------------------------------------------- 求解 + 落盘
def apply_fix():
    dk = Character('dk', BASELINE)
    ck('基准是 DK 原版 BF（BOYFRIEND 图集）',
       dk.data.get('image') == 'characters/bf/BOYFRIEND', dk.data.get('image'))

    ic = Character('ic', os.path.join(GAME, 'characters', 'bf.json'))
    sol = solve(dk, ic)
    print('[solve] position        %s  (原 %s)' % (sol['position'], ic.position))
    print('[solve] camera_position %s  (原 %s)' % (sol['camera_position'], ic.camera_position))

    for rel in ('characters/bf.json', 'characters/bf-ic.json'):
        p = os.path.join(GAME, rel)
        d = load_json(p)
        d['position'] = sol['position']
        d['camera_position'] = sol['camera_position']
        save_json(p, d)
    return sol


# ---------------------------------------------------------------- 几何回归
def verify(sol):
    dk = Character('dk', BASELINE)
    ic = Character('ic', os.path.join(GAME, 'characters', 'bf.json'))
    x, y = ic.sprite_xy()
    ck('position 已写入 = %s' % sol['position'], ic.position == sol['position'], ic.position)
    ck('camera_position 已写入 = %s' % sol['camera_position'],
       ic.camera_position == sol['camera_position'], ic.camera_position)

    # 1) idle 图形左缘 / 脚底 与 DK 原版一致
    dk_idle = idle_world(dk, *dk.sprite_xy())
    ic_idle = idle_world(ic, x, y)
    ck('idle 图形左缘对齐 DK 原版 (%.1f vs %.1f, 差 %.2fpx)' % (ic_idle[0], dk_idle[0], abs(ic_idle[0] - dk_idle[0])),
       abs(ic_idle[0] - dk_idle[0]) <= 1.0, '%.2f' % abs(ic_idle[0] - dk_idle[0]))
    ck('idle 脚底线对齐 DK 原版 (%.1f vs %.1f, 差 %.2fpx)' % (ic_idle[3], dk_idle[3], abs(ic_idle[3] - dk_idle[3])),
       abs(ic_idle[3] - dk_idle[3]) <= 1.0, '%.2f' % abs(ic_idle[3] - dk_idle[3]))

    # 2) 摄像机锚点回到 DK 原版
    dk_cam = dk.camera_target(*dk.sprite_xy())
    ic_cam = ic.camera_target(x, y)
    ck('camFollow 回到 DK 原版 (%.1f,%.1f vs %.1f,%.1f)' % (ic_cam[0], ic_cam[1], dk_cam[0], dk_cam[1]),
       abs(ic_cam[0] - dk_cam[0]) <= 0.01 and abs(ic_cam[1] - dk_cam[1]) <= 0.01,
       'dx=%.4f dy=%.4f' % (ic_cam[0] - dk_cam[0], ic_cam[1] - dk_cam[1]))

    # 3) 全动画脚底线不脱节（hurt 为 IC 官方受击下沉动作，attack 为特效动画，单独处理）
    base_feet = ic_idle[3]
    bad = []
    for a in ic.data['animations']:
        if a.get('anim') in ('attack', 'hurt'):
            continue
        wb = ic.anim_world_bbox(a, x, y)
        if wb is None:
            continue
        if abs(wb[3] - base_feet) > 12:
            bad.append('%s:%.0f' % (a.get('anim'), wb[3]))
    ck('除 attack/hurt 外全部动作脚底线脱节 ≤12px', not bad, ','.join(bad) if bad else '全部贴合')

    # 3b) hurt 动画：IC 官方 offsets，画布 280x273 比 idle 高 -> 受击下沉
    for a in ic.data['animations']:
        if a.get('anim') == 'hurt':
            wb = ic.anim_world_bbox(a, x, y)
            warn('hurt 动画脚底下探 %.0fpx（IC 官方 offsets[50,50] + 280x273 画布，'
                 '受击下蹲设定，未改动官方值）' % (wb[3] - base_feet), '%.0f' % (wb[3] - base_feet))
            break

    # 4) BF 落在 cargo 舞台可视范围内
    zoom = STAGE['defaultZoom']
    half_w, half_h = 1280 / zoom / 2.0, 720 / zoom / 2.0
    vis = (ic_cam[0] - half_w, ic_cam[0] + half_w, ic_cam[1] - half_h, ic_cam[1] + half_h)
    ck('BF idle 完整落在镜头视野内 (视野 x[%g,%g] y[%g,%g])' % vis,
       ic_idle[0] >= vis[0] and ic_idle[2] <= vis[1] and ic_idle[1] >= vis[2] and ic_idle[3] <= vis[3],
       'BF x[%g,%g] y[%g,%g]' % ic_idle[:4])

    # 5) attack：躯干帧必须留在 idle 位置附近（特效帧向左延伸，属 IC 设计）
    atk_anim = next((a for a in ic.data['animations'] if a.get('anim') == 'attack'), None)
    atk_body, atk_fx = [], []
    if atk_anim:
        from calc_bf_ic_layout import frames_for_prefix
        sel = frames_for_prefix(ic.frames, atk_anim['name'])
        for f in sel:
            wb = ic.frame_world_bbox(f, x, y, atk_anim['offsets'])
            (atk_body if wb[0] >= ic_idle[0] - 120 else atk_fx).append(wb)
    ck('attack 躯干帧保持在 idle 站位附近',
       bool(atk_body) and all(abs(b[0] - ic_idle[0]) <= 120 for b in atk_body),
       '躯干帧 %d 个, 左边 %s' % (len(atk_body), sorted({round(b[0]) for b in atk_body})))
    if atk_fx:
        reach = min(b[0] for b in atk_fx)
        warn('attack 特效左缘 %g（特效延伸 %.0fpx，IC 原版长度）' % (reach, ic_idle[0] - reach),
             '%.0f' % (ic_idle[0] - reach))

    # 6) 图集前缀全部命中
    txt = io.open(IC_XML, encoding='utf-8', errors='replace').read()
    import re
    frames = re.findall(r'name="([^"]+)"', txt)
    ok = True
    for a in ic.data['animations']:
        pref = a.get('name', '')
        if not any(f.startswith(pref) for f in frames):
            ok = False
            print('    !! 前缀无帧: %r' % pref)
    ck('全部动画前缀命中图集(%d 帧)' % len(frames), ok)

    # 7) 图集文件与 IC 原件 md5 一致
    ck('bf-ic 图集 png md5 与 IC 原件一致',
       md5(IC_PNG) == md5(IC + '/images/characters/cuphead/BoyFriend_ICCuphead.png'))
    ck('bf-ic 图集 xml md5 与 IC 原件一致',
       md5(IC_XML) == md5(IC + '/images/characters/cuphead/BoyFriend_ICCuphead.xml'))

    # 8) 两个角色 json 完全一致
    ck('bf.json 与 bf-ic.json 内容一致',
       md5(GAME + '/characters/bf.json') == md5(GAME + '/characters/bf-ic.json'))

    # 9) chart player1 仍是 bf
    for s in SONGS:
        p = GAME + '/data/%s/%s-hard.json' % (s, s)
        if os.path.exists(p):
            d = load_json(p)
            ck('%s player1 保持 bf' % s, d.get('player1') == 'bf', d.get('player1'))

    # 10) Lua 未被破坏（用 v6 的剥离注释/字符串逻辑，避免注释里的字样误报）
    from apply_dk_lua_v6 import code_only, lua_static_check
    for rel in ['scripts/DK_Fun.lua', 'scripts/DK_Push.lua', 'scripts/BOTPLAY_Pro.lua']:
        p = os.path.join(GAME, rel)
        if not os.path.exists(p):
            continue
        code = code_only(p)
        ck('%s 代码区无 runHaxeCode' % rel, 'runHaxeCode' not in code)
        ok_bal, ok_br, ok_then, ok_str, unknown, _ = lua_static_check(p)
        ck('%s Lua 静态检查通过（function/end 配平、括号、then、字符串闭合）' % rel,
           ok_bal and ok_br and ok_then and ok_str and not unknown,
           '未知调用:%s' % ','.join(unknown) if unknown else '')


# ---------------------------------------------------------------- 同步 + 打包
def sync_and_zip():
    for src in SOURCES:
        n = 0
        for rel in FILES:
            a, b = os.path.join(GAME, rel), os.path.join(src, rel)
            if not os.path.isfile(a):
                continue
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
            n += 1
        same = all(md5(os.path.join(GAME, r)) == md5(os.path.join(src, r))
                   for r in FILES if os.path.isfile(os.path.join(GAME, r)))
        ck('%s 同步 %d 文件且 md5 全一致' % (os.path.basename(src), n), same)

    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            p = os.path.join(GAME, rel)
            if os.path.isfile(p):
                z.write(p, 'DK_Duet/' + rel.replace('\\', '/'))
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        ck('zip CRC OK / %d 项' % len(z.namelist()), bad is None, bad)
    print('[zip] %s  %d bytes' % (ZIP, os.path.getsize(ZIP)))


def main():
    print('=== DK_Duet Lua v7 部署（bf-ic 站位/摄像机修正）===')
    backup_once()
    sol = apply_fix()
    verify(sol)
    sync_and_zip()
    fail = [n for n, ok, _ in CHECKS if not ok]
    print('\n=== 校验汇总: %d 项, 失败 %d 项, 提示 %d 项 ===' % (len(CHECKS), len(fail), len(WARNS)))
    for f in fail:
        print('  !! ' + f)
    for w in WARNS:
        print('  ~~ ' + w)
    return 1 if fail else 0


if __name__ == '__main__':
    sys.exit(main())
