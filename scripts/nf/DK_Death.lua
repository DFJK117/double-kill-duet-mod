--[[
  DK_Death.lua v11.21 - watermark / death cause / fast-forward
  Watermark top-left (camHud), Chinese death cause on top of death
  animation (camOther, upper-middle), number 1 = +5s.
  Chinese strings are UTF-8 byte escapes; source stays ASCII.
  Cause set by DK_God.lua / DK_Saw.lua via setVar(dkDeathCause, ...).
]]
local FONT = 'dkCN.ttf'
local WATER_TAG = 'dkWaterMark'
local CAUSE_TAG = 'dkCauseText'
local WATER_GODPLUS = 'DFJK117  GOD+'
local WATER_DEFAULT = 'DFJK117'

local causeMap = {
    trap = "\230\173\187\229\155\160\239\188\154\232\184\169\229\136\176\233\153\183\233\152\177\239\188\140\229\189\147\229\156\186\229\142\187\228\184\150",
    warn = "\230\173\187\229\155\160\239\188\154\230\188\143\230\140\137\232\173\166\229\145\138\239\188\140\229\189\147\229\156\186\229\142\187\228\184\150",
    opwarn = "\230\173\187\229\155\160\239\188\154\230\148\190\232\191\135\229\175\185\230\137\139\232\173\166\229\145\138\239\188\140\229\189\147\229\156\186\229\142\187\228\184\150",
    saw = "\230\173\187\229\155\160\239\188\154\230\178\161\232\186\178\229\188\128\231\148\181\233\148\175\239\188\140\232\162\171\229\138\136\228\186\134",
    miss = "\230\173\187\229\155\160\239\188\154\232\161\128\233\135\143\232\128\151\229\176\189",
}

local function gv(k, d)
    local ok, v = pcall(getVar, k)
    if ok and v ~= nil then return v end
    return d
end
local function sp(k, v) pcall(setProperty, k, v) end

local causeShown = false
local lastWaterText = nil

-- GOD+ only when storyDifficulty index == 2 (week = hard,GOD,GOD+).
-- Fallback: read Song metadata chart tag via getProperty('SONG.difficulty'),
-- then via player1 character ('bf-god' = a GOD/GOD+ chart).
local function isGodPlus()
    local ok, idx = pcall(getProperty, 'storyDifficulty')
    if ok and type(idx) == 'number' then
        return idx == 2
    end
    local ok2, d = pcall(getProperty, 'SONG.difficulty')
    if ok2 and type(d) == 'string' then
        return string.find(d, 'GOD+', 1, true) ~= nil
    end
    local ok3, p1 = pcall(getProperty, 'player1')
    if ok3 and p1 == 'bf-god' then
        return true
    end
    return false
end

local function desiredWater()
    return isGodPlus() and WATER_GODPLUS or WATER_DEFAULT
end

local function makeWater()
    local want = desiredWater()
    if luaTextExists(WATER_TAG) then
        if want ~= lastWaterText then
            pcall(setTextString, WATER_TAG, want)
            lastWaterText = want
        end
        return
    end
    pcall(makeLuaText, WATER_TAG, want, 520, 8, 6)
    lastWaterText = want
    pcall(setTextFont, WATER_TAG, FONT)
    pcall(setTextSize, WATER_TAG, 20)
    pcall(setTextAlignment, WATER_TAG, 'left')
    pcall(setTextBorder, WATER_TAG, 1.5, '000000')
    pcall(setObjectCamera, WATER_TAG, 'hud')
    pcall(addLuaText, WATER_TAG)
end

function onCreatePost()
    makeWater()
    causeShown = false
end

-- number 1 (FlxKey.ONE) -> fast forward 5 seconds
function onUpdate(elapsed)
    -- keep watermark in sync if difficulty changed without a state rebuild
    if luaTextExists(WATER_TAG) then
        local want = desiredWater()
        if want ~= lastWaterText then
            pcall(setTextString, WATER_TAG, want)
            lastWaterText = want
        end
    end
    local ok, pressed = pcall(keyboardJustPressed, 'ONE')
    if ok and pressed then
        local pok, pos = pcall(getSongPosition)
        if pok and type(pos) == 'number' then
            sp('songPosition', pos + 5000)
        end
    end
end

-- engine calls this as the Game Over substate opens (death animation running)
function onGameOverStart()
    if causeShown then return end
    causeShown = true
    local key = tostring(gv('dkDeathCause', 'miss'))
    local msg = causeMap[key] or causeMap.miss
    if luaTextExists(CAUSE_TAG) then return end
    pcall(makeLuaText, CAUSE_TAG, msg, 1000, 0, 96)
    pcall(setTextFont, CAUSE_TAG, FONT)
    pcall(setTextSize, CAUSE_TAG, 30)
    pcall(setTextAlignment, CAUSE_TAG, 'center')
    pcall(setTextBorder, CAUSE_TAG, 2, '000000')
    pcall(screenCenter, CAUSE_TAG, 'x')
    pcall(setObjectCamera, CAUSE_TAG, 'other')
    pcall(addLuaText, CAUSE_TAG)
end

function onDestroy()
    causeShown = false
end

