# -*- coding: utf-8 -*-
"""手/脸分离可行性试验：对指定帧做肤色掩膜 + 连通域分析，打印各块面积。
   纯 PIL（C 速度做颜色运算）+ 纯 Python 只做稀疏像素的连通域标记。"""
from PIL import Image, ImageFilter
import os, sys, collections

BASE = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/images/characters'


def skin_mask(rgba, rng):
    """rng = (hmin,hmax,smin,smax,vmin,vmax) in 0..255 HSV 空间"""
    hsv = rgba.convert('HSV')
    h, s, v = hsv.split()
    hmin, hmax, smin, smax, vmin, vmax = rng
    # 逐通道做阈值：255 表示通过
    def band(ch, lo, hi):
        return ch.point(lambda p, lo=lo, hi=hi: 255 if (lo <= p <= hi) else 0)
    mh = band(h, hmin, hmax)
    ms = band(s, smin, smax)
    mv = band(v, vmin, vmax)
    return Image.fromarray(__import__('numpy').bitwise_and(1, 1)) if False else _and3(mh, ms, mv)


def _and3(a, b, c):
    from PIL import ImageChops
    return ImageChops.multiply(ImageChops.multiply(a, b), c)


def components(mask):
    """返回 [(area, (x0,y0,x1,y1)), ...]，4 连通，>0 面积"""
    w, h = mask.size
    data = mask.tobytes()
    seen = bytearray(w * h)
    out = []
    for start in range(w * h):
        if seen[start] or data[start] == 0:
            continue
        stack = [start]
        seen[start] = 1
        area = 0
        x0 = y0 = 10 ** 9
        x1 = y1 = -1
        while stack:
            p = stack.pop()
            area += 1
            y, x = divmod(p, w)
            if x < x0: x0 = x
            if x > x1: x1 = x
            if y < y0: y0 = y
            if y > y1: y1 = y
            for q in (p - 1, p + 1, p - w, p + w):
                if 0 <= q < w * h and not seen[q] and data[q]:
                    # 防止左右换行
                    if abs((q % w) - x) > 1 and q != p:
                        continue
                    seen[q] = 1
                    stack.append(q)
        out.append((area, (x0, y0, x1 + 1, y1 + 1)))
    out.sort(reverse=True)
    return out


def frame_of(png, xml, name):
    import xml.etree.ElementTree as ET
    root = ET.parse(os.path.join(BASE, xml)).getroot()
    for t in root.iter('SubTexture'):
        if t.get('name') == name:
            x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
            return (x, y, w, h)
    raise KeyError(name)


if __name__ == '__main__':
    tests = [
        ('miku', 'miku_assets.png', 'miku_assets.xml', 'idle_miku0000', (10, 32, 20, 95, 170, 255)),
        ('teto', 'teto-2026.png', 'teto-2026.xml', 'idle0000', (8, 34, 20, 110, 170, 255)),
        ('bf', 'cuphead/BoyFriend_ICCuphead.png', 'cuphead/BoyFriend_ICCuphead.xml', 'BF idle dance', (8, 34, 20, 110, 170, 255)),
        ('momo', 'momo_assets.png', 'momo_assets.xml', 'Momo Up0000', (8, 34, 15, 90, 180, 255)),
    ]
    for tag, png, xml, fname, rng in tests:
        im = Image.open(os.path.join(BASE, png)).convert('RGBA')
        x, y, w, h = frame_of(png, xml, fname)
        fr = im.crop((x, y, x + w, y + h))
        m = skin_mask(fr, rng)
        # 只在不透明像素上算
        a = fr.getchannel('A').point(lambda p: 255 if p > 0 else 0)
        m = _and3(m, a, a)
        comps = components(m)
        print('%-6s %-22s 帧 %dx%d  肤色块: %s' % (tag, fname, w, h,
              [(c[0], c[1]) for c in comps[:8]]))
        er = m.filter(ImageFilter.MinFilter(3))
        comps2 = components(er)
        print('        腐蚀后: %s' % ([(c[0], c[1]) for c in comps2[:8]],))
