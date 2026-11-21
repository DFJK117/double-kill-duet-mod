# -*- coding: utf-8 -*-
"""把新光环 Trap 四向箭头帧拼成 dk_trap 图集 + XML，部署到三处。
光环戴在箭头头顶上方、扁横椭圆、带发光光晕（重做版，修"光环要在头上"）。"""
import os, shutil, hashlib
from PIL import Image
import sys
sys.path.insert(0, 'E:/UST_work/dk_miku/scripts')
from make_trap_arrow import build_trap_frames

GAME = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images'
ROOTS = [
    'E:/UST_work/dk_miku/DK_Dual/images',
    'E:/UST_work/dk_miku/DK_Miku/images',
    GAME,
]
OLD_ATLAS = os.path.join(GAME, 'dk_trap.png')
OLD_XML = os.path.join(GAME, 'dk_trap.xml')

frames = build_trap_frames()
# hold 帧从旧图集拷（这些不受光环改动影响）
old = Image.open(OLD_ATLAS).convert('RGBA')
# 旧 XML 里 hold 帧的坐标
import re, xml.etree.ElementTree as ET
root = ET.parse(OLD_XML).getroot()
hold = []
for s in root.findall('SubTexture'):
    n = s.get('name', '')
    if 'hold' in n.lower() or 'end' in n.lower():
        x, y, w, h = (int(s.get(k)) for k in ('x', 'y', 'width', 'height'))
        hold.append((n, old.crop((x, y, x + w, y + h))))

# 布局：四个箭头横排 + hold 帧横排
arrow_w = sum(f.width for _, f in frames) + 20 * (len(frames) + 1)
arrow_h = max(f.height for _, f in frames) + 40
hold_w = sum(im.width for _, im in hold) + 10 * (len(hold) + 1)
hold_h = max(im.height for _, im in hold) + 20
W = max(arrow_w, hold_w)
H = arrow_h + hold_h
sheet = Image.new('RGBA', (W, H), (0, 0, 0, 0))
subs = []
x = 20
for name, f in frames:
    sheet.paste(f, (x, 20), f)
    subs.append(('%s0000' % name, x, 20, f.width, f.height))
    x += f.width + 20
x = 10
yh = arrow_h
for n, im in hold:
    sheet.paste(im, (x, yh + 10), im)
    subs.append((n, x, yh + 10, im.width, im.height))
    x += im.width + 10

xml = ['<?xml version="1.0" encoding="utf-8"?>',
       '<TextureAtlas imagePath="dk_trap.png" width="%d" height="%d">' % (W, H)]
for n, x, y, w, h in subs:
    xml.append('  <SubTexture name="%s" x="%d" y="%d" width="%d" height="%d" '
               'frameX="0" frameY="0" frameWidth="%d" frameHeight="%d"/>' % (n, x, y, w, h, w, h))
xml.append('</TextureAtlas>')

md5 = lambda p: hashlib.md5(open(p, 'rb').read()).hexdigest()
for rd in ROOTS:
    ap = os.path.join(rd, 'dk_trap.png')
    xp = os.path.join(rd, 'dk_trap.xml')
    sheet.save(ap)
    open(xp, 'w', encoding='utf-8').write('\n'.join(xml))
    print('wrote', md5(ap), ap, sheet.size)
print('preview-subs:', [(s[0], s[3], s[4]) for s in subs[:4]])
