# -*- coding: utf-8 -*-
"""把 DK_Saw.lua + custom_events/DK Saw.lua/.txt 部署到三处模组。"""
import os, shutil, hashlib

SRC_SCRIPT = r'E:/UST_work/dk_miku/scripts/DK_Saw.lua'
GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ROOTS = [r'E:/UST_work/dk_miku/DK_Dual', r'E:/UST_work/dk_miku/DK_Miku', GAME]

EVENT_LUA = '''---
-- DK Saw —— 谱面事件注册壳（真逻辑在 scripts/DK_Saw.lua）
--
-- value1 = 方向 left / right / both（默认 left：锯从右飞向左）
-- value2 = 数量 1/2/3/4（默认 1）
-- 警告 -> 锯子飞过 -> 在判定点检查空格 dodge 窗口(dkDodgeActive)：
-- 窗口内躲开，窗口外 health=0 秒杀；BotPlay 自动躲开。
-- onEvent 保持空实现，避免与全局脚本重复触发。

function onEvent(name, value1, value2)
end
'''
EVENT_TXT = '''DK Saw

Warning triangle -> sawblade flies across -> dodge with SPACE.
value1: direction left / right / both (default left)
value2: saw count 1 / 2 / 3 / 4 (default 1)
Dodge window (dkDodgeActive) saves you; otherwise instant death.
'''


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def main():
    for root in ROOTS:
        sd = os.path.join(root, 'scripts')
        ed = os.path.join(root, 'custom_events')
        os.makedirs(sd, exist_ok=True)
        os.makedirs(ed, exist_ok=True)
        shutil.copyfile(SRC_SCRIPT, os.path.join(sd, 'DK_Saw.lua'))
        open(os.path.join(ed, 'DK Saw.lua'), 'w', encoding='utf-8').write(EVENT_LUA)
        open(os.path.join(ed, 'DK Saw.txt'), 'w', encoding='utf-8').write(EVENT_TXT)
        print('DEPLOY', root)
        print('  script', md5(os.path.join(sd, 'DK_Saw.lua')))
        print('  event ', md5(os.path.join(ed, 'DK Saw.lua')))


if __name__ == '__main__':
    main()
