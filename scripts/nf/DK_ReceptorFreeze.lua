--============================================================
--  DK_ReceptorFreeze.lua  v2  DK_Duet / NovaFlare  (2026-11-21)
--
--  F4 = 关闭所有人的回收动画（判定箭头的 confirm / 回弹）
--
--  v2 修正：v1 在 onUpdate 里压 static —— 但 NF 引擎派发顺序是
--    onUpdate(PlayState.hx:2520) → 音符命中(2663~2676，此处播放
--    confirm) → onUpdatePost(2762)。
--    所以 v1 压完 static 后，同一帧引擎又把 confirm 盖回来，
--    对手侧（每拍都在唱）看起来就像完全没生效。
--  v2 改在 onUpdatePost 压 static：命中处理之后、渲染之前，
--    玩家侧 + 对手侧的 confirm 当帧即被压掉（0 帧存活）。
--
--  开：玩家侧+对手侧全部箭头压回 static 帧（0..8 兼容多键谱），
--      打击、判定、计分、音符滚动完全不受影响。
--  关：恢复引擎原速动画，下一帧自动继续，无需重启。
--  ⚠ 全局脚本游戏启动时加载 —— 改完必须重启游戏才生效。
--============================================================

local TAG = 'dkRecvFreeze'
local TOGGLE_KEY = 'F4'

local enabled = false
local made   = false
local clock  = 0
local lastF4 = -1e9

local function ensureText()
    if made then return end
    made = true
    pcall(makeLuaText, TAG, '', 300, 8, 8)
    pcall(setTextSize, TAG, 18)
    pcall(setTextColor, TAG, 'FF5555')
    pcall(setObjectCamera, TAG, 'camHUD')
    pcall(addLuaText, TAG)
    pcall(setProperty, TAG .. '.alpha', 0)
end

local function setAllStatic()
    -- 玩家侧 + 对手侧全部箭头压回 static（0..8 兼容多键，pcall 静默跳过不存在的轨）
    for side, group in ipairs({'playerStrums', 'opponentStrums'}) do
        for i = 0, 8 do
            pcall(callMethod, group .. '.members[' .. i .. '].playAnim', {'static', true})
        end
    end
end

function onCreatePost()
    ensureText()
end

function onUpdate(elapsed)
    clock = clock + (tonumber(elapsed) or 0.016)

    local okK, pressed = pcall(keyboardJustPressed, TOGGLE_KEY)
    if okK and pressed and (clock - lastF4) > 0.25 then
        lastF4 = clock
        enabled = not enabled
        ensureText()
        if enabled then
            pcall(setTextString, TAG, '回收动画v2: 关 (F4)')
            pcall(setProperty, TAG .. '.alpha', 0.75)
            setAllStatic()   -- 开启瞬间清掉现存 confirm
        else
            pcall(setProperty, TAG .. '.alpha', 0)   -- 恢复后隐藏提示
        end
        return
    end
end

-- 关键：onUpdatePost 在引擎命中处理（confirm 播放）之后派发，
-- 每帧末尾压回 static，confirm 连 1 帧都活不过去（双侧生效）。
function onUpdatePost(elapsed)
    if enabled then
        setAllStatic()
    end
end
