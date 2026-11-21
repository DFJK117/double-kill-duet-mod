# -*- coding: utf-8 -*-
"""v9 总览验收图。

布局：
  行1  BEFORE 原画（角色 + 双人 icon）
  行2  AFTER 重着色（角色 + 双人 icon）
  行3  DK Trap 四向箭头 / DK Warn / GOD 徽章
  行4  God 难度特殊键数量统计表
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import xml.etree.ElementTree as ET
import recolor_characters as RC
import patch_charts_god_v9 as P9
import recolor_icons as RI

BACK = r'E:/UST_work/dk_miku/_backup_god_v8_20261115'
GOD = r'E:/UST_work/dk_miku/_godmode'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ASSETS = GOD + '/assets'
OUT = GOD + '/v9_overview.png'

ROLES = [
    ('teto', 'teto-2026.png', 'teto-2026.xml', 'idle', 'Teto'),
    ('momo', 'momo_assets.png', 'momo_assets.xml', 'Momo Idle', '桃音 Momo'),
    ('miku', 'miku_assets.png', 'miku_assets.xml', 'idle_miku', '初音 Miku'),
    ('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml',
     'BF idle dance instance', 'BF (Cuphead)'),
]

try:
    F_TITLE = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 30)
    F_SUB = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
    F_LBL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
    F_NUM = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 21)
except Exception:
    F_TITLE = F_SUB = F_LBL = F_NUM = ImageFont.load_default()

CELL_W, CELL_H = 230, 300
PAD = 14


def frame_of(base, png, xml, fam):
    RC.BASE = base
    src = Image.open(os.path.join(base, png)).convert('RGBA')
    t = RC.families(xml)[fam][0]
    x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
    return src.crop((x, y, x + w, y + h))


def fit(im, cw, ch):
    sc = min(cw / im.width, ch / im.height)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)


def cell(im, w=CELL_W, h=CELL_H, bg=(236, 236, 240)):
    c = fit(im, w, h)
    b = Image.new('RGB', (w, h), bg)
    b.paste(c, ((w - c.width) // 2, (h - c.height) // 2), c)
    return b


def note_frame(base, color):
    """从 Sparrow 图集裁出指定方向的第一帧"""
    root = ET.parse(os.path.join(ASSETS, base + '.xml')).getroot()
    im = Image.open(os.path.join(ASSETS, base + '.png')).convert('RGBA')
    for t in root.iter('SubTexture'):
        if t.get('name') == color + '0000':
            x, y = int(t.get('x')), int(t.get('y'))
            w, h = int(t.get('width')), int(t.get('height'))
            return im.crop((x, y, x + w, y + h))
    return im


def main():
    COLS = len(ROLES)
    # 行1/2 角色 + 双人 icon
    W = max(COLS * (CELL_W + PAD) + PAD, 1140)
    H = 66 + 2 * (CELL_H + 66) + 190 + 360
    S = Image.new('RGB', (W, H), (250, 250, 252))
    d = ImageDraw.Draw(S)
    d.text((PAD, 14), 'DK_Duet v9 · GOD 模式：全员黑身黄手 + 双方侧特殊键 + God 难度',
           fill=(20, 20, 25), font=F_TITLE)
    d.text((PAD, 44), '新难度请在 Freeplay 选 God；GOD 模式 F4 开关（开启后特殊键不再致死）',
           fill=(120, 120, 140), font=F_LBL)

    rows = [('BEFORE 原画', BACK + '/images/characters'),
            ('AFTER 重着色（黑身 + 黄手 + 话筒原色）', GAME + '/images/characters')]
    for ri, (title, base) in enumerate(rows):
        y0 = 66 + ri * (CELL_H + 66)
        d.text((PAD, y0 - 2), title, fill=(70, 70, 90), font=F_SUB)
        for ci, (tag, png, xml, fam, name) in enumerate(ROLES):
            fr = frame_of(base, png, xml, fam)
            x = PAD + ci * (CELL_W + PAD)
            S.paste(cell(fr), (x, y0 + 26))
            d.rectangle([x, y0 + 26, x + CELL_W - 1, y0 + 25 + CELL_H], outline=(180, 180, 195))
            d.text((x + 4, y0 + 30 + CELL_H), name, fill=(40, 40, 50), font=F_LBL)

    # 行3：icon BEFORE/AFTER
    y0 = 66 + 2 * (CELL_H + 66) + 22
    d.text((PAD, y0), '血条图标 BEFORE / AFTER（8 个：单人 x4 + 双人重叠 x3 + 表情包 x1）',
           fill=(70, 70, 90), font=F_SUB)
    iy = y0 + 28
    for tag, sub in (('BEFORE', BACK + '/images/icons'), ('AFTER', GOD)):
        d.text((PAD, iy + 3), tag, fill=(110, 110, 130), font=F_LBL)
        ix = PAD + 70
        for n in RI.ALL_NAMES:
            p = os.path.join(sub, 'icon-%s.png' % n[5:] if n.startswith('icon-') else n)
            if tag == 'BEFORE':
                p = os.path.join(sub, n + '.png')
            else:
                p = os.path.join(sub, 'recolored_%s.png' % n)
            if not os.path.exists(p):
                continue
            im = Image.open(p).convert('RGBA')
            c = fit(im, 118, 60)
            b = Image.new('RGB', (118, 60), (236, 236, 240))
            b.paste(c, ((118 - c.width) // 2, (60 - c.height) // 2), c)
            S.paste(b, (ix, iy))
            d.rectangle([ix, iy, ix + 117, iy + 59], outline=(180, 180, 195))
            ix += 122
        iy += 66

    # 行4：note 皮肤 + 徽章
    y1 = iy + 6
    d.text((PAD, y1), '自定义按键类型', fill=(70, 70, 90), font=F_SUB)
    items = []
    for cname, cap in (('purple', '紫色(左)'), ('blue', '蓝色(下)'),
                       ('green', '绿色(上)'), ('red', '红色(右)')):
        items.append((note_frame('dk_trap', cname), 'DK Trap · %s' % cap))
    items.append((note_frame('dk_warn', 'purple'), 'DK Warn · 漏按即死'))
    p = os.path.join(ASSETS, 'dk_god_badge.png')
    if os.path.exists(p):
        items.append((Image.open(p).convert('RGBA'), 'GOD 徽章 · F4'))
    x = PAD
    SLOT = 150
    for im, cap in items:
        c = fit(im, 118, 74)
        b = Image.new('RGB', (c.width, c.height), (245, 245, 248))
        b.paste(c, (0, 0), c)
        S.paste(b, (x + 14, y1 + 28))
        d.rectangle([x + 14, y1 + 28, x + 14 + c.width - 1, y1 + 27 + c.height],
                    outline=(180, 180, 195))
        words = cap.split(' ')
        lines, cur = [], ''
        for w in words:
            t2 = (cur + ' ' + w).strip()
            if d.textlength(t2, font=F_LBL) > SLOT - 10:
                lines.append(cur)
                cur = w
            else:
                cur = t2
        if cur:
            lines.append(cur)
        for li, ln in enumerate(lines):
            d.text((x + 14, y1 + 32 + c.height + li * 22), ln, fill=(50, 50, 60), font=F_LBL)
        x += SLOT

    # 行5：God 难度统计表
    y2 = y1 + 150
    d.text((PAD, y2), 'God 难度特殊键统计（双方侧）', fill=(70, 70, 90), font=F_SUB)
    ty = y2 + 30
    hdr = ['曲目 / 难度', '玩家 Trap', '玩家 Warn', '对手 Trap', '对手 Warn', '合计']
    colx = [PAD + 10, PAD + 230, PAD + 360, PAD + 490, PAD + 620, PAD + 760]
    for i, h in enumerate(hdr):
        d.text((colx[i], ty), h, fill=(90, 90, 110), font=F_LBL)
    ty += 26
    for song, label in P9.__dict__.get('_', []) or []:
        pass
    rows_tbl = []
    for song, label in (('double-kill', '桃音+Teto'), ('double-kill-miku', '初音+Teto')):
        for diff in ('hard', 'god'):
            p = os.path.join(GAME, 'data/%s/%s-%s.json' % (song, song, diff))
            if not os.path.exists(p):
                continue
            c = P9.load(p)
            sc = P9.side_count(c)
            rows_tbl.append(('%s %s' % (label, diff), sc['p_trap'], sc['p_warn'],
                             sc['o_trap'], sc['o_warn'],
                             sc['p_trap'] + sc['p_warn'] + sc['o_trap'] + sc['o_warn']))
    for r in rows_tbl:
        for i, v in enumerate(r):
            d.text((colx[i], ty), str(v), fill=(30, 30, 40),
                   font=F_NUM if i == 5 else F_LBL)
        ty += 28

    S = S.crop((0, 0, W, min(H, ty + 18)))
    S.save(OUT)
    print('总览图 ->', OUT, S.size)


if __name__ == '__main__':
    main()
