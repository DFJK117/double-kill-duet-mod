# -*- coding: utf-8 -*-
p = 'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
s = open(p, encoding='utf-8').read()
REPL = [
('"""v11.8 (恢复原版快速节奏 + 旧版噔噔音效 + timer 防误隐藏) 终检 + 打完整包。"""',
 '"""v11.9 (严格复刻原版 Dodge Mechanic 流程 + 原版音效) 终检 + 打完整包。"""'),
("OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.8_GODplus_20261116.zip'",
 "OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.9_GODplus_20261116.zip'"),
("              'alert', 'alertDouble', 'alertQuadruple', 'sawbladeHit', 'dodge01']:",
 "              'alert', 'attack', 'timing1', 'timing2']:"),
("""# 恢复原版快速节奏：ALERT_GAP<=0.25, JUDGE_DELAY<=0.20
import re as _re
_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)
_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)
ck('saw fast ALERT_GAP<=0.25', bool(_m) and float(_m.group(1)) <= 0.25)
ck('saw fast JUDGE_DELAY<=0.20', bool(_j) and float(_j.group(1)) <= 0.20)
ck('saw timer hide guard', 'local activeSaw = false' in saw_script)""",
 """# 原版默认 timing: 0.20 / 0.30, 黑幕 0.4
import re as _re
_m = _re.search(r'local timing1 = ([0-9.]+)', saw_script)
_j = _re.search(r'local timing2 = ([0-9.]+)', saw_script)
ck('orig timing1 0.20', bool(_m) and abs(float(_m.group(1)) - 0.20) < 0.001)
ck('orig timing2 0.30', bool(_j) and abs(float(_j.group(1)) - 0.30) < 0.001)
ck('orig black 0.4', "BLACK_TAG, 0.4, 0.3" in saw_script)
ck('orig alert x2', saw_script.count("playSound, 'alert'") == 2)
ck('orig attack judge', "playSound, 'attack'" in saw_script)
ck('saw timer hide guard', 'local activeSaw = false' in saw_script)"""),
("# 三阶段灯号警报（alert1/alert2/alert3）\nck('saw 3-stage alert', \"'alert1'\" in saw_script and \"'alert2'\" in saw_script and \"'alert3'\" in saw_script)\nck('saw stage machine', 'w.stage = 1' in saw_script and 'w.stage = 2' in saw_script and 'w.stage = 3' in saw_script and 'w.stage = 4' in saw_script)",
 "# 原版三段动画 1/2/dodge\nck('orig anim 1/2/dodge', \"'1'\" in saw_script and \"'2'\" in saw_script and \"'dodge'\" in saw_script)\nck('saw stage machine', 'w.stage = 1' in saw_script and 'w.stage = 2' in saw_script and 'w.stage = 3' in saw_script)"),
("""for rel in ['sounds/alert.ogg', 'sounds/alertDouble.ogg', 'sounds/alertTriple.ogg',
            'sounds/alertQuadruple.ogg', 'sounds/sawbladeHit.ogg', 'sounds/dodge01.ogg']:
    ck('OLD sound restored ' + rel, os.path.exists(os.path.join(G, rel)))""",
 """for rel, exp in [('sounds/alert.ogg', 29632), ('sounds/attack.ogg', 57378),
                  ('sounds/dodge.ogg', 22890)]:
    ck('ORIG sound ' + rel, os.path.getsize(os.path.join(G, rel)) == exp)"""),
("for s in ['dkAlert1.ogg', 'dkAlert2.ogg', 'dkAlert3.ogg', 'dkSawAttack.ogg', 'dkDodgeSound.ogg']:\n    ck('saw sound ' + s, len(rb('sounds/' + s)) > 0)",
 "# legacy sound files are harmless leftovers; original set above is required"),
]
for a, b in REPL:
    if a not in s:
        print('WARN not found:', a[:80].replace('\n', '|'))
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p, len(s))
