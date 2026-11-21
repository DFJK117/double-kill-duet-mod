# -*- coding: utf-8 -*-
"""v11.11:
  - no more ghost/stutter: 3 DISTINCT bell sounds, no same-file double play
  - timing1/2 = 0.30/0.30, third bell -> baguette thrust, judge after >=0.30s
  - black full-screen: use 'other' camera + screenCenter + 2x, no half-screen
  - projectile = dkBaguette.png (top baguette, transparent), thrust from lower-left,
    out and back fast, on the 3rd bell
  - BPM untouched, charts untouched.
"""
import os, shutil

ROOT = 'E:/UST_work/dk_miku'
G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DEPLOYS = [G, ROOT + '/DK_Dual', ROOT + '/DK_Miku']

SCRIPT = '''--[[
  DK_Saw.lua - GOD+ dodge (v11.11)
  3 distinct bells (alert / alertDouble / alertTriple) spaced 300 ms apart.
  3rd bell: baguette thrusts in from lower-left, out and back, then judge.
  Reaction window from 2nd bell to judge >= 300 ms. BPM and charts untouched.
  BotPlay auto-dodges; SPACE handled by DK_Fun.lua (dkDodgeActive).
  All text ASCII only (a fullwidth dash once broke LuaJIT).
]]

local timing1 = 0.30
local timing2 = 0.30
local timing3 = 0.32

local ALERT_TAG = 'dkSawAlert'
local BAG_TAG   = 'dkSawBag'
local POP_TAG   = 'dkSawDodged'
local BLACK_TAG = 'dkSawBlack'

local BAG_X0, BAG_Y0 = -520, 430     -- lower-left offscreen start
local BAG_X1, BAG_Y1 = 1180, 300     -- thrust target (upper-right)
local BAG_SCALE = 0.85

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
        pcall(addAnimationByPrefix, ALERT_TAG, '1', 'dkSawAlert1_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, '2', 'dkSawAlert2_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, 'dodge', 'dkSawAttack_', 24, false)
        pcall(setObjectCamera, ALERT_TAG, 'other')
        pcall(addLuaSprite, ALERT_TAG, true)
        pcall(screenCenter, ALERT_TAG)
        pcall(scaleObject, ALERT_TAG, 1, 1)
        sp(ALERT_TAG .. '.alpha', 0)
    end

    if not luaSpriteExists(BAG_TAG) then
        pcall(makeLuaSprite, BAG_TAG, 'dkBaguette', BAG_X0, BAG_Y0)
        pcall(scaleObject, BAG_TAG, BAG_SCALE, BAG_SCALE, false)
        pcall(setObjectCamera, BAG_TAG, 'other')
        pcall(addLuaSprite, BAG_TAG, false)
        sp(BAG_TAG .. '.visible', false)
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
        pcall(setObjectCamera, BLACK_TAG, 'other')
        pcall(addLuaSprite, BLACK_TAG, true)
        pcall(screenCenter, BLACK_TAG)
        pcall(scaleObject, BLACK_TAG, 2, 2, false)
        sp(BLACK_TAG .. '.alpha', 0)
    end

    spritesReady = true
end

function onCreatePost()
    ensureSprites()
end

function onEvent(name, v1, v2)
    if name ~= 'Dodge Mechanic' and name ~= 'DK Saw' then return end

    ensureSprites()
    local now = songMs()
    seq = seq + 1
    waves[#waves + 1] = {
        id = seq,
        t1 = now,
        t2 = now + timing1 * 1000,
        t3 = now + (timing1 + timing2) * 1000,
        tJudge = now + (timing1 + timing2 + timing3) * 1000,
        stage = 0,
        dodged = false,
    }
end

local function updateWaves()
    local now = songMs()
    local dodgeOn = gv('dkDodgeActive', false) == true

    for i = 1, #waves do
        local w = waves[i]
        if w.stage >= 2 and w.stage < 4 and not w.dodged then
            if botPlaying() or dodgeOn then w.dodged = true end
        end
    end

    for i = 1, #waves do
        local w = waves[i]

        if w.stage == 0 and now >= w.t1 then
            w.stage = 1
            pcall(playSound, 'alert', 1)
            sp(ALERT_TAG .. '.alpha', 1)
            pcall(playAnim, ALERT_TAG, '1', true)
            pcall(screenCenter, ALERT_TAG)
            pcall(doTweenAlpha, 'dkSawBlackIn', BLACK_TAG, 0.4, 0.3, 'linear')
            pcall(cameraFlash, 'game', 'FF5555', 0.15, true)
        end

        if w.stage == 1 and now >= w.t2 then
            w.stage = 2
            pcall(playSound, 'alertDouble', 1)
            pcall(playAnim, ALERT_TAG, '2', true)
            pcall(screenCenter, ALERT_TAG)
            pcall(setProperty, ALERT_TAG .. '.x', getProperty(ALERT_TAG .. '.x') - 15)
            pcall(setProperty, ALERT_TAG .. '.y', getProperty(ALERT_TAG .. '.y') - 8)
        end

        if w.stage == 2 and now >= w.t3 then
            w.stage = 3
            pcall(playSound, 'alertTriple', 1)
            pcall(playAnim, ALERT_TAG, 'dodge', true)
            pcall(screenCenter, ALERT_TAG)
            -- baguette: fast thrust out then retract on the 3rd bell
            sp(BAG_TAG .. '.x', BAG_X0)
            sp(BAG_TAG .. '.y', BAG_Y0)
            sp(BAG_TAG .. '.angle', 0)
            sp(BAG_TAG .. '.visible', true)
            pcall(doTweenX, 'dkBagOutX', BAG_TAG, BAG_X1, 0.13, 'expoOut')
            pcall(doTweenY, 'dkBagOutY', BAG_TAG, BAG_Y1, 0.13, 'expoOut')
            pcall(runTimer, 'dkBagBack', 0.17)
        end

        if w.stage == 3 and now >= w.tJudge then
            w.stage = 4
            pcall(playSound, 'attack', 1)
            if w.dodged then
                sp(POP_TAG .. '.y', 500)
                sp(POP_TAG .. '.alpha', 1)
                pcall(doTweenY, 'dkSawPopY', POP_TAG, 480, 0.3, 'sineOut')
                pcall(doTweenAlpha, 'dkSawPopA', POP_TAG, 0, 1, 'linear')
                pcall(setVar, 'dkSawDodged', true)
            else
                sp('health', 0)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
            end
            pcall(doTweenAlpha, 'dkSawAlertOut', ALERT_TAG, 0, 0.1, 'linear')
            pcall(doTweenAlpha, 'dkSawBlackOut', BLACK_TAG, 0, 0.1, 'linear')
            pcall(runTimer, 'dkSawHide', 0.2)
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
    if tag == 'dkBagBack' then
        pcall(doTweenX, 'dkBagInX', BAG_TAG, BAG_X0, 0.16, 'expoIn')
        pcall(doTweenY, 'dkBagInY', BAG_TAG, BAG_Y0, 0.16, 'expoIn')
    elseif tag == 'dkSawHide' then
        local active = false
        for i = 1, #waves do
            if waves[i].stage >= 1 and waves[i].stage < 4 then active = true end
        end
        if not active then sp(BAG_TAG .. '.visible', false) end
    end
end

function onDestroy()
    sp(BAG_TAG .. '.visible', false)
    sp(ALERT_TAG .. '.alpha', 0)
    sp(POP_TAG .. '.alpha', 0)
    sp(BLACK_TAG .. '.alpha', 0)
end
'''

# ASCII check before writing (fullwidth dash once killed LuaJIT)
assert all(b < 128 for b in SCRIPT.encode('utf-8')), 'non-ASCII in script'

for d in DEPLOYS:
    imgsrc = ROOT + '/_godmode/dkBaguette.png'
    shutil.copyfile(imgsrc, d + '/images/dkBaguette.png')
    p = d + '/scripts/DK_Saw.lua'
    open(p, 'w', encoding='utf-8', newline='\n').write(SCRIPT)
    print('deployed', p, len(SCRIPT), 'ascii OK')

# real Lua compile
import sys
sys.path.insert(0, 'E:/UST_work/_pylibs')
try:
    from lupa import LuaRuntime
    LuaRuntime().compile(SCRIPT)
    print('LUA COMPILE OK')
except Exception as e:
    print('LUA COMPILE FAIL', e)
    raise
