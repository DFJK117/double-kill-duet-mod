# -*- coding: utf-8 -*-
"""所有 health bar 图标（单人 + 双人重叠）的黑黄化。

要处理的 8 个（都在 mods/DK_Duet/images/icons/）：
  icon-bf          单人 BF
  icon-momo        单人 桃音
  icon-teto-cozy   单人 Teto
  icon-miku        单人 初音
  icon-momo-teto   双人 桃音+Teto
  icon-miku-teto   双人 初音+Teto
  icon-double-kill 双人 桃音+Teto（另一版）
  icon-surprise    真人表情包（惊喜脸）

规则与角色大图一致：
  * 主题色（头发/帽子/衣服）-> 黑（保留明暗层次，别糊成一团）
  * 脸 -> 黑
  * 话筒 -> 保持原色
  * 手 -> 黄（双人图里桃音握话筒的手）

icon-surprise 是真人照片，没法按色相分类 —— 用「整体去饱和 + 压暗成黑黄双色调」处理，
既符合黑黄主题，又保住表情包的脸能认出来。
"""
from PIL import Image, ImageEnhance
import os, collections

SRC = r'E:/UST_work/dk_miku/_backup_god_v8_20261115/images/icons'
OUT = r'E:/UST_work/dk_miku/_godmode'

YELLOW = (255, 205, 45)


def _near(px, ref, tol=46):
    return (abs(px[0] - ref[0]) <= tol and abs(px[1] - ref[1]) <= tol
            and abs(px[2] - ref[2]) <= tol)


def _black_ramp(r, g, b, floor=14, ceil=58, gain=0.30):
    lum = r * 0.3 + g * 0.59 + b * 0.11
    v = min(ceil, max(floor, int(lum * gain)))
    return (v, v, min(255, v + 4))


def recolor_single(name, theme, mic):
    """单个角色头像：主题色->黑，浅肤色->脸/手，话筒保留。"""
    p = os.path.join(SRC, name + '.png')
    im = Image.open(p).convert('RGBA')
    W, H = im.size
    px = im.load()

    mic_set, theme_set, skin_set = [], [], []
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            c = (r, g, b)
            if mic and any(_near(c, m) for m in mic):
                mic_set.append((x, y))
            elif any(_near(c, t) for t in theme):
                theme_set.append((x, y))
            elif r > 168 and g > 138 and b > 132 and (max(r, g, b) - min(r, g, b)) < 96:
                skin_set.append((x, y))

    # 肤色块分脸/手
    face, hand = set(), set()
    if skin_set:
        sset = set(skin_set)
        visited, blobs = set(), []
        for p0 in skin_set:
            if p0 in visited:
                continue
            stack, blob = [p0], []
            visited.add(p0)
            while stack:
                q = stack.pop()
                blob.append(q)
                qx, qy = q
                for nb in ((qx + 1, qy), (qx - 1, qy), (qx, qy + 1), (qx, qy - 1)):
                    if nb in sset and nb not in visited:
                        visited.add(nb)
                        stack.append(nb)
            blobs.append(blob)
        blobs.sort(key=lambda b: -len(b))
        for i, b in enumerate(blobs):
            avg_y = sum(q[1] for q in b) / float(len(b))
            if i == 0 and len(b) >= 60:
                face.update(b)
            elif avg_y < H * 0.55 and len(b) >= 40:
                hand.update(b)
            else:
                face.update(b)

    for (x, y) in theme_set:
        r, g, b, a = px[x, y]
        px[x, y] = _black_ramp(r, g, b) + (a,)
    for (x, y) in face:
        r, g, b, a = px[x, y]
        px[x, y] = _black_ramp(r, g, b, floor=12, ceil=64, gain=0.34) + (a,)
    for (x, y) in hand:
        r, g, b, a = px[x, y]
        px[x, y] = (YELLOW[0], YELLOW[1], YELLOW[2], a)
    outp = os.path.join(OUT, 'recolored_%s.png' % name)
    im.save(outp)
    return outp, len(theme_set), len(face), len(hand)


def recolor_photo(name):
    """真人表情包：整体去饱和 + 黑黄双色调（暗部压黑，亮部提黄）。

    为了让黑色占主导（和角色一致），提黄阈值抬高：只有很亮的部分才转黄，
    中间调一律压成深灰黑。
    """
    p = os.path.join(SRC, name + '.png')
    im = Image.open(p).convert('RGBA')
    px = im.load()
    W, H = im.size
    for y in range(H):
        for x in range(W):
            r, g, b, a = px[x, y]
            if a < 128:
                continue
            lum = r * 0.3 + g * 0.59 + b * 0.11
            # 阈值抬高：lum < 150 基本都进黑区，只有高光才转黄
            t = min(1.0, max(0.0, (lum - 150) / 105.0))
            nr = int(14 + (YELLOW[0] - 14) * t)
            ng = int(12 + (YELLOW[1] - 12) * t)
            nb = int(16 + (YELLOW[2] - 16) * t)
            px[x, y] = (nr, ng, nb, a)
    outp = os.path.join(OUT, 'recolored_%s.png' % name)
    im.save(outp)
    return outp


def recolor_duo(name, theme_sets, mic_sets):
    """双人重叠图：按左右分区分别处理主题色与话筒。"""
    p = os.path.join(SRC, name + '.png')
    im = Image.open(p).convert('RGBA')
    W, H = im.size
    px = im.load()

    for (x, y) in [(x, y) for y in range(H) for x in range(W)]:
        r, g, b, a = px[x, y]
        if a < 128:
            continue
        c = (r, g, b)
        # 话筒（任何一侧的 mic 色都保留）
        if any(_near(c, m) for ms in mic_sets for m in ms):
            continue
        # 主题色（任何一侧的 theme 色都变黑）
        if any(_near(c, t) for ts in theme_sets for t in ts):
            px[x, y] = _black_ramp(r, g, b) + (a,)
            continue
        # 浅肤色 -> 脸（黑）
        if r > 168 and g > 138 and b > 132 and (max(r, g, b) - min(r, g, b)) < 96:
            px[x, y] = _black_ramp(r, g, b, floor=12, ceil=64, gain=0.34) + (a,)
    outp = os.path.join(OUT, 'recolored_%s.png' % name)
    im.save(outp)
    return outp


PINK = (224, 128, 128)
ROSE = (224, 64, 96)
CYAN = (64, 192, 224)
BLUE = (32, 160, 192)
WHITE = (224, 224, 224)

JOBS = [
    ('icon-bf', dict(theme=[(32, 160, 192), (32, 128, 160)], mic=[])),
    ('icon-momo', dict(theme=[PINK], mic=[WHITE])),
    ('icon-teto-cozy', dict(theme=[ROSE, (192, 64, 96)], mic=[])),
    ('icon-miku', dict(theme=[CYAN], mic=[])),
]
DUOS = [
    ('icon-momo-teto', dict(theme_sets=[[PINK], [ROSE, (192, 64, 96)]],
                            mic_sets=[[WHITE], []])),
    ('icon-miku-teto', dict(theme_sets=[[CYAN], [ROSE, (192, 64, 96)]],
                            mic_sets=[[], []])),
    ('icon-double-kill', dict(theme_sets=[[PINK], [ROSE, (192, 64, 96)]],
                              mic_sets=[[WHITE], []])),
]
PHOTO = ['icon-surprise']


def run():
    for name, cfg in JOBS:
        p, nt, nf, nh = recolor_single(name, cfg['theme'], cfg['mic'])
        print('  %-18s 主题 %5d / 脸 %5d / 手 %5d' % (name, nt, nf, nh))
    for name, cfg in DUOS:
        p = recolor_duo(name, cfg['theme_sets'], cfg['mic_sets'])
        print('  %-18s 双人重叠 -> %s' % (name, os.path.basename(p)))
    for name in PHOTO:
        p = recolor_photo(name)
        print('  %-18s 真人双色调 -> %s' % (name, os.path.basename(p)))


ALL_NAMES = [n for n, _ in JOBS] + [n for n, _ in DUOS] + PHOTO


def make_sheet(tag):
    ims = []
    for n in ALL_NAMES:
        p = os.path.join(OUT, 'recolored_%s.png' % n)
        ims.append(Image.open(p).convert('RGBA'))
    W = max(i.width for i in ims)
    H = sum(i.height for i in ims) + 8 * len(ims)
    sheet = Image.new('RGBA', (W, H), (40, 40, 50, 255))
    y = 0
    for i in ims:
        sheet.paste(i, (0, y), i)
        y += i.height + 8
    p = os.path.join(OUT, 'icons_all_%s.png' % tag)
    sheet.save(p)
    return p


if __name__ == '__main__':
    run()
    print('拼图 ->', make_sheet('after'))
