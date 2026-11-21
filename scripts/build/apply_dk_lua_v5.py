# -*- coding: utf-8 -*-
"""
DK_Duet Lua v5 一次性部署 + 校验 + 打包（幂等，可重复运行）

1) 把用户给的惊讶脸做成 150x150 透明圆角 icon 覆盖图 + 300x150 双帧真 icon 备用图
2) 给 bf / momo / miku / bf-defeat-normal 的角色 json 补 name='hey' 动画别名
3) 在两首歌的 chart events 与 events.json 的 165600ms（BPM 200->220 变速段起点）
   同一组里插入 ["DK Surprise", "both", "1"]
4) 同步全部改动到两个构建源目录（DK_Dual / DK_Miku），并做三处 md5 一致性校验
5) Lua 静态语法/API 白名单校验、事件与角色/图片/JSON 结构校验
6) 产出增量 zip：E:/UST_work/dk_miku/DK_Duet_Lua_v5_20261115.zip
"""
import os, io, re, json, sys, shutil, zipfile, hashlib, ctypes, glob
from PIL import Image, ImageDraw

GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ROOT = r'E:/UST_work/dk_miku'
SOURCES = [ROOT + '/DK_Dual', ROOT + '/DK_Miku']
BACKUP = ROOT + '/_backup_lua_v5_20261115'
SRC_IMG = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\QQ20261115-185238.png'
ZIP = ROOT + '/DK_Duet_Lua_v5_20261115.zip'
TARGET_MS = 165600
NEW_EVENT = ['DK Surprise', 'both', '1']
SONGS = ['double-kill', 'double-kill-miku']

FILES = [
    'scripts/BOTPLAY_Pro.lua',
    'scripts/DK_Fun.lua',
    'custom_events/DK Surprise.lua',
    'custom_events/DK Hey.lua',
    'images/dk_surprise.png',
    'images/icons/icon-surprise.png',
    'characters/bf.json',
    'characters/momo.json',
    'characters/miku.json',
    'characters/bf-defeat-normal.json',
]
for s in SONGS:
    FILES += ['data/%s/%s-hard.json' % (s, s), 'data/%s/events.json' % s]

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

def backup_once():
    os.makedirs(BACKUP, exist_ok=True)
    n = 0
    for rel in FILES:
        src = os.path.join(GAME, rel)
        dst = os.path.join(BACKUP, rel)
        if os.path.exists(src) and not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)
            n += 1
    print('[backup] %s  新增备份 %d 个' % (BACKUP, n))

# ---------------------------------------------------------------- 1) 图片
def make_image():
    src = Image.open(SRC_IMG).convert('RGBA').resize((150, 150), Image.LANCZOS)
    mask = Image.new('L', (150, 150), 0)
    ImageDraw.Draw(mask).rounded_rectangle((1, 1, 148, 148), radius=18, fill=255)
    out = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
    out.paste(src, (0, 0), mask)
    ImageDraw.Draw(out).rounded_rectangle((1, 1, 148, 148), radius=18,
                                         outline=(18, 18, 22, 255), width=3)
    p1 = os.path.join(GAME, 'images/dk_surprise.png')
    os.makedirs(os.path.dirname(p1), exist_ok=True)
    out.save(p1)
    # 备用：300x150 双帧，符合 HealthIcon.changeIcon 的图标规格
    two = Image.new('RGBA', (300, 150), (0, 0, 0, 0))
    two.paste(out, (0, 0)); two.paste(out, (150, 0))
    p2 = os.path.join(GAME, 'images/icons/icon-surprise.png')
    two.save(p2)
    return p1, p2

# ---------------------------------------------------------------- 2) 角色 hey
HEY_SRC = {
    'bf': 'BF HEY!!',
    'bf-defeat-normal': 'up',
    'momo': 'Momo Up',
    'miku': 'up_miku',
}
def add_hey():
    for char, from_name in HEY_SRC.items():
        p = os.path.join(GAME, 'characters/%s.json' % char)
        d = load_json(p)
        anims = d.get('animations', [])
        if any(a.get('name') == 'hey' for a in anims):
            continue
        base = next((a for a in anims if a.get('name') == from_name), None)
        assert base is not None, '%s 找不到源动画 %s' % (char, from_name)
        alias = dict(base)
        alias['name'] = 'hey'
        alias['loop'] = False
        anims.append(alias)
        d['animations'] = anims
        save_json(p, d)
    # teto 原生就有 hey，只读校验
    d = load_json(os.path.join(GAME, 'characters/teto.json'))
    ck('teto 原生 hey 动画存在', any(a.get('name') == 'hey' for a in d.get('animations', [])))

# ---------------------------------------------------------------- 3) 事件
def insert_event(path, is_chart):
    d = load_json(path)
    # chart JSON 与 events.json 的事件都挂在顶层 "events" 数组里
    ev = d['events']
    grp = None
    for e in ev:
        try:
            if abs(float(e[0]) - TARGET_MS) < 0.001:
                grp = e; break
        except (TypeError, ValueError, IndexError):
            continue
    if grp is None:
        grp = [TARGET_MS, []]
        ev.append(grp)
        ev.sort(key=lambda x: float(x[0]))
    sub = grp[1]
    exists = any(isinstance(x, list) and len(x) >= 1 and x[0] == NEW_EVENT[0] for x in sub)
    if not exists:
        sub.append(list(NEW_EVENT))
    save_json(path, d)
    return sub

# ---------------------------------------------------------------- Lua 校验
LUA_API = set('''
pcall type tonumber tostring ipairs pairs select unpack error setmetatable
getProperty setProperty getPropertyFromGroup setPropertyFromGroup callMethod
setVar getVar keyboardJustPressed keyboardPressed keyboardReleased
playAnim characterPlayAnim makeLuaSprite addLuaSprite removeLuaSprite
setObjectCamera setObjectOrder getObjectOrder setGraphicSize scaleObject
setBlendMode setScrollFactor doTweenAlpha cancelTween runTimer cancelTimer
triggerEvent callOnLuas addScore getSongPosition makeLuaText setTextSize
setTextColor setTextBorder addLuaText setTextString getColorFromHex
makeGraphic luaSpriteExists cameraFlash debugPrint addHaxeCode runHaxeCode
'''.split())
LUA_STD_PREFIX = ('math.', 'string.', 'table.', 'os.')

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
    raw = io.open(path, encoding='utf-8-sig').read()
    return '\n'.join(strip_lua(l)[0] for l in raw.splitlines())

def lua_static_check(path):
    raw = io.open(path, encoding='utf-8-sig').read()
    parts = [strip_lua(l) for l in raw.splitlines()]
    code = '\n'.join(p[0] for p in parts)
    str_closed = all(p[1] for p in parts)
    opens = (len(re.findall(r'\bfunction\b', code))
             + len(re.findall(r'\bif\b', code))
             + len(re.findall(r'\bfor\b', code))
             + len(re.findall(r'\bwhile\b', code)))
    ends = len(re.findall(r'\bend\b', code))
    n_if = len(re.findall(r'(?<!else)\bif\b', code))
    n_elseif = len(re.findall(r'\belseif\b', code))
    n_then = len(re.findall(r'\bthen\b', code))
    ok_then = (n_if + n_elseif == n_then)
    ok_block = (opens == ends)
    pairs = {'(': ')', '{': '}', '[': ']'}
    ok_br = True
    for a, b in pairs.items():
        if code.count(a) != code.count(b):
            ok_br = False
    locals_defined = set(re.findall(r'local\s+function\s+(\w+)', code))
    func_names = set(re.findall(r'(?m)^\s*(?:local\s+)?function\s+(\w+)', raw))
    calls = set(re.findall(r'(?<![\w.:])([a-zA-Z_]\w*)\s*\(', code))
    KEYWORDS = ('if', 'for', 'while', 'function', 'return', 'and', 'or', 'not',
                'else', 'elseif', 'then', 'do', 'end', 'local', 'in',
                'repeat', 'until', 'break', 'nil', 'true', 'false')
    unknown = sorted(c for c in calls
                     if c not in LUA_API and c not in locals_defined
                     and c not in func_names
                     and not c.startswith(LUA_STD_PREFIX)
                     and c not in KEYWORDS)
    return ok_block, ok_br, ok_then, str_closed, unknown, (opens, ends)

def try_real_lua(path):
    """若本机存在 lua53/luajit dll，用 luaL_loadstring 做真语法编译。"""
    cands = []
    for base in [r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows',
                 r'I:/NF-1.2.1h2/export/release/windows/bin']:
        cands += glob.glob(base + '/**/*lua*.dll', recursive=True)
        cands += glob.glob(base + '/**/*Lua*.dll', recursive=True)
    for dll in cands[:6]:
        try:
            lib = ctypes.CDLL(dll)
            lib.luaL_newstate.restype = ctypes.c_void_p
            lib.luaL_loadstring.argtypes = [ctypes.c_void_p, ctypes.c_char_p]
            lib.luaL_loadstring.restype = ctypes.c_int
            lib.lua_close.argtypes = [ctypes.c_void_p]
            st = lib.luaL_newstate()
            if not st:
                continue
            data = open(path, 'rb').read()
            rc = lib.luaL_loadstring(st, data)
            lib.lua_close(st)
            return (rc == 0), dll, rc
        except Exception:
            continue
    return None, None, None

# ---------------------------------------------------------------- main
def main():
    print('=== DK_Duet Lua v5 部署 ===')
    backup_once()

    p1, p2 = make_image()
    im1, im2 = Image.open(p1), Image.open(p2)
    ck('dk_surprise.png 150x150 RGBA', im1.size == (150, 150) and im1.mode == 'RGBA', im1.size)
    ck('icon-surprise.png 300x150 双帧', im2.size == (300, 150), im2.size)
    ck('覆盖图四角透明', im1.getpixel((0, 0))[3] == 0)

    add_hey()
    for char in list(HEY_SRC) + ['teto']:
        d = load_json(os.path.join(GAME, 'characters/%s.json' % char))
        ck('%s.json 有 hey 动画' % char,
           any(a.get('name') == 'hey' for a in d.get('animations', [])))

    for s in SONGS:
        cp = os.path.join(GAME, 'data/%s/%s-hard.json' % (s, s))
        ep = os.path.join(GAME, 'data/%s/events.json' % s)
        for p, is_chart in ((cp, True), (ep, False)):
            sub = insert_event(p, is_chart)
            ck('%s 变速点 165600 挂上 DK Surprise' % os.path.basename(p),
               any(isinstance(x, list) and x[0] == 'DK Surprise' for x in sub),
               sub)

    # 事件注册壳 + 全局脚本
    for name in ['DK Surprise', 'DK Hey']:
        ck('custom_events/%s.lua 存在' % name,
           os.path.isfile(os.path.join(GAME, 'custom_events/%s.lua' % name)))
    for rel in ['scripts/BOTPLAY_Pro.lua', 'scripts/DK_Fun.lua']:
        path = os.path.join(GAME, rel)
        okb, okbr, ok_then, str_closed, unknown, cnt = lua_static_check(path)
        ck('%s 块配对 (open/end=%s/%s)' % (os.path.basename(rel), cnt[0], cnt[1]), okb)
        ck('%s 括号平衡' % os.path.basename(rel), okbr)
        ck('%s if/then 一致' % os.path.basename(rel), ok_then)
        ck('%s 字符串闭合' % os.path.basename(rel), str_closed)
        ck('%s 无未知 API' % os.path.basename(rel), not unknown, unknown)
        real, dll, rc = try_real_lua(path)
        if real is not None:
            ck('%s Lua 真编译' % os.path.basename(rel), real, '%s rc=%s' % (os.path.basename(dll), rc))
        else:
            print('  INFO  未找到可用 Lua DLL，采用静态语法检查')

    bpp = io.open(os.path.join(GAME, 'scripts/BOTPLAY_Pro.lua'), encoding='utf-8-sig').read()
    fun = io.open(os.path.join(GAME, 'scripts/DK_Fun.lua'), encoding='utf-8-sig').read()
    bpp_code, fun_code = code_only(os.path.join(GAME, 'scripts/BOTPLAY_Pro.lua')), \
                         code_only(os.path.join(GAME, 'scripts/DK_Fun.lua'))
    ck('BPP v5 含 F2 与回收开关', "RECYCLE_KEY" in bpp and 'function setRecycle' in bpp
       and re.search(r"keyboardJustPressed,\s*RECYCLE_KEY", bpp_code) is not None)
    ck('BPP v5 零 hscript', 'runHaxeCode' not in bpp_code)
    ck('DK_Fun 空格 hey', re.search(r"HEY_KEY\s*=\s*'SPACE'", fun) is not None
       and 'function playHey' in fun)
    ck('DK_Fun 彩蛋 1 秒渐隐', 'holdTime, fadeTime = 0.35, 0.65' in fun and 'doTweenAlpha' in fun)
    ck('DK_Fun 零 hscript', 'runHaxeCode' not in fun_code)
    ck('DK_Fun 用 camHUD 覆盖 icon', "'camHUD'" in fun and "iconP1.alpha" in fun)

    # 同步两个源目录
    for src in SOURCES:
        n = 0
        for rel in FILES:
            a = os.path.join(GAME, rel)
            b = os.path.join(src, rel)
            os.makedirs(os.path.dirname(b), exist_ok=True)
            shutil.copy2(a, b)
            n += 1
        same = all(md5(os.path.join(GAME, r)) == md5(os.path.join(src, r)) for r in FILES)
        ck('%s 同步 %d 个文件且 md5 全一致' % (os.path.basename(src), n), same)

    # 增量 zip
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in FILES:
            z.write(os.path.join(GAME, rel), 'DK_Duet/' + rel.replace('\\', '/'))
    with zipfile.ZipFile(ZIP) as z:
        bad = z.testzip()
        ck('zip CRC OK / %d 项' % len(z.namelist()), bad is None, bad)
    print('[zip] %s  %d bytes' % (ZIP, os.path.getsize(ZIP)))

    fail = [n for n, ok, _ in CHECKS if not ok]
    print('\n=== 校验汇总: %d 项, 失败 %d 项 ===' % (len(CHECKS), len(fail)))
    for f in fail:
        print('  !! ' + f)
    return 1 if fail else 0

if __name__ == '__main__':
    sys.exit(main())
