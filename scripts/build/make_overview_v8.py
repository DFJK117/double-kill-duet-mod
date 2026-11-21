# -*- coding: utf-8 -*-
"""v8 总览验收图：四角色 BEFORE/AFTER + 两个自定义 type 按键 + GOD 徽章。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import recolor_characters as RC

BACK = r'E:/UST_work/dk_miku/_backup_god_v8_20261115/images/characters'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'
ASSETS = r'E:/UST_work/dk_miku/_godmode/assets'
OUT = r'E:/UST_work/dk_miku/_godmode/v8_overview.png'

ROLES = [
    ('teto', 'teto-2026.png', 'teto-2026.xml', 'idle', 'Teto'),
    ('momo', 'momo_assets.png', 'momo_assets.xml', 'Momo Idle', '桃音 Momo'),
    ('miku', 'miku_assets.png', 'miku_assets.xml', 'idle_miku', '初音 Miku'),
    ('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml',
     'BF idle dance instance', 'BF (Cuphead)'),
]

try:
    F_TITLE = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 34)
    F_SUB = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
    F_LBL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 19)
except Exception:
    F_TITLE = F_SUB = F_LBL = ImageFont.load_default()

CELL_W, CELL_H = 250, 330
PAD = 14
COLS = len(ROLES)


def frame_of(base, png, xml, fam):
    RC.BASE = base
    src = Image.open(os.path.join(base, png)).convert('RGBA')
    t = RC.families(xml)[fam][0]
    x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
    return src.crop((x, y, x + w, y + h))


def fit(im, cw, ch):
    sc = min(cw / im.width, ch / im.height)
    return im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)


def cell(im):
    c = fit(im, CELL_W, CELL_H)
    bg = Image.new('RGB', (CELL_W, CELL_H), (236, 236, 240))
    bg.paste(c, ((CELL_W - c.width) // 2, (CELL_H - c.height) // 2), c)
    return bg


def main():
    W = COLS * (CELL_W + PAD) + PAD
    H = 70 + 2 * (CELL_H + 70) + 215
    S = Image.new('RGB', (W, H), (250, 250, 252))
    d = ImageDraw.Draw(S)
    d.text((PAD, 16), 'DK_Duet v8 · GOD 模式配色：主题色黑 / 手黄 / 话筒原色',
           fill=(20, 20, 25), font=F_TITLE)

    rows = [('BEFORE 原画', BACK), ('AFTER 重着色', GAME)]
    for ri, (title, base) in enumerate(rows):
        y0 = 70 + ri * (CELL_H + 70)
        d.text((PAD, y0 - 2), title, fill=(70, 70, 90), font=F_SUB)
        for ci, (tag, png, xml, fam, name) in enumerate(ROLES):
            fr = frame_of(base, png, xml, fam)
            x = PAD + ci * (CELL_W + PAD)
            S.paste(cell(fr), (x, y0 + 26))
            d.rectangle([x, y0 + 26, x + CELL_W - 1, y0 + 26 + CELL_H - 1],
                        outline=(180, 180, 195))
            d.text((x + 4, y0 + 26 + CELL_H + 4), name, fill=(40, 40, 50), font=F_LBL)

    # 底部：两个自定义 type + GOD 徽章
    y0 = 70 + 2 * (CELL_H + 70) + 8
    d.text((PAD, y0), '新增自定义按键类型（GOD 模式）', fill=(70, 70, 90), font=F_SUB)
    items = []

    def note_first(base):
        """从 Sparrow 图集里裁出第一帧（purple0000），否则缩略图看不清"""
        import xml.etree.ElementTree as ET
        root = ET.parse(os.path.join(ASSETS, base + '.xml')).getroot()
        for t in root.iter('SubTexture'):
            if t.get('name') == 'purple0000':
                x, y = int(t.get('x')), int(t.get('y'))
                w, h = int(t.get('width')), int(t.get('height'))
                im = Image.open(os.path.join(ASSETS, base + '.png')).convert('RGBA')
                return im.crop((x, y, x + w, y + h))
        return Image.open(os.path.join(ASSETS, base + '.png')).convert('RGBA')

    for name, cap in (('dk_trap', 'DK Trap · 红框黑内+红环（按到即死）'),
                      ('dk_warn', 'DK Warn · 黄三角黑感叹号（漏按即死）')):
        try:
            items.append((note_first(name), cap))
        except Exception as e:
            print('  跳过 %s: %s' % (name, e))
    p = os.path.join(ASSETS, 'dk_god_badge.png')
    if os.path.exists(p):
        items.append((Image.open(p).convert('RGBA'), 'GOD 模式徽章 · F4 切换'))
    x = PAD
    SLOT = 330
    for im, cap in items:
        c = fit(im, 210, 92)
        bg = Image.new('RGB', (c.width, c.height), (245, 245, 248))
        bg.paste(c, (0, 0), c)
        S.paste(bg, (x, y0 + 34))
        d.rectangle([x, y0 + 34, x + c.width - 1, y0 + 33 + c.height], outline=(180, 180, 195))
        # 说明文字按槽位宽度折行，避免互相压字
        words = cap.split(' ')
        lines, cur = [], ''
        for w in words:
            t2 = (cur + ' ' + w).strip()
            if d.textlength(t2, font=F_LBL) > SLOT - 8:
                lines.append(cur)
                cur = w
            else:
                cur = t2
        if cur:
            lines.append(cur)
        for li, ln in enumerate(lines):
            d.text((x + 2, y0 + 38 + c.height + li * 24), ln, fill=(50, 50, 60), font=F_LBL)
        x += SLOT
    S.save(OUT)
    print('总览图 ->', OUT, S.size)


if __name__ == '__main__':
    main()
