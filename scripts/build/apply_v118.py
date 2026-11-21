# -*- coding: utf-8 -*-
"""v11.8: restore fast saw timing + old punchy alert sounds (from v11.6)."""
import zipfile, os

ROOT = 'E:/UST_work/dk_miku'
G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DEPLOYS = [G, ROOT + '/DK_Dual', ROOT + '/DK_Miku']
OLD_ZIP = ROOT + '/DK_Duet_FULL_v11.6_GODplus_20261116.zip'

SOUNDS = ['alert.ogg', 'alertDouble.ogg', 'alertTriple.ogg',
          'alertQuadruple.ogg', 'dodge01.ogg', 'sawbladeHit.ogg']

z = zipfile.ZipFile(OLD_ZIP)
for d in DEPLOYS:
    os.makedirs(d + '/sounds', exist_ok=True)
    for s in SOUNDS:
        data = z.read('DK_Duet/sounds/' + s)
        open(d + '/sounds/' + s, 'wb').write(data)
        print('restored', d, s, len(data))

REPL = [
    ('local ALERT_GAP = 0.75', 'local ALERT_GAP = 0.20'),
    ('local JUDGE_DELAY = 0.55', 'local JUDGE_DELAY = 0.18'),
    ("playSound, 'dkAlert1'", "playSound, 'alert'"),
    ("playSound, 'dkAlert2'", "playSound, 'alertDouble'"),
    ("playSound, 'dkAlert3'", "playSound, 'alertQuadruple'"),
    ("playSound, 'dkSawAttack'", "playSound, 'sawbladeHit'"),
    ("playSound, 'dkDodgeSound'", "playSound, 'dodge01'"),
    ('sounds dkAlert1/2/3, dkSawAttack, dkDodgeSound',
     'sounds alert/alertDouble/alertQuadruple, sawbladeHit, dodge01'),
]

for d in DEPLOYS:
    p = d + '/scripts/DK_Saw.lua'
    raw = open(p, encoding='utf-8').read()
    for a, b in REPL:
        if a not in raw:
            print('WARN missing in', p, ':', a)
        raw = raw.replace(a, b)
    # guard: hide timer must not kill a newly spawned saw
    old = """function onTimerCompleted(tag)
    if tag == 'dkSawHide' then
        sp(SAW_TAG .. '.visible', false)
    end
end"""
    new = """function onTimerCompleted(tag)
    if tag == 'dkSawHide' then
        local activeSaw = false
        for i = 1, #waves do
            if waves[i].stage == 3 then activeSaw = true end
        end
        if not activeSaw then sp(SAW_TAG .. '.visible', false) end
    end
end"""
    if old in raw:
        raw = raw.replace(old, new)
        print('timer guard applied', p)
    else:
        print('WARN timer block not found', p)
    open(p, 'w', encoding='utf-8', newline='\n').write(raw)
    print('patched', p, len(raw))
