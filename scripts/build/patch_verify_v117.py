# -*- coding: utf-8 -*-
"""Patch verify_and_pack_v11.py saw block to v11.7 checks."""
p = r'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
t = open(p, encoding='utf-8').read()

start = t.index('# ===== v11.6：移植 QT 原版 Dodge Mechanic')
end = t.index('# ===== v11.1 新增：GOD+ 独立难度 =====')

new = '''# ===== v11.7：ASCII 脚本修复 + 放慢节奏 + 删旧素材 + Dodge Mechanic 事件壳 =====
saw_raw = rb('scripts/DK_Saw.lua')
saw_script = saw_raw.decode('utf-8')
# 致命根因回归：脚本必须纯 ASCII（全角破折号 —— 曾导致 LuaJIT 加载失败）
ck('saw source pure ASCII', all(b < 128 for b in saw_raw))
ck('saw no fullwidth dash', '\\u2014' not in saw_script)
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
for token in ['makeAnimatedLuaSprite', 'addAnimationByPrefix', 'makeFlxAnimateSprite',
              'addAnimationBySymbol', 'dk_saw_alert', 'dkSawAssets', 'dkDodged',
              'dkDodgeActive', 'botPlaying', "sp('health', 0)",
              'function onUpdate', 'function onDestroy', 'getSongPosition',
              'dkAlert1', 'dkAlert2', 'dkAlert3', 'dkSawAttack', 'dkDodgeSound']:
    ck('saw token ' + token, token in saw_script)
# 事件名兼容 DK Saw 与 Dodge Mechanic
ck('saw event names', "'DK Saw'" in saw_script and "'Dodge Mechanic'" in saw_script)
# 放慢节奏：ALERT_GAP>=0.7, JUDGE_DELAY>=0.5
import re as _re
_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)
_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)
ck('saw slow ALERT_GAP>=0.7', bool(_m) and float(_m.group(1)) >= 0.7)
ck('saw slow JUDGE_DELAY>=0.5', bool(_j) and float(_j.group(1)) >= 0.5)
# 单时钟：无 onUpdatePost tick
ck('saw single-clock no double tick', 'function onUpdatePost' not in saw_script)
ck('saw judge by songMs', 'local now = songMs()' in saw_script)
# 三阶段灯号警报（alert1/alert2/alert3）
ck('saw 3-stage alert', "'alert1'" in saw_script and "'alert2'" in saw_script and "'alert3'" in saw_script)
ck('saw stage machine', 'w.stage = 1' in saw_script and 'w.stage = 2' in saw_script and 'w.stage = 3' in saw_script and 'w.stage = 4' in saw_script)
ck('saw dodge opens at 2nd', 'w.stage >= 2 and w.stage < 4' in saw_script)
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
# 旧版素材必须已删除（撇掉旧版锯子）
for rel in ['images/dk_saw.png', 'images/dk_saw.xml', 'images/dk_alert.png',
            'images/dk_alert.xml', 'images/dk_alert_vignette.png',
            'sounds/alert.ogg', 'sounds/alertDouble.ogg', 'sounds/alertTriple.ogg',
            'sounds/alertQuadruple.ogg', 'sounds/sawbladeHit.ogg', 'sounds/dodge01.ogg']:
    ck('OLD removed ' + rel, not os.path.exists(os.path.join(G, rel)))
# 新素材 md5
def realmd5(rel): return hashlib.md5(rb(rel)).hexdigest()
for rel, exp in [
    ('images/dk_saw_alert.png', '1707608f70e56ee90630754501a295ac'),
    ('images/dk_saw_alert.xml', '20d6e654710549a14f497543598d64dc'),
    ('images/dkSawAssets/spritemap1.png', '9d03c3d93dc3'),
    ('images/dkSawAssets/spritemap1.json', 'dc7c28adb79a'),
    ('images/dkSawAssets/Animation.json', '2450cbe09686'),
    ('images/dkDodged.png', '0127f7ed2426'),
]:
    h = realmd5(rel)
    ck('saw asset ' + rel, (h == exp) if len(exp) == 32 else h.startswith(exp))
for s in ['dkAlert1.ogg', 'dkAlert2.ogg', 'dkAlert3.ogg', 'dkSawAttack.ogg', 'dkDodgeSound.ogg']:
    ck('saw sound ' + s, len(rb('sounds/' + s)) > 0)
alert_xml = rb('images/dk_saw_alert.xml').decode('utf-8-sig')
ck('saw alert atlas has width/height', 'width="2048"' in alert_xml and 'height="' in alert_xml)
# 谱面事件不变
for song in ['double-kill', 'double-kill-miku']:
    gd = json.loads(rb('data/%s/%s-god.json' % (song, song)).decode('utf-8-sig'))
    hd = json.loads(rb('data/%s/%s-hard.json' % (song, song)).decode('utf-8-sig'))
    gpd = json.loads(rb('data/%s/%s-god+.json' % (song, song)).decode('utf-8-sig'))
    saws = [e for e in gd['events'] if e[1] and e[1][0][0] == 'DK Saw']
    gps  = [e for e in gpd['events'] if e[1] and e[1][0][0] == 'DK Saw']
    hds  = [e for e in hd['events'] if e[1] and e[1][0][0] == 'DK Saw']
    ck('%s god saws=34' % song, len(saws) == 34)
    ck('%s god+ saws=34' % song, len(gps) == 34)
    ck('%s hard saws=0' % song, len(hds) == 0)
    ck('%s saw single-left' % song, all(e[1][0][1]=='left' and e[1][0][2]=='1' for e in saws))

'''

t = t[:start] + new + t[end:]
# header / output
t = t.replace('"""v11.7 (修 Lua 块注释头 ---[[ -> --[[ 导致脚本加载失败) 终检 + 打完整包。"""',
              '"""v11.7 (ASCII 脚本修复 + 放慢警报 + 删旧素材 + Dodge Mechanic 事件壳) 终检 + 打完整包。"""')
open(p, 'w', encoding='utf-8', newline='').write(t)
print('patched, len=', len(t))
