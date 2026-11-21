--[[
  DoubleGhostTrial.lua  —  DK_Duet / NovaFlare 修复版
  功能：每次 note hit 给对应角色生成一个半透明残影（ghost trail），
        0.75s 淡出 + 0.35s 滑动后自动销毁。
  适配 DK_Duet 实际角色：
    boyfriend = 玩家
    dad       = Miku（对手1）
    gf        = Teto（对手2 / 合唱）
  不依赖 boyfriendName / dadName / gfName 全局变量（本环境未稳定暴露，
  原版正是栽在这几个 nil 上，每次回调第一行就崩）。
  合唱(Both Opponents Sing) 会同时给 dad 和 gf 出残影（即「双动作」）。
  所有属性访问都 pcall 包裹，取不到就跳过，绝不连累整段脚本崩溃。
--]]

local WHO = { bf = 'boyfriend', dad = 'dad', gf = 'gf' }

local function gp(key, def)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return def end
    return v
end

local function ngp(i, field, def)
    local ok, v = pcall(getPropertyFromGroup, 'notes', i, field)
    if not ok or v == nil then return def end
    return v
end

-- 每角色记录最近一帧的动画前缀，用于生成残影
local rows = { boyfriend = {}, dad = {}, gf = {} }

local function curFrame(obj)
    local fn = gp(obj .. '.animation.frameName', '')
    return string.sub(fn, 1, math.max(0, string.len(fn) - 3))
end

local function record(charObj, id, dir)
    local t = math.floor(ngp(id, 'strumTime', 0))
    local key = tostring(t)
    rows[charObj][key] = {
        curFrame(charObj),
        gp(charObj .. '.offset.x', 0),
        gp(charObj .. '.offset.y', 0),
        dir
    }
    pcall(runTimer, charObj .. 'str' .. key)
    return key
end

function goodNoteHit(id, direction, noteType, isSustainNote)
    if isSustainNote then return end
    trailFrom('boyfriend', id, direction)   -- v2：多押（同刻异向）时 BF 也出残影
end

function opponentNoteHit(id, direction, noteType, isSustainNote)
    if isSustainNote then return end
    local gfNote = ngp(id, 'gfNote', false)
    gfNote = (gfNote == true or gfNote == 1)
    if gfNote or noteType == 'Opponent 2 Sing' or noteType == 'Both Opponents Sing' then
        trailFrom('gf', id, direction)        -- Teto（对手2 / 合唱）
    else
        trailFrom('dad', id, direction)       -- 对手1（无类型对手音符）
    end
    if noteType == 'Both Opponents Sing' then
        trailFrom('dad', id, direction)       -- 合唱双动作：dad 也出残影
    end
end

function trailFrom(charObj, id, dir)
    local t = math.floor(ngp(id, 'strumTime', 0))
    local key = tostring(t)
    local prev = rows[charObj][key]
    if prev and prev[4] ~= dir then
        ghostTrail(charObj, prev, key)
    end
    record(charObj, id, dir)
end

function ghostTrail(charObj, noteData, key)
    local ghost = charObj .. 'Ghost' .. key
    local dir = noteData[4]
    local dist = 25
    local tx = gp(charObj .. '.x', 0)
    local ty = gp(charObj .. '.y', 0)
    if dir == 0 then tx = tx - dist
    elseif dir == 1 then ty = ty + dist
    elseif dir == 2 then ty = ty - dist
    elseif dir == 3 then tx = tx + dist end

    local img = gp(charObj .. '.imageFile', '')
    if img == '' then return end   -- 取不到纹理就不生成，避免炸

    pcall(makeAnimatedLuaSprite, ghost, img, gp(charObj .. '.x', 0), gp(charObj .. '.y', 0))
    pcall(addAnimationByPrefix, ghost, 'idle', noteData[1], 24, false)
    pcall(setProperty, ghost .. '.antialiasing', gp(charObj .. '.antialiasing', true))
    pcall(setProperty, ghost .. '.offset.x', noteData[2])
    pcall(setProperty, ghost .. '.offset.y', noteData[3])
    pcall(setProperty, ghost .. '.scale.x', gp(charObj .. '.scale.x', 1))
    pcall(setProperty, ghost .. '.scale.y', gp(charObj .. '.scale.y', 1))
    pcall(setProperty, ghost .. '.flipX', gp(charObj .. '.flipX', false))
    pcall(setProperty, ghost .. '.flipY', gp(charObj .. '.flipY', false))
    pcall(setProperty, ghost .. '.visible', gp(charObj .. '.visible', true))
    pcall(setProperty, ghost .. '.alpha', 0.8 * gp(charObj .. '.alpha', 1))
    pcall(setBlendMode, ghost, 'hardlight')
    pcall(addLuaSprite, ghost)
    pcall(playAnim, ghost, 'idle', true)

    local ok, order = pcall(getObjectOrder, charObj .. 'Group')
    if ok and order then pcall(setObjectOrder, ghost, math.floor(order) - 1) end

    pcall(doTweenAlpha, ghost .. 'fade', ghost, 0, 0.75, 'linear')
    pcall(doTweenX, ghost .. 'moveX', ghost, tx, 0.35, 'sineOut')
    pcall(doTweenY, ghost .. 'moveY', ghost, ty, 0.35, 'sineOut')
end

function onTimerCompleted(tag, loops, loopsLeft)
    for _, obj in pairs(WHO) do
        local head = obj .. 'str'
        if string.sub(tag, 1, string.len(head)) == head then
            local k = string.sub(tag, string.len(head) + 1)
            rows[obj][k] = nil
        end
    end
end

function onTweenCompleted(tag)
    if string.match(tag, 'Ghost') then
        pcall(removeLuaSprite, tag, true)
    end
end
