--============================================================
--  BOTPLAY Pro (bpp)  v8      DK_Duet / NovaFlare Engine
--  v8(2026-11-21): 判定线回收动画【完全不播放】(用户点名: 不是速度快,
--      是直接不播)。引擎 playAnim('confirm') 后, onUpdate/onUpdatePost
--      每帧立即压回 static —— confirm 最多存活 1 帧, 实际不可见。
--      F2 变成 完全禁播(NONE, 默认) <-> 原速播放(NORMAL) 两档。
--  署名：DFJK117（名字，不是键位）   真实键位：A S J K
--
--  F1 = 自动打谱开关（默认关，不显示状态、不加 HUD 文字）
--  F2 = 回收动画切换：NONE(完全不播, 默认) <-> NORMAL(引擎原速 24fps)
--  事件 "BOTPLAY Pro"          1/on 开，0/off 关，留空 切换
--  事件 "BOTPLAY Pro Recycle"  1/on/normal = 原速播放，0/off/none = 完全不播(默认)，
--                               留空 切换
--  事件 "BOTPLAY Pro Map"      value1 = A,S,J,K（上传按键映射）
--                               value2 = 'acc=0' 关掉按压时长随 acc 联动
--
--  ============ v4 修了什么（用户反馈：自动没有用 / 还报错 / 开关回收动画）============
--  【死因 1：自动没有用】v3 开启时把 cpuControlled 设成 false，指望用
--    runHaxeCode('game.keyPressed(dir)') 自己注入按键。但引擎 PlayState.hx:4072
--    的 keyPressed 是 **private**，hscript 根本调不到；而 HScriptBase 的
--    runHaxeCode 内部自己 try/catch 把错误吞了、不往 Lua 抛，于是
--    pcall(runHaxeCode, code) 永远返回 ok=true -> INJECT 永远不降级。
--    结果：引擎不自动打(cpuControlled=false)，脚本又没真的按下去 -> 全 miss。
--    v4 改为直接 sp('cpuControlled', true)：走引擎 PlayState.hx:2662 的
--    goodNoteHit 原生自动打谱，音符真命中、自带箭头 confirm 与 BF 唱歌动画，
--    100% 可靠，且 0 行 hscript（17:41~18:17 那 4 次 native crash 全部来自
--    hscript 对 game 上不存在的数组做下标写，此路永久封死）。
--
--  【死因 2：还报错】v3 的 doRelease 调 playerStrums.playStatic —— 引擎
--    StrumNote 里压根没有这个方法（只有 playAnim + resetAnim），每次松键
--    都在刷一条报错。v4 全部换成引擎真有的 API：playAnim('static', true)
--    + setProperty('...resetAnim', 0)。
--
--  【死因 3：开关回收动画】F1 / 事件开关时，把 4 个箭头强制复位到 static
--    （resetAnim 清零），BF 回 idle(dance)，清掉上一轮遗留的 confirm 常亮，
--    并重置 active / seen / 统计。到期松键也逐轨回收。
--
--  ============ v8（2026-11-21）：回收动画完全不播放 ============
--    recycleMode='NONE'（默认）：每帧把 confirm 压回 static，零播放。
--    recycleMode='NORMAL'：原速自然回收。按压时长统一 40~60ms。
--
--  ============ v5（2026-11-15 早）：F2 关掉回收动画 ============
--    recycleEnabled=false 时整段跳过回收，confirm 常亮。用户后来改口：
--    「算了播放吧，但是速度快如逆天行不？」—— v5 这个状态已撤销。
--
--  ============ v6（2026-11-15 晚）：F2 = 回收速度 TURBO / NORMAL ============
--    recycleMode='TURBO'（默认）：
--      ① 按压时长压到 TURBO_HOLD（12~20ms，约 1 帧），
--      ② 回收时把 confirm 动画的 frameRate 拉到 240（整段 2~4 帧在
--         0.02 秒内播完）并把 resetAnim 设成 0.001（StrumNote.update
--         下一帧自动 playAnim('static')）。
--      引擎 PlayState.hx:5386 的 spr.playAnim('confirm', true) 与
--      StrumNote.hx 的 resetAnim 倒计时都照常执行 —— 动画真播了，
--      只是快如逆天；绝不跳过、绝不留下 confirm 常亮。
--    recycleMode='NORMAL'：沿用 v4 行为（40~60ms 按压 + 24fps 自然回收）。
--    两种模式都发布 bppRecycle / bppRecycleMode，事件可远程切档。
--    注：tick 同时挂在 onUpdate / onUpdatePost，F1/F2 都靠累计帧时间
--    clock 去重（>0.15s），同一帧内不会被切两次导致「按键像失灵」。
--
--  计分说明：引擎 popUpScore(PlayState.hx:3910) 在 cpuControlled=true 时
--    **不** 累加 songScore / songHits / ratingPercent（这是引擎既定行为），
--    所以分数、acc、评级全部由本脚本自己算，并用 addScore 写回引擎 scoreTxt，
--    HUD 与 icons.lua 读到的 bppScore/bppAcc 保持一致，不会出现「两张皮」。
--============================================================

local TAG         = 'BOTPLAY Pro'
local MAP_TAG     = 'BOTPLAY Pro Map'
local RECYCLE_TAG = 'BOTPLAY Pro Recycle'
local TOGGLE_KEY  = 'F1'
local RECYCLE_KEY = 'F2'
local EARLY       = 4
local LATE        = 140
local HOLD_MIN    = 40
local HOLD_MAX    = 60

local enabled, origCpu = false, false
local accLink = true
local keyMap  = {'A', 'S', 'J', 'K'}
local recycleMode = 'NONE'        -- v8: 'NONE'(完全不播, 默认) / 'NORMAL'(原速)

local HUD_TAG  = 'bppHud'
local hudMade  = false
-- v4：改用「累计帧时间」去重，不再用歌曲位置。
-- 旧版用 getSongPosition 去重，倒计时/暂停时歌曲位置不动 -> 按过一次 F1 之后
-- 就再也切不动（开关按键像是失灵）。累计时间不受歌曲状态影响。
local clock        = 0
local lastToggle   = -1e9
local lastRecycle  = -1e9

local active  = {}   -- [1..4] = {releaseAt = 歌曲毫秒}
local seen    = {}   -- 已处理过的音符（不用 wasGoodHit，见 v2 注释）

local S = {score = 0, hits = 0, total = 0, combo = 0,
           misses = 0, weighted = 0, keyCount = 0}

local rngState = 20261108
local function rnd()
    rngState = (rngState * 48271) % 2147483647
    return rngState / 2147483647
end
local function clamp(v, a, b)
    if v < a then return a end
    if v > b then return b end
    return v
end

local function gp(key, default)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return default end
    return v
end
local function sp(key, value)
    pcall(setProperty, key, value)
end
local function sv(name, value)
    if type(setVar) == 'function' then pcall(setVar, name, value) end
end
local function ngp(i, field, default)
    local ok, v = pcall(getPropertyFromGroup, 'notes', i, field)
    if not ok or v == nil then return default end
    return v
end
local function nflag(i, field)
    local v = ngp(i, field, false)
    return v == true or v == 1 or v == 'true'
end
local function nnum(i, field, default)
    return tonumber(ngp(i, field, default)) or default
end

-- Complements.lua 会在 botplay 时把 scoreTxt 一起 alpha->0，每帧抢回来
local function ensureScoreVisible()
    sp('scoreTxt.visible', true)
    sp('scoreTxt.alpha', 1)
end

-- 右下角开关提示：开启时显示 "ABCOX"（纯显示，无含义），关闭隐藏。
local function ensureHud()
    if hudMade then return end
    hudMade = true
    pcall(makeLuaText, HUD_TAG, 'ABCOX', 0, 0, 0)
    pcall(setTextSize, HUD_TAG, 22)
    pcall(setTextColor, HUD_TAG, 'FFFFFF')
    pcall(setTextBorder, HUD_TAG, 2, '000000')
    pcall(setObjectCamera, HUD_TAG, 'camOther')
    pcall(addLuaText, HUD_TAG)
    local sw, sh = 1280, 720
    local okw, w = pcall(getProperty, 'camOther.width')
    if okw and w then sw = w end
    local okh, h = pcall(getProperty, 'camOther.height')
    if okh and h then sh = h end
    pcall(setProperty, HUD_TAG .. '.x', sw - 110)
    pcall(setProperty, HUD_TAG .. '.y', sh - 30)
    pcall(setProperty, HUD_TAG .. '.visible', false)
end
local function setHud(on)
    ensureHud()
    pcall(setProperty, HUD_TAG .. '.visible', on == true)
end

local function currentAcc()
    if S.total <= 0 then return 100 end
    return clamp(S.weighted / S.total * 100, 0, 100)
end
local function currentRank(acc)
    if acc >= 95 then return 'P' end
    if acc >= 90 then return 'S' end
    if acc > 80 then return 'A' end
    if acc >= 70 then return 'G' end
    if acc >= 50 then return 'B' end
    if acc >= 30 then return 'F' end
    return 'BRO????'
end

-- 把当前统计发布给 HUD（icons.lua 会读），也供外部脚本 / 回放读取
local function publishStats()
    local acc = currentAcc()
    sv('bppScore',   S.score)
    sv('bppAcc',     acc)
    sv('bppRank',    currentRank(acc))
    sv('bppHits',    S.hits)
    sv('bppTotal',   S.total)
    sv('bppCombo',   S.combo)
    sv('bppMisses',  S.misses)
    sv('bppKeyCount', S.keyCount)
    return acc
end

-- 按压时长：v6 TURBO 档压到 12~20ms（约 1 帧），NORMAL 档沿用 40~60ms。
-- 中心随 acc 变化（acc 越高按得越短）；长音仍延长到尾，避免吞掉 sustain。
local function holdFor(acc, sustainMs)
    local lo, hi = HOLD_MIN, HOLD_MAX
    local t = clamp((tonumber(acc) or 100) / 100, 0, 1)
    local base = accLink and (hi - (hi - lo) * t) or ((lo + hi) / 2)
    local h = clamp(base + (rnd() * 2 - 1) * (hi - lo) * 0.5, lo, hi)
    if sustainMs and sustainMs > h and sustainMs < 4000 then h = sustainMs end
    return h
end

local function publishMap()
    for d = 1, 4 do
        sv('bppKey_' .. (d - 1), keyMap[d])
    end
    sv('bppKeyMap', table.concat(keyMap, ','))
end
local function applyMap(str)
    if type(str) ~= 'string' or str == '' then return false end
    local t = {}
    for part in string.gmatch(str, '[^,;|]+') do
        local k = string.match(part, '^%s*(.-)%s*$')
        if k ~= '' then t[#t + 1] = k end
    end
    if #t < 4 then return false end
    for d = 1, 4 do keyMap[d] = t[d] end
    publishMap()
    return true
end

--============================================================
--  动画回收：只用引擎确实存在的 API
--    StrumNote.playAnim('static', true) / resetAnim / animation.curAnim.frameRate
--    （v3 用的 playStatic 不存在，是「还报错」的元凶）
--
--  v6 关键改动：回收动画**永远播放**，只是速度不同。
--    TURBO（默认，快如逆天）：
--      把当前 confirm 动画帧率拉到 240（整段 2~4 帧在 0.02 秒内播完），
--      再把 resetAnim 压到 0.001 —— StrumNote.update 下一帧自动
--      playAnim('static')。动画真播了，肉眼几乎看不见，但绝不跳过。
--    NORMAL：不干预，交给引擎自己的 resetAnim 倒计时自然回收（约 0.15s）。
--  两档都依赖引擎的 resetAnim 兜底，任何路径解析失败都不会留下 confirm 常亮。
--============================================================
local function recycleLane(L)
    -- v8: 回收 = 压回 static，confirm 动画零播放时间
    local base = 'playerStrums.members[' .. L .. ']'
    if recycleMode == 'NONE' then
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
        pcall(setProperty, base .. '.resetAnim', 0)
    else
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
        pcall(setProperty, base .. '.resetAnim', 0.12)
    end
end

-- v8 核心：判定线动画完全不播放。引擎 goodNoteHit 播 confirm 后，
-- 本函数把该轨立即压回 static（onUpdate/onUpdatePost 双钩每帧扫，
-- confirm 最多存活 1 帧 ≈16ms，肉眼不可见；resetAnim=0 防引擎自动续播）。
local function killConfirm(L)
    local base = 'playerStrums.members[' .. L .. ']'
    local ok, an = pcall(getProperty, base .. '.animation.curAnim.name')
    if ok and an == 'confirm' then
        pcall(callMethod,  base .. '.playAnim', {'static', true})
        pcall(setProperty, base .. '.resetAnim', 0)
    end
end

-- 开关/切档时一次性回收全部 4 轨 + BF 回 idle，清掉残留 confirm 常亮
local function recycleAll()
    for L = 0, 3 do
        local base = 'playerStrums.members[' .. L .. ']'
        pcall(callMethod,  base .. '.playAnim', {'static', true})
        pcall(setProperty, base .. '.resetAnim', 0.001)
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
    end
    pcall(setProperty, 'boyfriend.holdTimer', 0)
    pcall(callMethod,  'boyfriend.dance', {})
end

-- v8: F2 / 事件共用的回收动画切换（NONE=完全不播 <-> NORMAL=原速）
local function setRecycle(turbo)
    recycleMode = (turbo == true) and 'NORMAL' or 'NONE'
    sv('bppRecycle', recycleMode == 'NORMAL')
    sv('bppRecycleMode', recycleMode)
    if recycleMode == 'NONE' then
        for L = 0, 3 do killConfirm(L) end   -- 切回禁播档立刻清掉现存 confirm
    else
        recycleAll()
    end
end

-- 松键：清理上报状态 + 该轨箭头回收（全部纯 Lua，零 hscript）
local function doRelease(d)
    local L = d - 1
    sv('bppKeyDown_' .. L, false)
    sv('bppKeyHeld_' .. L, false)
    recycleLane(L)
    active[d] = nil
end

-- 按下：真实「上报」模拟按键 —— Lua 全局 + 脚本事件总线 + 引擎事件
local function reportKey(d, holdMs, acc, pos)
    local L = d - 1
    local key = keyMap[d]
    S.keyCount = S.keyCount + 1
    sv('bppKeyDown_' .. L, true)
    sv('bppKeyHeld_' .. L, true)
    sv('bppKey_' .. L, key)
    sv('bppKeyHold_' .. L, holdMs)
    sv('bppKeyCount', S.keyCount)
    sv('bppLastKey', key)
    sv('bppLastHold', holdMs)
    sv('bppKeyEvent', string.format('%d|%s|%d|%.1f|%d',
        math.floor(pos), key, math.floor(holdMs), acc, L))
    if type(callOnLuas) == 'function' then
        pcall(callOnLuas, 'onBPPKey', {key, L, holdMs, acc, pos})
    end
    if type(triggerEvent) == 'function' then
        pcall(triggerEvent, 'BOTPLAY Pro Key', key, tostring(L))
    end
end

-- 上报 + 计分（命中本身交给引擎原生 cpuControlled，脚本不再碰输入通道）
local function reportVisual(lanes, holds, acc, pos)
    for d = 1, 4 do
        if lanes[d] then
            reportKey(d, holds[d] or HOLD_MIN, acc, pos)
        end
    end
end

local function resetStats()
    S = {score = 0, hits = 0, total = 0, combo = 0,
         misses = 0, weighted = 0, keyCount = 0}
    seen = {}
    active = {}
end

local function setEnabled(on)
    if on == enabled then return end
    enabled = on
    sv('bppRecycle', true)
    sv('bppRecycleMode', recycleMode)
    if enabled then
        origCpu = gp('cpuControlled', false) == true
        -- 引擎原生自动打谱：PlayState.hx:2662 goodNoteHit 真命中，
        -- 自带箭头 confirm + BF 唱歌动画，无需脚本注入按键。
        sp('cpuControlled', true)
        sp('botplayTxt.visible', false)
        sp('botPlayTxt.visible', false)
        resetStats()
        publishMap()
        sv('bppEnabled', true)
        publishStats()
        ensureScoreVisible()
        setHud(true)
        recycleAll()               -- 开：清掉上一次遗留的按键动画（F2 关掉时跳过）
    else
        for d = 1, 4 do if active[d] then doRelease(d) end end
        recycleAll()               -- 关：4 轨箭头复位 static + BF 回 idle（F2 关掉时跳过）
        sp('cpuControlled', origCpu)
        sv('bppEnabled', false)
        publishStats()
        ensureScoreVisible()
        setHud(false)
    end
end

function onEvent(name, value1, value2)
    if name == MAP_TAG then
        applyMap(value1)
        local v = string.lower(tostring(value2 or ''))
        if v == 'acc=0' or v == 'noacc' then accLink = false
        elseif v == 'acc=1' or v == 'acc' then accLink = true end
        return
    end
    -- v8: 事件远程控制回收动画（与 F2 等价）
    --   1/on/normal = NORMAL(原速播放)，0/off/none = NONE(完全不播)，留空 = 切换
    if name == RECYCLE_TAG then
        local v = string.lower(tostring(value1 or ''))
        if v == '1' or v == 'on' or v == 'true' or v == 'yes'
           or v == 'normal' or v == 'slow' then setRecycle(true)
        elseif v == '0' or v == 'off' or v == 'false' or v == 'no'
               or v == 'none' or v == 'turbo' or v == 'fast' then setRecycle(false)
        else setRecycle(recycleMode ~= 'NORMAL') end
        return
    end
    -- 兼容老谱面：v4 起只有「引擎原生自动打谱」一种模式，不再有注入开关。
    -- 收到该事件时重新同步 cpuControlled，避免被其它脚本改掉后自动打谱失效。
    if name == 'BOTPLAY Pro Inject' then
        if enabled then sp('cpuControlled', true) end
        sv('bppInject', false)
        return
    end
    if name ~= TAG then return end
    if value2 ~= nil and value2 ~= '' then applyMap(value2) end
    local v = string.lower(tostring(value1 or ''))
    if v == '1' or v == 'on' or v == 'true' or v == 'yes' then setEnabled(true)
    elseif v == '0' or v == 'off' or v == 'false' or v == 'no' then setEnabled(false)
    else setEnabled(not enabled) end
end

local function tick(elapsed)
    local pOk, rawPos = pcall(getSongPosition)
    local pos = (pOk and tonumber(rawPos)) or 0

    clock = clock + (tonumber(elapsed) or 0)

    -- F1：BPP 开关（clock 去重，避免 onUpdate + onUpdatePost 双调切两次）
    local kOk, kPress = pcall(keyboardJustPressed, TOGGLE_KEY)
    if kOk and kPress and (clock - lastToggle) > 0.15 then
        lastToggle = clock
        setEnabled(not enabled)
    end
    -- F2：回收动画切换 NONE(完全不播) <-> NORMAL(原速)（同一套去重）
    local rOk, rPress = pcall(keyboardJustPressed, RECYCLE_KEY)
    if rOk and rPress and (clock - lastRecycle) > 0.15 then
        lastRecycle = clock
        setRecycle(recycleMode ~= 'NORMAL')
    end

    -- v8: 判定线动画锁 —— 开/关 bpp 都每帧执行：confirm 一出现立即压回 static。
    --     NONE 档 = 完全不播放；NORMAL 档 = 原速自然回收（不干预）。
    if recycleMode == 'NONE' then
        for L = 0, 3 do killConfirm(L) end
    end
    if not enabled then
        return
    end
    ensureScoreVisible()

    -- 1) 到期松键（逐轨回收动画，F2 关掉时只清状态、不动动画）
    for d = 1, 4 do
        local a = active[d]
        if a and pos >= a.releaseAt then doRelease(d) end
    end

    -- 2) 扫描判定窗口：只按自己的 seen 去重，绝不看 wasGoodHit
    local count = tonumber(gp('notes.length', 0)) or 0
    local lanes, susMax = {}, {}
    for i = 0, count - 1 do
        local st = nnum(i, 'strumTime', 1e18)
        if (st - pos) <= EARLY and (pos - st) <= LATE then
            if nflag(i, 'mustPress') and not (nflag(i, 'hitCausesMiss') or nflag(i, 'ignoreNote')) then
                local d = (nnum(i, 'noteData', 0) % 4) + 1
                local sl = nnum(i, 'sustainLength', 0)
                local key = tostring(st) .. ':' .. d .. ':' .. tostring(sl)
                if not seen[key] then
                    seen[key] = true
                    lanes[d] = true
                    if sl > 0 and sl < 4000 then
                        susMax[d] = math.max(susMax[d] or 0, sl)
                    end
                    -- 自己计分：cpuControlled 下引擎不加 songScore，这里补回真实值
                    local ad = math.abs(pos - st) + rnd() * 30
                    local pts, w
                    if ad <= 45 then pts, w = 350, 1.0
                    elseif ad <= 90 then pts, w = 200, 0.7
                    elseif ad <= 135 then pts, w = 100, 0.4
                    else pts, w = 50, 0.2 end
                    S.total = S.total + 1
                    S.hits = S.hits + 1
                    S.combo = S.combo + 1
                    S.weighted = S.weighted + w
                    S.score = S.score + pts
                    if type(addScore) == 'function' then pcall(addScore, pts) end
                end
            end
        end
    end
    if not (lanes[1] or lanes[2] or lanes[3] or lanes[4]) then
        publishStats()
        return
    end

    local acc = publishStats()

    -- 3) 同轨连打：先松再按，保证是「新的一次按键」
    for d = 1, 4 do
        if lanes[d] and active[d] then doRelease(d) end
    end

    -- 4) 40~60ms 随机按压（随 acc 变化），长音延长到尾
    local holds = {}
    for d = 1, 4 do
        if lanes[d] then
            local h = holdFor(acc, susMax[d])
            holds[d] = h
            active[d] = {releaseAt = pos + h}
        end
    end
    reportVisual(lanes, holds, acc, pos)
end
-- NF 对 onUpdate / onUpdatePost 调用约定不确定，两个都挂上（逻辑幂等，重复跑无害）
function onUpdate(elapsed)     tick(elapsed) end
function onUpdatePost(elapsed) tick(elapsed) end

function onEndSong()
    for d = 1, 4 do if active[d] then doRelease(d) end end
    recycleAll()
    publishStats()
    if enabled then sp('cpuControlled', origCpu); enabled = false; sv('bppEnabled', false) end
end
function onDestroy()
    for d = 1, 4 do if active[d] then doRelease(d) end end
    recycleAll()
    if enabled then sp('cpuControlled', origCpu); enabled = false; sv('bppEnabled', false) end
end
