# -*- coding: utf-8 -*-
"""按动画家族生成蒙太奇：每个家族取肤色最多的代表帧，标出肤色连通块编号。
   输出 4 张图（每角色 1 张），用于人工指定「脸=几号 / 手=几号」。"""
from PIL import Image, ImageDraw, ImageFont
import os, sys, collections, xml.etree.ElementTree as ET

BASE = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'
OUT = r'E:/UST_work/dk_miku/_godmode'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe_skin import skin_mask, components, _and3

# 每角色的肤色 HSV 范围（已按「头发高光/围裙」逐个排除过）
HSV = {
    'miku': (10, 32, 20, 70, 170, 255),
    'teto': (5, 25, 30, 80, 170, 255),
    'momo': (5, 30, 15, 90, 180, 255),
    'bf':   (12, 38, 30, 90, 170, 255),
}

SETS = [
    ('miku', 'miku_assets.png', 'miku_assets.xml'),
    ('momo', 'momo_assets.png', 'momo_assets.xml'),
    ('teto', 'teto-2026.png', 'teto-2026.xml'),
    ('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml'),
]


def families(xml):
    root = ET.parse(os.path.join(BASE, xml)).getroot()
    fams = collections.OrderedDict()
    for t in root.iter('SubTexture'):
        n = t.get('name')
        key = n.rstrip('0123456789').rstrip('_ ') if n[-1].isdigit() else n
        fams.setdefault(key, []).append(t)
    return fams


def frame_info(t):
    x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
    fw = int(t.get('frameWidth') or w)
    fh = int(t.get('frameHeight') or h)
    return x, y, w, h, fw, fh


def build(tag, png, xml):
    im = Image.open(os.path.join(BASE, png)).convert('RGBA')
    rng = HSV[tag]
    fams = families(xml)
    cells = []
    for fam, ts in fams.items():
        best = None
        for t in ts:
            x, y, w, h, fw, fh = frame_info(t)
            fr = im.crop((x, y, x + w, y + h))
            a = fr.getchannel('A').point(lambda p: 255 if p > 0 else 0)
            m = _and3(skin_mask(fr, rng), a, a)
            area = sum(m.getdata()) // 255
            if best is None or area > best[0]:
                best = (area, t, fr)
        if best is None:
            continue
        area, t, fr = best
        a = fr.getchannel('A').point(lambda p: 255 if p > 0 else 0)
        m = _and3(skin_mask(fr, rng), a, a)
        comps = [c for c in components(m) if c[0] >= 25]
        cells.append((fam, fr, comps))
    # 拼图
    CELL_H = 300
    COLS = 4
    rows = (len(cells) + COLS - 1) // COLS
    W = COLS * 300
    H = rows * (CELL_H + 34)
    S = Image.new('RGB', (W, H), (245, 245, 248))
    d = ImageDraw.Draw(S)
    try:
        f1 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 19)
        f2 = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 15)
    except Exception:
        f1 = f2 = ImageFont.load_default()
    for i, (fam, fr, comps) in enumerate(cells):
        cx, cy = (i % COLS) * 300, (i // COLS) * (CELL_H + 34)
        sc = min(1.0, (CELL_H - 10) / max(1, fr.height), 280 / max(1, fr.width))
        nw, nh = max(1, int(fr.width * sc)), max(1, int(fr.height * sc))
        fr2 = fr.resize((nw, nh), Image.LANCZOS)
        bg = Image.new('RGB', (nw, nh), (255, 255, 255))
        bg.paste(fr2, (0, 0), fr2)
        d.rectangle([cx, cy, cx + nw - 1, cy + nh - 1], outline=(180, 180, 190))
        S.paste(bg, (cx, cy))
        for j, (ar, (x0, y0, x1, y1)) in enumerate(comps):
            d.rectangle([cx + x0 * sc, cy + y0 * sc, cx + x1 * sc - 1, cy + y1 * sc - 1],
                        outline=(0, 200, 0), width=2)
            d.text((cx + x0 * sc + 2, cy + y0 * sc + 1), str(j), fill=(220, 0, 0), font=f2)
        d.text((cx + 2, cy + CELL_H - 4), fam[:26], fill=(20, 20, 20), font=f1)
        d.text((cx + 2, cy + CELL_H + 14), 'blobs=%d  %s' % (len(comps), [c[0] for c in comps]),
               fill=(90, 90, 90), font=f2)
    p = os.path.join(OUT, 'families_%s.png' % tag)
    S.save(p)
    print('%s: %d 个家族 -> %s' % (tag, len(cells), p))


if __name__ == '__main__':
    for tag, png, xml in SETS:
        build(tag, png, xml)
