# -*- coding: utf-8 -*-
"""v11.7 deploy: new ASCII DK_Saw, remove old saw assets, add Dodge Mechanic event shell."""
import os, shutil, hashlib

ROOTS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SRC_SAW = r'E:/UST_work/dk_miku/scripts/DK_Saw.lua'

# old assets to remove (legacy QT saw, no longer referenced)
OLD_IMAGES = ['dk_saw.png', 'dk_saw.xml', 'dk_alert.png', 'dk_alert.xml', 'dk_alert_vignette.png']
OLD_SOUNDS = ['alert.ogg', 'alertDouble.ogg', 'alertTriple.ogg', 'alertQuadruple.ogg',
              'sawbladeHit.ogg', 'dodge01.ogg']
# keep DK Dodge shell (harmless, may be referenced manually); we only ADD an alias below
OLD_EVENTS = []

# new Dodge Mechanic event shell -> visible in editor event list; logic in scripts/DK_Saw.lua
DM_LUA = """-- Dodge Mechanic (GOD+ saw) - logic in scripts/DK_Saw.lua
-- onEvent left empty on purpose: global script handles it, avoids double trigger.
function onEvent(name, value1, value2)
end
"""
DM_TXT = """Dodge Mechanic

QT sawblade dodge (GOD+). 3 escalating alerts, then the saw flies.
Press SPACE from the 2nd alert to dodge. BotPlay auto-dodges.
value1: direction left/right (default left)
value2: saw count 1/2/3/4 (default 1)
"""


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest() if os.path.exists(p) else None


for root in ROOTS:
    name = root.rstrip('/').split('/')[-1]
    print('===', name, '===')

    # 1) deploy new DK_Saw.lua
    dst = os.path.join(root, 'scripts', 'DK_Saw.lua')
    shutil.copyfile(SRC_SAW, dst)
    print('  DK_Saw.lua md5', md5(dst))

    # 2) remove old assets
    for f in OLD_IMAGES:
        p = os.path.join(root, 'images', f)
        if os.path.exists(p):
            os.remove(p)
            print('  removed images/', f)
    for f in OLD_SOUNDS:
        p = os.path.join(root, 'sounds', f)
        if os.path.exists(p):
            os.remove(p)
            print('  removed sounds/', f)

    # 3) remove old DK Dodge event shell
    for f in OLD_EVENTS:
        p = os.path.join(root, 'custom_events', f)
        if os.path.exists(p):
            os.remove(p)
            print('  removed custom_events/', f)

    # 4) add Dodge Mechanic event shell (visible in event list)
    os.makedirs(os.path.join(root, 'custom_events'), exist_ok=True)
    with open(os.path.join(root, 'custom_events', 'Dodge Mechanic.lua'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(DM_LUA)
    with open(os.path.join(root, 'custom_events', 'Dodge Mechanic.txt'), 'w', encoding='utf-8', newline='') as fh:
        fh.write(DM_TXT)
    print('  added Dodge Mechanic event shell')

print('\nDONE')
