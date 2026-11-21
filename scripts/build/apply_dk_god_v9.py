# -*- coding: utf-8 -*-
"""DK_Duet v9 部署：箭头陷阱键 / 双方侧 God 特殊键 / God 难度 / 黑黄 icon。

改动清单：
  1. dk_trap 皮肤重做为「原版箭头剪影 + 黑内红边 + 红色光环」
  2. health bar 小图标（icon-*.png）黑黄化
  3. 谱面改造：玩家侧 + 对手侧都加 DK Trap / DK Warn，数量大幅提升
  4. 新增 God 难度：data/<song>/<song>-god.json，week difficulties = "hard,god"
  5. DK_God.lua 增加对手侧 DK Warn 的轮询判定（引擎不对手侧漏按不调 noteMiss）
"""
import json, os, shutil, sys, zipfile, hashlib, xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_charts_god_v9 as P9
import recolor_icons as RI
import make_trap_arrow as MTA

WORK = r'E:/UST_work/dk_miku'
GOD = WORK + '/_godmode'
STAGE = GOD + '/stage'
ASSETS = GOD + '/assets'
TARGETS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
BACKUP = WORK + '/_backup_god_v8_20261115'
ZIP = WORK + '/DK_Duet_Lua_v9_20261116.zip'

CHARTS = [
    ('double-kill', '桃音+Teto'),
    ('double-kill-miku', '初音+Teto'),
]
WEEKS = {
    'double-kill': 'weeks/dk-momo.json',
    'double-kill-miku': 'weeks/dk-miku.json',
}

CHECKS = []


def ck(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  | ' + str(detail)) if detail != '' else ''))
    return ok


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


# ---------------------------------------------------------------
def build_trap_skin():
    """生成 dk_trap 的 png + xml（4 方向箭头 + hold 帧）"""
    from PIL import Image, ImageDraw
    frames = MTA.build_trap_frames()          # [(color, Image), ...]
    imgs = [f for _, f in frames]
    n = len(imgs)
    W = sum(i.width for i in imgs)
    H = max(i.height for i in imgs)
    png = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    entries = []
    x = 0
    for (name, img), im in zip(frames, imgs):
        png.paste(im, (x, 0))
        entries.append((name + '0000', x, 0, im.width, im.height))
        x += im.width
    # hold 帧（保险用，两种 type 都不会带长音）
    piece = Image.new('RGBA', (50, 44), (0, 0, 0, 0))
    ImageDraw.Draw(piece).rectangle([6, 6, 43, 37], fill=(214, 34, 44, 255),
                                     outline=(14, 14, 18, 255), width=3)
    end = Image.new('RGBA', (50, 64), (0, 0, 0, 0))
    ImageDraw.Draw(end).rectangle([8, 10, 41, 53], fill=(214, 34, 44, 255),
                                  outline=(14, 14, 18, 255), width=3)
    for c in ('purple', 'blue', 'green', 'red'):
        entries.append((c + ' hold piece0000', 0, 0, piece.width, piece.height))
        entries.append((c + ' hold end0000', 0, 0, end.width, end.height))
    entries.append(('pruple end hold0000', 0, 0, end.width, end.height))
    # hold 帧直接复用第一张箭头的像素区域（引擎只在长音时用）
    # -> 单独拼在后面
    hold_imgs = [piece] * 4 + [end] * 4 + [end]
    hw = sum(i.width for i in hold_imgs)
    hh = max(i.height for i in hold_imgs)
    hold_png = Image.new('RGBA', (hw, hh), (0, 0, 0, 0))
    hx = 0
    hold_entries = []
    hold_names = []
    for c in ('purple', 'blue', 'green', 'red'):
        hold_names.append(c + ' hold piece0000')
    for c in ('purple', 'blue', 'green', 'red'):
        hold_names.append(c + ' hold end0000')
    hold_names.append('pruple end hold0000')
    for nm, im in zip(hold_names, hold_imgs):
        hold_png.paste(im, (hx, 0))
        hold_entries.append((nm, hx, 0, im.width, im.height))
        hx += im.width
    total = Image.new('RGBA', (W + hw, H), (0, 0, 0, 0))
    total.paste(png, (0, 0))
    total.paste(hold_png, (W, 0))
    all_entries = entries[:-9] + [(nm, W + ox, oy, w, h) for nm, ox, oy, w, h in hold_entries]

    png_path = os.path.join(ASSETS, 'dk_trap.png')
    total.save(png_path)
    xml = ['<?xml version="1.0" encoding="utf-8"?>',
           '<TextureAtlas imagePath="dk_trap.png" width="%d" height="%d">' % (total.width, total.height)]
    for nm, ox, oy, w, h in all_entries:
        xml.append('  <SubTexture name="%s" x="%d" y="%d" width="%d" height="%d" '
                   'frameX="0" frameY="0" frameWidth="%d" frameHeight="%d"/>' % (nm, ox, oy, w, h, w, h))
    xml.append('</TextureAtlas>')
    with open(os.path.join(ASSETS, 'dk_trap.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(xml))
    print('  dk_trap 皮肤：%d 帧，%dx%d' % (len(all_entries), total.width, total.height))


def build_icons():
    RI.run()
    for n in RI.ALL_NAMES:
        p = os.path.join(GOD, 'recolored_%s.png' % n)
        print('  %-18s -> %s' % (n, os.path.basename(p)))


def push_assets():
    for name in ('dk_trap.png', 'dk_trap.xml', 'dk_warn.png', 'dk_warn.xml', 'dk_god_badge.png'):
        for t in TARGETS:
            copy(os.path.join(ASSETS, name), os.path.join(t, 'images', name))
    for n in RI.ALL_NAMES:
        src = os.path.join(GOD, 'recolored_%s.png' % n)
        for t in TARGETS:
            copy(src, os.path.join(t, 'images', 'icons', n + '.png'))
    print('已推送：dk_trap 箭头皮肤 + %d 个黑黄 icon' % len(RI.ALL_NAMES))


def push_charts():
    """hard 难度改造 + 生成 god 难度"""
    for song, label in CHARTS:
        for t in TARGETS:
            hard_rel = 'data/%s/%s-hard.json' % (song, song)
            hard = os.path.join(t, hard_rel)
            god_rel = 'data/%s/%s-god.json' % (song, song)
            godp = os.path.join(t, god_rel)
            if not os.path.exists(hard):
                continue
            # --- hard：从备份原版重建，再叠加新配置 ---
            src_backup = os.path.join(BACKUP, hard_rel)
            if os.path.exists(src_backup):
                base = P9.load(src_backup)
            else:
                base = P9.load(hard)
            if not P9.has_special(base):
                P9.patch_chart(base, P9.HARD_TRAP_PLAYER, P9.HARD_WARN_PLAYER,
                               P9.HARD_TRAP_OPP, 0, seed=P9.SEED, label=label + ' hard')
                P9.dump(base, hard)
            else:
                print('  跳过（已改造）', hard_rel)
            # --- god：以 hard 为基底，特殊键更密 ---
            g = P9.load(hard)
            # 去掉 hard 里的特殊键，god 重新分配
            for sec in g['notes']:
                keep = []
                for n in sec['sectionNotes']:
                    if len(n) > 3 and n[3] in (P9.TRAP, P9.WARN):
                        n = n[:3]
                    keep.append(n)
                sec['sectionNotes'] = keep
            P9.patch_chart(g, P9.GOD_TRAP_PLAYER, P9.GOD_WARN_PLAYER,
                           P9.GOD_TRAP_OPP, P9.GOD_WARN_OPP,
                           seed=P9.SEED + 1, label=label + ' god')
            P9.dump(g, godp)
    print('已改造 hard + 生成 god 难度谱面')


def push_weeks():
    """week difficulties: 'hard' -> 'hard,god'"""
    for song, rel in WEEKS.items():
        for t in TARGETS:
            p = os.path.join(t, rel)
            if not os.path.exists(p):
                continue
            with open(p, encoding='utf-8') as f:
                w = json.load(f)
            if w.get('difficulties') != 'hard,god':
                w['difficulties'] = 'hard,god'
                with open(p, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(w, f, ensure_ascii=False, indent=1)
    print('week difficulties -> "hard,god"')


def push_lua():
    files = [
        ('scripts/DK_God.lua', 'scripts/DK_God.lua'),
        ('custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.lua'),
        ('custom_notetypes/DK Trap.txt', 'custom_notetypes/DK Trap.txt'),
        ('custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.lua'),
        ('custom_notetypes/DK Warn.txt', 'custom_notetypes/DK Warn.txt'),
    ]
    for s, d in files:
        for t in TARGETS:
            copy(os.path.join(STAGE, s), os.path.join(t, d))
    print('已推送 Lua')


# ---------------------------------------------------------------
def validate():
    print('\n=== 校验 ===')
    game = TARGETS[0]
    from PIL import Image

    # 1) dk_trap 是箭头造型（尺寸应与原版箭头一致：154x157 / 157x154）
    root = ET.parse(os.path.join(game, 'images', 'dk_trap.xml')).getroot()
    frames = {t.get('name'): (int(t.get('x')), int(t.get('y')),
                              int(t.get('width')), int(t.get('height')))
              for t in root.iter('SubTexture')}
    for c in ('purple', 'blue', 'green', 'red'):
        ck('dk_trap 有 %s0000 帧' % c, c + '0000' in frames)
    ck('dk_trap 帧数 >= 13', len(frames) >= 13, '%d 帧' % len(frames))
    # 箭头尺寸应为原版尺寸
    arrow_sizes = {'purple': (154, 157), 'blue': (157, 154),
                   'green': (157, 154), 'red': (154, 157)}
    for c, sz in arrow_sizes.items():
        f = frames.get(c + '0000')
        ck('dk_trap %s 箭头尺寸 %s' % (c, sz),
           f is not None and (f[2], f[3]) == sz,
           str((f[2], f[3]) if f else None))

    # 2) 全部 icon 都变了且是黑黄主题
    for n in RI.ALL_NAMES:
        o = md5(os.path.join(BACKUP, 'images', 'icons', n + '.png'))
        v = md5(os.path.join(game, 'images', 'icons', n + '.png'))
        ck('%s icon 已重着色' % n, o != v)
        im = Image.open(os.path.join(game, 'images', 'icons', n + '.png')).convert('RGBA')
        px = im.load()
        dark = 0
        yellow = 0
        for y in range(0, im.size[1], 2):
            for x in range(0, im.size[0], 2):
                r, g, b, a = px[x, y]
                if a < 128:
                    continue
                if r < 90 and g < 90 and b < 90:
                    dark += 1
                elif r > 150 and g > 110 and b < 130 and r > b + 60:
                    yellow += 1
        # 黑黄双色合计应占绝对多数（不能还有大片彩色残留）
        allpx = 0
        color = 0
        for y in range(0, im.size[1], 2):
            for x in range(0, im.size[0], 2):
                r, g, b, a = px[x, y]
                if a < 128:
                    continue
                allpx += 1
                if r > 150 and g > 110 and b < 130 and r > b + 60:
                    continue          # 黄色（主题色）
                if r < 90 and g < 90 and b < 90:
                    continue          # 黑色（主题色）
                color += 1
        ck('%s icon 无彩色残留' % n,
           allpx > 0 and color / float(allpx) < 0.22,
           '彩色 %d / 共 %d (%.1f%%)' % (color, allpx, 100.0 * color / max(allpx, 1)))
        ck('%s icon 黑黄主题' % n, dark + yellow > 0, '黑 %d / 黄 %d' % (dark, yellow))

    # 3) 谱面：双方侧特殊键数量 + God 难度文件
    for song, label in CHARTS:
        for diff, exp in (('hard', (P9.HARD_TRAP_PLAYER, P9.HARD_WARN_PLAYER, P9.HARD_TRAP_OPP, 0)),
                          ('god', (P9.GOD_TRAP_PLAYER, P9.GOD_WARN_PLAYER, P9.GOD_TRAP_OPP, P9.GOD_WARN_OPP))):
            rel = 'data/%s/%s-%s.json' % (song, song, diff)
            p = os.path.join(game, rel)
            if not ck('%s 难度文件存在 %s' % (diff, rel), os.path.exists(p)):
                continue
            c = P9.load(p)
            sc = P9.side_count(c)
            ck('%s %s 玩家侧 Trap=%d' % (label, diff, exp[0]), sc['p_trap'] == exp[0], sc['p_trap'])
            ck('%s %s 玩家侧 Warn=%d' % (label, diff, exp[1]), sc['p_warn'] == exp[1], sc['p_warn'])
            ck('%s %s 对手侧 Trap=%d' % (label, diff, exp[2]), sc['o_trap'] == exp[2], sc['o_trap'])
            ck('%s %s 对手侧 Warn=%d' % (label, diff, exp[3]), sc['o_warn'] == exp[3], sc['o_warn'])
            # 段级 mustHitSection 必须保留原样混合
            with open(os.path.join(BACKUP, 'data/%s/%s-hard.json' % (song, song)),
                      encoding='utf-8-sig') as f:
                oc = json.load(f)
            ck('%s %s 段数不变' % (label, diff),
               len(c['notes']) == len(oc['notes']), '%d vs %d' % (len(c['notes']), len(oc['notes'])))
            ck('%s %s mustHitSection 混合保留' % (label, diff),
               len(set(s['mustHitSection'] for s in c['notes'])) == 2)
            # 同轨同刻重复数不增加
            rows = [(n[0], n[1]) for s in c['notes'] for n in s['sectionNotes']]
            orows = [(n[0], n[1]) for s in oc['notes'] for n in s['sectionNotes']]
            ck('%s %s 未新增同轨同刻重复' % (label, diff),
               len(rows) - len(set(rows)) == len(orows) - len(set(orows)),
               '现 %d 原 %d' % (len(rows) - len(set(rows)), len(orows) - len(set(orows))))
            # 对手侧音符不能被误标成已有 type
            bad = []
            for s in c['notes']:
                for n in s['sectionNotes']:
                    if n[1] >= 4 and len(n) > 3 and n[3] not in (
                            'DK Trap', 'DK Warn', 'Opponent 2 Sing', 'Both Opponents Sing'):
                        bad.append(n)
            ck('%s %s 对手侧 type 合法' % (label, diff), not bad, str(bad[:2]))

    # 4) week 注册了 god 难度
    for song, rel in WEEKS.items():
        with open(os.path.join(game, rel), encoding='utf-8') as f:
            w = json.load(f)
        ck('%s week difficulties 含 god' % song,
           'god' in (w.get('difficulties') or ''), w.get('difficulties'))

    # 5) Lua 无 runHaxeCode
    for rel in ('scripts/DK_God.lua', 'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Warn.lua'):
        with open(os.path.join(game, rel), encoding='utf-8') as f:
            t = f.read()
        code = '\n'.join(l for l in t.splitlines() if not l.strip().startswith('--'))
        ck('%s 无 runHaxeCode' % rel, 'runHaxeCode' not in code)
    with open(os.path.join(game, 'scripts/DK_God.lua'), encoding='utf-8') as f:
        g = f.read()
    ck('DK_God.lua 注册 goodNoteHit', 'function goodNoteHit' in g)
    ck('DK_God.lua 注册 noteMiss', 'function noteMiss' in g)
    ck('DK_God.lua 处理对手侧 Warn', 'oppWarn' in g or 'opponentWarn' in g)

    # 6) 三处一致
    for rel in ('scripts/DK_God.lua', 'images/dk_trap.png',
                'images/icons/icon-momo-teto.png', 'images/icons/icon-surprise.png',
                'data/double-kill/double-kill-god.json',
                'data/double-kill-miku/double-kill-miku-god.json',
                'weeks/dk-momo.json', 'weeks/dk-miku.json'):
        hs = set(md5(os.path.join(t, rel)) for t in TARGETS)
        ck('三处一致 %s' % rel, len(hs) == 1, '%d 个不同' % len(hs))

    fail = [n for n, ok, _ in CHECKS if not ok]
    print('\n=== 汇总: %d 项, 失败 %d 项 ===' % (len(CHECKS), len(fail)))
    for f in fail:
        print('  !! ' + f)
    return 1 if fail else 0


def pack():
    files = [
        'scripts/DK_God.lua', 'scripts/DK_Push.lua',
        'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.txt',
        'custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.txt',
        'images/dk_trap.png', 'images/dk_trap.xml',
        'images/dk_warn.png', 'images/dk_warn.xml', 'images/dk_god_badge.png',
        'images/icons/icon-bf.png', 'images/icons/icon-momo.png',
        'images/icons/icon-teto-cozy.png', 'images/icons/icon-miku.png',
        'images/icons/icon-momo-teto.png', 'images/icons/icon-miku-teto.png',
        'images/icons/icon-double-kill.png', 'images/icons/icon-surprise.png',
        'images/characters/miku_assets.png', 'images/characters/momo_assets.png',
        'images/characters/teto-2026.png', 'images/characters/cuphead/BoyFriend_ICCuphead.png',
        'images/characters/bf/defeatBf-normal.png',
        'data/double-kill/double-kill-hard.json', 'data/double-kill/double-kill-god.json',
        'data/double-kill-miku/double-kill-miku-hard.json',
        'data/double-kill-miku/double-kill-miku-god.json',
        'weeks/dk-momo.json', 'weeks/dk-miku.json',
    ]
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            p = os.path.join(TARGETS[0], rel)
            if os.path.exists(p):
                z.write(p, 'DK_Duet/' + rel)
    zf = zipfile.ZipFile(ZIP)
    print('打包 -> %s  (%d 项, %d B, CRC %s)'
          % (ZIP, len(zf.namelist()), os.path.getsize(ZIP),
             'OK' if zf.testzip() is None else 'BAD'))
    print('md5:', md5(ZIP))


if __name__ == '__main__':
    print('=== 生成资源 ===')
    build_trap_skin()
    build_icons()
    print('\n=== 部署 ===')
    push_assets()
    push_lua()
    push_charts()
    push_weeks()
    rc = validate()
    pack()
    sys.exit(rc)
