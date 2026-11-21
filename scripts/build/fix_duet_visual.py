# -*- coding: utf-8 -*-
"""DK_Duet 视觉修复：
1) Teto 出现后常驻，不再忽隐忽现（Legacy / events.lua 里所有 gf 淡出清掉）
2) 删掉 blackIntro 黑色角色过渡动画，改成白屏 -> 白屏淡出 -> Teto 直接出现
3) 加 Duo Ghost.lua：和弦/双唱时叠一个半透明第二动画，过一会渐隐消失
4) 双人 icon 改成参考原版 DK：两个完整头像一个放左、一个放右
"""
import os, json, shutil, datetime
from PIL import Image

M = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ORIG = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods'
BACKUP = r'E:/UST_work/dk_duet/_backup_visual_' + datetime.datetime.now().strftime('%H%M%S')

NEWLOGIC = '''-- Double Kill：白屏登场，Teto 出现后常驻
-- 原版的 blackIntro（黑色 Impostor 从天而降的过渡动画）已整个去掉
function onCreate()
    makeLuaSprite('dkWhite', nil, 0, 0)
    makeGraphic('dkWhite', 1280, 720, 'FFFFFF')
    setObjectCamera('dkWhite', 'camOther')
    setProperty('dkWhite.alpha', 1)
    addLuaSprite('dkWhite', true)
end

function onCreatePost()
    -- 白屏盖着的时候先把第二对手藏好，白屏淡出后一次性显示，之后不再改
    setProperty('gfGroup.alpha', 0)
end

function onSongStart()
    doTweenAlpha('dkWhiteOut', 'dkWhite', 0, 0.8, 'linear')
end

function onStepHit()
    if curStep == 144 then
        -- 白屏过渡消失，Teto 直接出现在旁边并一直留着
        doTweenAlpha('dkWhiteOut2', 'dkWhite', 0, 0.6, 'linear')
        setProperty('gfGroup.alpha', 1)
        setProperty('gf.alpha', 1)
    end
end
'''

LEGACY = '''-- Legacy: 谱面里 39 次 black / not black 切换，原本负责半透明出现与渐隐。
-- 现在 Teto 是常驻角色，这里只保持可见，不再做淡入淡出（避免在旁边忽隐忽现）。
-- 合唱时的「半透明第二动画 + 过一会渐隐」由 custom_events/Duo Ghost.lua 负责。
function onEvent(name, v1, v2)
    if name ~= 'Legacy' then return end
    setProperty('gfGroup.alpha', 1)
    setProperty('gf.alpha', 1)
end
'''

DUOGHOST = '''-- Duo Ghost: 和弦 / 双唱时播放两个动作，额外叠一个半透明的第二动画，
-- 过一小会儿过渡淡出消失（Teto 本体不受影响，一直在旁边）。
-- 触发：谱面事件 Both Opponents = 1，或 noteType 为 WHITEANDBLACK / blackDuo / DuoSing。
local ghostTag = 'dkDuoGhost'
local ghostMade = false
local duoMode = false
local anims = {'left', 'down', 'up', 'right'}

function makeGhost()
    if ghostMade then return end
    makeAnimatedLuaSprite(ghostTag, 'characters/teto-2026', getProperty('gf.x'), getProperty('gf.y'))
    addAnimationByPrefix(ghostTag, 'left', 'left', 24, false)
    addAnimationByPrefix(ghostTag, 'down', 'down', 24, false)
    addAnimationByPrefix(ghostTag, 'up', 'up', 24, false)
    addAnimationByPrefix(ghostTag, 'right', 'right', 24, false)
    scaleObject(ghostTag, getProperty('gf.scale.x'), getProperty('gf.scale.y'))
    setProperty(ghostTag .. '.flipX', getProperty('gf.flipX'))
    setProperty(ghostTag .. '.alpha', 0)
    addLuaSprite(ghostTag, false)
    ghostMade = true
end

function showGhost(dir)
    makeGhost()
    cancelTween('dkGhostFade')
    setProperty(ghostTag .. '.x', getProperty('gf.x') + 22)
    setProperty(ghostTag .. '.y', getProperty('gf.y'))
    setProperty(ghostTag .. '.alpha', 0.5)
    local a = anims[math.abs(dir) + 1] or 'left'
    playAnim(ghostTag, a, true)
    runTimer('dkGhostHide', 0.55)
end

function onEvent(name, v1, v2)
    if name == 'Both Opponents' then duoMode = (v1 == '1') end
end

function opponentNoteHit(id, direction, noteType, isSustainNote)
    if duoMode or noteType == 'WHITEANDBLACK' or noteType == 'blackDuo' or noteType == 'DuoSing' then
        showGhost(direction)
    end
end

function onTimerCompleted(tag)
    if tag == 'dkGhostHide' then
        doTweenAlpha('dkGhostFade', ghostTag, 0, 0.5, 'linear')
    end
end
'''


def patch_events(path):
    t = open(path, encoding='utf-8').read()
    # 这两处会把 Teto 淡出，导致「一会儿出现一会儿消失」
    t = t.replace("        doTweenAlpha('GF', 'gf', 0, 1.3)\n", "        setProperty('gf.alpha', 1)\n")
    # 白屏闪一下替代原来的黑场过渡
    t = t.replace("cameraFlash('game', '000000', 0.8, true)", "cameraFlash('game', 'FFFFFF', 0.8, true)")
    open(path, 'w', encoding='utf-8', newline='').write(t)
    return t


def make_icons():
    src = os.path.join(M, 'images/icons')
    momo = Image.open(os.path.join(src, 'icon-momo.png')).convert('RGBA')
    teto = Image.open(os.path.join(src, 'icon-teto-cozy.png')).convert('RGBA')
    W, H = 300, 150
    # 每个 icon 是两帧各 150 宽；取第一帧的完整头像
    m = momo.crop((0, 0, 150, 150)) if momo.width >= 150 else momo
    t = teto.crop((0, 0, 150, 150)) if teto.width >= 150 else teto
    m = m.resize((150, H), Image.LANCZOS)
    t = t.resize((150, H), Image.LANCZOS)
    out = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    out.paste(m, (0, 0), m)
    out.paste(t, (150, 0), t)
    for fn in ('icon-double-kill.png', 'icon-momo-teto.png'):
        out.save(os.path.join(src, fn))
        print('  icon ->', fn, out.size)
    ref = Image.open(os.path.join(ORIG, 'images/icons/icon-double-kill.png'))
    print('  原版参考尺寸', ref.size, '（布局：左一个完整头像 + 右一个完整头像）')


def main():
    os.makedirs(BACKUP, exist_ok=True)
    targets = [
        ('data/double-kill/NewLogic.lua', NEWLOGIC),
        ('custom_events/Legacy.lua', LEGACY),
    ]
    for rel, content in targets:
        p = os.path.join(M, rel)
        shutil.copy2(p, os.path.join(BACKUP, rel.replace('/', '_')))
        open(p, 'w', encoding='utf-8', newline='').write(content)
        print('重写', rel)

    ep = os.path.join(M, 'data/double-kill/events.lua')
    shutil.copy2(ep, os.path.join(BACKUP, 'events.lua'))
    t = patch_events(ep)
    print('修补 events.lua: gf 淡出残留', t.count("doTweenAlpha('GF', 'gf', 0"), '| 白闪', t.count("'FFFFFF'"))

    gp = os.path.join(M, 'custom_events/Duo Ghost.lua')
    open(gp, 'w', encoding='utf-8', newline='').write(DUOGHOST)
    print('新增 custom_events/Duo Ghost.lua')

    make_icons()
    print('备份 ->', BACKUP)


if __name__ == '__main__':
    main()
