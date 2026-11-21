# -*- coding: utf-8 -*-
"""v11.7: rewrite DK_Saw.lua (ASCII-only comments, slower timing, Dodge Mechanic alias)."""
import os

CONTENT = """--[[
  DK_Saw.lua - GOD+ sawblade dodge (ported from QT Dodge Mechanic.lua)

  Flow (one DK Saw event runs all 3 alerts):
    alert1 (light 1) -> ALERT_GAP -> alert2 (light 2, dodge opens)
    -> ALERT_GAP -> alert3 (light 3, saw appears) -> JUDGE_DELAY -> judge.
    Dodged: show DODGED popup. Not dodged: health = 0. BotPlay auto-dodges.

  Changes vs original:
    1) No mobile virtual dodge button; dodge uses SPACE via dkDodgeActive
       (set by DK_Fun.lua).
    2) Clock uses getSongPosition() only (no onUpdate/onUpdatePost double tick).
    3) Event name 'DK Saw'; also accepts 'Dodge Mechanic'.
       value1 = direction, value2 = saw count (visual only).
    4) NOTE: all comments kept ASCII-only. A fullwidth dash in a long comment
       once caused a LuaJIT parse error and stopped this script from loading.

  Assets: dk_saw_alert (sparrow, 36f), dkSawAssets (FlxAnimate, symbol saw full),
    dkDodged popup, sounds dkAlert1/2/3, dkSawAttack, dkDodgeSound.
]]

local ALERT_GAP = 0.75      -- gap between the 3 alerts (s)
local JUDGE_DELAY = 0.55    -- after 3rd alert, before judge (s)

local ALERT_TAG = 'dkSawAlert'
local SAW_TAG = 'dkSawBlade'
local POP_TAG = 'dkSawDodged'
local BLACK_TAG = 'dkSawBlack'

local waves = {}
local seq = 0
local spritesReady = false

local function gv(k, d)
    local ok, v = pcall(getVar, k)
    if ok and v ~= nil then return v end
    return d
end
local function sp(k, v) pcall(setProperty, k, v) end

local function botPlaying()
    local a = gv('botPlay', false)
    local b = false
    pcall(function() b = getProperty('cpuControlled') == true end)
    return a == true or b == true
end

local function songMs()
    local ok, v = pcall(getSongPosition)
    if ok and type(v) == 'number' then return v end
    return 0
end

local function ensureSprites()
    if spritesReady then return end

    if not luaSpriteExists(ALERT_TAG) then
        pcall(makeAnimatedLuaSprite, ALERT_TAG, 'dk_saw_alert', 0, 0, 'sparrow')
        pcall(addAnimationByPrefix, ALERT_TAG, 'alert1', 'dkSawAlert1_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, 'alert2', 'dkSawAlert2_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, 'alert3', 'dkSawAttack_', 24, false)
        pcall(setObjectCamera, ALERT_TAG, 'other')
        pcall(addLuaSprite, ALERT_TAG, true)
        pcall(screenCenter, ALERT_TAG)
        pcall(scaleObject, ALERT_TAG, 1, 1)
        sp(ALERT_TAG .. '.alpha', 0)
    end

    if not luaSpriteExists(SAW_TAG) then
        pcall(makeFlxAnimateSprite, SAW_TAG, 500, 300, 'dkSawAssets')
        pcall(addAnimationBySymbol, SAW_TAG, 'spin', 'saw full', 24, false)
        pcall(setObjectCamera, SAW_TAG, 'game')
        pcall(addLuaSprite, SAW_TAG, false)
        sp(SAW_TAG .. '.visible', false)
    end

    if not luaSpriteExists(POP_TAG) then
        pcall(makeLuaSprite, POP_TAG, 'dkDodged', 0, 500)
        pcall(setObjectCamera, POP_TAG, 'other')
        pcall(addLuaSprite, POP_TAG, false)
        pcall(screenCenter, POP_TAG, 'x')
        pcall(scaleObject, POP_TAG, 0.55, 0.55, false)
        sp(POP_TAG .. '.alpha', 0)
    end

    if not luaSpriteExists(BLACK_TAG) then
        pcall(makeLuaSprite, BLACK_TAG, nil, 0, 0)
        pcall(makeGraphic, BLACK_TAG, 1280, 720, '0xFF000000')
        pcall(setObjectCamera, BLACK_TAG, 'game')
        pcall(addLuaSprite, BLACK_TAG, true)
        pcall(scaleObject, BLACK_TAG, 2, 2, false)
        sp(BLACK_TAG .. '.alpha', 0)
    end

    spritesReady = true
end

function onCreatePost()
    ensureSprites()
end

function onEvent(name, value1, value2)
    if name ~= 'DK Saw' and name ~= 'Dodge Mechanic' then return end

    ensureSprites()
    local now = songMs()
    seq = seq + 1
    local dir = value1 or 'left'
    local count = tonumber(value2) or 1
    if count < 1 then count = 1 end
    if count > 4 then count = 4 end

    local t1 = now
    local t2 = now + ALERT_GAP * 1000
    local t3 = now + ALERT_GAP * 2000
    local tJudge = t3 + JUDGE_DELAY * 1000

    waves[#waves + 1] = {
        id = seq,
        t1 = t1, t2 = t2, t3 = t3, tJudge = tJudge,
        stage = 0,
        dir = dir, count = count,
        dodged = false,
        sawSpawned = false,
    }
end

local function updateWaves()
    local now = songMs()
    local dodgeOn = gv('dkDodgeActive', false) == true

    for i = 1, #waves do
        local w = waves[i]
        if w.stage >= 2 and w.stage < 4 and not w.dodged then
            if botPlaying() or dodgeOn then
                w.dodged = true
            end
        end
    end

    for i = 1, #waves do
        local w = waves[i]

        if w.stage == 0 and now >= w.t1 then
            w.stage = 1
            pcall(playSound, 'dkAlert1', 1)
            sp(ALERT_TAG .. '.alpha', 1)
            pcall(playAnim, ALERT_TAG, 'alert1', true)
            pcall(screenCenter, ALERT_TAG)
            pcall(cameraFlash, 'game', 'FF5555', 0.15, true)
        end

        if w.stage == 1 and now >= w.t2 then
            w.stage = 2
            pcall(playSound, 'dkAlert2', 1)
            pcall(playAnim, ALERT_TAG, 'alert2', true)
            pcall(screenCenter, ALERT_TAG)
        end

        if w.stage == 2 and now >= w.t3 then
            w.stage = 3
            pcall(playSound, 'dkAlert3', 1)
            pcall(playAnim, ALERT_TAG, 'alert3', true)
            pcall(screenCenter, ALERT_TAG)
            if luaSpriteExists(SAW_TAG) then
                sp(SAW_TAG .. '.visible', true)
                pcall(playAnim, SAW_TAG, 'spin', true)
                pcall(doTweenAlpha, 'dkSawBlackIn', BLACK_TAG, 0.35, 0.15, 'linear')
                w.sawSpawned = true
            end
        end

        if w.stage == 3 and now >= w.tJudge then
            w.stage = 4
            if w.dodged then
                sp(POP_TAG .. '.alpha', 1)
                sp(POP_TAG .. '.y', 500)
                pcall(playSound, 'dkDodgeSound', 0.9)
                pcall(doTweenY, 'dkSawPopY', POP_TAG, 470, 0.35, 'sineOut')
                pcall(doTweenAlpha, 'dkSawPopA', POP_TAG, 0, 0.8, 'linear')
                pcall(setVar, 'dkSawDodged', true)
            else
                sp('health', 0)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(playSound, 'dkSawAttack', 1)
                pcall(setVar, 'dkSawKilled', true)
            end
            pcall(doTweenAlpha, 'dkSawAlertOut', ALERT_TAG, 0, 0.15, 'linear')
            pcall(doTweenAlpha, 'dkSawBlackOut', BLACK_TAG, 0, 0.25, 'linear')
            pcall(runTimer, 'dkSawHide', 0.55)
        end
    end

    local keep = {}
    for i = 1, #waves do
        if waves[i].stage < 4 or now < waves[i].tJudge + 800 then
            keep[#keep + 1] = waves[i]
        end
    end
    waves = keep
end

function onUpdate(elapsed)
    updateWaves()
end

function onTimerCompleted(tag)
    if tag == 'dkSawHide' then
        sp(SAW_TAG .. '.visible', false)
    end
end

function onDestroy()
    sp(SAW_TAG .. '.visible', false)
    sp(ALERT_TAG .. '.alpha', 0)
    sp(POP_TAG .. '.alpha', 0)
    sp(BLACK_TAG .. '.alpha', 0)
end
"""

# strict ASCII check (source must contain no non-ASCII char at all)
bad = [(i + 1, ord(c)) for i, c in enumerate(CONTENT) if ord(c) > 127]
assert not bad, ('non-ascii found at char offsets: %s' % bad[:10])

out = r'E:/UST_work/dk_miku/scripts/DK_Saw.lua'
with open(out, 'w', encoding='utf-8', newline='') as f:
    f.write(CONTENT)
print('WROTE', out, 'len=', len(CONTENT))

# block balance check, strings stripped
import re
lines = CONTENT.split('\n')
stack = []
for i, l in enumerate(lines, 1):
    code = re.sub(r"'[^']*'", "''", l.split('--')[0]) if not l.strip().startswith('--') else ''
    n = len(re.findall(r'\bfunction\b', code)) + len(re.findall(r'\bif\b', code)) - len(re.findall(r'\belseif\b', code)) + len(re.findall(r'\bfor\b', code)) + len(re.findall(r'\bwhile\b', code))
    c = len(re.findall(r'\bend\b', code))
    for _ in range(n):
        stack.append(i)
    for _ in range(c):
        if stack:
            stack.pop()
        else:
            print('EXTRA end line', i)
print('BALANCE', 'OK' if not stack else ('MISMATCH ' + str(stack)))
