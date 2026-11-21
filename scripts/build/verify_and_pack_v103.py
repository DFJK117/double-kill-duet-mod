# -*- coding: utf-8 -*-
"""v10.9 终检 + 打完整包：累积校验前面所有修复点不回退。"""
import os, zipfile, hashlib, json

G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v10.9_20261116.zip'
CHECKS = []

def ck(name, cond):
    CHECKS.append((name, bool(cond)))

def rb(rel):
    p = os.path.join(G, rel)
    return open(p, 'rb').read() if os.path.exists(p) else b''

# --- v10.3 新增修复 ---
GOD_XML = [
    'images/characters/miku_assets_god.xml',
    'images/characters/momo_assets_god.xml',
    'images/characters/teto-2026_god.xml',
    'images/characters/cuphead/BoyFriend_ICCuphead_god.xml',
    'images/characters/bf/defeatBf-normal_god.xml',
]
for rel in GOD_XML:
    ck('god xml  ' + os.path.basename(rel), os.path.exists(os.path.join(G, rel)))
for f in ['dk-miku.json', 'dk-momo.json']:
    ck('week GOD  ' + f, b'"hard,GOD"' in rb('weeks/' + f))
for song in ['double-kill', 'double-kill-miku']:
    raw = rb('data/' + song + '/icons.lua')
    ck('icons case ' + song, b"difficultyName == 'GOD'" in raw and b"difficultyName == 'god'" in raw)
    raw = rb('data/' + song + '/NewLogic.lua')
    ck('zoom cap  ' + song, b'ZOOM_CAP' in raw and b'if z > ZOOM_CAP then z = ZOOM_CAP end' in raw)

# --- 谱面链（大写后加载路径仍为 -god）---
for song in ['double-kill', 'double-kill-miku']:
    for diff in ['hard', 'god']:
        rel = 'data/%s/%s-%s.json' % (song, song, diff)
        ck('chart      ' + os.path.basename(rel), os.path.exists(os.path.join(G, rel)))
        d = json.loads(rb(rel).decode('utf-8-sig'))
        for key in ['player1', 'player2', 'gfVersion']:
            ch = d.get(key)
            jp = os.path.join(G, 'characters', ch + '.json')
            if not os.path.exists(jp):
                ck('char %s/%s/%s' % (song, diff, key), False); continue
            cd = json.load(open(jp, encoding='utf-8-sig'))
            img = cd.get('image', '')
            ck('img %s-%s-%s' % (song, diff, key), os.path.exists(os.path.join(G, 'images', img + '.png')))
            ck('xml %s-%s-%s' % (song, diff, key), os.path.exists(os.path.join(G, 'images', img + '.xml')))

# --- v10.4 新增：动作映射 / 法棍 / 模组图标 ---
fun = rb('scripts/DK_Fun.lua').decode('utf-8')
ck('fun baseChar norm', 'local function baseChar' in fun)
ck('fun bf-god attack', "['bf-god']" in fun and 'attack' in fun)
ck('fun heyAnimFor', 'local function heyAnimFor' in fun)
pk = rb('scripts/DK_Fun.lua').decode('utf-8')
hey_region = pk[pk.find('local function playHey'):pk.find('local function playAttack')]
ck('fun hey specialAnim lock', 'specialAnim' in hey_region and 'heyTimer' in hey_region)
# 法棍：God 图集三处 bbox 必须已恢复原版橙色（抽样点检查）
from PIL import Image
teto_god = Image.open(os.path.join(G, 'images/characters/teto-2026_god.png')).convert('RGB')
for (sx, sy) in [(1300, 420), (1900, 420), (1300, 1370)]:
    r, g, b = teto_god.getpixel((sx, sy))
    ck('baguette orange @%d,%d' % (sx, sy), r > 200 and 90 < g < 200 and b < 90)
pkicon = rb('pack.png')
ck('pack.png exists', len(pkicon) > 0)
if pkicon:
    im = Image.open(os.path.join(G, 'pack.png')).convert('RGBA')
    ck('pack.png 150x150', im.size == (150, 150))
    # 精确锁定三头版本（momo 上 / miku 左下 / teto 右下、每角各一次）：
    # 用整图 md5 锁死，防止再出现四头 / 双 momo 的旧版本。
    ck('pack.png exact 3-head md5', hashlib.md5(pkicon).hexdigest() == '6bd7039790c6804ade5aa20c0392ba12')
    px = im.load()
    n_blue = n_pink = n_teto = 0
    for y in range(0, 150, 2):
        for x in range(0, 150, 2):
            r, g, b, a = px[x, y]
            if a < 40:
                continue
            if b > 150 and b > r + 40 and g > 110:      # miku 青蓝
                n_blue += 1
            if r > 200 and 110 < g < 200 and b < 170 and r > g + 30:  # momo 粉
                n_pink += 1
            if r > 170 and g < 110 and b < 150 and r > g + 80:        # teto 玫红深（附赠 icon）
                n_teto += 1
    ck('pack.png has miku blue', n_blue > 200)
    ck('pack.png has momo pink', n_pink > 200)
    ck('pack.png has teto rose', n_teto > 100)
# teto 1.2 角色包附赠 icon 已随包部署（之前缺失）
teto_packed_icon = rb('images/icons/icon-teto-2026.png')
ck('teto pack icon deployed', len(teto_packed_icon) > 0 and hashlib.md5(teto_packed_icon).hexdigest() == '008dcf35dbe250279443325d5bb42ed6')

# --- v10.7 新增：空格躲锯子 / Shift attack 锁定 ---
fun = rb('scripts/DK_Fun.lua').decode('utf-8')
ck('DK_Fun dodge key = SPACE', "DODGE_KEY  = 'SPACE'" in fun)
ck('DK_Fun space no longer plays hey', 'playDodge()' in fun and 'keyboardJustPressed, DODGE_KEY' in fun)
ck('DK_Fun goodNoteHitPre noAnimation lock', 'goodNoteHitPre' in fun and "'noAnimation', true" in fun)
ck('DK_Fun attack lock window', 'ATTACK_LOCK' in fun and 'attackLockUntil = clock + ATTACK_LOCK' in fun)
ck('DK_Fun DK Dodge event', "name == DODGE_TAG" in fun)
ck('DK Dodge event shell exists', os.path.exists(os.path.join(G, 'custom_events', 'DK Dodge.lua')))
# v10.9 Trap 图集（md5 锁死"头顶大光环+强光晕+空心环+与箭尖分离"版，防回退）
trap_png = rb('images/dk_trap.png')
ck('trap atlas big-halo hollow md5', hashlib.md5(trap_png).hexdigest() == 'df989670d0cb71abbcc4ef278e888ead')

# --- 前几轮修复不回退 ---
trap = rb('custom_notetypes/DK Trap.txt').decode('utf-8')
ck('Trap ignoreNote', 'ignoreNote = true' in trap)
warn = rb('custom_notetypes/DK Warn.txt').decode('utf-8')
ck('Warn no ignoreNote', 'ignoreNote' not in warn)
lua = rb('scripts/DK_God.lua').decode('utf-8')
ck('botPlaying def', 'local function botPlaying' in lua)
ck('bot guard x3', lua.count('botPlaying()') >= 4)
for k in ['miku_assets.png','miku_assets_god.png','momo_assets.png','momo_assets_god.png',
          'teto-2026.png','teto-2026_god.png','cuphead/BoyFriend_ICCuphead.png','cuphead/BoyFriend_ICCuphead_god.png']:
    ck('charset   ' + k, os.path.exists(os.path.join(G, 'images/characters', k)))
# icon pairs (healthicon)
for ic in ['bf-god','miku-god','momo-god','teto-cozy-god','momo-teto-god','miku-teto-god']:
    ck('icon      ' + ic, os.path.exists(os.path.join(G, 'images/icons', 'icon-' + ic + '.png')))
# note skin
for k in ['dk_trap.png','dk_trap.xml','dk_warn.png','dk_warn.xml']:
    ck('note skin ' + k, os.path.exists(os.path.join(G, 'images', k)))
# hard 无特殊键 / god 有
for song in ['double-kill','double-kill-miku']:
    for diff, want in [('hard', False), ('god', True)]:
        d = json.loads(rb('data/%s/%s-%s.json' % (song,song,diff)).decode('utf-8-sig'))
        n = sum(1 for sec in d['notes'] for no in sec['sectionNotes'] if len(no)>3 and str(no[3]).startswith('DK '))
        ck('%s-%s special %d' % (song,diff,n), (n>0)==want)

print('=== VERIFY ===')
bad = [n for n,ok in CHECKS if not ok]
for n,ok in CHECKS:
    if not ok: print('  FAIL', n)
print('total=%d  pass=%d  fail=%d' % (len(CHECKS), len(CHECKS)-len(bad), len(bad)))
if bad:
    raise SystemExit('VERIFY FAILED: ' + ', '.join(bad))

print()
print('=== PACK ===')
files = []
for root, dirs, fs in os.walk(G):
    for f in fs:
        p = os.path.join(root, f)
        files.append((p, 'DK_Duet/' + os.path.relpath(p, G).replace(os.sep, '/')))
files.sort()
zf = zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED, compresslevel=6)
for p, arc in files:
    zf.write(p, arc)
zf.close()
z = zipfile.ZipFile(OUT)
print('zip:', OUT)
print('entries:', len(z.namelist()), '| size:', os.path.getsize(OUT), 'B')
print('crc bad:', z.testzip())
print('md5:', hashlib.md5(open(OUT,'rb').read()).hexdigest())
for rel in GOD_XML:
    print('  inzip', ('OK ' if ('DK_Duet/'+rel) in z.namelist() else 'MISS'), rel)
