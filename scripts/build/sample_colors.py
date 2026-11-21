# -*- coding: utf-8 -*-
"""采样某角色某一帧的颜色分布（HSV 聚类），并输出放大原图便于定位脸/手。"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageChops, ImageDraw
import recolor_characters as R

tag = sys.argv[1] if len(sys.argv) > 1 else 'teto'
fam = sys.argv[2] if len(sys.argv) > 2 else 'idle'
cfg = R.CFG[tag]
src = Image.open(os.path.join(R.BASE, cfg['png'])).convert('RGBA')
t = R.families(cfg['xml'])[fam][0]
x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
fr = src.crop((x, y, x + w, y + h))
fr.save(r'E:/UST_work/dk_miku/_godmode/raw_%s_%s.png' % (tag, fam))

px = fr.load()
hsv = fr.convert('HSV')
hp, sp, vp = hsv.split()
cnt = collections.Counter()
for yy in range(h):
    for xx in range(w):
        r, g, b, a = px[xx, yy]
        if a < 128:
            continue
        hh_, ss_, vv_ = hp.getpixel((xx, yy)), sp.getpixel((xx, yy)), vp.getpixel((xx, yy))
        cnt[(hh_ // 20 * 20, ss_ // 20 * 20, vv_ // 20 * 20, r // 32 * 32, g // 32 * 32, b // 32 * 32)] += 1
print('=== %s / %s  %dx%d  opaque=%d' % (tag, fam, w, h, sum(cnt.values())))
for k, c in cnt.most_common(18):
    print('   HSV(%3d,%3d,%3d) RGB(%3d,%3d,%3d)  n=%d' % (k[0], k[1], k[2], k[3], k[4], k[5], c))
