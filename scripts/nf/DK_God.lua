--============================================================
--  DK_God.lua  v1   DK_Duet / NovaFlare Engine   (2026-11-15)
--
--  ① GOD 模式已删除（2026-11-21 用户要求：F4 热键 / GOD MODE 徽章 /
--     'DK God' 事件全部撇掉，god 恒 false）。
--     本脚本现在只剩 ② Trap/Warn 秒杀判定 + ③ 对手侧 Warn 轮询。
--
--  ② 两个自定义 type 按键的死亡判定（谱面 noteType 字段）：
--       'DK Trap' = 原版箭头造型（黑内红边）+ 箭头上套红色光环  →  按到即死
--       'DK Warn' = 黄色三角 + 黑色感叹号警告牌                  →  漏按即死
--     贴图由 custom_notetypes/DK Trap.txt / DK Warn.txt 指定
--     （texture = 'dk_trap' / 'dk_warn'），同时关掉 RGB 染色，
--     保证红框和黄色三角不被按道的颜色染掉。
--
--  ③ 对手侧（轨道 4-7）的特殊键：
--     引擎对「对手侧音符漏按」不会调 noteMiss（只对 mustPress 音符调），
--     所以对手侧 DK Warn 由本脚本自己轮询判定：
--     音符过了判定线且没被打中 -> 秒杀。
--     对手侧 DK Trap 无需特殊处理：引擎的 opponentNoteHit 也会调 goodNoteHit，
--     上面的 goodNoteHit 回调已经覆盖。
--
--  死亡实现：把血条直接归零 -> 引擎每帧 doDeathCheck() 触发 Game Over
--  （练习模式 practiceMode 下引擎本身免死，这是引擎既定行为，不改）。
--
--  纯 Lua、零 hscript / 零 runHaxeCode。所用 API 都在 FunkinLua /
--  ExtraFunctions / ReflectionFunctions 里逐个核对过：
--  keyboardJustPressed、setProperty、getProperty、getVar、setVar、
--  makeLuaSprite、addLuaSprite、removeLuaSprite、setObjectCamera。
--============================================================

local TRAP_TYPE = 'DK Trap'
local WARN_TYPE = 'DK Warn'

local god = false          -- 恒 false：GOD 模式已删，永不可开
local killCount = 0

-- 对手侧 DK Warn 轮询用：记录已判定过的音符，避免重复触发
local oppWarnChecked = {}
local oppWarnKillCount = 0

local function gp(key, default)
    local ok, v = pcall(getProperty, key)
    if not ok or v == nil then return default end
    return v
end
local function sp(key, value)
    pcall(setProperty, key, value)
end
local function sv(name, value)
    if type(setVar) == 'function' then pcall(setVar, name, value) end
end
local function gv(name)
    if type(getVar) == 'function' then
        local ok, v = pcall(getVar, name)
        if ok then return v end
    end
    return nil
end

local function publish()
    sv('dkGodMode', god)
end

--============================================================
--  死亡
--============================================================
local function killPlayer(cause)
    if god then return false end
    local h = tonumber(gp('health', 1)) or 1
    if h <= 0.001 then return false end
    killCount = killCount + 1
    sv('dkGodKills', killCount)
    -- 血条归零 -> 引擎 doDeathCheck() -> Game Over
    sp('health', 0)
    sv('dkGodLastKill', killCount)
    sv('dkDeathCause', cause or 'miss')
    return true
end

--============================================================
--  Botplay 判定（引擎无关兜底）
--
--  Botplay 是「看谱演示」，绝不能让 Trap/Warn 把 bot 自己杀死：
--   · 引擎层已在 DK Trap.txt 里设 ignoreNote=true，
--     PlayState.goodNoteHit 开头 `if(cpuControlled && note.ignoreNote) return`
--     会让 bot 自动打音符时跳过 Trap；漏按判定那支也有 `!ignoreNote`。
--   · 这里再加一道 Lua 兜底：只要 botPlay 开着，所有死亡判定直接跳过。
--     即使将来换了引擎/改了 noteType 配置，bot 也绝不会被自己按死。
--
--  引擎 PlayState 有 public var cpuControlled（botplay 开关），
--  并在 2740 行 setOnScripts('botPlay', cpuControlled) 注入脚本变量。
--  两个都试，取到哪个算哪个。
--============================================================
local function botPlaying()
    local ok, v = pcall(getProperty, 'cpuControlled')
    if ok and v == true then return true end
    if type(getVar) == 'function' then
        local ok2, v2 = pcall(getVar, 'botPlay')
        if ok2 and v2 == true then return true end
    end
    return false
end

--============================================================
--  对手侧 DK Warn 轮询判定
--
--  引擎只对「玩家侧(mustPress)」音符漏按时调 noteMiss，
--  对手侧(轨道 4-7)音符漏按不会触发任何 Lua 回调。
--  所以这里自己轮询 PlayState.notes：
--    · noteType == 'DK Warn'
--    · not mustPress（对手侧）
--    · strumTime 已过判定线（songPosition - strumTime > 安全偏移）
--    · wasGoodHit == false（没被打中）
--  满足即秒杀。
--============================================================
local function checkOppWarn()
    if god then return end
    if botPlaying() then return end -- botplay 演示：对手侧 Warn 也不杀 bot
    local ok, notes = pcall(getProperty, 'notes')
    if not ok or notes == nil then return end

    local songPos = tonumber(gp('songPosition', nil))
    if songPos == nil then
        songPos = tonumber(gp('conductor.songPosition', nil))
    end
    if songPos == nil then return end

    local safe = tonumber(gp('conductor.safeZoneOffset', 0)) or 0
    local n = 0
    while n < #notes do
        local note = notes[n + 1]
        n = n + 1
        if note ~= nil then
            local nt = note.noteType
            local mustPress = note.mustPress
            local hit = note.wasGoodHit
            local st = tonumber(note.strumTime)
            if nt == WARN_TYPE and mustPress == false and hit ~= true
                and st ~= nil and (songPos - st) > safe then
                local key = tostring(st) .. ':' .. tostring(note.noteData)
                if not oppWarnChecked[key] then
                    oppWarnChecked[key] = true
                    oppWarnKillCount = oppWarnKillCount + 1
                    sv('dkGodOppWarnKills', oppWarnKillCount)
                    killPlayer('opwarn')
                    return
                end
            end
        end
    end
end

--============================================================
--  回调
--============================================================
-- 玩家命中：'DK Trap' 按到即死（botplay 下跳过，绝不杀死 bot）
function goodNoteHit(id, dir, noteType, sus)
    if noteType == TRAP_TYPE and not botPlaying() then
        killPlayer('trap')
    end
end

-- 玩家漏按：'DK Warn' 漏按即死（botplay 下跳过）
function noteMiss(id, noteData, noteType, isSustainNote)
    if noteType == WARN_TYPE and not botPlaying() then
        killPlayer('warn')
    end
end

function onUpdate(elapsed)
    checkOppWarn()
end

function onUpdatePost(elapsed)
    checkOppWarn()
end

function onCreatePost()
    publish()          -- dkGodMode 恒 false（DK_Push.lua 的免疫分支永不触发）
end
