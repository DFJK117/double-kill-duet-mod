# -*- coding: utf-8 -*-
"""
DK_Duet Lua v6 一次性部署 + 校验 + 打包（幂等，可重复运行）

本次（2026-11-15 晚）四项需求：
  1) F2 改口：回收动画**照播**，但 TURBO 档压到 1~2 帧（快如逆天）；
     v5 的「完全不播放 / confirm 常亮」状态撤销。F2 在 TURBO / NORMAL 间切。
  2) 对手推条：纯 Lua 绕开引擎 healthDrainOPPO 的 0.4 保底，能一路推到
     health<=0 触发 doDeathCheck；长音不扣 + 和弦节流 + 默认温和档（不逆天）。
  3) 玩家 BF 换成 Indie Cross v15 的 bf-ic 角色（12 个动作，含 attack /
     dodge / hurt / 四向 miss），不再用旧 BOYFRIEND 的 Dlow Scared 残血姿势。
     图集复制进本模组，单模组独立可跑；另附一份 characters/bf-ic.json。
  4) SHIFT 播放 attack 动作（事件 "DK Attack" 亦可触发，可指定 bf/dad/gf/all）。

顺带修掉 v5 遗留 bug：add_hey 只改了 name（图集前缀）没改 anim（动画名），
导致 momo/miku/bf-defeat-normal 根本没有名为 'hey' 的动画，且 name='hey'
前缀在它们的图集里不存在；DK_Fun v1 的 HEY_ANIM 传的是 name 而非 anim。
本脚本重建正确的 hey 别名并删掉坏别名。

校验：Lua 静态语法/API 白名单、角色 anim 与图集前缀匹配、图集文件、
事件注册壳、游戏侧与两个构建源 md5 一致、增量 zip CRC。
"""
import os, io, re, json, sys, shutil, zipfile, hashlib, glob, collections
from PIL import Image

GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
IC   = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/Indie Cross v15'
ROOT = r'E:/UST_work/dk_miku'
SOURCES = [ROOT + '/DK_Dual', ROOT + '/DK_Miku']
BACKUP = ROOT + '/_backup_lua_v6_20261115'
ZIP = ROOT + '/DK_Duet_Lua_v6_20261115.zip'
SONGS = ['double-kill', 'double-kill-miku']

IC_PNG = IC + '/images/characters/cuphead/BoyFriend_ICCuphead.png'
IC_XML = IC + '/images/characters/cuphead/BoyFriend_ICCuphead.xml'
DST_PNG = GAME + '/images/characters/cuphead/BoyFriend_ICCuphead.png'
DST_XML = GAME + '/images/characters/cuphead/BoyFriend_ICCuphead.xml'

CHECKS = []
def ck(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  | ' + str(detail)) if detail else ''))

def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()

def load_json(p):
    return json.load(io.open(p, encoding='utf-8-sig'))

def save_json(p, obj):
    with io.open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')

# ---------------------------------------------------------------- 备份
FILES = [
    'scripts/BOTPLAY_Pro.lua',
    'scripts/DK_Fun.lua',
    'scripts/DK_Push.lua',
    'custom_events/DK Push.lua',
    'custom_events/DK Attack.lua',
    'characters/bf.json',
    'characters/bf-ic.json',
    'characters/momo.json',
    'characters/miku.json',
    'characters/bf-defeat-normal.json',
    'images/characters/cuphead/BoyFriend_ICCuphead.png',
    'images/characters/cuphead/BoyFriend_ICCuphead.xml',
]

def backup_once():
    os.makedirs(BACKUP, exist_ok=True)
    n = 0
    for rel in FILES:
        src, dst = os.path.join(GAME, rel), os.path.join(BACKUP, rel)
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print('[backup] %s  新增备份 %d 个' % (BACKUP, n))

# ---------------------------------------------------------------- 1) bf-ic 图集
def copy_atlas():
    os.makedirs(os.path.dirname(DST_PNG), exist_ok=True)
    for a, b in ((IC_PNG, DST_PNG), (IC_XML, DST_XML)):
        if not os.path.exists(b) or md5(a) != md5(b):
            shutil.copy2(a, b)
    ck('bf-ic 图集 png 复制且与源 md5 一致', md5(IC_PNG) == md5(DST_PNG), os.path.getsize(DST_PNG))
    ck('bf-ic 图集 xml 复制且与源 md5 一致', md5(IC_XML) == md5(DST_XML), os.path.getsize(DST_XML))
    im = Image.open(DST_PNG)
    ck('图集是真图（非 1x1 占位）', im.size[0] > 1000 and im.size[1] > 1000, im.size)
    txt = io.open(DST_XML, encoding='utf-8', errors='replace').read()
    frames = re.findall(r'name="([^"]+)"', txt)
    ck('图集帧数 186', len(frames) == 186, len(frames))
    return frames

# ---------------------------------------------------------------- 2) 角色 json
def build_bf(frames):
    """bf-ic 动作表 + DK 舞台参数 + hey / scared 别名（不再有残血姿势）"""
    ic = load_json(IC + '/characters/bf-ic.json')
    anims = []
    for a in ic['animations']:
        # attack 帧是 775px 宽画布、frameX≈-569，scale=2 下会右偏 ~1138px；
        # IC 原 offsets=[1094,-9] 正好抵消，必须原样保留，改成 [0,0] 会让
        # BF 冲出屏幕。其它动画 offsets 也一律沿用 IC 官方值。
        anims.append(dict(a))

    # 前缀合法性：addByPrefix 用 name 做前缀匹配
    for a in anims:
        pref = a.get('name', '')
        hit = [f for f in frames if f.startswith(pref)]
        if not hit:
            raise AssertionError('bf-ic 动画前缀在图集里无匹配帧: %r' % pref)

    # hey：bf-ic 没有 hey，用现成的 singUP 帧做别名（空格全员 hey 需要）
    sing_up = next(a for a in anims if a.get('anim') == 'singUP')
    hey = dict(sing_up)
    hey['anim'] = 'hey'
    hey['loop'] = False
    anims.append(hey)

    # scared / idle-scared：指向普通 idle，绝不出现 Dlow Scared 残血姿势
    idle = next(a for a in anims if a.get('anim') == 'idle')
    for nm in ('scared', 'idle-scared'):
        al = dict(idle)
        al['anim'] = nm
        al['loop'] = True
        anims.append(al)

    d = {
        'animations': anims,
        'image': 'characters/cuphead/BoyFriend_ICCuphead',
        'position': [-12, 342],          # DK 原值；cargo 舞台会覆盖
        'healthicon': 'bf',              # 保持 DK 双人 icon 体系不变
        'flip_x': True,
        'healthbar_colors': [49, 176, 209],
        'camera_position': [0, 0],       # 保持 DK 原镜头，不引入 IC 的 [930,-110]
        'sing_duration': 4,
        'scale': 2,                      # IC 帧约 200x200，scale2 ≈ DK 原 438x435
        'no_antialiasing': False,
        'vocals_file': '',
        '_editor_isPlayer': True,
    }
    save_json(GAME + '/characters/bf.json', d)
    save_json(GAME + '/characters/bf-ic.json', d)
    return d

# v5 的 add_hey 把 name 改成 'hey'（前缀）却没改 anim，导致：
#   - 角色没有名为 'hey' 的动画（空格 hey 无效）
#   - name='hey' 前缀在各图集里不存在（动画是空的）
# 这里删掉坏别名，重建 anim='hey'、name=真实前缀 的正确别名。
HEY_SRC = {
    'momo': 'Momo Up',
    'miku': 'up_miku',
    'bf-defeat-normal': 'up',
}
def fix_hey():
    for char, src_name in HEY_SRC.items():
        p = GAME + '/characters/%s.json' % char
        d = load_json(p)
        anims = [a for a in d.get('animations', [])
                 if not (a.get('name') == 'hey' and a.get('anim') != 'hey')]
        base = next((a for a in anims if a.get('name') == src_name), None)
        if base is None:
            base = next((a for a in anims if a.get('anim') in ('singUP', 'hey')), None)
        assert base is not None, '%s 找不到 hey 源动画' % char
        if not any(a.get('anim') == 'hey' for a in anims):
            al = dict(base)
            al['anim'] = 'hey'
            al['loop'] = False
            anims.append(al)
        d['animations'] = anims
        save_json(p, d)
    # teto 原生就有 anim='hey'，只读校验
    d = load_json(GAME + '/characters/teto.json')
    ck('teto 原生 anim=hey 存在', any(a.get('anim') == 'hey' for a in d.get('animations', [])))

def check_chars(frames):
    pref_ok, hey_ok, bad_ok = True, True, True
    for char in ['bf', 'bf-ic', 'momo', 'miku', 'teto', 'bf-defeat-normal']:
        d = load_json(GAME + '/characters/%s.json' % char)
        anims = d.get('animations', [])
        if not any(a.get('anim') == 'hey' for a in anims):
            hey_ok = False
        # teto 原生就有 name='hey' 的 cheer/hey 条目，属正常；
        # 只查 v5 制造的特征：name='hey' 且 anim 仍是 singUP。
        if any(a.get('name') == 'hey' and a.get('anim') == 'singUP' for a in anims):
            bad_ok = False
        if char in ('bf', 'bf-ic'):
            names = [a.get('name', '') for a in anims]
            for nm in names:
                if not any(f.startswith(nm) for f in frames):
                    pref_ok = False
                    print('    !! %s 前缀无帧: %r' % (char, nm))
    ck('全部 6 个角色都有 anim=hey', hey_ok)
    ck('v5 坏 hey 别名已清除', bad_ok)
    ck('bf / bf-ic 全部动画前缀命中图集', pref_ok)
    d = load_json(GAME + '/characters/bf.json')
    ck('BF 用 bf-ic 图集', d.get('image') == 'characters/cuphead/BoyFriend_ICCuphead', d.get('image'))
    ck('BF 有 attack 动画', any(a.get('anim') == 'attack' for a in d['animations']))
    ck('BF attack 沿用 IC 官方 offsets=[1094,-9]（抵消宽画布偏移）',
       next(a for a in d['animations'] if a.get('anim') == 'attack')['offsets'] == [1094, -9])
    ck('BF 保留 healthicon=bf（双人 icon 不破坏）', d.get('healthicon') == 'bf')
    ck('BF 动作数 >= 15（超多动作）', len(d['animations']) >= 15, len(d['animations']))
    ck('BF 不再使用 Dlow Scared 残血帧',
       not any('Scared' in a.get('name', '') for a in d['animations']))

# ---------------------------------------------------------------- 3) Lua 校验
LUA_API = set('''
pcall type tonumber tostring ipairs pairs select unpack error setmetatable
getProperty setProperty getPropertyFromGroup setPropertyFromGroup callMethod
setVar getVar keyboardJustPressed keyboardPressed keyboardReleased
playAnim characterPlayAnim makeLuaSprite addLuaSprite removeLuaSprite
setObjectCamera setObjectOrder getObjectOrder setGraphicSize scaleObject
setBlendMode setScrollFactor doTweenAlpha cancelTween runTimer cancelTimer
triggerEvent callOnLuas addScore addHealth getHealth setHealth getSongPosition
makeLuaText setTextSize setTextColor setTextBorder addLuaText setTextString
getColorFromHex makeGraphic luaSpriteExists cameraFlash debugPrint
'''.split())
LUA_STD_PREFIX = ('math.', 'string.', 'table.', 'os.')
KEYWORDS = ('if', 'for', 'while', 'function', 'return', 'and', 'or', 'not',
            'else', 'elseif', 'then', 'do', 'end', 'local', 'in',
            'repeat', 'until', 'break', 'nil', 'true', 'false')

def strip_lua(line):
    out, i, quote = [], 0, None
    while i < len(line):
        c = line[i]
        if quote:
            out.append(' ')
            if c == '\\' and i + 1 < len(line):
                out.append(' '); i += 2; continue
            if c == quote:
                quote = None
            i += 1; continue
        if c in ('"', "'"):
            quote = c; out.append(' '); i += 1; continue
        if c == '-' and i + 1 < len(line) and line[i + 1] == '-':
            break
        out.append(c); i += 1
    return ''.join(out), quote is None

def code_only(path):
    return '\n'.join(strip_lua(l)[0] for l in io.open(path, encoding='utf-8-sig').read().splitlines())

def lua_static_check(path):
    raw = io.open(path, encoding='utf-8-sig').read()
    parts = [strip_lua(l) for l in raw.splitlines()]
    code = '\n'.join(p[0] for p in parts)
    str_closed = all(p[1] for p in parts)
    opens = sum(len(re.findall(r'\b%s\b' % k, code)) for k in ('function', 'if', 'for', 'while'))
    ends = len(re.findall(r'\bend\b', code))
    n_if = len(re.findall(r'(?<!else)\bif\b', code))
    n_elseif = len(re.findall(r'\belseif\b', code))
    n_then = len(re.findall(r'\bthen\b', code))
    ok_then = (n_if + n_elseif == n_then)
    ok_br = all(code.count(a) == code.count(b) for a, b in (('(', ')'), ('{', '}'), ('[', ']')))
    locals_defined = set(re.findall(r'local\s+function\s+(\w+)', code))
    func_names = set(re.findall(r'(?m)^\s*(?:local\s+)?function\s+(\w+)', raw))
    calls = set(re.findall(r'(?<![\w.:])([a-zA-Z_]\w*)\s*\(', code))
    unknown = sorted(c for c in calls
                     if c not in LUA_API and c not in locals_defined
                     and c not in func_names
                     and not c.startswith(LUA_STD_PREFIX)
                     and c not in KEYWORDS)
    return (opens == ends), ok_br, ok_then, str_closed, unknown, (opens, ends)

def check_lua():
    luanames = ['scripts/BOTPLAY_Pro.lua', 'scripts/DK_Fun.lua', 'scripts/DK_Push.lua',
                'custom_events/DK Push.lua', 'custom_events/DK Attack.lua',
                'custom_events/DK Hey.lua', 'custom_events/DK Surprise.lua']
    codes = {}
    for rel in luanames:
        p = os.path.join(GAME, rel)
        if not os.path.isfile(p):
            ck('%s 存在' % os.path.basename(rel), False)
            continue
        okb, okbr, okt, str_closed, unknown, cnt = lua_static_check(p)
        ck('%s 块配对 (%s/%s)' % (os.path.basename(rel), cnt[0], cnt[1]), okb, cnt)
        ck('%s 括号平衡' % os.path.basename(rel), okbr)
        ck('%s if/then 一致' % os.path.basename(rel), okt)
        ck('%s 字符串闭合' % os.path.basename(rel), str_closed)
        ck('%s 无未知 API' % os.path.basename(rel), not unknown, unknown)
        codes[rel] = code_only(p)
    def raw(rel):
        return io.open(GAME + '/' + rel, encoding='utf-8').read()
    bpp, fun, push = codes.get('scripts/BOTPLAY_Pro.lua', ''), codes.get('scripts/DK_Fun.lua', ''), codes.get('scripts/DK_Push.lua', '')
    bpp_raw, fun_raw = raw('scripts/BOTPLAY_Pro.lua'), raw('scripts/DK_Fun.lua')
    ck('BPP v6 默认 TURBO', "recycleMode = 'TURBO'" in bpp_raw)
    ck('BPP v6 撤销「不播放」状态', 'recycleEnabled' not in bpp and 'if not recycleEnabled then return end' not in bpp)
    ck('BPP v6 TURBO 提速 frameRate',
       'TURBO_FPS' in bpp and 'animation.curAnim.frameRate' in bpp_raw)
    ck('BPP v6 F2 切档', re.search(r'keyboardJustPressed,\s*RECYCLE_KEY', bpp) is not None)
    ck('DK_Fun SHIFT attack', "ATTACK_KEY = 'SHIFT'" in fun_raw
       and 'function playAttack' in fun and '.specialAnim' in fun_raw)
    ck('DK_Fun HEY_ANIM 用 anim 名', "['bf-ic']            = 'hey'" in fun_raw)
    ck('DK_Push 有 opponentNoteHit 回调', 'function opponentNoteHit' in push)
    ck('DK_Push 用 addHealth 直改血量', re.search(r'addHealth,\s*-amount', push) is not None)
    ck('DK_Push 长音不扣', 'isSustainNote' in push)
    ck('DK_Push 无 0.4 保底', '0.4' not in re.sub(r'--.*', '', push).replace('0.001', ''))
    ck('DK_Push 有节流', 'cfg.gap' in push and 'lastPushAt' in push)
    ck('零 hscript / runHaxeCode', all('runHaxeCode' not in c for c in codes.values()))
    return codes

# ---------------------------------------------------------------- 4) 事件注册壳
def write_event_shells():
    p = GAME + '/custom_events/DK Attack.lua'
    txt = '''-- DK Attack —— 谱面事件注册壳（真逻辑在 scripts/DK_Fun.lua）
--
-- 按 SHIFT 等价于触发本事件。
--   value1 = bf(默认) / dad / p2 / gf / all
-- 只有 bf-ic 玩家角色有原生 attack 动画；其余角色会退回通用 attack 名，
-- 角色 json 未定义时引擎忽略，不会报错。
-- onEvent 保持空实现，避免事件脚本与全局脚本重复播放。

function onEvent(name, value1, value2)
end
'''
    io.open(p, 'w', encoding='utf-8').write(txt)
    for n in ['DK Push', 'DK Attack', 'DK Hey', 'DK Surprise']:
        ck('custom_events/%s.lua 存在' % n, os.path.isfile(GAME + '/custom_events/%s.lua' % n))

# ---------------------------------------------------------------- 5) 同步 + 打包
def sync_and_zip():
    for src in SOURCES:
        n = 0
        for rel in FILES:
            a, b = os.path.join(GAME, rel), os.path.join(src, rel)
            if not os.path.isfile(a):
                continue
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
            n += 1
        same = all(md5(os.path.join(GAME, r)) == md5(os.path.join(src, r))
                   for r in FILES if os.path.isfile(os.path.join(GAME, r)))
        ck('%s 同步 %d 文件且 md5 全一致' % (os.path.basename(src), n), same)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            p = os.path.join(GAME, rel)
            if os.path.isfile(p):
                z.write(p, 'DK_Duet/' + rel.replace('\\', '/'))
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        ck('zip CRC OK / %d 项' % len(z.namelist()), bad is None, bad)
    print('[zip] %s  %d bytes' % (ZIP, os.path.getsize(ZIP)))

# ---------------------------------------------------------------- main
def main():
    print('=== DK_Duet Lua v6 部署 ===')
    backup_once()
    frames = copy_atlas()
    build_bf(frames)
    fix_hey()
    check_chars(frames)
    write_event_shells()
    check_lua()

    # chart 的 player1 仍是 'bf'（最小改动，避免破坏换装/事件/双人 icon 链）
    for s in SONGS:
        p = GAME + '/data/%s/%s-hard.json' % (s, s)
        d = load_json(p)
        ck('%s player1 保持 bf' % s, d.get('player1') == 'bf', d.get('player1'))

    sync_and_zip()
    fail = [n for n, ok, _ in CHECKS if not ok]
    print('\n=== 校验汇总: %d 项, 失败 %d 项 ===' % (len(CHECKS), len(fail)))
    for f in fail:
        print('  !! ' + f)
    return 1 if fail else 0

if __name__ == '__main__':
    sys.exit(main())
