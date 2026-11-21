--[[
  DK_Saw.lua v11.25 - baguette thrust + instant-hit judgement
  timeline per event (GAP=300ms between bells):
    t0          bell1 (deng)
    t1=t0+300   bell2 (deng)
    t2=t0+600   bell3 (ci) + baguette OUT starts
    t2..t2+100  OUT: 100ms fast thrust (sineIn accel)
    tHit=t2+100 HIT: judge at impact. Dodge counts ONLY if pressed before
                this instant. Not dodged -> health=0 immediately (no delay).
    tHit..+300  HOLD: 300ms shake/linger (visible when dodged)
    +300..+600  BACK: 300ms retract
  Fix vs v11.20: judgement moved from ci+900ms (after whole anim) to the
  impact instant ci+100ms, and dodge is locked at impact so a late SPACE
  press can no longer fake a dodge ("failed but not dead" bug).
  Dodge: SPACE, DK_Fun dkDodgeActive (window 1.0s). Botplay always dodges.
  ASCII-only Lua source. One clock: getSongPosition(). No black overlay.
]]
local GAP = 300
local BAG_OUT = 100
local BAG_HOLD = 300
local BAG_BACK = 300
local T_HIT = BAG_OUT                    -- 100ms from ci to impact
local JUDGE_MS = 2 * GAP + T_HIT         -- 700ms from event start to impact
local ANIM_TAIL = BAG_HOLD + BAG_BACK    -- 600ms after impact

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
        pcall(addAnimationByPrefix, ALERT_TAG, 'a3', 'dkSawAttack_', 24, true)
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
        id = seq, t0 = now, stage = 0, dodged = false, judged = false,
        t1 = now + GAP, t2 = now + 2 * GAP,
        tHit = now + JUDGE_MS,
        tHoldEnd = now + JUDGE_MS + BAG_HOLD,
        tBackEnd = now + JUDGE_MS + ANIM_TAIL,
        backStarted = false,
    }
end

local function updateWaves()
    local now = songMs()
    local dodgeOn = gv('dkDodgeActive', false) == true
    for i = 1, #waves do
        local w = waves[i]

        -- bell sequence
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
            pcall(playSound, 'dkSawWhir', 1)
            pcall(playAnim, ALERT_TAG, 'a3', true)
            pcall(screenCenter, ALERT_TAG)
            -- fast 100ms thrust
            sp(BAG_TAG .. '.x', BAG_X0)
            sp(BAG_TAG .. '.y', BAG_Y0)
            sp(BAG_TAG .. '.angle', 0)
            sp(BAG_TAG .. '.visible', true)
            pcall(doTweenX, 'dkBagOutX', BAG_TAG, BAG_X1, BAG_OUT / 1000, 'sineIn')
            pcall(doTweenY, 'dkBagOutY', BAG_TAG, BAG_Y1, BAG_OUT / 1000, 'sineIn')
        end

        -- pre-impact: only presses BEFORE tHit count as a dodge
        if w.stage == 3 and now < w.tHit then
            if not w.dodged and (botPlaying() or dodgeOn) then
                w.dodged = true
            end
        end

        -- impact: lock the result at this instant, no delayed judgement
        if w.stage == 3 and now >= w.tHit and not w.judged then
            w.judged = true
            w.stage = 4
            pcall(cancelTween, 'dkBagOutX')
            pcall(cancelTween, 'dkBagOutY')
            sp(BAG_TAG .. '.x', BAG_X1)
            sp(BAG_TAG .. '.y', BAG_Y1)
            if w.dodged then
                pcall(playSound, 'dkDodgeSound', 1)
                pcall(setVar, 'dkSawDodged', true)
            else
                sp('health', 0)
                pcall(setVar, 'dkDeathCause', 'saw')
                pcall(cameraFlash, 'game', 'FF2222', 0.4, true)
                pcall(setVar, 'dkSawKilled', true)
            end
        end

        -- post-impact animation: 300ms shake/linger + 300ms retract
        if w.stage == 4 then
            if now < w.tHoldEnd then
                local ph = (now - w.tHit) * 0.05
                sp(BAG_TAG .. '.x', BAG_X1 + math.sin(ph) * 6)
                sp(BAG_TAG .. '.y', BAG_Y1 + math.cos(ph * 1.3) * 4)
                sp(BAG_TAG .. '.angle', math.sin(ph * 0.8) * 8)
            elseif now < w.tBackEnd then
                if not w.backStarted then
                    w.backStarted = true
                    sp(BAG_TAG .. '.angle', 0)
                    pcall(doTweenX, 'dkBagInX', BAG_TAG, BAG_X0, BAG_BACK / 1000, 'sineInOut')
                    pcall(doTweenY, 'dkBagInY', BAG_TAG, BAG_Y0, BAG_BACK / 1000, 'sineInOut')
                end
            else
                w.stage = 5
                hideAll()
            end
        end
    end

    local keep = {}
    for i = 1, #waves do
        if waves[i].stage < 5 or now < waves[i].tBackEnd + 300 then
            keep[#keep + 1] = waves[i]
        end
    end
    waves = keep
end

function onUpdate(elapsed)
    updateWaves()
end

function onTimerCompleted(tag)
    if tag == 'dkSawCleanup' then
        hideAll()
    end
end

function onDestroy()
    hideAll()
end
