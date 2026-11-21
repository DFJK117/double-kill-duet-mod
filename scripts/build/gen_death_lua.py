# -*- coding: utf-8 -*-
"""Generate ASCII-only DK_Death.lua with Chinese text as UTF-8 byte escapes."""
OUT = r'E:/UST_work/dk_miku/scripts/DK_Death_v1121.lua'

def esc(s):
    # Lua decimal byte escapes -> UTF-8 bytes -> renders Chinese via dkCN.ttf
    return ''.join('\\%d' % b for b in s.encode('utf-8'))

# Chinese death-cause lines (upper-middle, on top of death animation)
CAUSES = {
    'trap':   '死因：踩到陷阱，当场去世',
    'warn':   '死因：漏按警告，当场去世',
    'opwarn': '死因：放过对手警告，当场去世',
    'saw':    '死因：没躲开电锯，被劈了',
    'miss':   '死因：血量耗尽',
}
WATERMARK_GODPLUS = 'DFJK117  GOD+'   # ASCII, only on GOD+ difficulty
WATERMARK_DEFAULT = 'DFJK117'         # ASCII, all other difficulties

lines = []
lines.append('--[[')
lines.append('  DK_Death.lua v11.21 - watermark / death cause / fast-forward')
lines.append('  Watermark top-left (camHud), Chinese death cause on top of death')
lines.append('  animation (camOther, upper-middle), number 1 = +5s.')
lines.append('  Chinese strings are UTF-8 byte escapes; source stays ASCII.')
lines.append('  Cause set by DK_God.lua / DK_Saw.lua via setVar(dkDeathCause, ...).')
lines.append(']]')
lines.append("local FONT = 'dkCN.ttf'")
lines.append("local WATER_TAG = 'dkWaterMark'")
lines.append("local CAUSE_TAG = 'dkCauseText'")
# Watermark is decided at runtime by difficulty:
#   week difficulties = hard,GOD,GOD+  ->  storyDifficulty index 2 == GOD+
#   fallback: getText('difficultyText') containing 'GOD+'
lines.append('local WATER_GODPLUS = %r' % WATERMARK_GODPLUS)
lines.append('local WATER_DEFAULT = %r' % WATERMARK_DEFAULT)
lines.append('')
lines.append('local causeMap = {')
for k in ['trap','warn','opwarn','saw','miss']:
    lines.append('    %s = "%s",' % (k, esc(CAUSES[k])))
lines.append('}')
lines.append('')
lines.append('''local function gv(k, d)
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
''')

src = '\n'.join(lines) + '\n'
# hard guarantee: ASCII only
src.encode('ascii')
open(OUT, 'w', encoding='ascii', newline='\n').write(src)
print('written', OUT, len(src), 'bytes, ascii OK')
for k, v in CAUSES.items():
    print(' ', k, '=', v)
