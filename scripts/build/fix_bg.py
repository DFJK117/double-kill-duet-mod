# -*- coding: utf-8 -*-
"""木箱 TANK in a BOX -> DFJK117 + 左上水印（按实际像素色擦字）"""
import os, collections
from PIL import Image, ImageDraw, ImageFont

SRC = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods/images/stages/airship/double-kill/cargo.png'
DST = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/stages/airship/double-kill/cargo.png'
FONTDIR = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods/fonts'
SIGN = 'DFJK117'

im = Image.open(SRC).convert('RGBA')
px = im.load()

def is_text(c):
    r, g, b = c
    return abs(r - g) <= 7 and abs(g - b) <= 13 and 58 <= r <= 105

n = 0
for y in range(150, 380):
    row = [px[x, y][:3] for x in range(870, 1120)]
    plain = [c for c in row if not is_text(c)]
    fill = collections.Counter(plain).most_common(1)[0][0] if plain else (131, 95, 66)
    for x in range(870, 1120):
        if is_text(px[x, y][:3]):
            px[x, y] = (fill[0], fill[1], fill[2], 255)
            n += 1
print('擦除文字像素', n)

# 文字描边/抗锯齿残留：用木箱主色做羽化软覆盖（边缘渐变，不出现硬方块）
X0, Y0, X1, Y1, FEATHER = 893, 172, 1092, 362, 9
MAIN = (131, 95, 66, 255)
for y in range(Y0, Y1):
    for x in range(X0, X1):
        edge = min(x - X0, X1 - 1 - x, y - Y0, Y1 - 1 - y)
        a = min(1.0, edge / FEATHER)
        o = px[x, y]
        px[x, y] = tuple(int(o[i] * (1 - a) + MAIN[i] * a) for i in range(3)) + (255,)

d = ImageDraw.Draw(im, 'RGBA')
big = ImageFont.truetype(os.path.join(FONTDIR, 'vcr.ttf'), 42)
small = ImageFont.truetype(os.path.join(FONTDIR, 'arial.ttf'), 26)
d.text((905, 243), SIGN, font=big, fill=(75, 74, 67, 255))     # 木箱上的字
d.text((22, 20), SIGN, font=small, fill=(60, 55, 70, 150))      # 左上水印
im.save(DST)
print('saved', DST, im.size)
