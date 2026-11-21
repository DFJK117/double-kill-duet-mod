# -*- coding: utf-8 -*-
"""统计四个角色图集的调色板，输出色卡图 + 颜色清单，供人工归类
   (skin=手 / mic=话筒 / body=其余)。"""
from PIL import Image
import os, collections, sys

BASE = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'
OUT = r'E:/UST_work/dk_miku/_godmode'

SETS = [
    ('miku', 'miku_assets.png'),
    ('momo', 'momo_assets.png'),
    ('teto', 'teto-2026.png'),
    ('bf', 'cuphead/BoyFriend_ICCuphead.png'),
]

for name, png in SETS:
    p = os.path.join(BASE, png)
    im = Image.open(p).convert('RGBA')
    # 采样：缩小不可行(会混色)，直接全量统计但跳过全透明
    px = im.load()
    cnt = collections.Counter()
    W, H = im.size
    data = im.getdata()
    for r, g, b, a in data:
        if a < 8:
            continue
        cnt[(r, g, b)] += 1
    top = cnt.most_common(40)
    print('=' * 70)
    print('%s  %s  %dx%d  不透明色数=%d' % (name, png, W, H, len(cnt)))
    for i, (c, n) in enumerate(top):
        print('  %2d  rgb(%3d,%3d,%3d)  %8d px' % (i, c[0], c[1], c[2], n))
    # 色卡图
    cols, cell = 10, 120
    rows = (len(top) + cols - 1) // cols
    S = Image.new('RGB', (cols * cell, rows * (cell + 26)), (240, 240, 244))
    from PIL import ImageDraw, ImageFont
    d = ImageDraw.Draw(S)
    try:
        fnt = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 16)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (c, n) in enumerate(top):
        cx, cy = (i % cols) * cell, (i // cols) * (cell + 26)
        d.rectangle([cx + 4, cy + 4, cx + cell - 8, cy + cell - 8], fill=c)
        d.text((cx + 6, cy + cell - 4), '#%02d %d' % (i, n), fill=(20, 20, 20), font=fnt)
    S.save(os.path.join(OUT, 'palette_%s.png' % name))
    print('  -> palette_%s.png' % name)
