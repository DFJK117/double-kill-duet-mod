# -*- coding: utf-8 -*-
"""v11.13: SAW = QT OFFICIAL alert animation + QT OFFICIAL 3-beep rising bell
         + baguette (top loaf from user's white-background photo) as projectile.

No hand-drawn replacements. No stacked/mixed audio.

  warning sprite : dk_saw_alert.png/xml  (QT attack_alert_NEW, sparrow,
                   prefixes dkSawAlert1_ / dkSawAlert2_ / dkSawAttack_)
  sound 3 beeps  : dkAlert1 / dkAlert2 / dkAlert3
                   = QT alert / alertDouble / alertTriple, 0.6s apart (no overlap)
  projectile     : dkBaguette.png (top baguette, user source), thrust out-and-back
  judge          : >=300ms after 3rd beep; SPACE dodges; BotPlay auto-dodges

Deploys to all three roots; deletes v11.12 hand-drawn leftovers; packs full zip.
"""
import os, shutil, zipfile, hashlib, sys
sys.path.insert(0, r'E:/UST_work/_pylibs')
from lupa import LuaRuntime

ROOT = r'E:/UST_work/dk_miku'
GAMEMOD = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ROOTS = [GAMEMOD, ROOT + '/DK_Dual', ROOT + '/DK_Miku']
STAGE = ROOT + '/_godmode'
QT_SND = (r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/qt_psyched-up-edition_v22_0832a'
          '/assets/shared/sounds/hazard')
ZIP_OUT = ROOT + '/DK_Duet_FULL_v11.13_GODplus_20261116.zip'

# ---- source files that are already staged / authoritative ----
SRC_IMG = {
    'dk_saw_alert.png': STAGE + '/dk_saw_alert.png',
    'dk_saw_alert.xml': STAGE + '/dk_saw_alert.xml',
    'dkBaguette.png':   STAGE + '/dkBaguette_source.png',
}
# QT official bells. dkAlert1 must be the true QT alert (f39a.. was a wrong file).
SRC_SND = {
    'dkAlert1.ogg': QT_SND + '/alert.ogg',
    'dkAlert2.ogg': QT_SND + '/alertDouble.ogg',
    'dkAlert3.ogg': QT_SND + '/alertTriple.ogg',
    'dkSawAttack.ogg': QT_SND + '/sawbladeHit.ogg',
    'dkDodgeSound.ogg': QT_SND + '/dodge01.ogg',
}
# hand-drawn leftovers from v11.12 we are removing
PURGE_IMG = ['dkSawWarning.png', 'dkDodged.png']
PURGE_SND = ['alert.ogg', 'attack.ogg', 'dodge.ogg', 'dkBaguette.ogg']

LUA = r'''--[[
  DK_Saw.lua v11.13 - QT OFFICIAL saw-dodge, unified clean re-port.
  Warning: QT dk_saw_alert animation (1 -> 2 -> 3 dots) with its own 3 bells.
  Sound:   QT alert / alertDouble / alertTriple, 0.6s apart -> no overlap.
  Projectile: baguette (top loaf), thrust at 3rd bell, retract, judge +0.30s.
  SPACE to dodge (DK_Fun.lua dkDodgeActive); BotPlay auto-dodges.
  ASCII-only Lua source. One clock: getSongPosition(). No black overlay.
]]
local GAP = 600
local AFTER_3RD = 300
local JUDGE_MS = 2 * GAP + AFTER_3RD

local BAG_TAG = 'dkSawBag'
local ALERT_TAG = 'dkSawAlert'
local BAG_X0, BAG_Y0 = -520, 430
local BAG_X1, BAG_Y1 = 1180, 300
local BAG_SCALE = 0.85

local waves = {}
local seq = 0
local ready = false

local function gv(k, d)
    local ok, v = pcall(getVar, k)
    if ok and v ~= nil then return v end
    return d
end
local function sp(k, v) pcall(setProperty, k, v) end
local function songMs()
    local ok, v = pcall(getSongPosition)
    if ok and type(v) == 'number' then return v end
    return 0
end
local function botPlaying()
    local a = gv('botPlay', false)
    local b = false
    pcall(function() b = getProperty('cpuControlled') == true end)
    return a == true or b == true
end

local function ensure()
    if ready then return end
    if not luaSpriteExists(ALERT_TAG) then
        pcall(makeAnimatedLuaSprite, ALERT_TAG, 'dk_saw_alert', 0, 0, 'sparrow')
        pcall(addAnimationByPrefix, ALERT_TAG, 'a1', 'dkSawAlert1_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, 'a2', 'dkSawAlert2_', 24, false)
        pcall(addAnimationByPrefix, ALERT_TAG, 'a3', 'dkSawAttack_', 24, false)
        pcall(setObjectCamera, ALERT_TAG, 'other')
        pcall(addLuaSprite, ALERT_TAG, true)
        pcall(screenCenter, ALERT_TAG)
        sp(ALERT_TAG .. '.alpha', 0)
    end
    if not luaSpriteExists(BAG_TAG) then
        pcall(makeLuaSprite, BAG_TAG, 'dkBaguette', BAG_X0, BAG_Y0)
        pcall(scaleObject, BAG_TAG, BAG_SCALE, BAG_SCALE, false)
        pcall(setObjectCamera, BAG_TAG, 'other')
        pcall(addLuaSprite, BAG_TAG, false)
        sp(BAG_TAG .. '.visible', false)
    end
    ready = true
end

local function hideAll()
    sp(ALERT_TAG .. '.alpha', 0)
    sp(BAG_TAG .. '.visible', false)
end

function onCreatePost()
    ensure()
    hideAll()
end

function onEvent(name, v1, v2)
    if name ~= 'Dodge Mechanic' and name ~= 'DK Saw' then return end
    ensure()
    hideAll()
    local now = songMs()
    seq = seq + 1
    waves[#waves + 1] = {
        id = seq, t0 = now, stage = 0, dodged = false,
        t1 = now + GAP, t2 = now + 2 * GAP, tJudge = now + JUDGE_MS,
    }
end

local function updateWaves()
    local now = songMs()
    local dodgeOn = gv('dkDodgeActive', false) == true
    for i = 1, #waves do
        local w = waves[i]
        -- dodge may be pressed any time from 1st bell through judging
        if w.stage >= 1 and w.stage < 4 and not w.dodged then
            if botPlaying() or dodgeOn then w.dodged = true end
        end

        if w.stage == 0 and now >= w.t0 then
            w.stage = 1
            pcall(playSound, 'dkAlert1', 1)
            pcall(playAnim, ALERT_TAG, 'a1', true)
            sp(ALERT_TAG .. '.alpha', 1)
            pcall(screenCenter, ALERT_TAG)
        elseif w.stage == 1 and now >= w.t1 then
            w.stage = 2
            pcall(playSound, 'dkAlert2', 1)
            pcall(playAnim, ALERT_TAG, 'a2', true)
            pcall(screenCenter, ALERT_TAG)
        elseif w.stage == 2 and now >= w.t2 then
            w.stage = 3
            pcall(playSound, 'dkAlert3', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)
            pcall(screenCenter, ALERT_TAG)
            -- baguette thrust out-and-back exactly on the 3rd bell
            sp(BAG_TAG .. '.x', BAG_X0)
            sp(BAG_TAG .. '.y', BAG_Y0)
            sp(BAG_TAG .. '.angle', 0)
            sp(BAG_TAG .. '.visible', true)
            pcall(doTweenX, 'dkBagOutX', BAG_TAG, BAG_X1, 0.13, 'expoOut')
            pcall(doTweenY, 'dkBagOutY', BAG_TAG, BAG_Y1, 0.13, 'expoOut')
            pcall(runTimer, 'dkBagBack', 0.17)
        elseif w.stage == 3 and now >= w.tJudge then
            w.stage = 4
            if w.dodged then
                pcall(playSound, 'dkDodgeSound', 1)
                pcall(setVar, 'dkSawDodged', true)
            else
                pcall(playSound, 'dkSawAttack', 1)
                sp('health', 0)
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
            end
            pcall(runTimer, 'dkSawCleanup', 0.25)
        end
    end
    local keep = {}
    for i = 1, #waves do
        if waves[i].stage < 4 or now < waves[i].tJudge + 600 then
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
    elseif tag == 'dkSawCleanup' then
        hideAll()
    end
end

function onDestroy()
    hideAll()
end
'''


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    # 0) Lua must compile before touching anything
    L = LuaRuntime()
    r = L.eval('(function(s) local f,e=load(s) return {ok=(f~=nil),err=tostring(e)} end)(%r)' % LUA)
    if not r['ok']:
        print('LUA COMPILE FAIL', r['err'])
        return
    print('LUA compile OK')

    for root in ROOTS:
        print('=== deploy', root)
        for name, src in SRC_IMG.items():
            assert os.path.exists(src), 'missing ' + src
            dst = os.path.join(root, 'images', name)
            shutil.copyfile(src, dst)
            print('  IMG', md5(dst)[:10], name)
        for name, src in SRC_SND.items():
            assert os.path.exists(src), 'missing ' + src
            dst = os.path.join(root, 'sounds', name)
            shutil.copyfile(src, dst)
            print('  SND', md5(dst)[:10], name)
        for name in PURGE_IMG:
            p = os.path.join(root, 'images', name)
            if os.path.exists(p):
                shutil.move(p, os.path.join(STAGE, '_purged_' + name))
                print('  PURGE IMG', name)
        for name in PURGE_SND:
            p = os.path.join(root, 'sounds', name)
            if os.path.exists(p):
                shutil.move(p, os.path.join(STAGE, '_purged_' + name))
                print('  PURGE SND', name)
        lp = os.path.join(root, 'scripts', 'DK_Saw.lua')
        with open(lp, 'w', encoding='ascii', newline='\n') as fh:
            fh.write(LUA)
        print('  LUA', md5(lp)[:10])

    # pack from game-side authoritative tree
    pref = 'DK_Duet/'
    with zipfile.ZipFile(ZIP_OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for base, dirs, files in os.walk(GAMEMOD):
            dirs[:] = [d for d in dirs if d not in ('.git', '__pycache__')]
            for f in files:
                p = os.path.join(base, f)
                rel = os.path.relpath(p, GAMEMOD).replace('\\', '/')
                z.write(p, pref + rel)
    print('ZIP', ZIP_OUT, os.path.getsize(ZIP_OUT), 'items',
          len(zipfile.ZipFile(ZIP_OUT).namelist()))


if __name__ == '__main__':
    main()
