# -*- coding: utf-8 -*-
"""
v10.4：把 Teto God 图集里被误染黑的法棍恢复成原版橙色。
只替换法棍的 3 个矩形区域（含划痕和抗锯齿边缘，外扩 3px）；
其余部分保持 God 黑黄主题不变。

输入源 = 原版备份（_backup_god_v8_20261115），绝不读已染色的游戏目录做二次处理。
三块 bbox 由原版图集橙色像素分布程序化求出（R>200, 90<G<200, B<90, R>G+40, G>B+30）。
"""
import os
from PIL import Image

BAK = 'E:/UST_work/dk_miku/_backup_god_v8_20261115/images/characters/teto-2026.png'
ROOTS = [
    'E:/UST_work/dk_miku/DK_Dual/images/characters/teto-2026_god.png',
    'E:/UST_work/dk_miku/DK_Miku/images/characters/teto-2026_god.png',
    'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters/teto-2026_god.png',
]
# 法棍在原版图集中的三个搜索窗口 (x0,y0,x1,y1)，从 hey 帧布局得出
SEARCH = [(1100, 1720, 280, 700), (1720, 2220, 280, 700), (1100, 1720, 1150, 1520)]
PAD = 3

orig = Image.open(BAK).convert('RGBA')
op = orig.load()
boxes = []
for gx0, gx1, gy0, gy1 in SEARCH:
    xs, ys = [], []
    for y in range(gy0, min(gy1, orig.height)):
        for x in range(gx0, min(gx1, orig.width)):
            r, g, b, a = op[x, y]
            if a > 0 and r > 200 and 90 < g < 200 and b < 90 and r > g + 40 and g > b + 30:
                xs.append(x); ys.append(y)
    assert xs, 'no baguette orange found in window'
    boxes.append((min(xs), min(ys), max(xs) + 1, max(ys) + 1))
print('baguette boxes:', boxes)

for dst in ROOTS:
    god = Image.open(dst).convert('RGBA')
    for x0, y0, x1, y1 in boxes:
        bx0, by0 = max(0, x0 - PAD), max(0, y0 - PAD)
        bx1, by1 = min(god.width, x1 + PAD), min(god.height, y1 + PAD)
        god.paste(orig.crop((bx0, by0, bx1, by1)), (bx0, by0))
    god.save(dst)
    print('wrote', dst)
