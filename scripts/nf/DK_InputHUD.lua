--============================================================
--  DK_InputHUD.lua  v5   DK_Duet / NovaFlare Engine  (2026-11-21)
--
--  ① 按下延迟显示（游戏内）：
--     每次玩家按下音符，屏幕下方显示 实际按下时刻 - 音符应到时刻
--     （正 = 按晚了，负 = 按早了，单位 ms）。
--       ±45ms 内绿色 / ±90ms 内黄色 / 其余红色，0.8 秒后淡出。
--     v4：BOTPLAY（含 BOTPLAY Pro）也显示 —— 用于看 BPP/代打器命中时机。
--     v5：就绪提示带版本号「延迟显示v5就绪」，重启后一眼确认新版已加载
--         （16:48 那局实测还是旧进程：debug 报告里无 ReceptorFreeze，
--          全局脚本只在游戏启动时加载，改完不重启 = 一直跑旧版）。
--     进歌后屏幕下方短暂显示就绪提示，证明本脚本已加载。
--
--  ② F8 快速重来（游戏内）：
--     v1 用 onKeyPress —— NF 引擎根本没有这个回调（源码 grep 证实，
--     callOnLuas/callOnScripts 只派发 goodNoteHit/noteMiss/onUpdate/
--     onEvent 等，无 onKeyPress）→ 永不触发。v2 改用 onUpdate +
--     keyboardJustPressed('F8')（与 BOTPLAY_Pro 的 F1/F2 同一条
--     实测可靠路径），重开走 PauseSubState.restartSong(true)
--     （public static，callMethodFromClass 可调；NF fork 复用已解码
--     音频，不重新加载）。菜单里按了没反应。
--
--  引擎 API 核对（NF 源码逐个 grep）：keyboardJustPressed(ExtraFunctions:17)
--  / callMethodFromClass(ReflectionFunctions:195，签名 类名,方法名,参数)
--  / makeLuaText、setTextString、setTextColor、setTextSize、
--  setTextAlignment、setObjectCamera、addLuaText(TextFunctions)
--  / getPropertyFromGroup(ReflectionFunctions:110) / getSongPosition
--  (FunkinLua:989) / goodNoteHit 派发于 note 销毁前(PlayState.hx:4873
--  在 invalidateNote 之前，indexOf 有效)。
--============================================================

local TAG      = 'dkDev'
local FADE_MS  = 800
local RESTART_KEY = 'F8'

local made     = false
local shownAt  = -1e9
local clock    = 0
local lastF8   = -1e9

local function gp(key, default)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return default end
    return v
end

local function sp(key, value)
    pcall(setProperty, key, value)
end

-- botplay 检测（与 DK_God.lua 同一套）
local function botPlaying()
    local ok, v = pcall(getProperty, 'cpuControlled')
    if ok and v == true then return true end
    if type(getVar) == 'function' then
        local ok2, v2 = pcall(getVar, 'botPlay')
        if ok2 and v2 == true then return true end
    end
    return false
end

local function ensureText()
    if made then return end
    made = true
    local sw, sh = 1280, 720
    local okw, w = pcall(getProperty, 'camHUD.width')
    if okw and w then sw = w end
    local okh, h = pcall(getProperty, 'camHUD.height')
    if okh and h then sh = h end
    pcall(makeLuaText, TAG, '', 400, (sw - 400) / 2, sh - 90)
    pcall(setTextSize, TAG, 26)
    pcall(setTextAlignment, TAG, 'center')
    pcall(setObjectCamera, TAG, 'camHUD')
    pcall(addLuaText, TAG)
    sp(TAG .. '.alpha', 0)
end

-- 进歌：显示「就绪」证明脚本已加载（3 秒后淡出）
function onCreatePost()
    ensureText()
    pcall(setTextString, TAG, '延迟显示v5就绪 | F8重来')
    pcall(setTextColor, TAG, '66AAFF')
    sp(TAG .. '.alpha', 0.6)
    shownAt = -1e9   -- 就绪提示走 clock 淡出
    clock = 0
end

-- 玩家命中：真实按键时刻 = 引擎触发本回调的时刻（songPosition）
-- v4：去掉 botplay 闸门 —— BPP（BOTPLAY Pro）开cpuControlled 时也显示
--     （用户要看 BPP/代打器的命中时机数字），只保留归属与长按过滤。
function goodNoteHit(id, dir, noteType, isSustain)
    -- ① 长按尾帧不算按键（sustain 持续派发，会把数字刷成串）
    if isSustain then return end
    -- ② NF 引擎对手侧命中也会派发 goodNoteHit —— 只认玩家自己的音符，
    --    否则对手开唱时延迟数字狂蹦（「不开始的都来了」的根因）
    local okMP, must = pcall(getPropertyFromGroup, 'notes', id, 'mustPress')
    if not okMP or must ~= true then return end
    local ok, st = pcall(getPropertyFromGroup, 'notes', id, 'strumTime')
    if not ok or st == nil then return end
    st = tonumber(st)
    if st == nil then return end
    local pos = tonumber(gp('songPosition', nil))
    if pos == nil then return end
    local dev = pos - st

    ensureText()
    local a = math.abs(dev)
    local col
    if a <= 45 then
        col = '00FF66'   -- 准
    elseif a <= 90 then
        col = 'FFD400'   -- 偏
    else
        col = 'FF3333'   -- 歪
    end
    local dirName = ({['0'] = '左', ['1'] = '下', ['2'] = '上', ['3'] = '右'})[tostring(dir)] or '?'
    local word = dev >= 0 and '晚' or '早'
    pcall(setTextString, TAG,
        string.format('%s键 %s%+dms', dirName, word, math.abs(math.floor(dev + 0.5))))
    pcall(setTextColor, TAG, col)
    sp(TAG .. '.alpha', 1)
    local okp, p = pcall(getSongPosition)
    if okp and tonumber(p) then shownAt = tonumber(p) end
end

function onUpdate(elapsed)
    clock = clock + (tonumber(elapsed) or 0.016)

    -- F8 快速重来（NF 真实回调路径：onUpdate + keyboardJustPressed）
    local okK, pressed = pcall(keyboardJustPressed, RESTART_KEY)
    if okK and pressed and (clock - lastF8) > 0.25 then
        lastF8 = clock
        -- 首选：PauseSubState.restartSong(true)（public static，noTrans 直接重置）
        local okR = pcall(callMethodFromClass, 'substates.PauseSubState',
                          'restartSong', {true})
        if not okR then
            pcall(callMethod, 'restartSong', {true})
        end
        return
    end

    if not made then return end
    -- 淡出：命中偏差显示 0.8s（歌曲时间）；就绪提示 3s（clock 时间）
    local a = tonumber(gp(TAG .. '.alpha', 0)) or 0
    if a <= 0 then return end
    local okp, p = pcall(getSongPosition)
    local pos = (okp and tonumber(p)) or 0
    local expired = (shownAt > -1e8) and ((pos - shownAt) > FADE_MS)
                    or (shownAt <= -1e8 and clock > 3.0)
    if expired then
        sp(TAG .. '.alpha', math.max(0, a - (tonumber(elapsed) or 0.016) * 2.5))
    end
end
