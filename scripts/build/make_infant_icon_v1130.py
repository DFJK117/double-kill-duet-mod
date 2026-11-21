# -*- coding: utf-8 -*-
"""把生成的坐姿婴儿图抠成透明底，裁掉水印/阴影，做成 Infant 难度图标。"""
import numpy as np
from PIL import Image

SRC = r'E:/UST_work/dk_miku/_godmode/A_cute_chubby_baby_sitting_upr_2026-11-18T10-20-56.png'
OUT = r'E:/UST_work/dk_miku/_godmode/infant_icon.png'
OUT_WEBP = r'E:/UST_work/dk_miku/_godmode/infant_icon.webp'

im = Image.open(SRC).convert('RGBA')
a = np.array(im).astype(np.float32)
h, w = a.shape[:2]
rgb = a[:, :, :3]

# 白底亮度：取每像素最小通道（白底三通道都高）
mx = rgb.max(axis=2)   # 高=亮
mn = rgb.min(axis=2)
# 背景判定：接近白/浅灰 且 低饱和
sat = mx - mn
bright = mn
bg = (bright > 205) & (sat < 30)

# 右下角水印区(约 x>900,y>940)直接归背景
yy, xx = np.mgrid[0:h, 0:w]
bg |= (xx > w*0.86) & (yy > h*0.90)

# 柔化 alpha：亮度越高越透明
alpha = np.clip((250 - bright) / 45.0 * 255, 0, 255)
alpha = np.where(sat > 40, np.maximum(alpha, np.clip((255 - mx) / 30 * 255, 0, 255)), alpha)
alpha[bg] = 0
# 去孤立噪点：小 alpha 归零
alpha[alpha < 18] = 0

out = a.copy()
out[:, :, 3] = alpha
img = Image.fromarray(out.astype('uint8'), 'RGBA')

# 按 alpha 裁剪到主体
ys, xs = np.where(alpha > 25)
y0, y1 = max(0, ys.min()-8), min(h, ys.max()+9)
x0, x1 = max(0, xs.min()-8), min(w, xs.max()+9)
img = img.crop((x0, y0, x1, y1))

# 缩放到高度 200 保留全身（难度图会再按需缩放）
ratio = 200 / img.height
img = img.resize((max(1, int(img.width*ratio)), 200), Image.LANCZOS)
img.save(OUT)
img.save(OUT_WEBP, quality=95)
print('icon', OUT, img.size, 'alpha>0 px', int((np.array(img)[:, :, 3] > 25).sum()))
