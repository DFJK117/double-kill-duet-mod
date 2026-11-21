# -*- coding: utf-8 -*-
"""DK_Duet 角色重着色（v8 GOD 模式配色）：主题色 -> 黑，手 -> 黄，话筒保持原色。

输入永远是**原画**（_backup_god_v8_20261115/images/characters），
输出到 _godmode/recolored_*.png，避免在旧重着色结果上二次处理。

分类流程
--------
1. skin 色带 -> 肤色原掩膜（脸、手同色）
2. 膨胀 2px 合并描边缝隙 -> 连通块
3. 丢弃「细长条」块（头发高光的抗锯齿残片）
4. 脸 = 眼窝孔洞最多的块；脸框内的碎块（眼白/瞳孔高光）归脸
5. 手 = 其余肤色块（>= MIN_HAND 面积）
6. 话筒 = mic 色带里「与手相邻」的块，保持原色
7. 着色：手 -> 黄色斜坡，话筒 -> 原色，其余（含脸） -> 黑色斜坡
"""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
import os, sys, math, collections, xml.etree.ElementTree as ET

# 原画来源：绝不能用游戏目录（那里已被重着色覆盖，会二次处理）
SRC = r'E:/UST_work/dk_miku/_backup_god_v8_20261115/images/characters'
OUT = r'E:/UST_work/dk_miku/_godmode'
BASE = SRC

YELLOW = (255, 205, 45)
MIN_HAND = 40          # 手的最小面积（帧内像素）
SLENDER = 3.0          # 块宽高比超过此值视为细长条（头发高光/描边残片）
HOLE_MIN = 8           # 判定为「脸」的最低眼窝孔洞数
NEAR_FACE = 0.85       # 脸附属块的中心距阈值（相对脸的尺寸）
TOP_BAND = 42          # 判定「位于轮廓顶端」时向上检查的像素高度


# ---------------- 角色配置 ----------------
# skin = (H0,H1, S0,S1, V0,V1)   —— PIL HSV，H 0-255 对应 0-360°
# mic  = ('hue',(H0,H1,S0,S1,V0,V1)) | ('gray',(S0,S1,V0,V1)) | ('none',None)
CFG = {
    'teto': dict(png='teto-2026.png', xml='teto-2026.xml',
                 skin=(0, 28, 35, 90, 180, 255),
                 mic=('hue', (195, 222, 120, 235, 60, 255)),
                 hand_mode='all'),
    'momo': dict(png='momo_assets.png', xml='momo_assets.xml',
                 skin=(0, 28, 12, 92, 180, 255),
                 mic=('gray', (0, 12, 190, 255)),
                 mic_zone=(0.0, 0.40),
                 hand_mode='all'),
    'miku': dict(png='miku_assets.png', xml='miku_assets.xml',
                 skin=(0, 28, 10, 92, 175, 255),
                 mic=('none', None),
                 hand_mode='all'),
    'bf': dict(png='cuphead/BoyFriend_ICCuphead.png', xml='cuphead/BoyFriend_ICCuphead.xml',
               skin=(0, 30, 30, 92, 175, 255),
               mic=('none', None),
               hand_mode='all'),
    'bfdefeat': dict(png='bf/defeatBf-normal.png', xml='bf/defeatBf-normal.xml',
                     skin=(0, 30, 20, 92, 110, 255),
                     mic=('none', None),
                     hand_mode='all'),
}


# ---------------- 通用工具 ----------------
def band(ch, lo, hi):
    return ch.point(lambda p: 255 if (lo <= p <= hi) else 0)


def hsv_mask(rgba, rng):
    h, s, v = rgba.convert('HSV').split()
    hmin, hmax, smin, smax, vmin, vmax = rng
    return ImageChops.multiply(ImageChops.multiply(band(h, hmin, hmax), band(s, smin, smax)),
                               band(v, vmin, vmax))


def components(mask, min_area=1):
    """4 连通标记，返回 [(area, [pixel indices...], bbox)]"""
    w, h = mask.size
    data = mask.tobytes()
    seen = bytearray(w * h)
    out = []
    pos = data.find(b'\xff')
    while pos != -1:
        if not seen[pos]:
            stack = [pos]
            seen[pos] = 1
            pix = []
            x0 = y0 = 10 ** 9
            x1 = y1 = -1
            while stack:
                p = stack.pop()
                pix.append(p)
                y, x = divmod(p, w)
                if x < x0: x0 = x
                if x > x1: x1 = x
                if y < y0: y0 = y
                if y > y1: y1 = y
                for q in (p - 1, p + 1, p - w, p + w):
                    if q < 0 or q >= w * h or seen[q] or not data[q]:
                        continue
                    if abs(q - p) == 1 and (q // w) != (p // w):   # 横向不能跨行
                        continue
                    seen[q] = 1
                    stack.append(q)
            if len(pix) >= min_area:
                out.append((len(pix), pix, (x0, y0, x1 + 1, y1 + 1)))
        pos = data.find(b'\xff', pos + 1)
    out.sort(key=lambda c: -c[0])
    return out


def blob_hole_count(blob_pix, w, x0, y0, x1, y1):
    """肤色块包围盒内、被它完全包住的「孔洞」像素数（眼窝/嘴）。
       脸有眼窝，手没有 —— 这是区分脸和手最稳的判据。"""
    bw, bh = x1 - x0, y1 - y0
    if bw <= 0 or bh <= 0:
        return 0
    wall = bytearray(bw * bh)
    for p in blob_pix:
        gx, gy = p % w, p // w
        if 0 <= gx < bw and 0 <= gy < bh:
            wall[(gy - y0) * bw + (gx - x0)] = 1
    seen = bytearray(bw * bh)
    stack = []
    for x in range(bw):
        for p in (x, (bh - 1) * bw + x):
            if not wall[p] and not seen[p]:
                seen[p] = 1
                stack.append(p)
    for y in range(bh):
        for p in (y * bw, y * bw + bw - 1):
            if not wall[p] and not seen[p]:
                seen[p] = 1
                stack.append(p)
    while stack:
        p = stack.pop()
        x, y = p % bw, p // bw
        for q, ok in ((p - 1, x > 0), (p + 1, x < bw - 1), (p - bw, y > 0), (p + bw, y < bh - 1)):
            if ok and not seen[q] and not wall[q]:
                seen[q] = 1
                stack.append(q)
    holes = 0
    for i in range(bw * bh):
        if not wall[i] and not seen[i]:
            holes += 1
    return holes


def mask_from_pixels(size, blobs):
    m = Image.new('L', size, 0)
    px = m.load()
    for _, pix, _ in blobs:
        for p in pix:
            px[p % size[0], p // size[0]] = 255
    return m


def dilate(mask, r=1):
    return mask.filter(ImageFilter.MaxFilter(2 * r + 1))


def families(xml):
    root = ET.parse(os.path.join(BASE, xml)).getroot()
    fams = collections.OrderedDict()
    for t in root.iter('SubTexture'):
        n = t.get('name')
        key = n.rstrip('0123456789').rstrip('_ ') if n and n[-1].isdigit() else n
        fams.setdefault(key, []).append(t)
    return fams


def slender(b):
    x0, y0, x1, y1 = b[2]
    w, h = max(1, x1 - x0), max(1, y1 - y0)
    return (w / float(h) > SLENDER) or (h / float(w) > SLENDER)


# ---------------- 单帧分类 ----------------
def classify(fr, cfg):
    """返回 (hand_mask, mic_mask)"""
    w, h = fr.size
    rgba = fr.convert('RGBA')
    a = rgba.getchannel('A').point(lambda p: 255 if p > 0 else 0)
    skin_raw = ImageChops.multiply(hsv_mask(rgba, cfg['skin']), a)

    kind, rng = cfg['mic']
    if kind == 'hue':
        mic = ImageChops.multiply(hsv_mask(rgba, rng), a)
    elif kind == 'gray':
        hh, ss, vv = rgba.convert('HSV').split()
        mic = ImageChops.multiply(ImageChops.multiply(band(ss, rng[0], rng[1]), band(vv, rng[2], rng[3])), a)
    else:
        mic = Image.new('L', (w, h), 0)

    # 肤色被黑色描边切碎 -> 膨胀合并碎片，判定完再与原掩膜求交
    skin_blobs = [b for b in components(dilate(skin_raw, 2), 30) if not slender(b)]
    skin_blobs = [b for b in skin_blobs if b[0] >= MIN_HAND]
    if not skin_blobs:
        return Image.new('L', (w, h), 0), mic

    # 角色在帧内的纵向范围（用于把「脸部在上、大腿在下」变成可比较的相对位置）
    am = a.getbbox()
    top_y = am[1] if am else 0
    bot_y = am[3] if am else h
    span = max(1, bot_y - top_y)
    body_cx = ((am[0] + am[2]) / 2.0) if am else w / 2.0
    body_w = max(1, (am[2] - am[0]) if am else w)

    def rel_y(b):
        return ((b[2][1] + b[2][3]) / 2.0 - top_y) / span

    def is_leg(b):
        """靠下 + 落在身体中轴上 = 裸露的腿（既不是脸也不是手）"""
        if rel_y(b) <= 0.65:
            return False
        cx = (b[2][0] + b[2][2]) / 2.0
        return abs(cx - body_cx) < body_w * 0.15

    # 脸 = 眼窝孔洞最多的块；没有孔洞时退回「综合得分最高的块」
    #   得分 = 面积 × 位置权重（越靠上越像脸） × 顶端降权
    #   原因：举起的手会在脸之上，但手的上方是背景，脸的上方一定是头发
    holes = [blob_hole_count(b[1], w, *b[2]) for b in skin_blobs]
    best = max(holes)
    if best >= HOLE_MIN:
        face = skin_blobs[holes.index(best)]
    else:
        apx = a.load()

        def top_exposed(b):
            """该块正上方是否是背景（透明）—— 是则它不可能是脸"""
            x0, y0, x1, y1 = b[2]
            ya = y0 - TOP_BAND
            if ya < 0:
                return False
            xa, xb = max(0, x0), min(w, x1)
            if xb <= xa:
                return False
            bg = 0
            total = 0
            for y in range(ya, y0):
                for x in range(xa, xb):
                    total += 1
                    if not apx[x, y]:
                        bg += 1
            return total > 0 and bg * 2 > total

        def score(b):
            rel = rel_y(b)
            if is_leg(b):           # 大腿小腿一带，不可能是脸
                return 0.0
            pos = 1.0 - 1.2 * max(0.0, rel)
            # 脸几乎总是落在身体中轴上；举在胸前的手会偏离中轴 -> 降权
            cx = (b[2][0] + b[2][2]) / 2.0
            off = abs(cx - body_cx) / body_w
            axis = 1.0 if off <= 0.12 else (0.55 if off <= 0.28 else 0.22)
            # 「上方是背景」只对偏离中轴的块有意义：脸的正上方可能是刘海/发饰的空隙
            top_pen = 0.35 if (top_exposed(b) and off > 0.12) else 1.0
            return b[0] * pos * axis * top_pen

        face = max(skin_blobs, key=score)

    # 腿部块（裙下露出的腿等）既不是脸也不是手 -> 走黑色斜坡
    skin_blobs = [b for b in skin_blobs if not is_leg(b)]

    # 脸的附属块：被刘海/描边切碎、但紧贴脸的肤色块（也算脸，不算手）
    fx0, fy0, fx1, fy1 = face[2]
    fcx, fcy = (fx0 + fx1) / 2.0, (fy0 + fy1) / 2.0
    fw = max(fx1 - fx0, fy1 - fy0)
    near_d = fw * NEAR_FACE

    def near_face(b):
        x0, y0, x1, y1 = b[2]
        cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
        if x0 >= fx0 - 2 and x1 <= fx1 + 2 and y0 >= fy0 - 2 and y1 <= fy1 + 2:
            return True
        return math.hypot(cx - fcx, cy - fcy) < near_d

    face_blobs = [b for b in skin_blobs if b is face or near_face(b)]
    hand_blobs = [b for b in skin_blobs if b not in face_blobs]

    # 话筒 = mic 色带里「与手相邻」的块（手握着话筒）
    mic_keep = Image.new('L', (w, h), 0)
    if hand_blobs:
        hand_dil = dilate(mask_from_pixels((w, h), hand_blobs), 12)
        hd = hand_dil.load()
        keep = []
        z0, z1 = cfg.get('mic_zone', (0.0, 1.0))
        for b in components(mic, 12):
            cy = (b[2][1] + b[2][3]) / 2.0 / max(1, h)
            if not (z0 <= cy <= z1):
                continue
            touch = 0
            for p in b[1]:
                if hd[p % w, p // w]:
                    touch += 1
                    if touch > 10:
                        break
            if touch > 10:
                keep.append(b)
        if keep:
            mic_keep = mask_from_pixels((w, h), keep)

    # 与原肤色掩膜求交：只染真正的皮肤像素，描边缝隙保持黑色
    hand = ImageChops.multiply(mask_from_pixels((w, h), hand_blobs), skin_raw)
    face_m = ImageChops.multiply(mask_from_pixels((w, h), face_blobs), skin_raw)
    hand = ImageChops.subtract(hand, face_m)
    return hand, mic_keep


# ---------------- 着色 ----------------
def recolor(fr, hand, mic):
    rgba = fr.convert('RGBA')
    a = rgba.getchannel('A')
    lum = rgba.convert('L')
    # 黑色斜坡：保留体积感，不是死黑片
    black = lum.point(lambda v: min(46, int(v * 0.15))).convert('RGB')
    # 黄色斜坡
    y = Image.merge('RGB', (
        lum.point(lambda v: min(255, int(v * 1.00))),
        lum.point(lambda v: int(v * 0.80)),
        lum.point(lambda v: int(v * 0.18))))
    out = black.copy()
    out.paste(y, (0, 0), hand)
    out.paste(rgba.convert('RGB'), (0, 0), mic)
    out = out.convert('RGBA')
    out.putalpha(a)
    return out


def process(tag, verbose=True):
    cfg = CFG[tag]
    src = Image.open(os.path.join(SRC, cfg['png'])).convert('RGBA')
    W, H = src.size
    out = src.copy()
    done = {}
    stats = dict(frames=0, handpx=0, micpx=0)
    for fam, ts in families(cfg['xml']).items():
        for t in ts:
            x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
            key = (x, y, w, h)
            if key not in done:
                fr = src.crop((x, y, x + w, y + h))
                hand, mic = classify(fr, cfg)
                done[key] = recolor(fr, hand, mic)
                stats['handpx'] += sum(1 for v in hand.getdata() if v)
                stats['micpx'] += sum(1 for v in mic.getdata() if v)
            out.paste(done[key], (x, y))
            stats['frames'] += 1
    dst = os.path.join(OUT, 'recolored_%s.png' % tag)
    out.save(dst)
    if verbose:
        print('%-8s %-34s -> %s  (%d 帧, %d 唯一区域, 手 %d px, 话筒 %d px)'
              % (tag, cfg['png'], dst, stats['frames'], len(done), stats['handpx'], stats['micpx']))
    return dst


def montage(tag, maxw=260, maxh=300, cols=4):
    """输出重着色后的每个家族代表帧，用于人工验收"""
    cfg = CFG[tag]
    dst = Image.open(os.path.join(OUT, 'recolored_%s.png' % tag)).convert('RGBA')
    cells = []
    for fam, ts in families(cfg['xml']).items():
        t = ts[0]
        x, y, w, h = [int(t.get(k)) for k in ('x', 'y', 'width', 'height')]
        cells.append((fam, dst.crop((x, y, x + w, y + h))))
    CW, CH = maxw + 20, maxh + 40
    rows = (len(cells) + cols - 1) // cols
    S = Image.new('RGB', (cols * CW, rows * CH), (250, 250, 252))
    d = ImageDraw.Draw(S)
    try:
        f1 = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 16)
    except Exception:
        f1 = ImageFont.load_default()
    for i, (fam, fr) in enumerate(cells):
        cx, cy = (i % cols) * CW + 10, (i // cols) * CH + 6
        sc = min(1.0, maxh / max(1, fr.height), maxw / max(1, fr.width))
        c = fr.resize((max(1, int(fr.width * sc)), max(1, int(fr.height * sc))), Image.LANCZOS)
        bg = Image.new('RGB', c.size, (255, 255, 255))
        bg.paste(c, (0, 0), c)
        S.paste(bg, (cx, cy))
        d.rectangle([cx, cy, cx + c.width - 1, cy + c.height - 1], outline=(170, 170, 180))
        d.text((cx, cy + c.height + 4), fam[:30], fill=(20, 20, 20), font=f1)
    p = os.path.join(OUT, 'check_%s.png' % tag)
    S.save(p)
    print('  ->', p)


if __name__ == '__main__':
    only = sys.argv[1:] if len(sys.argv) > 1 else list(CFG.keys())
    for tag in only:
        process(tag)
        montage(tag)
