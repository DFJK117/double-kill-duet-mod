# -*- coding: utf-8 -*-
"""把 QT 原版 Dodge Mechanic 全套素材部署到 DK 三处目录。
素材源：_godmode/ 下已提取好的文件。
- 警告三段动画 -> images/dk_saw_alert.png/xml (sparrow, 36帧, 带 width/height)
- 锯子 FlxAnimate -> images/dkSawAssets/{spritemap1.png,spritemap1.json,Animation.json}
- DODGED 弹字 -> images/dkDodged.png
- 音效 -> sounds/dkAlert1,dkAlert2,dkAlert3,dkSawAttack,dkDodgeSound.ogg
"""
import os, shutil, hashlib

ROOTS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
STAGE = r'E:/UST_work/dk_miku/_godmode'

# (源文件, 目标相对路径)
FILES = [
    ('dk_saw_alert.png', 'images/dk_saw_alert.png'),
    ('dk_saw_alert.xml', 'images/dk_saw_alert.xml'),
    ('dkSawSpritemap1.png', 'images/dkSawAssets/spritemap1.png'),
    ('dkSawSpritemap1.json', 'images/dkSawAssets/spritemap1.json'),
    ('dkSawAnimation.json', 'images/dkSawAssets/Animation.json'),
    ('dkDodged.png', 'images/dkDodged.png'),
    ('dkAlert1.ogg', 'sounds/dkAlert1.ogg'),
    ('dkAlert2.ogg', 'sounds/dkAlert2.ogg'),
    ('dkAlert3.ogg', 'sounds/dkAlert3.ogg'),
    ('dkSawAttack.ogg', 'sounds/dkSawAttack.ogg'),
    ('dkDodgeSound.ogg', 'sounds/dkDodgeSound.ogg'),
]

def md5(path):
    return hashlib.md5(open(path, 'rb').read()).hexdigest()

for root in ROOTS:
    print('===', root)
    for src, rel in FILES:
        s = os.path.join(STAGE, src)
        d = os.path.join(root, rel)
        os.makedirs(os.path.dirname(d), exist_ok=True)
        shutil.copy2(s, d)
    # 校验
    ok = True
    for src, rel in FILES:
        s = os.path.join(STAGE, src)
        d = os.path.join(root, rel)
        same = md5(s) == md5(d)
        ok = ok and same
        if not same:
            print('  MISMATCH', rel)
    print('  deployed', len(FILES), 'files;', 'ALL MATCH' if ok else 'HAS MISMATCH')

# 三处一致性
print('=== 三处一致性 ===')
allok = True
for src, rel in FILES:
    hs = [md5(os.path.join(r, rel)) for r in ROOTS]
    same = len(set(hs)) == 1
    allok = allok and same
    print(('OK ' if same else 'DIFF'), rel, hs[0][:10])
print('ALL SYNC', allok)
