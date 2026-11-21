# -*- coding: utf-8 -*-
p = 'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
s = open(p, encoding='utf-8').read()
REPL = [
('"""v11.7 (ASCII 脚本修复 + 放慢警报 + 删旧素材 + Dodge Mechanic 事件壳) 终检 + 打完整包。"""',
 '"""v11.8 (恢复原版快速节奏 + 旧版噔噔音效 + timer 防误隐藏) 终检 + 打完整包。"""'),
("OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.7_GODplus_20261116.zip'",
 "OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.8_GODplus_20261116.zip'"),
("              'dkAlert1', 'dkAlert2', 'dkAlert3', 'dkSawAttack', 'dkDodgeSound']:",
 "              'alert', 'alertDouble', 'alertQuadruple', 'sawbladeHit', 'dodge01']:"),
("""# 放慢节奏：ALERT_GAP>=0.7, JUDGE_DELAY>=0.5
import re as _re
_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)
_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)
ck('saw slow ALERT_GAP>=0.7', bool(_m) and float(_m.group(1)) >= 0.7)
ck('saw slow JUDGE_DELAY>=0.5', bool(_j) and float(_j.group(1)) >= 0.5)""",
 """# 恢复原版快速节奏：ALERT_GAP<=0.25, JUDGE_DELAY<=0.20
import re as _re
_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)
_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)
ck('saw fast ALERT_GAP<=0.25', bool(_m) and float(_m.group(1)) <= 0.25)
ck('saw fast JUDGE_DELAY<=0.20', bool(_j) and float(_j.group(1)) <= 0.20)
ck('saw timer hide guard', 'local activeSaw = false' in saw_script)"""),
("""# 旧版素材必须已删除（撇掉旧版锯子）
for rel in ['images/dk_saw.png', 'images/dk_saw.xml', 'images/dk_alert.png',
            'images/dk_alert.xml', 'images/dk_alert_vignette.png',
            'sounds/alert.ogg', 'sounds/alertDouble.ogg', 'sounds/alertTriple.ogg',
            'sounds/alertQuadruple.ogg', 'sounds/sawbladeHit.ogg', 'sounds/dodge01.ogg']:
    ck('OLD removed ' + rel, not os.path.exists(os.path.join(G, rel)))""",
 """# 旧版图片保持删除；旧版噔噔音效必须已恢复
for rel in ['images/dk_saw.png', 'images/dk_saw.xml', 'images/dk_alert.png',
            'images/dk_alert.xml', 'images/dk_alert_vignette.png']:
    ck('OLD img removed ' + rel, not os.path.exists(os.path.join(G, rel)))
for rel in ['sounds/alert.ogg', 'sounds/alertDouble.ogg', 'sounds/alertTriple.ogg',
            'sounds/alertQuadruple.ogg', 'sounds/sawbladeHit.ogg', 'sounds/dodge01.ogg']:
    ck('OLD sound restored ' + rel, os.path.exists(os.path.join(G, rel)))"""),
]
for a, b in REPL:
    if a not in s:
        print('WARN not found:', a[:70].replace('\n', '|'))
    s = s.replace(a, b)
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', p, len(s))
