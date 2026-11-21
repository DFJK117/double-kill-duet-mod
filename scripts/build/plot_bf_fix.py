#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 bf-ic 站位/摄像机修正前后对比图 (舞台坐标系俯视图)"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from calc_bf_ic_layout import Character, STAGE, idle_world  # noqa: E402

OUT = r'E:/UST_work/dk_miku/bf_ic_position_fix.png'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
BASE = r'E:/UST_work/dk_miku/_backup_lua_v6_20261115/characters/bf.json'

W, H = 1500, 900
X0, X1 = 1600.0, 3400.0
Y0, Y1 = 520.0, 1600.0
SCALE = W / (X1 - X0)

BG = (18, 20, 27)
GRID = (38, 42, 54)
TXT = (214, 219, 230)
DIM = (130, 138, 155)
CAM = (255, 196, 61)
OLD = (255, 88, 88)
NEW = (86, 214, 133)
REF = (96, 165, 250)
OPP = (168, 130, 220)

img = Image.new("RGB", (W, H), BG)
d = ImageDraw.Draw(img)


def font(sz, bold=False):
    for p in (r'C:/Windows/Fonts/msyhbd.ttc' if bold else r'C:/Windows/Fonts/msyh.ttc',
              r'C:/Windows/Fonts/arialbd.ttf' if bold else r'C:/Windows/Fonts/arial.ttf'):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, sz)
            except Exception:
                pass
    return ImageFont.load_default()


F_T = font(19, True)
F_S = font(15)
F_M = font(13)


def px(x):
    return (x - X0) * SCALE


def py(y):
    return (y - Y0) * SCALE


# 网格
for gx in range(int(X0 // 100 * 100), int(X1) + 100, 100):
    d.line([(px(gx), 0), (px(gx), H)], fill=GRID, width=1)
    d.text((px(gx) + 3, H - 22), str(gx), font=F_M, fill=DIM)
for gy in range(int(Y0 // 100 * 100), int(Y1) + 100, 100):
    d.line([(0, py(gy)), (W, py(gy))], fill=GRID, width=1)
    d.text((4, py(gy) + 2), str(gy), font=F_M, fill=DIM)

# 镜头视野
cam = (2517.0, 1029.5)
half_w, half_h = 1280 / STAGE['defaultZoom'] / 2.0, 720 / STAGE['defaultZoom'] / 2.0
v = (cam[0] - half_w, cam[0] + half_w, cam[1] - half_h, cam[1] + half_h)
d.rectangle([px(v[0]), py(v[2]), px(v[1]), py(v[3])], outline=CAM, width=2)
d.text((px(v[0]) + 8, py(v[2]) + 6),
       '镜头视野 x[%g,%g] y[%g,%g]  (zoom %g, camFollow %g,%g)' % (v[0], v[1], v[2], v[3], STAGE['defaultZoom'], cam[0], cam[1]),
       font=F_S, fill=CAM)

# 对手在镜头视野之外（玩家段镜头只框右侧 BF），用方向提示
d.text((18, H - 46), '← 对手方向：对手 x=1250，位于镜头视野 x[1806,3228] 之外（玩家段镜头本就不框对手）', font=F_S, fill=OPP)


def box(ch, x, y, color, label, sub, ldy=-24, sdy=6):
    wb = idle_world(ch, x, y)
    d.rectangle([px(wb[0]), py(wb[1]), px(wb[2]), py(wb[3])], outline=color, width=3)
    d.text((px(wb[0]), py(wb[1]) + ldy), label, font=F_T, fill=color)
    d.text((px(wb[0]), py(wb[3]) + sdy), sub, font=F_M, fill=color)


dk = Character('dk', BASE)
ic = Character('ic', GAME + '/characters/bf.json')

box(dk, *dk.sprite_xy(), REF,
    'DK 原版 BF（BOYFRIEND, scale1）',
    'idle 图形 x[%g,%g] y[%g,%g]  脚底 %g' % (idle_world(dk, *dk.sprite_xy())[0], idle_world(dk, *dk.sprite_xy())[2],
                                             idle_world(dk, *dk.sprite_xy())[1], idle_world(dk, *dk.sprite_xy())[3],
                                             idle_world(dk, *dk.sprite_xy())[3]), ldy=-50, sdy=-30)

# 修正前：用备份里的 v6 值 [-12,342] / cam[0,0]
old = Character('ic', r'E:/UST_work/dk_miku/_backup_lua_v7_20261115/characters/bf.json')
box(old, *old.sprite_xy(), OLD,
    'v6 现状（照抄 DK 的 position/camera）',
    'idle 图形 x[%g,%g] y[%g,%g]  脚底 %g' % (idle_world(old, *old.sprite_xy())[0], idle_world(old, *old.sprite_xy())[2],
                                             idle_world(old, *old.sprite_xy())[1], idle_world(old, *old.sprite_xy())[3],
                                             idle_world(old, *old.sprite_xy())[3]), ldy=-26, sdy=6)

box(ic, *ic.sprite_xy(), NEW,
    'v7 修正后（position %s / camera %s）' % (ic.position, ic.camera_position),
    'idle 图形 x[%g,%g] y[%g,%g]  脚底 %g' % (idle_world(ic, *ic.sprite_xy())[0], idle_world(ic, *ic.sprite_xy())[2],
                                             idle_world(ic, *ic.sprite_xy())[1], idle_world(ic, *ic.sprite_xy())[3],
                                             idle_world(ic, *ic.sprite_xy())[3]), ldy=30, sdy=34)

d.text((18, 14), 'DK_Duet / cargo 舞台 · BF 落点与镜头对比（世界坐标俯视）', font=F_T, fill=TXT)
d.text((18, 40), '蓝=DK 原版（基准）  红=v6 出错状态  绿=v7 修正后  —— 绿框与蓝框完全重合，镜头锚点也回到原位', font=F_S, fill=DIM)

img.save(OUT)
print('[img] %s  %dx%d' % (OUT, W, H))
