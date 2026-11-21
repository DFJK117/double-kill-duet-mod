# -*- coding: utf-8 -*-
"""DK Trap 皮肤 = 原版箭头剪影（黑内红边）+ 套在上面的红色光环。

复用引擎自带的 NOTE_assets 四向箭头，保证四个方向的形状/朝向与普通按键
完全一致（紫色=左、蓝色=下、绿色=上、红色=右）。

着色规则：
  * 箭头内部（原版红色填充区）-> 黑色斜坡（保留立体感）
  * 箭头描边（原版绿边+蓝边）  -> 红色
  * 箭头【头顶上方】戴一个红色光环（亮红扁椭圆 + 外发光），不是套在箭头腰部
"""
from PIL import Image, ImageDraw, ImageFilter
import os

NOTE_ATLAS = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/assets/shared/images/noteSkins/NOTE_assets.png'

# 原版箭头帧在 NOTE_assets 图集里的坐标
ARROWS = {
    'purple': (795, 234, 154, 157),
    'blue':   (1854, 1, 157, 154),
    'green':  (1854, 156, 157, 154),
    'red':    (1, 237, 154, 157),
}

EDGE_RED = (214, 34, 44, 255)     # 箭头描边：红
HALO_RED = (255, 58, 62, 255)     # 光环：亮红
SS = 3                          # 超采样倍数


def _load_arrow(name):
    im = Image.open(NOTE_ATLAS).convert('RGBA')
    x, y, w, h = ARROWS[name]
    return im.crop((x, y, x + w, y + h))


def _recolor_arrow(fr):
    """原版箭头 -> 黑内红边。返回 RGBA。"""
    w, h = fr.size
    px = fr.load()
    out = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    op = out.load()
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a < 24:
                continue
            # 原版箭头：内部为纯红填充，描边是绿边 + 蓝边
            if r > 150 and g < 110 and b < 110:
                # 内部（红填充）-> 黑色斜坡，保留一点层次
                lum = (r * 0.3 + g * 0.59 + b * 0.11)
                v = min(46, int(lum * 0.16))
                op[x, y] = (v, v, v + 3, a)
            else:
                # 描边（绿边/蓝边）-> 红色
                op[x, y] = (EDGE_RED[0], EDGE_RED[1], EDGE_RED[2], a)
    return out


def _draw_halo(arrow):
    """光环【戴在箭头头顶上方】——天使光环浮在头顶，不是套在箭头腰部。

    用户最终明确：光环在"箭头头上"。所以：
      * 箭头本体放在画布中下部，光环浮在它正上方；
      * 光环中心 x = 箭头水平中心，y = 箭头顶部再往上一点点（轻贴头顶）；
      * 横向扁椭圆（rx≈箭头宽 0.50、ry≈箭头高 0.115）；
      * 多层高斯模糊外发光做光晕（加厚加强）。
      * 关键修复：光环下缘必须完全高于箭头顶端最高点，绝不能让箭头红尖
        穿进光环内部造成"光环断了三处"的错觉 —— 光环上移 + 箭头不动。
    """
    aw, ah = arrow.size
    rx = int(aw * 0.50)
    ry = int(ah * 0.115)
    lw = max(5, int(aw * 0.046))

    # 画布：上方要多留一截给光环 + 光晕，下方稍留边
    pad_top = int(ah * 0.40)
    pad_bottom = int(ah * 0.12)
    pad_x = int(aw * 0.13)
    W, H = aw + pad_x * 2, ah + pad_top + pad_bottom
    canvas = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    ax, ay = pad_x, pad_top
    canvas.alpha_composite(arrow, (ax, ay))

    # 光环中心：水平正中 = 箭头中心；垂直 = 上移到光环下缘完全离开箭头顶端
    cx = ax + aw // 2
    cy = ay - int(ah * 0.21)      # 下缘 = cy+ry = ay-0.095ah，与箭头顶部留 9.5% 空隙
    box = [cx - rx, cy - ry, cx + rx, cy + ry]

    # 发光光晕：四层不同半径/透明度的高斯模糊叠加（更亮更厚）。
    # 做法：画椭圆描边 -> 模糊 -> 把环心内部清零。扁椭圆纵向很薄，若用
    # "实心椭圆挖洞"会因 inset 大于纵半径而挖空失败→环心糊成红饼；
    # 这里改为描边后模糊、再把内部椭圆区域 alpha 归零，光晕只向外扩。
    inner_clear = (lw + 3)
    clear_box = [box[0] + inner_clear, box[1] + inner_clear,
                 box[2] - inner_clear, box[3] - inner_clear]
    for outline, width, radius in [
        ((255, 40, 48, 245), lw + 12, max(8, int(aw * 0.075))),   # 外层大范围红雾
        ((255, 55, 60, 235), lw + 7,  max(6, int(aw * 0.048))),   # 中层
        ((255, 110, 90, 210), lw + 3, max(4, int(aw * 0.026))),   # 内层亮边
        ((255, 175, 140, 170), lw,    max(3, int(aw * 0.012))),   # 贴环白热高光
    ]:
        g = Image.new('L', (W, H), 0)
        ImageDraw.Draw(g).ellipse(box, outline=255, width=width)
        g = g.filter(ImageFilter.GaussianBlur(radius=radius))
        # 环心清零：只保留环线外侧的辉光
        if clear_box[2] > clear_box[0] and clear_box[3] > clear_box[1]:
            ImageDraw.Draw(g).ellipse(clear_box, fill=0)
        tint = Image.new('RGBA', (W, H), outline)
        tint.putalpha(g)
        canvas.alpha_composite(tint)

    # 环本体（亮红，戴在头顶）
    d = ImageDraw.Draw(canvas)
    d.ellipse(box, outline=HALO_RED, width=lw)
    # 内侧暗红描边增加厚度
    inner = [cx - rx + lw, cy - ry + lw, cx + rx - lw, cy + ry - lw]
    d.ellipse(inner, outline=(150, 16, 22, 235), width=max(2, lw // 3))
    return canvas


def build_trap_frames():
    """返回 [(颜色名, PIL.Image), ...]。画布只比箭头略大，光环居中贴箭头。"""
    frames = []
    for name in ('purple', 'blue', 'green', 'red'):
        fr = _recolor_arrow(_load_arrow(name))
        w, h = fr.size
        big_arrow = fr.resize((w * SS, h * SS), Image.LANCZOS)
        haloed = _draw_halo(big_arrow)
        # 输出：画布比例缩回，箭头仍接近原尺寸（略大 1.1 倍留光晕）
        out_w = int(w * 1.15)
        out_h = int(haloed.height * out_w / haloed.width)
        frames.append((name, haloed.resize((out_w, out_h), Image.LANCZOS)))
    return frames


if __name__ == '__main__':
    OUT = r'E:/UST_work/dk_miku/_godmode'
    frames = build_trap_frames()
    # 拼一张预览
    W = sum(f.width for _, f in frames) + 20 * (len(frames) + 1)
    H = max(f.height for _, f in frames) + 40
    sheet = Image.new('RGBA', (W, H), (24, 24, 32, 255))
    x = 20
    for name, f in frames:
        sheet.paste(f, (x, 20), f)
        x += f.width + 20
    sheet.save(os.path.join(OUT, 'trap_arrow_preview.png'))
    print('预览 ->', os.path.join(OUT, 'trap_arrow_preview.png'), sheet.size)
    for name, f in frames:
        print('  %s: %dx%d' % (name, f.width, f.height))
