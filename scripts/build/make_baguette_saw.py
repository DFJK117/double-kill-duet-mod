# -*- coding: utf-8 -*-
"""v11.11: cut the TOP baguette out of the white-background photo -> transparent PNG.
Used as the GOD+ 'saw' projectile sprite (dkBaguette).
"""
from PIL import Image

SRC = r'C:\Users\Administrator\.workbuddy\clipboard-images\clipboard-2026-11-16T13-01-28-277Z-7342d596.png'
OUT_LOCAL = 'E:/UST_work/dk_miku/_godmode/dkBaguette.png'
DEPLOY_IMG = 'E:/UST_work/dk_miku/DK_Dual/images/dkBaguette.png'

im = Image.open(SRC).convert('RGBA')
# top baguette bounding box (measured): x 35..756, y 53..165; add small margin
crop = im.crop((28, 46, 764, 173))
px = crop.load()
W, H = crop.size

# White -> transparent with soft anti-aliased edge: alpha from luminance distance to white.
# The bread is orange (low blue), background near (255,255,255).
for y in range(H):
    for x in range(W):
        r, g, b, a = px[x, y]
        dist = 255 - min(r, g, b)          # 0 on pure white, large on saturated bread
        if dist < 12:
            na = 0
        elif dist < 55:
            na = int((dist - 12) / 43 * 255)
        else:
            na = 255
        px[x, y] = (r, g, b, na)

crop.save(OUT_LOCAL)
crop.save(DEPLOY_IMG)
print('saved', OUT_LOCAL, crop.size)
print('saved', DEPLOY_IMG)

# alpha stats
alphas = [px[x, y][3] for y in range(H) for x in range(W)]
print('opaque px', sum(1 for a in alphas if a > 200), 'transparent px',
      sum(1 for a in alphas if a == 0), 'soft px', sum(1 for a in alphas if 0 < a <= 200))
