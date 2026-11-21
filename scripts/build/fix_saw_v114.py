# v11.4 修复：
#  1) dk_alert.xml / dk_saw.xml 的 <TextureAtlas> 补 width/height（对齐同 mod 成功加载的 dk_trap/dk_warn）
#  2) DK_Saw.lua：onEvent 里立即 ensureSaw（v11.3 从未调用 -> 锯子精灵不存在）
#  3) 音效：第1/2下都用 alert（同一声"噔"），第3下用 sawbladeHit（锯子声）
#  4) 精灵显示加多重保障：每次都确保存在、alpha=1；用 luaSpriteExists 校验
import os, re, sys

ROOTS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SRC = r'E:/UST_work/dk_miku/scripts/DK_Saw.lua'
IMG_SIZES = {'dk_alert.xml': (2048, 2048), 'dk_saw.xml': (4096, 4096)}

# ---------- 1) 图集补 width/height ----------
for root in ROOTS:
    for fn, (w, h) in IMG_SIZES.items():
        p = os.path.join(root, 'images', fn)
        t = open(p, encoding='utf-8-sig').read()
        def repl(m):
            tag = m.group(0)
            if 'width=' in tag:
                return re.sub(r'width="\d+"', 'width="%d"' % w, tag)
            return tag[:-1] + ' width="%d" height="%d">' % (w, h)
        t2 = re.sub(r'<TextureAtlas[^>]*>', repl, t, count=1)
        if t2 != t:
            open(p, 'w', encoding='utf-8', newline='').write(t2)
            print('XML fixed', root.split('/')[-1], fn)
        else:
            print('XML ok   ', root.split('/')[-1], fn)

# ---------- 2~4) 重写 DK_Saw.lua ----------
new_lua = r'''--============================================================
--  DK_Saw.lua   GOD+ 锯子（QT v2.2 素材 / 事件驱动）  v11.4
--  DK_Duet / NovaFlare Engine   2026-11-16
--
--  QT 原版三下警报召唤锯子（用户实机口述）：
--    第一下 -> 1 个警告三角 + "噔"（alert）
--    第二下 -> 2 个警告三角 + "噔"（alert，与第一下同一个音）★从这下起按空格算躲
--    第三下 -> 3 个警告三角 + 锯子声（sawbladeHit）★第三下结束出锯
--  锯子从左边飞入；单锯。判定时机=锯心到 BF 屏幕 x。
--  唯一时钟 getSongPosition()(歌曲毫秒)，单回调，BotPlay 免疫。
--
--  v11.4 修复：
--   * v11.3 里 ensureSaw() 从未被调用 -> 锯子精灵根本不存在（"没从左边出现"）。
--     现 onEvent 立即 ensureSaw。
--   * 图集 dk_alert.xml/dk_saw.xml 补 width/height，修动态加载静默失败（"告示牌没出现"）。
--   * 音效改为前两下同一声 alert、第三下 sawbladeHit。
--
--  谱面事件 "DK Saw"：value1=方向(left/right/both)；value2=数量 1~4
--============================================================

local SAW_TAG    = 'DK Saw'
local IMG_SAW    = 'dk_saw'
local IMG_ALERT  = 'dk_alert'

local ALERT_GAP  = 450
local WARN_COUNT = 3
local FLY_MS     = 1200
local MULTI_GAP  = 420
local HIT_X      = 430
local SAW_SCALE  = 0.60
local ALERT_SCALE= 0.70
local SCREEN_W, SCREEN_H = 1280, 720

local sawTag   = 'dkSawSprite'
local alertTag = 'dkAlertSprite'
local spriteReady = {saw = false, alert = false}

local waves = {}
local started = false

local function songMs()
    local ok, v = pcall(getSongPosition)
    if ok and type(v) == 'number' then return v end
    return 0
end
local function gv(name, default)
    if type(getVar) ~= 'function' then return default end
    local ok, v = pcall(getVar, name)
    if not ok or v == nil then return default end
    return v
end
local function sv(name, value)
    if type(setVar) == 'function' then pcall(setVar, name, value) end
end
local function sp(key, value) pcall(setProperty, key, value) end
local function exists(tag)
    if type(luaSpriteExists) ~= 'function' then return true end
    local ok, v = pcall(luaSpriteExists, tag)
    return ok and v == true
end
local function botPlaying()
    if gv('botPlay', false) == true then return true end
    local ok, v = pcall(getProperty, 'cpuControlled')
    return ok and v == true
end

local function ensureSaw()
    if spriteReady.saw and exists(sawTag) then return true end
    pcall(makeAnimatedLuaSprite, sawTag, IMG_SAW, 0, 0)
    if not exists(sawTag) then return false end
    pcall(addAnimationByPrefix, sawTag, 'idle', 'dkSaw_idle', 24, true)
    pcall(addAnimationByPrefix, sawTag, 'move', 'dkSaw_move', 24, true)
    pcall(setObjectCamera, sawTag, 'camGame')
    sp(sawTag .. '.scale.x', SAW_SCALE)
    sp(sawTag .. '.scale.y', SAW_SCALE)
    sp(sawTag .. '.alpha', 0)
    pcall(addLuaSprite, sawTag, true)
    spriteReady.saw = true
    return true
end
local function ensureAlert()
    if spriteReady.alert and exists(alertTag) then return true end
    pcall(makeAnimatedLuaSprite, alertTag, IMG_ALERT, 0, 0)
    if not exists(alertTag) then return false end
    for _, pre in ipairs({'single', 'double', 'triple', 'quad'}) do
        pcall(addAnimationByPrefix, alertTag, pre, 'dkAlert_' .. pre, 12, true)
    end
    pcall(setObjectCamera, alertTag, 'camGame')
    sp(alertTag .. '.scale.x', ALERT_SCALE)
    sp(alertTag .. '.scale.y', ALERT_SCALE)
    local aw = 256 * ALERT_SCALE
    sp(alertTag .. '.x', (SCREEN_W - aw) / 2)
    sp(alertTag .. '.y', (SCREEN_H - aw) / 2 - 70)
    sp(alertTag .. '.alpha', 0)
    pcall(addLuaSprite, alertTag, true)
    spriteReady.alert = true
    return true
end

local function alertPrefix(n)
    if n >= 4 then return 'quad' end
    if n == 3 then return 'triple' end
    if n == 2 then return 'double' end
    return 'single'
end
-- 前两下同一个"噔"(alert)；第三下锯子声(sawbladeHit)；多锯不细分
local function alertSfx(n)
    if n >= 3 then return 'sawbladeHit' end
    return 'alert'
end

-- 播第 n 下警报：警告牌 n 个三角 + 对应音 + 轻红闪兜底
local function playAlert(n)
    if ensureAlert() then
        sp(alertTag .. '.alpha', 1)
        pcall(playAnim, alertTag, alertPrefix(n), true)
    end
    pcall(playSound, alertSfx(n), 0.95)
    pcall(cameraFlash, 'game', 'FF4444', 0.14, true)
end

function onEvent(name, value1, value2)
    if name ~= SAW_TAG then return end
    local dir = string.lower(tostring(value1 or ''))
    if dir ~= 'left' and dir ~= 'right' and dir ~= 'both' then dir = 'left' end
    local count = math.floor(tonumber(value2) or 1)
    if count < 1 then count = 1 end
    if count > 4 then count = 4 end

    -- 立即创建两只精灵（v11.3 漏掉这步 -> 锯子从没出现）
    ensureAlert()
    ensureSaw()

    local now = songMs()
    local sawW = 1416 * SAW_SCALE
    local alertAt = {}
    for i = 1, WARN_COUNT do alertAt[i] = now + (i - 1) * ALERT_GAP end
    local sawStart = now + WARN_COUNT * ALERT_GAP
    local wave = {
        alertAt = alertAt, alertIdx = 0,
        dodgeOpenAt = alertAt[2], dodgeOpen = false, dodged = false,
        saws = {}
    }
    for i = 1, count do
        local d = (dir == 'both') and ((i % 2 == 1) and 'left' or 'right') or dir
        local startAt = sawStart + (i - 1) * MULTI_GAP
        local fromX, toX
        if d == 'left' then
            fromX, toX = SCREEN_W + sawW, -sawW * 0.3      -- 从右飞向左
        else
            fromX, toX = -sawW * 0.7, SCREEN_W + sawW      -- 从左飞向右
        end
        local centerFrom = fromX + sawW / 2
        local centerTo   = toX + sawW / 2
        local ratio = (centerFrom - HIT_X) / (centerFrom - centerTo)
        if ratio < 0.02 then ratio = 0.02 end
        if ratio > 0.98 then ratio = 0.98 end
        wave.saws[#wave.saws + 1] = {
            dir = d, fromX = fromX, toX = toX,
            startAt = startAt, hitAt = startAt + FLY_MS * ratio,
            hitDone = false, dodged = false
        }
    end
    waves[#waves + 1] = wave
    started = true
    sv('dkSawCount', (gv('dkSawCount', 0) or 0) + 1)
end

local function resolveHit(saw)
    if botPlaying() or saw.dodged or gv('dkDodgeActive', false) == true then
        pcall(playSound, 'dodge01', 0.9)
        sv('dkSawDodged', true)
        return
    end
    sp('health', 0)
    pcall(cameraFlash, 'game', 'FF2020', 0.5, true)
    pcall(playSound, 'sawbladeHit', 1)
    sv('dkSawKilled', true)
end

local function update()
    if not started then return end
    local now = songMs()
    for wi = 1, #waves do
        local w = waves[wi]
        while w.alertIdx < WARN_COUNT and now >= w.alertAt[w.alertIdx + 1] do
            w.alertIdx = w.alertIdx + 1
            playAlert(w.alertIdx)
        end
        if not w.dodgeOpen and now >= w.dodgeOpenAt then w.dodgeOpen = true end
        if w.dodgeOpen and (not w.dodged) and gv('dkDodgeActive', false) == true then
            w.dodged = true
            for si = 1, #w.saws do w.saws[si].dodged = true end
            sv('dkSawDodged', true)
        end
        if w.alertIdx >= WARN_COUNT and now >= w.alertAt[WARN_COUNT] + ALERT_GAP * 0.8
           and spriteReady.alert then
            sp(alertTag .. '.alpha', 0)
        end
        for si = 1, #w.saws do
            local s = w.saws[si]
            if now >= s.startAt and now <= s.startAt + FLY_MS then
                local p = (now - s.startAt) / FLY_MS
                local x = s.fromX + (s.toX - s.fromX) * p
                if ensureSaw() then
                    sp(sawTag .. '.x', x)
                    sp(sawTag .. '.y', SCREEN_H * 0.58)
                    sp(sawTag .. '.alpha', 1)
                    pcall(playAnim, sawTag, 'move', true)
                end
            end
            if (not s.hitDone) and now >= s.hitAt then
                s.hitDone = true
                resolveHit(s)
            end
        end
    end
    local keep = {}
    for wi = 1, #waves do
        local w = waves[wi]
        local done = true
        for si = 1, #w.saws do
            if not w.saws[si].hitDone then done = false end
        end
        if not done then keep[#keep + 1] = w end
    end
    waves = keep
end

function onUpdate() update() end

function onEndSong()
    waves = {}
    started = false
    if spriteReady.saw then sp(sawTag .. '.alpha', 0) end
    if spriteReady.alert then sp(alertTag .. '.alpha', 0) end
end
function onDestroy()
    if spriteReady.saw then pcall(removeLuaSprite, sawTag, true) end
    if spriteReady.alert then pcall(removeLuaSprite, alertTag, true) end
    spriteReady.saw, spriteReady.alert = false, false
    onEndSong()
end
'''

open(SRC, 'w', encoding='utf-8', newline='').write(new_lua)
import hashlib
print('DK_Saw.lua written, md5', hashlib.md5(new_lua.encode()).hexdigest())

# ---------- 部署脚本到三处 ----------
for root in ROOTS:
    p = os.path.join(root, 'scripts', 'DK_Saw.lua')
    open(p, 'w', encoding='utf-8', newline='').write(new_lua)
    print('deployed', root.split('/')[-1])
