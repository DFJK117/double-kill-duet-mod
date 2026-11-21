# -*- coding: utf-8 -*-
"""v10 验收图：hard 原版彩色 vs God 黑黄，两套角色并列 + 谱面规则实证。"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont
import recolor_characters as RC
import patch_charts_god_v9 as P9

GOD = r'E:/UST_work/dk_miku/_godmode'
BACK = r'E:/UST_work/dk_miku/_backup_god_v8_20261115'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
OUT = GOD + '/v10_overview.png'

ROLES = [
    ('teto', 'teto-2026.png', 'teto-2026.xml', 'idle', 'Teto'),
    ('momo', 'momo_assets.png', 'momo_assets.xml', 'Momo Idle', '桃音 Momo'),
    ('miku', 'miku_assets.png', 'miku_assets.xml', 'idle_miku', '初音 Miku'),
    ('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml',
     'BF idle dance instance', 'BF'),
]

try:
    F_TITLE = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 30)
    F_SUB = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 22)
    F_LBL = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 18)
    F_NUM = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 21)
except Exception:
    F_TITLE = F_SUB = F_LBL = F_NUM = ImageFont.load_default()

CELL_W, CELL_H = 220, 280
PAD = 14


def frame_of(base, png, xml, fam):
    RC.BASE = base
    src = Image.open(os.path.join(base, png)).convert('RGBA')
    t = RC.families(xml)[fam][0]
    x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
    return src.crop((x, y, x + w, y + h))


def cell(im, w=CELL_W, h=CELL_H, bg=(238, 238, 242)):
    sc = min(w / im.width, h / im.height)
    r = im.resize((max(1, int(im.width * sc)), max(1, int(im.height * sc))), Image.LANCZOS)
    b = Image.new('RGB', (w, h), bg)
    b.paste(r, ((w - r.width) // 2, (h - r.height) // 2), r)
    return b


def main():
    cols = len(ROLES)
    W = max(cols * (CELL_W + PAD) + PAD, 1100)
    H = 74 + 2 * (CELL_H + 60) + 210
    S = Image.new('RGB', (W, H), (250, 250, 252))
    d = ImageDraw.Draw(S)
    d.text((PAD, 12), 'DK_Duet v10 · 难度资源彻底分离', fill=(20, 20, 25), font=F_TITLE)
    d.text((PAD, 46), 'hard = 原版彩色（干净，无特殊键） ｜ God = 黑黄（独立贴图 + 特殊键）',
           fill=(110, 110, 130), font=F_LBL)

    # 两行：hard 原版 / God 黑黄
    rows = [
        ('HARD 原版彩色（角色名 bf / momo / miku / teto，0 特殊键）', BACK + '/images/characters'),
        ('GOD 黑黄（角色名 *-god，指向 *_god 独立贴图）', GAME + '/images/characters'),
    ]
    for ri, (title, base) in enumerate(rows):
        y0 = 74 + ri * (CELL_H + 60)
        d.text((PAD, y0), title, fill=(70, 70, 90), font=F_SUB)
        for ci, (tag, png, xml, fam, name) in enumerate(ROLES):
            if ri == 1:
                # God 行：读 *_god 图集，但帧坐标来自原版 xml
                godpng = png.replace('.png', '_god.png')
                gp = os.path.join(base, godpng)
                if os.path.exists(gp):
                    src = Image.open(gp).convert('RGBA')
                    RC.BASE = BACK + '/images/characters'
                    t = RC.families(xml)[fam][0]
                    x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
                    fr = src.crop((x, y, x + w, y + h))
                else:
                    fr = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
            else:
                fr = frame_of(base, png, xml, fam)
            x = PAD + ci * (CELL_W + PAD)
            S.paste(cell(fr), (x, y0 + 26))
            d.rectangle([x, y0 + 26, x + CELL_W - 1, y0 + 25 + CELL_H], outline=(180, 180, 195))
            d.text((x + 4, y0 + 30 + CELL_H), name, fill=(40, 40, 50), font=F_LBL)

    # 底部：谱面规则实证表
    y2 = 74 + 2 * (CELL_H + 60)
    d.text((PAD, y2), 'God 谱面特殊键规则（每曲）', fill=(70, 70, 90), font=F_SUB)
    hdr = ['曲目', '玩家 Trap\n(和弦附加)', '玩家 Warn\n(替换普通键)',
           '对手 Trap\n(和弦附加)', '对手 Warn\n(替换普通键)', 'Trap 孤立数\n(必须=0)']
    colx = [PAD + 8, PAD + 180, PAD + 360, PAD + 550, PAD + 730, PAD + 890]
    ty = y2 + 34
    for i, h in enumerate(hdr):
        for li, line in enumerate(h.split('\n')):
            d.text((colx[i], ty + li * 20), line, fill=(90, 90, 110), font=F_LBL)
    ty += 52
    for song, label in (('double-kill', '桃音+Teto'), ('double-kill-miku', '初音+Teto')):
        c = P9.load(os.path.join(GAME, 'data', song, song + '-god.json'))
        sc = P9.side_count(c)
        # Trap 孤立数
        alone = 0
        for sec in c['notes']:
            bytime = {}
            for n in sec['sectionNotes']:
                bytime.setdefault(n[0], []).append(n)
            for t, ns in bytime.items():
                for n in ns:
                    if len(n) > 3 and n[3] == 'DK Trap':
                        sibs = [x for x in ns if (x[1] < 4) == (n[1] < 4)]
                        if len(sibs) < 2:
                            alone += 1
        row = [label, sc['p_trap'], sc['p_warn'], sc['o_trap'], sc['o_warn'], alone]
        for i, v in enumerate(row):
            d.text((colx[i], ty), str(v), fill=(30, 30, 40),
                   font=F_NUM if i in (1, 2, 3, 4, 5) else F_LBL)
        ty += 30
    d.text((PAD, ty + 8), 'hard 难度：0 个 DK Trap / DK Warn（原谱合唱 type 不计）',
           fill=(120, 60, 60), font=F_LBL)

    S = S.crop((0, 0, W, min(H, ty + 48)))
    S.save(OUT)
    print('总览图 ->', OUT, S.size)


if __name__ == '__main__':
    main()
