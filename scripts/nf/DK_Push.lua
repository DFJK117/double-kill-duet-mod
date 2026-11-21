--============================================================
--  DK_Push.lua  v1      DK_Duet / NovaFlare Engine   (2026-11-15)
--
--  对手推条：对手每命中一个音符，就把血条往对手侧推一格。
--  ★ 与引擎自带 healthDrainOPPO 的区别：
--    引擎 PlayState.hx 的 healthDrainOPPO 写死了
--        if (health <= 0.4) health = 0.4;
--    —— 有 0.4 保底，永远推不死。本脚本直接改 game.health，
--    没有下限，能一路推到 0，由 PlayState.doDeathCheck(health <= 0)
--    正常触发 Game Over（练习模式 practiceMode 下引擎仍会免死，
--    这是引擎既定行为，不改）。
--
--  ★「不要很逆天」的三道保险：
--    ① 长音尾 (isSustainNote) 完全不扣，避免拖尾反复刷扣血；
--    ② 和弦节流：同一小段时间内的多个对手音符只结算一次；
--    ③ 默认 normal 档，每次 -0.026 / 最短间隔 0.075s，
--       即最多约 0.35 血/秒，从满血推到死需要连续几秒对手段，
--       不是一瞬间清空。玩家自己命中仍正常回血，能拉锯。
--
--  F3 = 开 / 关（默认开）
--  事件 "DK Push": value1 = off/on/toggle/soft/normal/hard
--                  value2 = 每次扣血量（可选，覆盖档位默认值）
--  状态发布: dkPushEnabled / dkPushMode / dkPushAmount
--
--  纯 Lua、零 hscript。使用的引擎 API 都在 FunkinLua.hx 里核对过：
--  addHealth (902)、getProperty/setProperty (ReflectionFunctions.hx)、
--  keyboardJustPressed/keyboardPressed (ExtraFunctions.hx)、setVar。
--============================================================

local PUSH_TAG  = 'DK Push'
local TOGGLE_KEY = 'F3'

-- 档位：amount = 每次扣血量，gap = 最短结算间隔（秒，按累计帧时间）
local MODES = {
    soft   = {amount = 0.018, gap = 0.110},
    normal = {amount = 0.026, gap = 0.075},
    hard   = {amount = 0.040, gap = 0.050},
}

local enabled      = true
local mode         = 'normal'
local customAmount = nil
local clock        = 0
local lastPushAt   = -1e9
local lastToggle   = -1e9
local pushCount    = 0

local function gp(key, default)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return default end
    return v
end
local function sv(name, value)
    if type(setVar) == 'function' then pcall(setVar, name, value) end
end
local function publish()
    sv('dkPushEnabled', enabled)
    sv('dkPushMode', mode)
    sv('dkPushAmount', customAmount or (MODES[mode] or MODES.normal).amount)
end
local function setEnabled(on)
    enabled = (on == true)
    publish()
end
local function setMode(m)
    if MODES[m] then
        mode = m
        customAmount = nil
    end
    publish()
end

--============================================================
--  对手命中回调
--  引擎 PlayState.hx: opponentNoteHit 里
--    callOnLuas('opponentNoteHit', [id, noteData, noteType, isSustainNote])
--  duet 谱面里 gf / 'Opponent 2 Sing' 的音符同样会走这里，一并结算。
--============================================================
function opponentNoteHit(id, direction, noteType, isSustainNote)
    if not enabled then return end
    -- GOD 模式免疫推条（DK_God.lua 写入 dkGodMode）
    local okGod, godVal = pcall(getVar, 'dkGodMode')
    if okGod and godVal == true then return end
    -- 长音尾不重复扣
    if isSustainNote == true or isSustainNote == 1 or isSustainNote == 'true' then return end

    local cfg = MODES[mode] or MODES.normal
    if (clock - lastPushAt) < cfg.gap then return end
    lastPushAt = clock

    local h = tonumber(gp('health', 1)) or 1
    if h <= 0.001 then return end   -- 已经推到死，别再刷负数

    local amount = tonumber(customAmount) or cfg.amount
    if amount > h then amount = h end
    if amount <= 0 then return end

    -- addHealth = game.health += value，会走 set_health 同步血条与 icon
    pcall(addHealth, -amount)
    pushCount = pushCount + 1
    sv('dkPushCount', pushCount)
end

--============================================================
--  事件 + F3
--============================================================
function onEvent(name, value1, value2)
    if name ~= PUSH_TAG then return end
    local v = string.lower(tostring(value1 or ''))
    if v == 'off' or v == '0' or v == 'false' or v == 'no' then
        setEnabled(false)
    elseif v == 'on' or v == '1' or v == 'true' or v == 'yes' then
        setEnabled(true)
    elseif v == 'soft' or v == 'normal' or v == 'hard' then
        setEnabled(true)
        setMode(v)
    elseif v == 'toggle' or v == '' then
        setEnabled(not enabled)
    elseif tonumber(v) then
        -- value1 也可以是数值：直接当每次扣血量
        local a = tonumber(v)
        if a and a > 0 and a <= 0.2 then customAmount = a end
        setEnabled(true)
    end
    local v2 = tonumber(value2)
    if v2 and v2 > 0 and v2 <= 0.2 then
        customAmount = v2
        publish()
    end
end

local function tick(elapsed)
    clock = clock + (tonumber(elapsed) or 0)
    local ok, pressed = pcall(keyboardJustPressed, TOGGLE_KEY)
    if ok and pressed and (clock - lastToggle) > 0.15 then
        lastToggle = clock
        setEnabled(not enabled)
    end
end
function onUpdate(elapsed) tick(elapsed) end

function onCreatePost()
    publish()
end
