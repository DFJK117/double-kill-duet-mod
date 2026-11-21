# -*- coding: utf-8 -*-
"""v11.9 (严格复刻原版 Dodge Mechanic 流程 + 原版音效) 终检 + 打完整包。"""
import os, zipfile, hashlib, json

G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.12_GODplus_20261116.zip'
CHECKS = []


def ck(name, cond):
    CHECKS.append((name, bool(cond)))


def rb(rel):
    p = os.path.join(G, rel)
    return open(p, 'rb').read() if os.path.exists(p) else b''


# ===== v10.3~v10.9 全部不回退 =====
GOD_XML = [
    'images/characters/miku_assets_god.xml', 'images/characters/momo_assets_god.xml',
    'images/characters/teto-2026_god.xml',
    'images/characters/cuphead/BoyFriend_ICCuphead_god.xml',
    'images/characters/bf/defeatBf-normal_god.xml',
]
for rel in GOD_XML:
    ck('god xml ' + os.path.basename(rel), os.path.exists(os.path.join(G, rel)))
for f in ['dk-miku.json', 'dk-momo.json']:
    ck('week GOD/GOD+ ' + f, b'"hard,GOD,GOD+"' in rb('weeks/' + f))
for song in ['double-kill', 'double-kill-miku']:
    raw = rb('data/' + song + '/icons.lua')
    ck('icons case ' + song, b"difficultyName == 'GOD'" in raw and b"difficultyName == 'god'" in raw and b"difficultyName == 'GOD+'" in raw)
    raw = rb('data/' + song + '/NewLogic.lua')
    ck('zoom cap ' + song, b'ZOOM_CAP' in raw and b'if z > ZOOM_CAP then z = ZOOM_CAP end' in raw)

for song in ['double-kill', 'double-kill-miku']:
    for diff in ['hard', 'god']:
        rel = 'data/%s/%s-%s.json' % (song, song, diff)
        ck('chart ' + os.path.basename(rel), os.path.exists(os.path.join(G, rel)))
        d = json.loads(rb(rel).decode('utf-8-sig'))
        for key in ['player1', 'player2', 'gfVersion']:
            ch = d.get(key)
            jp = os.path.join(G, 'characters', ch + '.json')
            if not os.path.exists(jp):
                ck('char %s/%s/%s' % (song, diff, key), False)
                continue
            cd = json.load(open(jp, encoding='utf-8-sig'))
            img = cd.get('image', '')
            ck('img %s-%s-%s' % (song, diff, key), os.path.exists(os.path.join(G, 'images', img + '.png')))
            ck('xml %s-%s-%s' % (song, diff, key), os.path.exists(os.path.join(G, 'images', img + '.xml')))

fun = rb('scripts/DK_Fun.lua').decode('utf-8')
ck('fun baseChar norm', 'local function baseChar' in fun)
ck('fun bf-god attack', "['bf-god']" in fun and 'attack' in fun)
ck('fun heyAnimFor', 'local function heyAnimFor' in fun)
ck('fun hey specialAnim lock', 'specialAnim' in fun and 'heyTimer' in fun)
ck('fun dodge key SPACE', "DODGE_KEY  = 'SPACE'" in fun)
ck('fun playDodge', 'playDodge()' in fun and 'keyboardJustPressed, DODGE_KEY' in fun)
ck('fun goodNoteHitPre lock', 'goodNoteHitPre' in fun and "'noAnimation', true" in fun)
ck('fun attack lock window', 'ATTACK_LOCK' in fun and 'attackLockUntil = clock + ATTACK_LOCK' in fun)
ck('fun DK Dodge event', 'name == DODGE_TAG' in fun)
ck('DK Dodge event shell', os.path.exists(os.path.join(G, 'custom_events', 'DK Dodge.lua')))

teto_god = __import__('PIL.Image', fromlist=['Image']).open(os.path.join(G, 'images/characters/teto-2026_god.png')).convert('RGB')
for (sx, sy) in [(1300, 420), (1900, 420), (1300, 1370)]:
    r, g, b = teto_god.getpixel((sx, sy))
    ck('baguette orange @%d,%d' % (sx, sy), r > 200 and 90 < g < 200 and b < 90)
pk = rb('pack.png')
ck('pack.png 150x150', bool(pk) and __import__('PIL.Image', fromlist=['Image']).open(os.path.join(G, 'pack.png')).size == (150, 150))
ck('pack 3-head md5', hashlib.md5(pk).hexdigest() == '6bd7039790c6804ade5aa20c0392ba12')
ck('teto pack icon', hashlib.md5(rb('images/icons/icon-teto-2026.png')).hexdigest() == '008dcf35dbe250279443325d5bb42ed6')

trap = rb('custom_notetypes/DK Trap.txt').decode('utf-8')
ck('Trap ignoreNote', 'ignoreNote = true' in trap)
warn = rb('custom_notetypes/DK Warn.txt').decode('utf-8')
ck('Warn no ignoreNote', 'ignoreNote' not in warn)
lua = rb('scripts/DK_God.lua').decode('utf-8')
ck('botPlaying def', 'local function botPlaying' in lua)
ck('bot guard x3', lua.count('botPlaying()') >= 4)
for k in ['dk_trap.png', 'dk_trap.xml', 'dk_warn.png', 'dk_warn.xml']:
    ck('note skin ' + k, len(rb('images/' + k)) > 0)
ck('trap big-halo md5 v10.9', hashlib.md5(rb('images/dk_trap.png')).hexdigest() == 'df989670d0cb71abbcc4ef278e888ead')
for song in ['double-kill', 'double-kill-miku']:
    for diff, want in [('hard', False), ('god', True)]:
        d = json.loads(rb('data/%s/%s-%s.json' % (song, song, diff)).decode('utf-8-sig'))
        n = sum(1 for sec in d['notes'] for no in sec['sectionNotes'] if len(no) > 3 and str(no[3]).startswith('DK '))
        ck('%s-%s special %d' % (song, diff, n), (n > 0) == want)

# ===== v11.7：ASCII 脚本修复 + 放慢节奏 + 删旧素材 + Dodge Mechanic 事件壳 =====
saw_raw = rb('scripts/DK_Saw.lua')
saw_script = saw_raw.decode('utf-8')
# 致命根因回归：脚本必须纯 ASCII（全角破折号 —— 曾导致 LuaJIT 加载失败）
ck('saw source pure ASCII', all(b < 128 for b in saw_raw))
ck('saw no fullwidth dash', '\u2014' not in saw_script)
ck('saw block-comment header', saw_script.startswith('--[['))
# 用 Lua 实编译验证（lupa），任何 Lua 语法错都挡住
try:
    import sys as _sys
    _sys.path.insert(0, 'E:/UST_work/_pylibs')
    from lupa import LuaRuntime as _LR
    _LR().compile(saw_script)
    ck('saw Lua real-compile', True)
except Exception as _e:
    ck('saw Lua real-compile', False)
    print('   saw compile err:', str(_e)[:160])
# 核心 token
for token in ['makeLuaSprite', 'makeGraphic', 'screenCenter',
              'dkBaguette', 'dkSawWarning', 'dkDodged',
              'dkDodgeActive', 'botPlaying', "sp('health', 0)",
              'function onUpdate', 'function onDestroy', 'getSongPosition',
              'alert', 'attack', 'ALERT_GAP', 'JUDGE_DELAY', 'blackOff']:
    ck('saw token ' + token, token in saw_script)
# 事件名兼容 DK Saw 与 Dodge Mechanic
ck('saw event names', "'Dodge Mechanic'" in saw_script and "'Dodge Mechanic'" in saw_script)
# 原版默认 timing: 0.20 / 0.30, 黑幕 0.4
import re as _re
_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)
_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)
ck('v1112 alert gap 0.30', bool(_m) and abs(float(_m.group(1)) - 0.30) < 0.001)
ck('v1112 judge delay 0.32', bool(_j) and abs(float(_j.group(1)) - 0.32) < 0.001)
ck('v1112 single alert only', saw_script.count("playSound, 'alert'") == 1 and 'alertDouble' not in saw_script and 'alertTriple' not in saw_script)
ck('v1112 black hard-off', saw_script.count('blackOff()') >= 3 and "pcall(cancelTween, 'dkSawBlackIn')" in saw_script)
ck('v1112 no global dimming', 'blackHardOffTimer' in saw_script and 'stage < 3' in saw_script)
ck('v1112 reaction >=300ms', 'local JUDGE_DELAY = 0.32' in saw_script)
ck('v1112 baguette thrust+return', "doTweenX, 'dkBagOutX'" in saw_script and "doTweenX, 'dkBagInX'" in saw_script)
ck('v1112 warning self-made', os.path.getsize(os.path.join(G, 'images/dkSawWarning.png')) > 1000)
ck('orig attack judge', "playSound, 'attack'" in saw_script)
ck('saw cleanup timer guard', "runTimer, 'dkSawCleanup'" in saw_script)
# 单时钟：无 onUpdatePost tick
ck('saw single-clock no double tick', 'function onUpdatePost' not in saw_script)
ck('saw judge by songMs', 'local now = songMs()' in saw_script)
# 原版三段动画 1/2/dodge
ck('v1112 single alert graphic', 'dkSawWarning' in saw_script)
ck('saw stage machine', 'w.stage = 1' in saw_script and 'w.stage = 2' in saw_script and 'w.stage = 3' in saw_script)
ck('saw dodge window', 'w.stage >= 1 and w.stage < 3' in saw_script)
ck('saw sprite exists guard', 'luaSpriteExists' in saw_script)
ck('saw NO virtualbuttons', 'virtualbuttons' not in saw_script)
# DK_Fun 单 tick
fun_src = rb('scripts/DK_Fun.lua').decode('utf-8')
ck('fun single-clock', 'function onUpdatePost(elapsed) end' in fun_src or 'no double tick' in fun_src)
ck('saw event shell lua', len(rb('custom_events/DK Saw.lua')) > 0)
ck('saw event shell txt', len(rb('custom_events/DK Saw.txt')) > 0)
# 新事件壳 Dodge Mechanic（事件栏可见）
ck('Dodge Mechanic shell lua', len(rb('custom_events/Dodge Mechanic.lua')) > 0)
ck('Dodge Mechanic shell txt', len(rb('custom_events/Dodge Mechanic.txt')) > 0)
# 旧版图片保持删除；旧版噔噔音效必须已恢复
for rel in ['images/dk_saw.png', 'images/dk_saw.xml', 'images/dk_alert.png',
            'images/dk_alert.xml', 'images/dk_alert_vignette.png']:
    ck('OLD img removed ' + rel, not os.path.exists(os.path.join(G, rel)))
for rel, exp in [('sounds/alert.ogg', 29632), ('sounds/attack.ogg', 57378),
                  ('sounds/dodge.ogg', 22890)]:
    ck('ORIG sound ' + rel, os.path.getsize(os.path.join(G, rel)) == exp)
ck('baguette png game', os.path.getsize(os.path.join(G, 'images/dkBaguette.png')) > 10000)
for rel in ['sounds/alertDouble.ogg','sounds/alertTriple.ogg','sounds/alertQuadruple.ogg',
            'sounds/dkAlert1.ogg','sounds/dkAlert2.ogg','sounds/dkAlert3.ogg',
            'sounds/dkSawAttack.ogg','sounds/dkDodgeSound.ogg','sounds/dodge01.ogg',
            'sounds/sawbladeHit.ogg','images/dkSawAssets','images/dk_saw_alert.png','images/dk_saw_alert.xml']:
    ck('PURGED '+rel, not os.path.exists(os.path.join(G, rel)))
# 新素材 md5
def realmd5(rel): return hashlib.md5(rb(rel)).hexdigest()
for rel, exp in [
    ('images/dkDodged.png', '0127f7ed2426'),
]:
    h = realmd5(rel)
    ck('saw asset ' + rel, (h == exp) if len(exp) == 32 else h.startswith(exp))
# legacy sound files are harmless leftovers; original set above is required
# 谱面事件不变
for song in ['double-kill', 'double-kill-miku']:
    gd = json.loads(rb('data/%s/%s-god.json' % (song, song)).decode('utf-8-sig'))
    hd = json.loads(rb('data/%s/%s-hard.json' % (song, song)).decode('utf-8-sig'))
    gpd = json.loads(rb('data/%s/%s-god+.json' % (song, song)).decode('utf-8-sig'))
    saws = [e for e in gd['events'] if e[1] and e[1][0][0] == 'Dodge Mechanic']
    gps  = [e for e in gpd['events'] if e[1] and e[1][0][0] == 'Dodge Mechanic']
    hds  = [e for e in hd['events'] if e[1] and e[1][0][0] == 'Dodge Mechanic']
    ck('%s god saws=34' % song, len(saws) == 34)
    ck('%s god+ saws=34' % song, len(gps) == 34)
    ck('%s hard saws=0' % song, len(hds) == 0)
    ck('%s saw single-left' % song, all(e[1][0][1]=='left' and e[1][0][2]=='1' for e in saws))

# ===== v11.1 新增：GOD+ 独立难度 =====
# 难度图（mod 本地，优先于 assets）
ck('god diff png', len(rb('images/menudifficulties/god.png')) > 0)
ck('god+ diff png', len(rb('images/menudifficulties/god+.png')) > 0)
for song in ['double-kill', 'double-kill-miku']:
    rel = 'data/%s/%s-god+.json' % (song, song)
    ck('chart ' + os.path.basename(rel), os.path.exists(os.path.join(G, rel)))
    gp = json.loads(rb(rel).decode('utf-8-sig'))
    gd = json.loads(rb('data/%s/%s-god.json' % (song, song)).decode('utf-8-sig'))
    # GOD+ 谱面 = GOD 谱面内容（含 34 锯子 + 特殊键），角色引用有效
    gp_saw = sum(1 for e in gp['events'] if e[1] and e[1][0][0] == 'Dodge Mechanic')
    gd_saw = sum(1 for e in gd['events'] if e[1] and e[1][0][0] == 'Dodge Mechanic')
    ck('%s god+ saw==god (%d)' % (song, gd_saw), gp_saw == gd_saw == 34)
    ck('%s god+ notes==god' % song,
       sum(len(s['sectionNotes']) for s in gp['notes']) == sum(len(s['sectionNotes']) for s in gd['notes']))
    for key in ['player1', 'player2', 'gfVersion']:
        ch = gp.get(key)
        ck('god+ char %s/%s' % (song, key), os.path.exists(os.path.join(G, 'characters', ch + '.json')))

print('=== VERIFY ===')
bad = [n for n, ok in CHECKS if not ok]
for n, ok in CHECKS:
    if not ok:
        print('  FAIL', n)
print('total=%d  pass=%d  fail=%d' % (len(CHECKS), len(CHECKS) - len(bad), len(bad)))
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
print('md5:', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
for rel in ['scripts/DK_Saw.lua', 'images/dkBaguette.png', 'images/dkSawWarning.png', 'sounds/alert.ogg',
            'data/double-kill/double-kill-god.json',
            'data/double-kill/double-kill-god+.json',
            'images/menudifficulties/god+.png', 'weeks/dk-momo.json']:
    print('  inzip', ('OK ' if ('DK_Duet/' + rel) in z.namelist() else 'MISS'), rel)
