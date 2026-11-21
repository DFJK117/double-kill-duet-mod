# -*- coding: utf-8 -*-
"""从原画按 bbox 精确取样，输出像素 RGB/HSV 直方图，用于标定 skin / mic 色带。

用法: python sample_region.py <tag> <family> <x0> <y0> <x1> <y1> [topN]
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import recolor_characters as R

R.BASE = r'E:/UST_work/dk_miku/_backup_god_v8_20261115/images/characters'

tag, fam = sys.argv[1], sys.argv[2]
x0, y0, x1, y1 = [int(v) for v in sys.argv[3:7]]
topn = int(sys.argv[7]) if len(sys.argv) > 7 else 12
cfg = R.CFG[tag]
src = Image.open(os.path.join(R.BASE, cfg['png'])).convert('RGBA')
t = R.families(cfg['xml'])[fam][0]
X, Y, W, H = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
fr = src.crop((X, Y, X + W, Y + H))
px = fr.load()
hp, sp, vp = fr.convert('HSV').split()
cnt = collections.Counter()
for yy in range(max(0, y0), min(H, y1)):
    for xx in range(max(0, x0), min(W, x1)):
        r, g, b, a = px[xx, yy]
        if a < 128:
            continue
        cnt[(r, g, b)] += 1
print('=== %s / %s  region (%d,%d)-(%d,%d)  n=%d' % (tag, fam, x0, y0, x1, y1, sum(cnt.values())))
for (r, g, b), c in cnt.most_common(topn):
    rgb = (r, g, b)
    hh, ss, vv = Image.new('RGB', (1, 1), rgb).convert('HSV').getpixel((0, 0))
    print('   RGB(%3d,%3d,%3d)  HSV(%3d,%3d,%3d)  n=%d' % (r, g, b, hh, ss, vv, c))
