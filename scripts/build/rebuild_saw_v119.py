# -*- coding: utf-8 -*-
"""v11.9: rebuild DK_Saw.lua to mirror the ORIGINAL Dodge Mechanic.lua flow."""
import zipfile, os

ROOT = 'E:/UST_work/dk_miku'
G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DEPLOYS = [G, ROOT + '/DK_Dual', ROOT + '/DK_Miku']
ORIG = 'I:/mods.zip'

# Pull the EXACT original sounds from the official mobile port.
z = zipfile.ZipFile(ORIG)
ORIG_SOUNDS = {
    'alert.ogg': 'mods/sounds/alert.ogg',            # 29632 B, punchy double beep
    'attack.ogg': 'mods/sounds/attack.ogg',          # 57378 B, saw hit
    'dodge.ogg': 'mods/sounds/dodge.ogg',            # 22890 B, pop
}
for d in DEPLOYS:
    for dest, src in ORIG_SOUNDS.items():
        open(d + '/sounds/' + dest, 'wb').write(z.read(src))
        print('orig sound', d, dest, z.getinfo(src).file_size)

SCRIPT = '''--[[
  DK_Saw.lua - GOD+ sawblade dodge.
  Flow mirrors the ORIGINAL Dodge Mechanic.lua from the official mobile port:
    onEvent -> alert 1 (sound alert, black fades to 0.4 in 0.3s, saw visible)
            -> timing1 0.20s -> alert 2 (sound alert, dodge window opens)
            -> timing2 0.30s -> judge: dodged -> pop + sound attack
                                       failed -> health 0 + sound attack
    No mobile virtual button; SPACE is handled by DK_Fun.lua (dkDodgeActive).
    BotPlay auto-dodges. Clock uses getSongPosition(), single tick.
  All text kept ASCII (a fullwidth dash once broke LuaJIT).
]]

local timing1 = 0.20
local timing2 = 0.30

local ALERT_TAG = 'dkSawAlert'
local SAW_TAG = 'dkSawBlade'
local POP_TAG = 'dkSawDodged'
local BLACK_TAG = 'dkSawBlack'
local DODGE_TAG = 'dkDodgeAnim'

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

function onEvent(name, v1, v2)
    if name ~= 'Dodge Mechanic' and name ~= 'DK Saw' then return end

    ensureSprites()
    local now = songMs()
    seq = seq + 1
    waves[#waves + 1] = {
        id = seq,
        t1 = now,
        t2 = now + timing1 * 1000,
        tJudge = now + (timing1 + timing2) * 1000,
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
            sp(SAW_TAG .. '.visible', true)
            pcall(playAnim, SAW_TAG, 'spin', true)
            pcall(doTweenAlpha, 'dkSawBlackIn', BLACK_TAG, 0.4, 0.3, 'linear')
            pcall(cameraFlash, 'game', 'FF5555', 0.15, true)
        end

        if w.stage == 1 and now >= w.t2 then
            w.stage = 2
            pcall(playSound, 'alert', 1)
            pcall(playAnim, ALERT_TAG, '2', true)
            pcall(screenCenter, ALERT_TAG)
            pcall(setProperty, ALERT_TAG .. '.x', getProperty(ALERT_TAG .. '.x') - 15)
            pcall(setProperty, ALERT_TAG .. '.y', getProperty(ALERT_TAG .. '.y') - 8)
        end

        if w.stage == 2 and now >= w.tJudge then
            w.stage = 3
            pcall(playSound, 'attack', 1)
            pcall(playAnim, ALERT_TAG, 'dodge', true)
            pcall(screenCenter, ALERT_TAG)
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
            pcall(runTimer, 'dkSawHide', 0.55)
        end
    end

    local keep = {}
    for i = 1, #waves do
        if waves[i].stage < 3 or now < waves[i].tJudge + 800 then
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
        local activeSaw = false
        for i = 1, #waves do
            if waves[i].stage >= 1 and waves[i].stage < 3 then activeSaw = true end
        end
        if not activeSaw then sp(SAW_TAG .. '.visible', false) end
    end
end

function onDestroy()
    sp(SAW_TAG .. '.visible', false)
    sp(ALERT_TAG .. '.alpha', 0)
    sp(POP_TAG .. '.alpha', 0)
    sp(BLACK_TAG .. '.alpha', 0)
end
'''

for d in DEPLOYS:
    p = d + '/scripts/DK_Saw.lua'
    open(p, 'w', encoding='utf-8', newline='\n').write(SCRIPT)
    print('rebuilt', p, len(SCRIPT), 'ascii', all(ord(c) < 128 for c in SCRIPT))
