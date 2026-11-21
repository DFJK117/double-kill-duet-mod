# -*- coding: utf-8 -*-
"""把 Vs Impostor Legacy 的 Double Kill 裁成「单模组单曲目」。

白(第一对手) -> Momo      黑(第二对手) -> Teto      玩家 -> BF
第二对手默认隐藏且不唱歌；靠事件叫出(半透明)；两个新增 Note Type 控制独唱/合唱。
"""
import os, json, shutil, subprocess, sys

SRC = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods'
COZY = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/Monochrome_Cozy'
OUT = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
FFMPEG = r'C:/Users/Administrator/Documents/fosu-converter/ffmpeg.exe'
SONG = 'double-kill'

# ---------------------------------------------------------------- 工具
def cp(rel, dst=None, base=SRC):
    s = os.path.join(base, rel)
    if not os.path.exists(s):
        raise FileNotFoundError(s)
    d = os.path.join(OUT, dst or rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(s, d)
    return d

def put(rel, text):
    d = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    with open(d, 'w', encoding='utf-8', newline='\r\n') as f:
        f.write(text.replace('\r\n', '\n'))
    return d

def putb(rel, data):
    d = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    open(d, 'wb').write(data)
    return d

def jload(p):
    return json.load(open(p, encoding='utf-8-sig'))

if os.path.isdir(OUT):
    os.rename(OUT, OUT + '_old')
    print('旧目录已改名为', OUT + '_old')
os.makedirs(OUT, exist_ok=True)

# ---------------------------------------------------------------- 1. 音频 / 谱面 / 舞台
cp('songs/%s/Inst.ogg' % SONG)
cp('songs/%s/Voices.ogg' % SONG)
cp('stages/cargo.json')
cp('stages/cargo.lua')
for f in os.listdir(os.path.join(SRC, 'images/stages/airship/double-kill')):
    cp('images/stages/airship/double-kill/' + f)

chart = jload(os.path.join(SRC, 'data/double-kill/double-kill-hard.json'))
chart['player1'] = 'bf'
chart['player2'] = 'momo'
chart['gfVersion'] = 'teto'
retag = {'GF Sing': 'Opponent 2 Sing', 'blackDuo': 'Both Opponents Sing'}
n_retag = 0
for sec in chart['notes']:
    for n in sec['sectionNotes']:
        if len(n) > 3 and n[3] in retag:
            n[3] = retag[n[3]]
            n_retag += 1
putb('data/double-kill/double-kill-hard.json',
     json.dumps(chart, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))
cp('data/double-kill/events.json')          # 原曲 82 行特殊事件，原样保留
print('谱面：%d 个音符重打 Type，%d 行事件原样保留' % (n_retag, len(chart['events'])))

# ---------------------------------------------------------------- 2. 角色
# 玩家 BF（沿用大包自带 bf + defeat 换装，贴图全带）
for f in ('bf.json', 'bf-defeat-normal.json'):
    cp('characters/' + f)
for f in ('BOYFRIEND.png', 'BOYFRIEND.xml', 'defeatBf-normal.png', 'defeatBf-normal.xml'):
    cp('images/characters/bf/' + f)

# 第一对手 Momo：修正 healthicon（原来是 "icon-momo" 会去找 icon-icon-momo.png）
momo = jload(os.path.join(COZY, 'characters/momo-cozy.json'))
momo['healthicon'] = 'momo'
putb('characters/momo.json', json.dumps(momo, ensure_ascii=False, indent=1).encode('utf-8'))
for f in ('momo_assets.png', 'momo_assets.xml'):
    cp('images/characters/' + f, base=COZY)
cp('images/icons/icon-momo.png', base=COZY)

# 第二对手 Teto：GF 槽需要 danceLeft/danceRight/cheer，另需 sing*，合并成一份完整表
teto_src = jload(os.path.join(COZY, 'characters/teto-cozy.json'))
anims = {a['anim']: a for a in teto_src['animations']}
def anim(anim_name, prefix, loop=False):
    a = dict(anims[prefix])
    a['anim'] = anim_name
    return a
gfanims = []
for nm in ('idle', 'danceLeft', 'danceRight', 'sad', 'scared', 'hurt', 'combo50'):
    gfanims.append(anim(nm, 'idle', loop=(nm == 'idle')))
gfanims.append(anim('cheer', 'hey'))
gfanims.append(anim('hey', 'hey'))
for k, v in (('singLEFT', 'singLEFT'), ('singDOWN', 'singDOWN'),
             ('singUP', 'singUP'), ('singRIGHT', 'singRIGHT')):
    gfanims.append(anim(k, v))
teto = {
    'animations': gfanims,
    'image': 'characters/teto-2026',
    'healthicon': 'teto-cozy',
    'healthbar_colors': [233, 120, 145],
    'position': [-60, 20],
    'camera_position': [0, 0],
    'scale': 0.5,
    'flip_x': False,
    'sing_duration': 4,
    'no_antialiasing': False,
    'vocals_file': '',
    '_editor_isPlayer': False,
}
putb('characters/teto.json', json.dumps(teto, ensure_ascii=False, indent=1).encode('utf-8'))
for f in ('teto-2026.png', 'teto-2026.xml'):
    cp('images/characters/' + f, base=COZY)
cp('images/icons/icon-teto-cozy.png', base=COZY)

# ---------------------------------------------------------------- 3. 双人合成 icon (300x150, 两帧)
cmd = [FFMPEG, '-y', '-loglevel', 'error',
       '-i', os.path.join(COZY, 'images/icons/icon-momo.png'),
       '-i', os.path.join(COZY, 'images/icons/icon-teto-cozy.png'),
       '-filter_complex',
       '[0:v]crop=75:150:0:0[m0];[1:v]crop=75:150:75:0[t0];[m0][t0]hstack=inputs=2[f0];'
       '[0:v]crop=75:150:150:0[m1];[1:v]crop=75:150:225:0[t1];[m1][t1]hstack=inputs=2[f1];'
       '[f0][f1]hstack=inputs=2,format=rgba[o]',
       '-map', '[o]', '-frames:v', '1',
       os.path.join(OUT, 'images/icons/icon-momo-teto.png')]
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print('!! icon 合成失败:', r.stderr[-500:])
else:
    print('双人合成 icon 已生成 300x150')

# ---------------------------------------------------------------- 4. 曲目脚本（原三份 + 新增总控）
cp('data/double-kill/NewLogic.lua')
ev = open(os.path.join(SRC, 'data/double-kill/events.lua'), encoding='utf-8-sig').read()
ev = ev.replace("setProperty('gf.alpha', 1)", "setProperty('gf.alpha', 0.5)")
put('data/double-kill/events.lua', ev)

ICONS = r'''-- 双人合唱时把血条左边 icon 换成 Momo+Teto 合成图标
local specialIcon = 'momo-teto'

function onEvent(name, value1)
    if name == 'Both Opponents' then
        if value1 == '1' then
            runHaxeCode("game.iconP2.changeIcon('" .. specialIcon .. "');")
        else
            runHaxeCode("game.iconP2.changeIcon(game.dad.healthIcon);")
        end
    end
    if name == 'Legacy' and value1 == 'black' then
        runHaxeCode("game.iconP2.changeIcon('" .. specialIcon .. "');")
    end
    if name == 'Legacy' and value1 == 'not black' then
        runHaxeCode("game.iconP2.changeIcon(game.dad.healthIcon);")
    end
end

function opponentNoteHit(id, direction, noteType, isSustainNote)
    if noteType == 'Both Opponents Sing' or noteType == 'blackDuo' then
        runHaxeCode("game.iconP2.changeIcon('" .. specialIcon .. "');")
    end
end
'''
put('data/double-kill/icons.lua', ICONS)

DUET = r'''-- ============================================================
--  Double Kill Duet 总控（只在本曲加载）
--  第一对手 dad = Momo（常驻，普通音符默认由它唱）
--  第二对手 gf  = Teto（默认隐藏 / 不播放唱歌动作）
--
--  事件：
--    Legacy        black / not black / kill  -> 第二对手淡入(半透明)/淡出
--    Opponent Two  1 / 0                     -> 该段只让第二对手唱
--    Both Opponents 1 / 0                   -> 合唱段，两个对手都播动作
--  Note Type：
--    Opponent 2 Sing       -> 只让第二对手播放唱歌动作
--    Both Opponents Sing   -> 两个对手同时播放唱歌动作（和弦/合唱）
-- ============================================================
local SECOND_ALPHA   = 0.5    -- 第二对手半透明程度
local CHORD_AUTO_DUET = true  -- 同一时刻两个音符(和弦)时自动双播；不想自动就改 false

local secondOn   = false
local soloSecond = false
local chorus     = false
local lastStrum  = -1
local SING = {'singLEFT', 'singDOWN', 'singUP', 'singRIGHT'}

local function showSecond(on)
    secondOn = on
    cancelTween('duetSecondFade')
    doTweenAlpha('duetSecondFade', 'gf', on and SECOND_ALPHA or 0, 0.45, 'linear')
end

function onCreatePost()
    setProperty('gf.alpha', 0)
end

function onEvent(name, value1)
    if name == 'Legacy' then
        if value1 == 'black' or value1 == 'kill' then
            showSecond(true)
        elseif value1 == 'not black' then
            showSecond(false)
        end
    elseif name == 'Opponent Two' then
        soloSecond = (value1 == '1')
        if soloSecond then showSecond(true) end
    elseif name == 'Both Opponents' then
        chorus = (value1 == '1')
        if chorus then showSecond(true) end
    end
end

-- 只让第二对手唱时，先掐掉 dad 的默认动画
function opponentNoteHitPre(id, direction, noteType, isSustainNote)
    if noteType == 'Opponent 2 Sing' or (soloSecond and not chorus) then
        setPropertyFromGroup('notes', id, 'noAnimation', true)
    end
end

function opponentNoteHit(id, direction, noteType, isSustainNote)
    if not secondOn then return end

    local strum = getPropertyFromGroup('notes', id, 'strumTime')
    local isChord = (strum == lastStrum)
    lastStrum = strum

    local byType = (noteType == 'Opponent 2 Sing' or noteType == 'Both Opponents Sing'
                 or noteType == 'blackDuo' or noteType == 'GF Sing')
    local wantSecond = byType or soloSecond or chorus or (CHORD_AUTO_DUET and isChord)
    if not wantSecond then return end

    local a = SING[math.abs(direction) + 1]
    characterPlayAnim('gf', a, true)
    setProperty('gf.holdTimer', 0)

    -- 合唱：补上第一对手的动作（普通音符时引擎自己已播，这里兼容被 Pre 掐掉的情况）
    if noteType == 'Both Opponents Sing' or chorus or (CHORD_AUTO_DUET and isChord) then
        characterPlayAnim('dad', a, true)
        setProperty('dad.holdTimer', 0)
    end
end
'''
put('data/double-kill/duet.lua', DUET)

# ---------------------------------------------------------------- 5. custom_events（补齐缺失，且不重复播动画）
for f in ('Reactor Beep.lua', 'flash.lua', 'Camera Set Target.lua'):
    cp('custom_events/' + f)

STUB = lambda n, body: '-- %s：事件登记用；实际动作在 data/double-kill/duet.lua 统一处理\nfunction onEvent(name, v1, v2)\n%s\nend\n' % (n, body)
put('custom_events/Both Opponents.lua', STUB('Both Opponents', '    -- chorus 由 duet.lua 接管'))
put('custom_events/Opponent Two.lua',  STUB('Opponent Two',  '    -- soloSecond 由 duet.lua 接管'))
put('custom_events/Legacy.lua', '''-- Legacy：第二对手(Teto)出场/退场，实际动作在 data/double-kill/duet.lua
-- 参数：black = 淡入半透明 / not black = 淡出 / kill = 终局
function onEvent(name, v1, v2)
    -- no-op (duet.lua 处理)
end
''')
put('custom_events/Extra Cam Zoom.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Extra Cam Zoom' then return end
    local z = tonumber(v1) or 0.02
    setProperty('camGame.zoom', getProperty('camGame.zoom') + z)
    if v2 ~= nil and v2 ~= '' then
        setProperty('camHUD.zoom', getProperty('camHUD.zoom') + (tonumber(v2) or 0))
    end
end
''')
put('custom_events/Add Camera Zoom.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Add Camera Zoom' then return end
    if v1 ~= nil and v1 ~= '' then
        setProperty('camGame.zoom', getProperty('camGame.zoom') + (tonumber(v1) or 0))
    end
    if v2 ~= nil and v2 ~= '' then
        setProperty('camHUD.zoom', getProperty('camHUD.zoom') + (tonumber(v2) or 0))
    end
end
''')
put('custom_events/Set Cams.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Set Cams' then return end
    local t = string.lower(v1 or '')
    if t == 'bf' or t == 'b' then cameraSetTarget('boyfriend')
    elseif t == 'dad' or t == 'd' then cameraSetTarget('dad')
    elseif t == 'gf' or t == 'g' then cameraSetTarget('gf') end
end
''')

# ---------------------------------------------------------------- 6. custom_notetypes（两个 Type 按键）
put('custom_notetypes/Opponent 2 Sing.lua', '''-- Type: Opponent 2 Sing —— 只让第二对手(Teto)播放唱歌动作
function onCreate()
    for i = 0, getProperty('unspawnNotes.length')-1 do
        if getPropertyFromGroup('unspawnNotes', i, 'noteType') == 'Opponent 2 Sing' then
            setPropertyFromGroup('unspawnNotes', i, 'texture', '')
            setPropertyFromGroup('unspawnNotes', i, 'noAnimation', true)
        end
    end
end
''')
put('custom_notetypes/Both Opponents Sing.lua', '''-- Type: Both Opponents Sing —— Momo + Teto 同时播放唱歌动作（合唱/和弦）
function onCreate()
    for i = 0, getProperty('unspawnNotes.length')-1 do
        if getPropertyFromGroup('unspawnNotes', i, 'noteType') == 'Both Opponents Sing' then
            setPropertyFromGroup('unspawnNotes', i, 'texture', '')
            setPropertyFromGroup('unspawnNotes', i, 'noAnimation', false)
        end
    end
end
''')
put('custom_notetypes/blackDuo.lua', '''-- 兼容旧谱面残留的 blackDuo，动作统一由 duet.lua 处理
function onCreate()
    for i = 0, getProperty('unspawnNotes.length')-1 do
        if getPropertyFromGroup('unspawnNotes', i, 'noteType') == 'blackDuo' then
            setPropertyFromGroup('unspawnNotes', i, 'texture', '')
            setPropertyFromGroup('unspawnNotes', i, 'noAnimation', false)
        end
    end
end
''')

# ---------------------------------------------------------------- 7. week / pack
week = {
    'songs': [['double-kill', 'momo-teto', [200, 180, 220]]],
    'hiddenUntilUnlocked': False, 'hideFreeplay': False,
    'weekBackground': 'yellow', 'difficulties': 'hard',
    'weekCharacters': ['', '', ''], 'storyName': 'Double Kill Duet',
    'weekName': 'Momo & Teto', 'hideStoryMode': False,
    'weekBefore': 'tutorial', 'startUnlocked': True,
}
putb('weeks/dk-duet.json', json.dumps(week, ensure_ascii=False, indent=1).encode('utf-8'))
putb('pack.json', json.dumps({
    'name': 'Double Kill Duet (Momo & Teto)',
    'description': 'Single-song mod | BF vs Momo + Teto',
    'restart': True, 'runsGlobally': False, 'color': [200, 180, 220],
}, ensure_ascii=False, indent=1).encode('utf-8'))

# 全局脚本：不启用，单独放一份供参考
os.makedirs(os.path.join(OUT, '_全局脚本_可选_不要放进scripts'), exist_ok=True)
for f in os.listdir(os.path.join(SRC, 'scripts')):
    if f.lower().endswith(('.lua', '.hx')):
        shutil.copy2(os.path.join(SRC, 'scripts', f),
                     os.path.join(OUT, '_全局脚本_可选_不要放进scripts', f))

# 说明
put('README_双人说明.txt', '''Double Kill Duet — 单模组单曲目
================================
角色： 玩家 BF / 第一对手 Momo(原白) / 第二对手 Teto(原黑，占 GF 槽)
音源： songs/double-kill/Inst.ogg + Voices.ogg（原曲未改）
谱面： data/double-kill/double-kill-hard.json（252 段，事件 82 行原样保留）

【双人属性】 chart 顶层 keys=4 / lanes=2 / arrowSkins 两组 / speed=3 / bpm=200
【特殊事件】 全部在 data/double-kill/events.json 与谱面 events 里，custom_events/ 下都有同名 lua：
    Legacy          black / not black / kill -> Teto 淡入(半透明 0.5) / 淡出 / 终局
    Opponent Two    1 / 0 -> 该段只让 Teto 唱
    Both Opponents  1 / 0 -> 合唱段，两个对手都播动作
    Reactor Beep / flash / Camera Set Target / Extra Cam Zoom / Add Camera Zoom / Set Cams
【Note Type】 编辑器里给音符填 Type：
    Opponent 2 Sing      -> 只有 Teto 播唱歌动作（Momo 不动）
    Both Opponents Sing  -> Momo + Teto 同时播（合唱/和弦）
    空 Type              -> 默认只有 Momo 唱，Teto 不播
    同一时刻两个音符(和弦)会自动双播，可在 duet.lua 把 CHORD_AUTO_DUET 改 false 关掉
【双人合成 icon】 images/icons/icon-momo-teto.png (300x150)
    触发 Both Opponents / Legacy=black 时自动换上，退出换回 Momo
【总控】 data/double-kill/duet.lua —— 所有双人状态集中在这一个文件，
         custom_events 里的同名 lua 只负责让编辑器能选到事件，不重复播动画。

【为什么没有 scripts/ 目录】
    原大包 scripts/ 下 9 个 lua + 2 个 hx 是【全局脚本】，每首歌都执行：
    screenBeat.lua(57KB 全局 onBeatHit)、CustomVideos.lua(引用不存在的视频)、
    CustomGameOvers.lua(引用 overLegacy 等音效)、CustomDialogue.lua(38KB 全曲对白)、
    Complements.lua(甚至有一处语法错误 `or name 'bars'`) —— 全塞进单曲 mod 必炸。
    已原样放在 _全局脚本_可选_不要放进scripts/ 供参考，不要直接拷进 scripts/。
''')

print('\n完成 ->', OUT)
