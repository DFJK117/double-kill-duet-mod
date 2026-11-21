# -*- coding: utf-8 -*-
"""诊断：复现 classify 的脸/手判定，打印每个肤色块的归类打分。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageChops
import recolor_characters as R

tag = sys.argv[1] if len(sys.argv) > 1 else 'miku'
fam = sys.argv[2] if len(sys.argv) > 2 else 'idle_miku'
cfg = R.CFG[tag]
src = Image.open(os.path.join(R.SRC, cfg['png'])).convert('RGBA')
t = R.families(cfg['xml'])[fam][0]
X, Y, W, H = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
fr = src.crop((X, Y, X + W, Y + H))
w, h = fr.size
rgba = fr.convert('RGBA')
a = rgba.getchannel('A').point(lambda p: 255 if p > 0 else 0)
skin_raw = ImageChops.multiply(R.hsv_mask(rgba, cfg['skin']), a)
px = fr.load()

am = a.getbbox()
top_y, bot_y = am[1], am[3]
span = max(1, bot_y - top_y)
body_cx = (am[0] + am[2]) / 2.0
body_w = max(1, am[2] - am[0])
rel_y = lambda b: ((b[2][1] + b[2][3]) / 2.0 - top_y) / span
is_leg = lambda b: rel_y(b) > 0.65 and abs((b[2][0] + b[2][2]) / 2.0 - body_cx) < body_w * 0.15

blocks = [b for b in R.components(R.dilate(skin_raw, 2), 30) if not R.slender(b)]
blocks = [b for b in blocks if b[0] >= R.MIN_HAND]
apx = a.load()


def top_exposed(b):
    x0, y0, x1, y1 = b[2]
    ya = y0 - R.TOP_BAND
    if ya < 0:
        return False
    xa, xb = max(0, x0), min(w, x1)
    if xb <= xa:
        return False
    bg = tot = 0
    for y in range(ya, y0):
        for x in range(xa, xb):
            tot += 1
            if not apx[x, y]:
                bg += 1
    return tot > 0 and bg * 2 > tot


def score(b):
    rel = rel_y(b)
    if is_leg(b):
        return 0.0
    pos = 1.0 - 0.7 * max(0.0, rel)
    cx = (b[2][0] + b[2][2]) / 2.0
    off = abs(cx - body_cx) / body_w
    axis = 1.0 if off <= 0.12 else (0.55 if off <= 0.28 else 0.22)
    return b[0] * pos * axis * (0.25 if top_exposed(b) else 1.0)


print('=== %s / %s  %dx%d  body: y[%d..%d] cx=%.0f w=%d' % (tag, fam, w, h, top_y, bot_y, body_cx, body_w))
for b in blocks:
    area, pix, bb = b
    rs = gs = bs = 0
    for p in pix:
        r, g, bl, _ = px[p % w, p // w]
        rs += r; gs += g; bs += bl
    n = len(pix)
    print('  area=%-7d bbox=%-26s rel=%.2f leg=%-5s score=%-10.0f rgb=(%3d,%3d,%3d)'
          % (area, bb, rel_y(b), is_leg(b), score(b), rs // n, gs // n, bs // n))
