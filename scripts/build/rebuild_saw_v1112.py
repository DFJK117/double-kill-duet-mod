# -*- coding: utf-8 -*-
"""v11.12 CLEAN RE-PORT of the GOD+ dodge mechanic.
  Root causes fixed:
   1) THREE different 1.08s bell files overlapped (alert/alertDouble/alertTriple)
      -> stitched-monster sound. Now ONE file 'alert' (itself a 3-beep rising alert),
         played ONCE per wave.
   2) Black overlay tween left alpha=0.4 between waves -> global dimming.
      Now black is set to 0 by a hard timer after every wave, onDestroy, and on
      every new wave start (no reliance on tween completion).
   3) Legacy sounds/images purged from the mod so nothing old can load.
   4) Projectile = dkBaguette.png (top baguette), fast out-and-back on the alert.
  Charts, BPM, difficulty separation untouched.
"""
import os, glob, shutil

def make_warning_png(path):
    """Fresh warning badge: 3 rising red chevrons, independent of the purged legacy atlas."""
    from PIL import Image, ImageDraw
    W, H = 420, 260
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    for i, cy in enumerate([70, 140, 210]):
        col = [(255, 90, 80, 255), (255, 150, 60, 255), (255, 215, 70, 255)][i]
        w = [110, 145, 180][i]
        dr.polygon([(W//2 - w, cy - 40), (W//2 + w, cy - 40),
                    (W//2, cy + 40)], fill=col)
        dr.line([(W//2 - w, cy - 40), (W//2, cy + 40), (W//2 + w, cy - 40)],
                fill=(30, 0, 0, 255), width=7, joint='curve')
    im.save(path)
    print('made warning', path, im.size)

ROOT = 'E:/UST_work/dk_miku'
G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DEPLOYS = [G, ROOT + '/DK_Dual', ROOT + '/DK_Miku']
TRASH = 'I:/_trash_ust_work/saw_legacy_purge_20261116'

# --- 1) purge legacy saw sounds from every deploy, keep only the clean set ---
KEEP_SOUNDS = {'alert.ogg', 'attack.ogg', 'dodge.ogg', 'dkBaguette.ogg'}
PURGE_SOUNDS = ['alertDouble.ogg', 'alertTriple.ogg', 'alertQuadruple.ogg',
                'dkAlert1.ogg', 'dkAlert2.ogg', 'dkAlert3.ogg',
                'dkSawAttack.ogg', 'dkDodgeSound.ogg', 'dodge01.ogg', 'sawbladeHit.ogg']
os.makedirs(TRASH, exist_ok=True)
for d in DEPLOYS:
    for n in PURGE_SOUNDS:
        p = os.path.join(d, 'sounds', n)
        if os.path.exists(p):
            dst = os.path.join(TRASH, os.path.basename(d), n)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.move(p, dst)
            print('purged sound', os.path.basename(d), n)

# purge legacy saw image/animation assets (old rotating saw, old alert atlas)
PURGE_IMG = ['dkSawAssets', 'dk_saw_alert.png', 'dk_saw_alert.xml']
for d in DEPLOYS:
    for n in PURGE_IMG:
        p = os.path.join(d, 'images', n)
        if os.path.exists(p):
            dst = os.path.join(TRASH, os.path.basename(d), n)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            if os.path.isdir(p):
                shutil.move(p, dst)
            else:
                shutil.move(p, dst)
            print('purged image', os.path.basename(d), n)

# --- 2) clean script ---
SCRIPT = '''--[[
  DK_Saw.lua - GOD+ dodge, clean re-port (v11.12).
  ONE rising 3-beep alert (sounds/alert.ogg) per wave; no stacked bell files.
  3rd beep = baguette thrust out-and-back; judge 0.30s later (>=300ms window).
  Black overlay is hard-reset to 0 after every wave - no global dimming.
  BotPlay auto-dodges; SPACE handled by DK_Fun.lua (dkDodgeActive).
  All text ASCII (a fullwidth dash once broke LuaJIT).
]]

local ALERT_GAP = 0.30
local JUDGE_DELAY = 0.32

local ALERT_TAG = 'dkSawAlert'
local BAG_TAG   = 'dkSawBag'
local POP_TAG   = 'dkSawDodged'
local BLACK_TAG = 'dkSawBlack'

local BAG_X0, BAG_Y0 = -520, 430
local BAG_X1, BAG_Y1 = 1180, 300
local BAG_SCALE = 0.85

local waves = {}
local seq = 0
local spritesReady = false
local blackHardOffTimer = 0

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

local function blackOff()
    pcall(cancelTween, 'dkSawBlackIn')
    pcall(cancelTween, 'dkSawBlackOut')
    sp(BLACK_TAG .. '.alpha', 0)
end

local function ensureSprites()
    if spritesReady then return end

    if not luaSpriteExists(ALERT_TAG) then
        pcall(makeLuaSprite, ALERT_TAG, 'dkSawWarning', 0, 0)
        pcall(setObjectCamera, ALERT_TAG, 'other')
        pcall(addLuaSprite, ALERT_TAG, true)
        pcall(screenCenter, ALERT_TAG)
        pcall(scaleObject, ALERT_TAG, 0.9, 0.9, false)
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
    blackOff()
end

function onEvent(name, v1, v2)
    if name ~= 'Dodge Mechanic' and name ~= 'DK Saw' then return end

    ensureSprites()
    -- hard reset any previous wave's dim before starting a new one
    blackOff()
    local now = songMs()
    seq = seq + 1
    waves[#waves + 1] = {
        id = seq,
        t1 = now,
        tAlertEnd = now + 800,          -- single 3-beep alert is ~1.08s; main hits in first 0.8s
        tJudge = now + 800 + JUDGE_DELAY * 1000,
        stage = 0,
        dodged = false,
    }
end

local function updateWaves()
    local now = songMs()
    local dodgeOn = gv('dkDodgeActive', false) == true

    for i = 1, #waves do
        local w = waves[i]
        if w.stage >= 1 and w.stage < 3 and not w.dodged then
            if botPlaying() or dodgeOn then w.dodged = true end
        end
    end

    for i = 1, #waves do
        local w = waves[i]

        if w.stage == 0 and now >= w.t1 then
            w.stage = 1
            pcall(playSound, 'alert', 1)
            sp(ALERT_TAG .. '.alpha', 1)
            pcall(screenCenter, ALERT_TAG)
            pcall(doTweenAlpha, 'dkSawAlertIn', ALERT_TAG, 0.35, 0.25, 'linear')
            pcall(cameraFlash, 'game', 'FF5555', 0.15, true)
        end

        -- 3rd beep of the single alert file (~0.45s in): baguette thrust
        if w.stage == 1 and now >= w.t1 + 450 then
            w.stage = 2
            sp(BAG_TAG .. '.x', BAG_X0)
            sp(BAG_TAG .. '.y', BAG_Y0)
            sp(BAG_TAG .. '.angle', 0)
            sp(BAG_TAG .. '.visible', true)
            pcall(doTweenX, 'dkBagOutX', BAG_TAG, BAG_X1, 0.13, 'expoOut')
            pcall(doTweenY, 'dkBagOutY', BAG_TAG, BAG_Y1, 0.13, 'expoOut')
            pcall(runTimer, 'dkBagBack', 0.17)
        end

        if w.stage == 2 and now >= w.tJudge then
            w.stage = 3
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
            blackHardOffTimer = now + 250
            pcall(runTimer, 'dkSawCleanup', 0.3)
        end
    end

    if blackHardOffTimer > 0 and now >= blackHardOffTimer then
        blackHardOffTimer = 0
        blackOff()
        sp(ALERT_TAG .. '.alpha', 0)
        sp(BAG_TAG .. '.visible', false)
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
    if tag == 'dkBagBack' then
        pcall(doTweenX, 'dkBagInX', BAG_TAG, BAG_X0, 0.16, 'expoIn')
        pcall(doTweenY, 'dkBagInY', BAG_TAG, BAG_Y0, 0.16, 'expoIn')
    end
end

function onDestroy()
    sp(BAG_TAG .. '.visible', false)
    sp(ALERT_TAG .. '.alpha', 0)
    sp(POP_TAG .. '.alpha', 0)
    blackOff()
end
'''

assert all(b < 128 for b in SCRIPT.encode('utf-8')), 'non-ASCII in script'

make_warning_png(ROOT + '/_godmode/dkSawWarning.png')

for d in DEPLOYS:
    # copy clean assets
    shutil.copyfile(ROOT + '/_godmode/dkBaguette.png', d + '/images/dkBaguette.png')
    shutil.copyfile(ROOT + '/_godmode/dkSawWarning.png', d + '/images/dkSawWarning.png')
    # ensure clean sounds present (from original zip copy stored earlier)
    src_alert = os.path.join(TRASH, os.path.basename(d), 'dkAlert1.ogg')
    if os.path.exists(src_alert):
        shutil.copyfile(src_alert, d + '/sounds/alert.ogg')
    p = d + '/scripts/DK_Saw.lua'
    open(p, 'w', encoding='utf-8', newline='\n').write(SCRIPT)
    print('rebuilt', p)

import sys
sys.path.insert(0, 'E:/UST_work/_pylibs')
from lupa import LuaRuntime
LuaRuntime().compile(SCRIPT)
print('LUA COMPILE OK')
