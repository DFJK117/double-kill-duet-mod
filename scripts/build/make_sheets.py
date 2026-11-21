# -*- coding: utf-8 -*-
"""生成角色联络表：每个角色若干代表帧，拼成一张图方便看清手/话筒位置。"""
from PIL import Image
import xml.etree.ElementTree as ET
import re, collections, os, sys

BASE = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'
OUT = r'E:/UST_work/dk_miku/_godmode'


def groups(xml):
    root = ET.parse(xml).getroot()
    g = collections.OrderedDict()
    for t in root.iter('SubTexture'):
        n = t.get('name')
        m = re.match(r'^(.*?) instance (\d+)$', n)
        key = m.group(1) if m else n
        g.setdefault(key, []).append(t)
    return g


def crop_frame(im, t):
    x = int(t.get('x') or 0)
    y = int(t.get('y') or 0)
    w = int(t.get('width') or 0)
    h = int(t.get('height') or 0)
    if w <= 0 or h <= 0:
        return None
    x1 = min(x + w, im.width)
    y1 = min(y + h, im.height)
    return im.crop((x, y, x1, y1))


def sheet(png, xml, pick, outfile, scale=0.5, cols=3):
    im = Image.open(os.path.join(BASE, png)).convert('RGBA')
    G = groups(os.path.join(BASE, xml))
    tiles = []
    for key in pick:
        ts = G.get(key)
        if not ts:
            print('  缺组', key)
            continue
        c = crop_frame(im, ts[0])
        if c is None:
            print('  空帧', key)
            continue
        nw = max(1, int(c.width * scale))
        nh = max(1, int(c.height * scale))
        tiles.append((key, c.resize((nw, nh), Image.LANCZOS)))
    if not tiles:
        return
    cw = max(t[1].width for t in tiles) + 20
    ch = max(t[1].height for t in tiles) + 30
    rows = (len(tiles) + cols - 1) // cols
    S = Image.new('RGBA', (cw * cols, ch * rows), (235, 235, 240, 255))
    for i, (k, c) in enumerate(tiles):
        S.alpha_composite(c, ((i % cols) * cw + 10, (i // cols) * ch + 20))
    S.convert('RGB').save(outfile)
    print(outfile, S.size, [t[0] for t in tiles])


if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    sheet('miku_assets.png', 'miku_assets.xml',
          ['idle_miku0000', 'down_miku0000', 'up_miku0000',
           'left_miku0000', 'right_miku0000', 'come_on_baby_pose_miku0000'],
          OUT + '/sheet_miku.png', 0.5, 3)
    sheet('momo_assets.png', 'momo_assets.xml',
          ['Momo Idle0000', 'Momo Up0000', 'Momo Down0000',
           'Momo Left0000', 'Momo Right0000'],
          OUT + '/sheet_momo.png', 0.6, 3)
    sheet('teto-2026.png', 'teto-2026.xml',
          ['idle0000', 'up0000', 'down0000', 'left0000', 'right0000'],
          OUT + '/sheet_teto.png', 0.5, 3)
    sheet('cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml',
          ['BF idle dance', 'BF NOTE UP', 'BF NOTE DOWN', 'BF NOTE LEFT',
           'BF NOTE RIGHT', '0BF attack'],
          OUT + '/sheet_bfic.png', 0.5, 3)
