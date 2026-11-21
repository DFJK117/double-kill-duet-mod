# -*- coding: utf-8 -*-
"""v2：对肤色块逐块统计主色 + 输出带编号的预览图，用来判断「脸」与「手」能否按颜色/位置区分。"""
from PIL import Image, ImageDraw, ImageFont
import os, sys, collections, xml.etree.ElementTree as ET

BASE = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'
OUT = r'E:/UST_work/dk_miku/_godmode'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from probe_skin import skin_mask, components, _and3


def frame_of(png, xml, prefix):
    root = ET.parse(os.path.join(BASE, xml)).getroot()
    for t in root.iter('SubTexture'):
        n = t.get('name')
        if n == prefix or n.startswith(prefix + ' instance') or n.startswith(prefix + '0'):
            x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
            return (x, y, w, h)
    raise KeyError(prefix)


def analyze(tag, png, xml, fname, rng):
    im = Image.open(os.path.join(BASE, png)).convert('RGBA')
    x, y, w, h = frame_of(png, xml, fname)
    fr = im.crop((x, y, x + w, y + h))
    a = fr.getchannel('A').point(lambda p: 255 if p > 0 else 0)
    m = _and3(skin_mask(fr, rng), a, a)
    comps = components(m)
    px = fr.load()
    print('== %s  %s  %dx%d  肤色块 %d 个' % (tag, fname, w, h, len(comps)))
    prev = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    prev.alpha_composite(fr)
    d = ImageDraw.Draw(prev)
    try:
        fnt = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 20)
    except Exception:
        fnt = ImageFont.load_default()
    for i, (area, (x0, y0, x1, y1)) in enumerate(comps[:6]):
        cnt = collections.Counter()
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                if xx < w and yy < h:
                    r, g, b, aa = px[xx, yy]
                    if aa > 0:
                        cnt[(r, g, b)] += 1
        top = cnt.most_common(3)
        print('   #%d area=%-6d bbox=%-22s 主色=%s' % (i, area, (x0, y0, x1, y1), top))
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=(0, 255, 0, 255), width=3)
        d.text((x0 + 2, y0 + 2), str(i), fill=(255, 255, 0, 255), font=fnt)
    prev.convert('RGB').save(os.path.join(OUT, 'probe_%s.png' % tag))
    print('   -> probe_%s.png' % tag)


if __name__ == '__main__':
    analyze('miku', 'miku_assets.png', 'miku_assets.xml', 'idle_miku0000', (10, 32, 20, 95, 170, 255))
    analyze('teto', 'teto-2026.png', 'teto-2026.xml', 'idle0000', (8, 34, 20, 110, 170, 255))
    analyze('momo', 'momo_assets.png', 'momo_assets.xml', 'Momo Up0000', (8, 34, 15, 90, 180, 255))
    analyze('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml',
            'BF idle dance', (8, 34, 20, 110, 170, 255))
