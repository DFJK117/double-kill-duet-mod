#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flixel 角色落点/摄像机锚点模拟器 (为 DK_Duet + bf-ic 修复服务)

严格复刻 NF 1.2.1h2 / Flixel 5.9 的几何语义:
  - FlxAtlasFrames.fromSparrow:
        size      = FlxRect(frameX, frameY, frameWidth, frameHeight)
        offset    = (-frameX, -frameY)          # 内容在原始画布内的偏移(正数)
        sourceSize= (frameWidth, frameHeight)   # 未裁剪画布尺寸
  - FlxSprite.set_frames -> frame = frames[0]; resetHelpers() -> centerOrigin()
        origin = (frame0.sourceSize.x/2, frame0.sourceSize.y/2)   # 常量
  - Character.loadCharacterFile: scale.set(jsonScale); updateHitbox()
        width  = |scale| * frameWidth(frame0)   # 命中框常量
        height = |scale| * frameHeight(frame0)
        origin = (frameWidth/2, frameHeight/2)
  - 渲染矩阵 (drawComplex, tile 路径, 不翻转):
        M = T(frameOffset) . T(-origin) . S(sx,sy) . T(point)
        point = (x + origin.x - animOffset.x, y + origin.y - animOffset.y)
        世界坐标:  worldX = (canvasX - origin.x)*sx + x + origin.x - animOffset.x
  - PlayState.moveCamera(bf):
        camFollow.x = midpoint.x - 100 - cameraPosition[0] + camera_boyfriend[0]
        camFollow.y = midpoint.y - 100 + cameraPosition[1] + camera_boyfriend[1]
        midpoint = (x + width/2, y + height/2)
"""

import json
import os
import re
import sys
import xml.etree.ElementTree as ET

from PIL import Image

# ---------------------------------------------------------------- 路径常量
GAME = r"E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\windows\mods\DK_Duet"
IC_MOD = r"E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\windows\mods\Indie Cross v15"
DK_BACKUP = r"E:\UST_work\dk_miku\_backup_lua_v6_20261115"

ATLAS = {
    "ic": (os.path.join(GAME, "images", "characters", "cuphead", "BoyFriend_ICCuphead.png"),
           os.path.join(GAME, "images", "characters", "cuphead", "BoyFriend_ICCuphead.xml")),
    "dk": (os.path.join(GAME, "images", "characters", "bf", "BOYFRIEND.png"),
           os.path.join(GAME, "images", "characters", "bf", "BOYFRIEND.xml")),
}

# cargo 舞台
STAGE = {"boyfriend": (2550.0, 650.0), "camera_boyfriend": (-140.0, -80.0),
         "defaultZoom": 0.9}

_alpha_cache = {}
_img_cache = {}


def load_rgba(png_path):
    if png_path not in _img_cache:
        im = Image.open(png_path)
        if im.mode != "RGBA":
            im = im.convert("RGBA")
        _img_cache[png_path] = im
    return _img_cache[png_path]


def parse_atlas(xml_path):
    """返回按 XML 顺序排列的 frame 列表 (Flixel frames[0] = 第一条 SubTexture)."""
    tree = ET.parse(xml_path)
    out = []
    for tex in tree.getroot().iter("SubTexture"):
        def num(k, d=0):
            v = tex.get(k)
            return int(v) if v is not None else d
        out.append({
            "name": tex.get("name") or "",
            "x": num("x"), "y": num("y"),
            "w": num("width"), "h": num("height"),
            "frameX": num("frameX"), "frameY": num("frameY"),
            "frameWidth": num("frameWidth", num("width")),
            "frameHeight": num("frameHeight", num("height")),
            "rotated": tex.get("rotated") == "true",
        })
    return out


def alpha_bbox(png_path, frame):
    """帧内容矩形内的不透明像素包围盒 (相对帧内容左上角)."""
    key = (png_path, frame["x"], frame["y"], frame["w"], frame["h"])
    if key in _alpha_cache:
        return _alpha_cache[key]
    im = load_rgba(png_path)
    if frame["x"] + frame["w"] > im.width or frame["y"] + frame["h"] > im.height:
        bb = (0, 0, frame["w"], frame["h"])
    else:
        crop = im.crop((frame["x"], frame["y"], frame["x"] + frame["w"], frame["y"] + frame["h"]))
        bb = crop.getchannel("A").getbbox()
        if bb is None:
            bb = (0, 0, frame["w"], frame["h"])
    _alpha_cache[key] = bb
    return bb


def frames_for_prefix(frames, prefix, indices=None):
    """FlxAnimationController.addByPrefix 的选帧规则: 前缀匹配 + 数字后缀排序."""
    sel = [f for f in frames if f["name"].startswith(prefix)]
    def order(f):
        m = re.search(r"(\d+)", f["name"][len(prefix):])
        return int(m.group(1)) if m else 0
    sel.sort(key=order)
    if indices:
        sel = [sel[i] for i in indices if i < len(sel)]
    return sel


def canvas_bbox(png_path, frame):
    """帧内容在原始画布(canvas)坐标系里的 alpha 包围盒."""
    ox, oy = -frame["frameX"], -frame["frameY"]
    ax0, ay0, ax1, ay1 = alpha_bbox(png_path, frame)
    return (ox + ax0, oy + ay0, ox + ax1, oy + ay1)


class Character:
    def __init__(self, atlas_key, json_path):
        self.png, self.xml = ATLAS[atlas_key]
        self.frames = parse_atlas(self.xml)
        with open(json_path, encoding="utf-8") as f:
            self.data = json.load(f)
        self.scale = float(self.data.get("scale", 1))
        self.position = [float(v) for v in self.data.get("position", [0, 0])]
        self.camera_position = [float(v) for v in self.data.get("camera_position", [0, 0])]
        f0 = self.frames[0]
        self.fw0, self.fh0 = float(f0["frameWidth"]), float(f0["frameHeight"])
        self.origin = (self.fw0 / 2.0, self.fh0 / 2.0)
        self.hit_w = abs(self.scale) * self.fw0
        self.hit_h = abs(self.scale) * self.fh0

    # ---- 世界坐标换算 -------------------------------------------------
    def world_x(self, canvas_x, x, anim_off_x):
        s = self.scale
        return (canvas_x - self.origin[0]) * s + x + self.origin[0] - anim_off_x

    def world_y(self, canvas_y, y, anim_off_y):
        s = self.scale
        return (canvas_y - self.origin[1]) * s + y + self.origin[1] - anim_off_y

    def anim_canvas_bbox(self, anim):
        prefix = anim["name"]
        sel = frames_for_prefix(self.frames, prefix, anim.get("indices") or None)
        if not sel:
            return None
        boxes = [canvas_bbox(self.png, f) for f in sel]
        return (min(b[0] for b in boxes), min(b[1] for b in boxes),
                max(b[2] for b in boxes), max(b[3] for b in boxes), len(sel))

    def anim_world_bbox(self, anim, x, y):
        cb = self.anim_canvas_bbox(anim)
        if cb is None:
            return None
        ox, oy = anim.get("offsets", [0, 0])
        wx0 = self.world_x(cb[0], x, ox)
        wx1 = self.world_x(cb[2], x, ox)
        wy0 = self.world_y(cb[1], y, oy)
        wy1 = self.world_y(cb[3], y, oy)
        return (min(wx0, wx1), min(wy0, wy1), max(wx0, wx1), max(wy0, wy1), cb[4], cb)

    def frame_world_bbox(self, frame, x, y, anim_off=(0, 0)):
        """单帧的世界包围盒 (用于区分 attack 的躯干帧与特效帧)."""
        cb = canvas_bbox(self.png, frame)
        ox, oy = anim_off
        wx0 = self.world_x(cb[0], x, ox)
        wx1 = self.world_x(cb[2], x, ox)
        wy0 = self.world_y(cb[1], y, oy)
        wy1 = self.world_y(cb[3], y, oy)
        return (min(wx0, wx1), min(wy0, wy1), max(wx0, wx1), max(wy0, wy1))

    def midpoint(self, x, y):
        return (x + self.hit_w / 2.0, y + self.hit_h / 2.0)

    def camera_target(self, x, y, cam_pos=None):
        cp = cam_pos if cam_pos is not None else self.camera_position
        mid = self.midpoint(x, y)
        cbo = STAGE["camera_boyfriend"]
        return (mid[0] - 100.0 - cp[0] + cbo[0],
                mid[1] - 100.0 + cp[1] + cbo[1])

    def sprite_xy(self):
        return (STAGE["boyfriend"][0] + self.position[0],
                STAGE["boyfriend"][1] + self.position[1])


def report(tag, ch, x=None, y=None, cam=None):
    x, y = (ch.sprite_xy() if x is None else (x, y))
    print("\n" + "=" * 78)
    print("[%s] image=%s scale=%s" % (tag, ch.data.get("image"), ch.scale))
    print("  首帧画布 = %gx%g   origin=(%g,%g)   命中框=%gx%g" %
          (ch.fw0, ch.fh0, ch.origin[0], ch.origin[1], ch.hit_w, ch.hit_h))
    print("  精灵 x,y = (%g, %g)   midpoint=%s" % (x, y, ch.midpoint(x, y)))
    print("  camFollow = %s   (camera_position=%s)" %
          (ch.camera_target(x, y, cam), ch.camera_position if cam is None else cam))
    print("  %-16s %-28s %-28s" % ("anim", "世界包围盒 x", "世界包围盒 y"))
    for a in ch.data["animations"]:
        wb = ch.anim_world_bbox(a, x, y)
        if wb is None:
            print("  %-16s <无帧>" % a.get("anim"))
            continue
        print("  %-16s [%8.1f,%8.1f]      [%8.1f,%8.1f]  n=%d canvas=%s" %
              (a.get("anim"), wb[0], wb[2], wb[1], wb[3], wb[4], wb[5][:4]))


def solve(dk, ic):
    """以 DK 原版 BF 的 idle 图形包围盒为基准, 反解 IC BF 的 position / camera_position。

    对齐基准:
      x -> idle 图形左边 (角色左缘)
      y -> idle 图形下边 (脚底线, 决定是否踩在地面上)
    摄像机: camFollow 必须回到 DK 原版的世界坐标点。
    """
    dk_idle = idle_world(dk, *dk.sprite_xy())
    ic_idle = idle_world(ic, *ic.sprite_xy())

    dk_anim = next(a for a in dk.data["animations"] if a.get("anim") == "idle")
    ic_anim = next(a for a in ic.data["animations"] if a.get("anim") == "idle")

    # x: 让 IC idle 图形左边 == DK idle 图形左边
    cb = ic.anim_canvas_bbox(ic_anim)
    new_x = dk_idle[0] - (cb[0] - ic.origin[0]) * ic.scale - ic.origin[0] + ic_anim["offsets"][0]
    # y: 让 IC idle 图形下边 == DK idle 图形下边 (脚底)
    new_y = dk_idle[3] - (cb[3] - ic.origin[1]) * ic.scale - ic.origin[1] + ic_anim["offsets"][1]

    # 摄像机: 反解 camera_position 使 camFollow == DK 原版 camFollow
    dk_cam = dk.camera_target(*dk.sprite_xy())
    mid = ic.midpoint(new_x, new_y)
    cbo = STAGE["camera_boyfriend"]
    cp_x = mid[0] - 100.0 + cbo[0] - dk_cam[0]
    cp_y = dk_cam[1] - (mid[1] - 100.0 + cbo[1])

    return {
        "position": [round(new_x - STAGE["boyfriend"][0], 2), round(new_y - STAGE["boyfriend"][1], 2)],
        "camera_position": [round(cp_x, 2), round(cp_y, 2)],
        "sprite_xy": (new_x, new_y),
        "dk_idle_world": dk_idle[:4],
        "ic_idle_world_before": ic_idle[:4],
        "dk_cam": dk_cam,
    }


def idle_world(ch, x, y):
    for a in ch.data["animations"]:
        if a.get("anim") == "idle":
            return ch.anim_world_bbox(a, x, y)
    return None


def main():
    dk = Character("dk", os.path.join(DK_BACKUP, "characters", "bf.json"))
    ic_cur = Character("ic", os.path.join(GAME, "characters", "bf.json"))

    report("A: DK 原版 BF (BOYFRIEND, scale1)", dk)
    report("B: 当前 v6 BF (IC 图集, scale2, position 照抄 DK)", ic_cur)

    # ---- 对齐基准: idle 动画的图形包围盒 --------------------------------
    x_dk, y_dk = dk.sprite_xy()
    x_ic, y_ic = ic_cur.sprite_xy()
    dk_idle = idle_world(dk, x_dk, y_dk)
    ic_idle = idle_world(ic_cur, x_ic, y_ic)
    print("\n" + "=" * 78)
    print("idle 对齐:")
    print("  DK 原版  world x[%g,%g] y[%g,%g]" % dk_idle[:4])
    print("  IC 现状  world x[%g,%g] y[%g,%g]" % ic_idle[:4])

    sol = solve(dk, ic_cur)
    new_x, new_y = sol["sprite_xy"]
    print("  => position        = %s   (原 %s)" % (sol["position"], ic_cur.position))
    print("  => camera_position = %s   (原 %s)" % (sol["camera_position"], ic_cur.camera_position))
    print("  => 精灵 x,y = (%g, %g)" % (new_x, new_y))
    print("  camFollow: DK=%s  IC新=%s" % (sol["dk_cam"], ic_cur.camera_target(new_x, new_y, sol["camera_position"])))

    # ---- 用新参数复算, 校验所有动画 -------------------------------------
    report("C: 修正后 IC BF", ic_cur, new_x, new_y, sol["camera_position"])


if __name__ == "__main__":
    main()
