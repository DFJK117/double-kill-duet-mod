--============================================================
--  DK_RatingFall.lua  v1  DK_Duet / NovaFlare  (2026-11-21)
--
--  评分贴图（SICK! 评级图 / combo 字样 / combo 数字）下落消失：
--  NF 引擎 popUpScore 只做原地淡出（FlxTween alpha→0，
--  PlayState.hx:4020 起），没有任何位移 —— 本脚本补上重力下落。
--
--  实现：
--   · onCreatePost 记录 comboGroup 6 个成员的基准坐标
--     （comboGroup.members[0]=评级图 [1]=combo字样 [2..5]=combo数字）
--   · goodNoteHit / opponentNoteHit 回调（引擎在 popUpScore 之后
--     派发）→ 把贴图复位到基准坐标并记录下落起始时刻（每次命中
--     重新开始，因为引擎不复位坐标，不复位会越落越低）
--   · onUpdatePost → 按重力加速度 2800px/s² 下落（0.5*a*t²），
--     带轻微横向漂移；引擎自身的 alpha 淡出（0.6s 后 0.4s 淡完）
--     负责消失，落+淡组合 = 下落消失。
--  ⚠ 全局脚本游戏启动时加载 —— 改完必须重启游戏才生效。
--============================================================

local N        = 6        -- comboGroup 成员数
local GRAVITY  = 2800     -- px/s^2
local DRIFT    = 45       -- 横向漂移 px/s（按次随机方向）
local MAX_T    = 1.6      -- 下落秒数上限（之后不再追）

local baseX = {}
local baseY = {}
local haveBase = false
local fallStart = nil     -- songPosition（ms）；nil = 不在下落
local fallDir   = 1

local function songPos()
    local ok, v = pcall(getProperty, 'songPosition')
    if ok and type(v) == 'number' then return v end
    return nil
end

local function captureBase()
    if haveBase then return end
    local okN, cnt = pcall(getProperty, 'comboGroup.members.length')
    if not okN or not cnt or cnt < 2 then return end
    for i = 0, cnt - 1 do
        local okx, x = pcall(getPropertyFromGroup, 'comboGroup', i, 'x')
        local oky, y = pcall(getPropertyFromGroup, 'comboGroup', i, 'y')
        if okx and oky and x ~= nil and y ~= nil then
            baseX[i] = x
            baseY[i] = y
        end
    end
    haveBase = true
end

local function resetToBase()
    for i = 0, N - 1 do
        if baseX[i] ~= nil then
            pcall(setPropertyFromGroup, 'comboGroup', i, 'x', baseX[i])
            pcall(setPropertyFromGroup, 'comboGroup', i, 'y', baseY[i])
        end
    end
end

function onCreatePost()
    captureBase()
end

-- 命中回调（双侧都派发；对手侧可能以 goodNoteHit 名义来
-- —— opponentCodeFix 开关 —— 所以 goodNoteHit 里不做归属过滤）
local function onAnyHit(isSustain)
    if isSustain then return end
    captureBase()
    local pos = songPos()
    if pos == nil then return end
    -- 复位到基准坐标（清掉上一次的下落位移），再开始新一轮下落
    resetToBase()
    fallStart = pos
    fallDir = (math.random(0, 1) == 0) and -1 or 1
end

function goodNoteHit(id, dir, noteType, isSustain)
    onAnyHit(isSustain)
end

function opponentNoteHit(id, dir, noteType, isSustain)
    onAnyHit(isSustain)
end

function onUpdatePost(elapsed)
    if fallStart == nil then return end
    local pos = songPos()
    if pos == nil then return end
    local t = (pos - fallStart) / 1000.0
    if t > MAX_T then
        fallStart = nil
        return
    end
    local dy = 0.5 * GRAVITY * t * t
    local dx = DRIFT * fallDir * t
    for i = 0, N - 1 do
        if baseX[i] ~= nil then
            pcall(setPropertyFromGroup, 'comboGroup', i, 'y', baseY[i] + dy)
            pcall(setPropertyFromGroup, 'comboGroup', i, 'x', baseX[i] + dx)
        end
    end
end
