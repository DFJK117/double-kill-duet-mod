--============================================================
--  DK_Fun.lua  v2   DK_Duet / NovaFlare Engine   (2026-11-15)
--
--  ① 空格 = 躲锯子（dodge）：玩家播放 bf-ic 原生 'dodge' 动作（15 帧/24fps），
--     并置 dodgeActive 标志 + 派发 'DK Dodge' 事件，供 GOD+ 锯子判定读取
--     （在躲闪窗口内按空格 = 避开 sawblade）。空格不再播放 hey。
--     全员 hey 改为只用事件 "DK Hey" 触发（键盘不再占用）。
--
--  ② SHIFT = 玩家播放 attack 动作（bf-ic 角色原生 'attack'，
--     Indie Cross 的 "0BF attack" 31 帧 @24fps = 1.29s）。
--     播完前不被打断：specialAnim 锁 + 播放窗口内用 goodNoteHitPre 把
--     命中音符的 noAnimation 设 true（分数/血量照常，只屏蔽 sing 动画），
--     直到 ATTACK_LOCK(=1.3s) 结束。事件 "DK Attack" 也能触发；
--     value1 可填 bf / dad / gf / all。
--
--  ③ 小彩蛋：事件 "DK Surprise"（挂在谱面 165600ms = BPM 200→220 变速段
--     起点，与 Legacy '552' 同刻）。触发时把血条两个 icon 临时换成
--     images/dk_surprise.png（用户给的那张惊讶脸），保持 0.35s，
--     再用 0.65s 渐变透明消失，合计 1 秒；结束后自动恢复原 icon。
--     value1: 'both'(默认) / 'p1' / 'p2'   value2: 总秒数（默认 1）
--     事件 "DK Hey" / "DK Attack" / "DK Surprise" 的注册壳在 custom_events/ 里。
--
--  v2 角色变更：DK 的玩家 BF 换成 Indie Cross v15 的 bf-ic
--     （12 个动作：idle / 四向 sing / 四向 miss / hurt / dodge / attack），
--     不再使用旧 BOYFRIEND 图集里的 Dlow Scared 残血姿势。
--     图集已复制进本模组 images/characters/cuphead/，单模组可独立运行。
--
--  实现纪律：纯 Lua、零 runHaxeCode / hscript（本工程 BPP v3 的 native
--  crash 就是 hscript 造成的）。所有引擎 API 都在 FunkinLua / ExtraFunctions
--  / ReflectionFunctions 里逐个核对过：keyboardJustPressed('SPACE'/'F2')、
--  playAnim、getProperty、setProperty、makeLuaSprite、addLuaSprite、
--  removeLuaSprite、setObjectCamera('camHUD')、doTweenAlpha、runTimer、
--  cancelTween、cancelTimer、getVar/setVar。
--  不真的调 HealthIcon.changeIcon（需要 hscript 才能拿到原 icon 名来恢复），
--  改为「覆盖层 + 原 icon alpha 归零」：视觉等价替换，恢复零风险。
--============================================================

local HEY_KEY    = 'SPACE'     -- 保留常量但不再用于 hey（空格改为躲锯子）
local DODGE_KEY  = 'SPACE'
local ATTACK_KEY = 'SHIFT'
local HEY_TAG    = 'DK Hey'
local ATTACK_TAG = 'DK Attack'
local DODGE_TAG  = 'DK Dodge'
local EGG_TAG    = 'DK Surprise'
local ATTACK_LOCK = 1.3        -- attack 动画 31 帧@24fps=1.29s，取整 1.3s 锁定窗口
local DODGE_LOCK  = 0.7        -- dodge 动画 15 帧@24fps=0.625s，取整 0.7s 锁定窗口：
                               -- 播完前不被 sing 顶掉（强制播完才播其他动作）
local DODGE_WINDOW = 1.0       -- 躲闪有效窗口（供 GOD+ 锯子判定）
local IMG        = 'dk_surprise'        -- images/dk_surprise.png (150x150 RGBA)
local P1, P2     = 'dkEggP1', 'dkEggP2'
local ICONS      = {{P1, 'iconP1'}, {P2, 'iconP2'}}

local holdTime, fadeTime = 0.35, 0.65   -- 0.35 + 0.65 = 1.00 秒
local clock, lastHey, lastAttack, lastDodge = 0, -1e9, -1e9, -1e9
local heyCount, attackCount, dodgeCount = 0, 0, 0
local attackLockUntil = -1     -- attack 播放锁定截止时刻（clock 秒）
local dodgeLockUntil = -1      -- dodge 动画播放锁定截止时刻（强制播完）
local dodgeActiveUntil = -1    -- 躲闪判定有效截止时刻
local eggReady, eggActive = false, false
local eggUse = {[P1] = true, [P2] = true}
local savedAlpha = {iconP1 = 1, iconP2 = 1}

-- curCharacter -> hey 动画名（都来自 characters/*.json 的真实 anim 字段）
-- God 难度角色名带 -god 后缀，靠 baseChar() 归一化后复用基础表；
-- 这里也显式列出 God 名做双保险。
local HEY_ANIM = {
    ['bf']               = 'hey',
    ['bf-ic']            = 'hey',
    ['bf-defeat-normal'] = 'hey',
    ['miku']             = 'hey',
    ['momo']             = 'hey',
    ['teto']             = 'hey',
    ['teto-cozy']        = 'hey',
    ['bf-god']           = 'hey',
    ['bf-defeat-normal-god'] = 'hey',
    ['miku-god']         = 'hey',
    ['momo-god']         = 'hey',
    ['teto-god']         = 'hey',
}

-- curCharacter -> attack 动画名；表外的角色（Miku/Momo/Teto）没有 attack，
-- 退回 hey，避免向引擎请求不存在的动画名。
local ATTACK_ANIM = {
    ['bf']               = 'attack',
    ['bf-ic']            = 'attack',
    ['bf-god']           = 'attack',   -- God 难度玩家：Indie Cross 31 帧挥拳
}

-- 难度后缀归一化：'bf-god' -> 'bf'、'miku-god' -> 'miku'、
-- 'bf-defeat-normal-god' -> 'bf-defeat-normal'。只剥末尾一个 -后缀。
local function baseChar(cc)
    if not cc then return nil end
    local s = tostring(cc)
    local b = s:gsub('%-[%w_]+$', '')
    return b
end

local function heyAnimFor(cc)
    if not cc then return 'hey' end
    if HEY_ANIM[cc] then return HEY_ANIM[cc] end
    local b = baseChar(cc)
    if b and HEY_ANIM[b] then return HEY_ANIM[b] end
    return 'hey'
end

local function attackAnimFor(cc)
    if not cc then return 'hey' end
    if ATTACK_ANIM[cc] then return ATTACK_ANIM[cc] end
    local b = baseChar(cc)
    if b and ATTACK_ANIM[b] then return ATTACK_ANIM[b] end
    return 'hey'
end

-- dodge 动画：bf / bf-ic / bf-god 都有原生 'dodge'（15 帧），表外角色退回 nil 不播
local DODGE_ANIM = {
    ['bf'] = 'dodge', ['bf-ic'] = 'dodge', ['bf-god'] = 'dodge',
}
local function dodgeAnimFor(cc)
    if not cc then return nil end
    if DODGE_ANIM[cc] then return DODGE_ANIM[cc] end
    local b = baseChar(cc)
    if b and DODGE_ANIM[b] then return DODGE_ANIM[b] end
    return nil
end

local function gp(key, default)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return default end
    return v
end
local function sp(key, value)
    pcall(setProperty, key, value)
end

--============================================================
--  ① 空格全员 hey
--============================================================
local function playHey()
    local who = {'boyfriend', 'dad', 'gf'}
    for i = 1, #who do
        local c = who[i]
        local okc, cc = pcall(getProperty, c .. '.curCharacter')
        local anim = heyAnimFor(okc and cc or nil)
        -- 与 attack 相同的「先播后锁」：playAnim 内部会清 specialAnim，
        -- 必须播完立刻重新锁住，否则 Character.update 的 dance 会把 hey 顶掉。
        pcall(playAnim, c, anim, true)
        sp(c .. '.specialAnim', true)
        sp(c .. '.heyTimer', 0)
        sp(c .. '.holdTimer', 0)
    end
    heyCount = heyCount + 1
    if type(setVar) == 'function' then pcall(setVar, 'dkHeyCount', heyCount) end
end

--============================================================
--  ② SHIFT 播放 attack 动作
--  引擎 Character.playAnim 第一行会 specialAnim=false，所以必须**先播后锁**：
--  playAnim -> specialAnim=true -> heyTimer=0。
--  Character.update 里 `else if (specialAnim && isAnimationFinished())`
--  会在攻击动画播完时自动 dance() 回 idle，不会僵在最后一帧。
--============================================================
local function playAttack(which)
    local w = string.lower(tostring(which or 'bf'))
    if w == '' or w == 'bf' or w == '1' or w == 'boyfriend' then w = 'bf' end
    local targets = {'boyfriend'}
    if w == 'all' then targets = {'boyfriend', 'dad', 'gf'} end
    if w == 'dad' or w == 'p2' or w == '2' then targets = {'dad'} end
    if w == 'gf'  or w == '3' then targets = {'gf'} end

    for i = 1, #targets do
        local c = targets[i]
        local okc, cc = pcall(getProperty, c .. '.curCharacter')
        local anim = attackAnimFor(okc and cc or nil)
        pcall(playAnim, c, anim, true)
        sp(c .. '.specialAnim', true)
        sp(c .. '.heyTimer', 0)
        sp(c .. '.holdTimer', 0)
    end
    -- 锁定窗口：这段时间内命中音符不播 sing（goodNoteHitPre 里处理），
    -- 保证 attack 31 帧完整放完不被顶掉。
    attackLockUntil = clock + ATTACK_LOCK
    attackCount = attackCount + 1
    if type(setVar) == 'function' then pcall(setVar, 'dkAttackCount', attackCount) end
end

--============================================================
--  ②b 空格躲锯子（dodge）
--  播 bf-ic 原生 dodge（15 帧）+ 开一个 DODGE_WINDOW 判定窗，
--  把 dodgeActive 暴露给 GOD+ 的锯子事件读取（窗内按空格=躲开）。
--============================================================
local function playDodge()
    local okc, cc = pcall(getProperty, 'boyfriend.curCharacter')
    local anim = dodgeAnimFor(okc and cc or nil)
    if anim then
        pcall(playAnim, 'boyfriend', anim, true)
        sp('boyfriend.specialAnim', true)
        sp('boyfriend.heyTimer', 0)
        sp('boyfriend.holdTimer', 0)
    end
    -- 动画锁：和 attack 一样，播完前屏蔽命中音符的 sing，强制 dodge 播完
    dodgeLockUntil = clock + DODGE_LOCK
    dodgeActiveUntil = clock + DODGE_WINDOW
    dodgeCount = dodgeCount + 1
    if type(setVar) == 'function' then
        pcall(setVar, 'dkDodgeActive', true)
        pcall(setVar, 'dkDodgeUntil', dodgeActiveUntil)
        pcall(setVar, 'dkDodgeCount', dodgeCount)
    end
end

-- attack / dodge 锁定期间：屏蔽命中音符的 sing 动画（分数/血量照常）
-- 保证 attack(31帧) / dodge(15帧) 强制播完，才轮到下一个 sing
function goodNoteHitPre(id, noteData, noteType, isSustain)
    if clock < attackLockUntil or clock < dodgeLockUntil then
        pcall(setPropertyFromGroup, 'notes', id, 'noAnimation', true)
    end
end

--============================================================
--  ③ BPM 变速段 icon 彩蛋
--============================================================
local function ensureSprites()
    if eggReady then return true end
    local a = pcall(makeLuaSprite, P1, IMG, 0, 0)
    local b = pcall(makeLuaSprite, P2, IMG, 0, 0)
    if not (a and b) then return false end
    for _, pair in ipairs(ICONS) do
        pcall(setObjectCamera, pair[1], 'camHUD')
        pcall(addLuaSprite, pair[1], true)
        sp(pair[1] .. '.alpha', 0)
        sp(pair[1] .. '.visible', false)
    end
    eggReady = true
    return true
end

-- icon 会随血条每帧移动，覆盖层必须逐帧跟随
local function followIcons()
    for _, pair in ipairs(ICONS) do
        local ox, x = pcall(getProperty, pair[2] .. '.x')
        local oy, y = pcall(getProperty, pair[2] .. '.y')
        if ox and oy and x and y then
            sp(pair[1] .. '.x', x)
            sp(pair[1] .. '.y', y)
        end
    end
end

local function finishEgg()
    if not eggActive then return end
    eggActive = false
    sp('iconP1.alpha', savedAlpha.iconP1)
    sp('iconP2.alpha', savedAlpha.iconP2)
    for _, pair in ipairs(ICONS) do
        sp(pair[1] .. '.alpha', 0)
        sp(pair[1] .. '.visible', false)
    end
end

local function startEgg(which, total)
    if not ensureSprites() then return end
    -- 允许重复触发：先取消上一轮 tween/timer，再从头开始
    pcall(cancelTween, 'dkEggFadeP1')
    pcall(cancelTween, 'dkEggFadeP2')
    pcall(cancelTimer, 'dkEggHold')
    pcall(cancelTimer, 'dkEggDone')
    finishEgg()

    local secs = tonumber(total)
    if secs and secs >= 0.3 and secs <= 10 then
        holdTime, fadeTime = secs * 0.35, secs * 0.65
    else
        holdTime, fadeTime = 0.35, 0.65
    end

    eggUse[P1] = (which ~= 'p2')
    eggUse[P2] = (which ~= 'p1')
    savedAlpha.iconP1 = gp('iconP1.alpha', 1)
    savedAlpha.iconP2 = gp('iconP2.alpha', 1)

    for _, pair in ipairs(ICONS) do
        local on = eggUse[pair[1]]
        sp(pair[1] .. '.alpha', on and 1 or 0)
        sp(pair[1] .. '.visible', on)
        if on then sp(pair[2] .. '.alpha', 0) end   -- 原 icon 隐藏 = 视觉替换
    end
    followIcons()
    eggActive = true
    pcall(runTimer, 'dkEggHold', holdTime, 1)
end

--============================================================
--  回调
--============================================================
function onEvent(name, value1, value2)
    if name == HEY_TAG then
        playHey()
        return
    end
    if name == ATTACK_TAG then
        playAttack(value1)
        return
    end
    if name == DODGE_TAG then
        playDodge()
        return
    end
    if name ~= EGG_TAG then return end
    local w = string.lower(tostring(value1 or ''))
    if w == '' or w == 'all' or w == 'both' then w = 'both'
    elseif w == 'p1' or w == '1' or w == 'bf' then w = 'p1'
    elseif w == 'p2' or w == '2' or w == 'dad' then w = 'p2'
    else w = 'both' end
    startEgg(w, value2)
end

function onTimerCompleted(tag)
    if tag == 'dkEggHold' then
        if not eggActive then return end
        for _, pair in ipairs(ICONS) do
            if eggUse[pair[1]] then
                pcall(doTweenAlpha, 'dkEggFade' .. pair[1]:sub(-2), pair[1], 0, fadeTime, 'linear')
            end
        end
        pcall(runTimer, 'dkEggDone', fadeTime + 0.03, 1)
    elseif tag == 'dkEggDone' then
        finishEgg()
    end
end

local function tick(elapsed)
    clock = clock + (tonumber(elapsed) or 0)
    -- onUpdate 与 onUpdatePost 都挂了，用累计帧时间去重防止同帧触发两次
    -- 空格现在 = 躲锯子，不再播 hey
    local dOk, dPressed = pcall(keyboardJustPressed, DODGE_KEY)
    if dOk and dPressed and (clock - lastDodge) > 0.15 then
        lastDodge = clock
        playDodge()
    end
    local aOk, aPressed = pcall(keyboardJustPressed, ATTACK_KEY)
    if aOk and aPressed and (clock - lastAttack) > 0.25 then
        lastAttack = clock
        playAttack('bf')
    end
    -- 躲闪窗口到期，清标志
    if dodgeActiveUntil > 0 and clock >= dodgeActiveUntil then
        dodgeActiveUntil = -1
        if type(setVar) == 'function' then pcall(setVar, 'dkDodgeActive', false) end
    end
    if eggActive then followIcons() end
end
function onUpdate(elapsed)     tick(elapsed) end
-- 修复：原 onUpdatePost 也调 tick 导致 clock 两倍速（dodge 窗口 0.5s 实际 0.25s、
-- attack 锁定/hey 计时全部减半）。统一只由 onUpdate 累加。
function onUpdatePost(elapsed) end

function onEndSong()
    finishEgg()
end
function onDestroy()
    pcall(cancelTween, 'dkEggFadeP1')
    pcall(cancelTween, 'dkEggFadeP2')
    pcall(cancelTimer, 'dkEggHold')
    pcall(cancelTimer, 'dkEggDone')
    finishEgg()
    if eggReady then
        pcall(removeLuaSprite, P1, true)
        pcall(removeLuaSprite, P2, true)
        eggReady = false
    end
end
