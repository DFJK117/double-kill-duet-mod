# -*- coding: utf-8 -*-
"""生成 DK_Duet 的两个自定义 note 皮肤 + GOD 模式徽章。

* dk_trap：红色边框 + 黑色内部 + 上方红色环  ——  按到即死
* dk_warn：黄色警告三角 + 黑色感叹号        ——  漏按即死

note 皮肤必须是 Sparrow 图集（引擎 addSkinCache 用 Paths.getSparrowAtlas），
帧名必须为 purple0/blue0/green0/red0（引擎按前缀 'purple0' 等取帧），
这里直接沿用原版命名 purple0000/blue0000/green0000/red0000。
"""
from PIL import Image, ImageDraw, ImageFont
import os

OUT = r'E:/UST_work/dk_miku/_godmode/assets'
FW, FH = 157, 154          # 与 NOTE_assets 箭头帧同尺寸
SS = 4                     # 超采样倍数

RED = (226, 30, 42, 255)
DARK = (12, 12, 16, 255)
YEL = (255, 214, 0, 255)
BLK = (16, 16, 16, 255)


def ring(d, cx, cy, r, w, color):
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=w)


def draw_trap():
    im = Image.new('RGBA', (FW * SS, FH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    # 上方红环
    ring(d, FW * SS // 2, 42 * SS, 26 * SS, 8 * SS, RED)
    # 红色边框 + 黑色内部的方块
    d.rounded_rectangle([28 * SS, 68 * SS, (FW - 28) * SS, (FH - 6) * SS],
                        radius=10 * SS, fill=DARK, outline=RED, width=7 * SS)
    # 内部一道细红框，层次更清楚
    d.rounded_rectangle([40 * SS, 80 * SS, (FW - 40) * SS, (FH - 18) * SS],
                        radius=6 * SS, outline=(120, 14, 20, 255), width=3 * SS)
    return im.resize((FW, FH), Image.LANCZOS)


def draw_warn():
    im = Image.new('RGBA', (FW * SS, FH * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    tri = [(FW * SS // 2, 6 * SS), ((FW - 8) * SS, (FH - 8) * SS), (8 * SS, (FH - 8) * SS)]
    d.polygon(tri, fill=YEL, outline=BLK)
    d.line(tri + [tri[0]], fill=BLK, width=7 * SS, joint='curve')
    # 感叹号
    d.rounded_rectangle([70 * SS, 52 * SS, 87 * SS, 104 * SS], radius=8 * SS, fill=BLK)
    d.ellipse([66 * SS, 114 * SS, 91 * SS, 139 * SS], fill=BLK)
    return im.resize((FW, FH), Image.LANCZOS)


def atlas(frames):
    """把若干帧排成一行，写 PNG + Sparrow XML。
       frames = [(name, PIL.Image), ...]"""
    n = len(frames)
    W = sum(f[1].width for f in frames)
    H = max(f[1].height for f in frames)
    png = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    entries = []
    x = 0
    for name, img in frames:
        png.paste(img, (x, 0))
        entries.append((name, x, 0, img.width, img.height))
        x += img.width
    png_path = os.path.join(OUT, 'x.png')
    png.save(png_path)
    xml = ['<?xml version="1.0" encoding="utf-8"?>',
           '<TextureAtlas imagePath="%s" width="%d" height="%d">' % (os.path.basename(png_path), W, H)]
    for name, x, y, w, h in entries:
        xml.append('  <SubTexture name="%s" x="%d" y="%d" width="%d" height="%d" '
                   'frameX="0" frameY="0" frameWidth="%d" frameHeight="%d"/>' % (name, x, y, w, h, w, h))
    xml.append('</TextureAtlas>')
    return png, '\n'.join(xml)


def build_skin(base, drawer):
    img = drawer()
    frames = [(c + '0000', img) for c in ('purple', 'blue', 'green', 'red')]
    # 长音件（保险用，谱面里这两种 type 不会带长音）
    piece = Image.new('RGBA', (50, 44), (0, 0, 0, 0))
    dp = ImageDraw.Draw(piece)
    dp.rectangle([6, 6, 43, 37], fill=RED if base == 'dk_trap' else YEL, outline=DARK, width=3)
    end = Image.new('RGBA', (50, 64), (0, 0, 0, 0))
    de = ImageDraw.Draw(end)
    de.rectangle([8, 10, 41, 53], fill=RED if base == 'dk_trap' else YEL, outline=DARK, width=3)
    frames += [('purple hold piece0000', piece), ('blue hold piece0000', piece),
               ('green hold piece0000', piece), ('red hold piece0000', piece),
               ('purple hold end0000', end), ('blue hold end0000', end),
               ('green hold end0000', end), ('red hold end0000', end),
               ('pruple end hold0000', end)]
    png, xml = atlas(frames)
    png.save(os.path.join(OUT, base + '.png'))
    with open(os.path.join(OUT, base + '.xml'), 'w', encoding='utf-8', newline='\n') as f:
        f.write(xml)
    print('  %s.png / %s.xml  (%d 帧, %dx%d)' % (base, base, len(frames), png.width, png.height))


def build_badge():
    W, H = 360, 96
    im = Image.new('RGBA', (W * 2, H * 2), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([4, 4, W * 2 - 4, H * 2 - 4], radius=28, fill=(14, 14, 18, 235),
                        outline=(255, 205, 45, 255), width=7)
    try:
        f = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 72)
    except Exception:
        f = ImageFont.load_default()
    txt = 'GOD MODE'
    bb = d.textbbox((0, 0), txt, font=f)
    d.text(((W * 2 - (bb[2] - bb[0])) / 2, (H * 2 - (bb[3] - bb[1])) / 2 - bb[1]),
           txt, fill=(255, 214, 60, 255), font=f)
    im = im.resize((W, H), Image.LANCZOS)
    im.save(os.path.join(OUT, 'dk_god_badge.png'))
    print('  dk_god_badge.png (%dx%d)' % (W, H))


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    print('生成 note 皮肤：')
    build_skin('dk_trap', draw_trap)
    build_skin('dk_warn', draw_warn)
    print('生成徽章：')
    build_badge()
    if os.path.exists(os.path.join(OUT, 'x.png')):
        os.remove(os.path.join(OUT, 'x.png'))
