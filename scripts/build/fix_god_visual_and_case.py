# -*- coding: utf-8 -*-
"""
DK_Duet v10.3 修复：
  1) 为 5 个 God 图集补配套 Sparrow XML（帧布局与原版完全一致，照抄 + 改 imagePath）
     —— 缺 XML 导致引擎无法解析帧，角色完全不渲染（人消失）
  2) weeks 难度名 god -> GOD（显示大写；getFilePath 走 formatToSongPath 仍为 -god，谱面不用改）
  3) icons.lua 的难度判断改成大小写兼容，避免大写后双人 icon 不切换
  4) NewLogic.lua 的 camGame.zoom / camHUD.zoom 每拍累加加封顶，防止背景无限放大

单一数据源：游戏主部署 windows/mods/DK_Duet 的原版 XML 为权威；
同步到 stage 源 + DK_Dual + DK_Miku + 游戏部署。
"""
import os
import re

ROOTS = [
    'E:/UST_work/dk_miku/_godmode/stage',
    'E:/UST_work/dk_miku/DK_Dual',
    'E:/UST_work/dk_miku/DK_Miku',
    'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
]
AUTHORITY = ROOTS[-1]

# (原版 xml, 要生成的 god xml) —— 相对部署根
XML_PAIRS = [
    ('images/characters/miku_assets.xml',                    'images/characters/miku_assets_god.xml'),
    ('images/characters/momo_assets.xml',                    'images/characters/momo_assets_god.xml'),
    ('images/characters/teto-2026.xml',                      'images/characters/teto-2026_god.xml'),
    ('images/characters/cuphead/BoyFriend_ICCuphead.xml',    'images/characters/cuphead/BoyFriend_ICCuphead_god.xml'),
    ('images/characters/bf/defeatBf-normal.xml',             'images/characters/bf/defeatBf-normal_god.xml'),
]

BEAT_OLD = (
    "function onBeatHit()\n"
    "    if curBeat % 1 == 0 then\n"
    "        setProperty('camGame.zoom', getProperty('camGame.zoom') + camZoom)\n"
    "        setProperty('camHUD.zoom', getProperty('camHUD.zoom') + hudZoom)\n"
    "    end\n"
    "end"
)
BEAT_NEW = (
    "-- 镜头推进封顶：events.lua 的 defaultCamZoom 最高 1.4，这里封 1.5，\n"
    "-- 防止每拍累加无限放大把背景糊掉（原版无上限，几百拍后 zoom 涨到 3~4）\n"
    "local ZOOM_CAP = 1.5\n"
    "local HUD_ZOOM_CAP = 1.15\n\n"
    "function onBeatHit()\n"
    "    if curBeat % 1 == 0 then\n"
    "        local z = getProperty('camGame.zoom') + camZoom\n"
    "        if z > ZOOM_CAP then z = ZOOM_CAP end\n"
    "        setProperty('camGame.zoom', z)\n"
    "        local hz = getProperty('camHUD.zoom') + hudZoom\n"
    "        if hz > HUD_ZOOM_CAP then hz = HUD_ZOOM_CAP end\n"
    "        setProperty('camHUD.zoom', hz)\n"
    "    end\n"
    "end"
)


def write_all(rel, data, label):
    """把同一份二进制写到所有存在的部署根"""
    n = 0
    for root in ROOTS:
        dst = os.path.join(root, rel)
        if not os.path.isdir(os.path.dirname(dst)):
            continue
        old = open(dst, 'rb').read() if os.path.exists(dst) else None
        if old == data:
            print('  = %-58s %s' % (rel, os.path.basename(root)))
        else:
            open(dst, 'wb').write(data)
            print('  + %-58s %s' % (rel, os.path.basename(root)))
        n += 1
    if n == 0:
        print('  ! no target for', rel)
    return n


def make_god_xml(src_path):
    raw = open(src_path, 'rb').read()
    m = re.search(rb'imagePath="([^"]*)"', raw)
    if not m:
        raise RuntimeError('no imagePath in ' + src_path)
    base, ext = os.path.splitext(m.group(1).decode('utf-8'))
    newval = (base + '_god' + ext).encode('utf-8')
    out = raw[:m.start(1)] + newval + raw[m.end(1):]
    return out, raw.count(b'<SubTexture')


print('=== 1) God XML ===')
for src_rel, dst_rel in XML_PAIRS:
    src = os.path.join(AUTHORITY, src_rel)
    data, frames = make_god_xml(src)
    write_all(dst_rel, data, 'xml')
    print('     frames=%d imagePath->%s' % (
        frames, re.search(rb'imagePath="([^"]*)"', data).group(1).decode()))

print()
print('=== 2) weeks difficulty -> GOD ===')
for root in ROOTS:
    wdir = os.path.join(root, 'weeks')
    if not os.path.isdir(wdir):
        continue
    for fn in sorted(os.listdir(wdir)):
        if not fn.endswith('.json'):
            continue
        p = os.path.join(wdir, fn)
        raw = open(p, 'rb').read()
        if b'"hard,god"' not in raw:
            if b'"hard,GOD"' in raw:
                print('  = %s/%s already GOD' % (os.path.basename(root), fn))
            continue
        open(p, 'wb').write(raw.replace(b'"hard,god"', b'"hard,GOD"'))
        print('  + %s/%s hard,god -> hard,GOD' % (os.path.basename(root), fn))

print()
print('=== 3) icons.lua case-insensitive ===')
ICON_OLD = b"difficultyName == 'god'"
ICON_NEW = b"difficultyName == 'GOD' or difficultyName == 'god'"
for root in ROOTS:
    ddir = os.path.join(root, 'data')
    if not os.path.isdir(ddir):
        continue
    for song in sorted(os.listdir(ddir)):
        p = os.path.join(ddir, song, 'icons.lua')
        if not os.path.exists(p):
            continue
        raw = open(p, 'rb').read()
        if ICON_OLD not in raw:
            if ICON_NEW in raw:
                print('  = %s/%s already compatible' % (os.path.basename(root), song))
            continue
        open(p, 'wb').write(raw.replace(ICON_OLD, ICON_NEW))
        print('  + %s/%s/icons.lua' % (os.path.basename(root), song))

print()
print('=== 4) NewLogic.lua zoom cap ===')
for root in ROOTS:
    ddir = os.path.join(root, 'data')
    if not os.path.isdir(ddir):
        continue
    for song in ['double-kill', 'double-kill-miku']:
        p = os.path.join(ddir, song, 'NewLogic.lua')
        if not os.path.exists(p):
            continue
        raw = open(p, 'rb').read()
        if BEAT_OLD.encode('utf-8') in raw:
            open(p, 'wb').write(raw.replace(BEAT_OLD.encode('utf-8'), BEAT_NEW.encode('utf-8')))
            print('  + %s/%s/NewLogic.lua capped' % (os.path.basename(root), song))
        elif b'ZOOM_CAP' in raw:
            print('  = %s/%s already capped' % (os.path.basename(root), song))
        else:
            print('  ! %s/%s pattern not found' % (os.path.basename(root), song))
