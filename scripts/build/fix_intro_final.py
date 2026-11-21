# -*- coding: utf-8 -*-
"""收尾：白屏只用 events.lua 里那一层，Teto 白屏淡出时立刻常驻；残影放上层。"""
import os

M = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'

NEWLOGIC = '''-- Double Kill 第二对手（Teto）：白屏过渡消失后直接出现，之后一直显示在旁边。
-- 原版从天而降的黑色 Impostor 过渡动画（blackIntro / dkblack-intro）已整个删除。
function onCreatePost()
    -- 白屏盖住画面时先隐藏，避免穿帮
    setProperty('gfGroup.alpha', 0)
end

function onSongStart()
    -- 白屏开始淡出的同一时刻出现，此后不再有任何 alpha 改动
    setProperty('gfGroup.alpha', 1)
    setProperty('gf.alpha', 1)
end
'''

p = os.path.join(M, 'data/double-kill/NewLogic.lua')
open(p, 'w', encoding='utf-8', newline='').write(NEWLOGIC)
print('重写 NewLogic.lua（无 blackIntro、无第二层白屏）')

ep = os.path.join(M, 'data/double-kill/events.lua')
t = open(ep, encoding='utf-8').read()
t = t.replace("makeGraphic('black', 640, 360, '000000')", "makeGraphic('black', 640, 360, 'FFFFFF')")
t = t.replace("doTweenAlpha('xd', 'black', 0, 2)", "doTweenAlpha('xd', 'black', 0, 0.8)")
open(ep, 'w', encoding='utf-8', newline='').write(t)
print('events.lua: 开场黑屏改成白屏，淡出 2s -> 0.8s')

gp = os.path.join(M, 'custom_events/Duo Ghost.lua')
g = open(gp, encoding='utf-8').read()
g = g.replace("    addLuaSprite(ghostTag, false)", "    addLuaSprite(ghostTag, true)")
open(gp, 'w', encoding='utf-8', newline='').write(g)
print('Duo Ghost.lua: 半透明残影移到角色上层')

# 静态检查：括号平衡、旧黑过渡动画残留
for rel in ('data/double-kill/NewLogic.lua', 'custom_events/Legacy.lua',
            'custom_events/Duo Ghost.lua', 'data/double-kill/events.lua'):
    s = open(os.path.join(M, rel), encoding='utf-8').read()
    bal = s.count('(') - s.count(')')
    print(' ', rel, '括号差', bal, '| blackIntro 残留', 'blackIntro' in s)
