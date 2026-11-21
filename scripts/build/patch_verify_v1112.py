# -*- coding: utf-8 -*-
p = 'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
s = open(p, encoding='utf-8').read()
s = s.replace("DK_Duet_FULL_v11.11_GODplus_20261116.zip", "DK_Duet_FULL_v11.12_GODplus_20261116.zip")
# token set for clean re-port
s = s.replace("'dkBaguette', 'dk_saw_alert', 'dkDodged',", "'dkBaguette', 'dkSawWarning', 'dkDodged',")
s = s.replace("'alert', 'alertDouble', 'alertTriple', 'attack', 'timing1', 'timing2', 'timing3']:", "'alert', 'attack', 'ALERT_GAP', 'JUDGE_DELAY', 'blackOff']:")
# remove stale timing regex assertions (v11.12 uses ALERT_GAP / JUDGE_DELAY)
s = s.replace("_m = _re.search(r'local timing1 = ([0-9.]+)', saw_script)", "_m = _re.search(r'local ALERT_GAP = ([0-9.]+)', saw_script)")
s = s.replace("_j = _re.search(r'local timing2 = ([0-9.]+)', saw_script)", "_j = _re.search(r'local JUDGE_DELAY = ([0-9.]+)', saw_script)")
s = s.replace("ck('v1111 timing1 0.30', bool(_m) and abs(float(_m.group(1)) - 0.30) < 0.001)", "ck('v1112 alert gap 0.30', bool(_m) and abs(float(_m.group(1)) - 0.30) < 0.001)")
s = s.replace("ck('v1112 timing2 0.30', bool(_j) and abs(float(_j.group(1)) - 0.30) < 0.001)", "ck('v1112 judge delay 0.32', bool(_j) and abs(float(_j.group(1)) - 0.32) < 0.001)")
s = s.replace("ck('v1111 timing2 0.30', bool(_j) and abs(float(_j.group(1)) - 0.30) < 0.001)", "ck('v1112 judge delay 0.32', bool(_j) and abs(float(_j.group(1)) - 0.32) < 0.001)")
# replace v1111 assertions block
old = """ck('v1111 black 0.4', "BLACK_TAG, 0.4, 0.3" in saw_script)
ck('v1111 black fullscreen other-cam', "setObjectCamera, BLACK_TAG, 'other'" in saw_script and "screenCenter, BLACK_TAG" in saw_script)
ck('v1111 three distinct bells', saw_script.count("playSound, 'alert'") == 1 and "playSound, 'alertDouble'" in saw_script and "playSound, 'alertTriple'" in saw_script)
ck('v1111 reaction >=300ms', "timing3 = 0.32" in saw_script)
ck('v1111 baguette thrust+return', "doTweenX, 'dkBagOutX'" in saw_script and "doTweenX, 'dkBagInX'" in saw_script)"""
new = """ck('v1112 single alert only', saw_script.count("playSound, 'alert'") == 1 and 'alertDouble' not in saw_script and 'alertTriple' not in saw_script)
ck('v1112 black hard-off', saw_script.count('blackOff()') >= 3 and "pcall(cancelTween, 'dkSawBlackIn')" in saw_script)
ck('v1112 no global dimming', 'blackHardOffTimer' in saw_script and 'stage < 3' in saw_script)
ck('v1112 reaction >=300ms', 'local JUDGE_DELAY = 0.32' in saw_script)
ck('v1112 baguette thrust+return', "doTweenX, 'dkBagOutX'" in saw_script and "doTweenX, 'dkBagInX'" in saw_script)
ck('v1112 warning self-made', os.path.getsize(os.path.join(G, 'images/dkSawWarning.png')) > 1000)"""
s = s.replace(old, new)
# purge checks: legacy sounds/images must NOT exist
s = s.replace("# 新素材 md5", """for rel in ['sounds/alertDouble.ogg','sounds/alertTriple.ogg','sounds/alertQuadruple.ogg',
            'sounds/dkAlert1.ogg','sounds/dkAlert2.ogg','sounds/dkAlert3.ogg',
            'sounds/dkSawAttack.ogg','sounds/dkDodgeSound.ogg','sounds/dodge01.ogg',
            'sounds/sawbladeHit.ogg','images/dkSawAssets','images/dk_saw_alert.png','images/dk_saw_alert.xml']:
    ck('PURGED '+rel, not os.path.exists(os.path.join(G, rel)))
# 新素材 md5""")
# remove old md5 assertions for purged assets
s = s.replace("    ('images/dk_saw_alert.png', '1707608f70e56ee90630754501a295ac'),\n    ('images/dk_saw_alert.xml', '20d6e654710549a14f497543598d64dc'),\n    ('images/dkSawAssets/spritemap1.png', '9d03c3d93dc3'),\n    ('images/dkSawAssets/spritemap1.json', 'dc7c28adb79a'),\n    ('images/dkSawAssets/Animation.json', '2450cbe09686'),\n", "")
s = s.replace("alert_xml = rb('images/dk_saw_alert.xml').decode('utf-8-sig')\nck('saw alert atlas has width/height', 'width=\"2048\"' in alert_xml and 'height=\"' in alert_xml)\n", "")
# old sound size assertion list references dkAlert1 removed - just check alert/attack/dodge
s = s.replace("for rel, exp in [('sounds/alert.ogg', 29632), ('sounds/attack.ogg', 57378),\n                  ('sounds/dodge.ogg', 22890)]:", "for rel, exp in [('sounds/alert.ogg', 29632), ('sounds/attack.ogg', 57378),\n                  ('sounds/dodge.ogg', 22890)]:")
# inzip list: replaced old assets with new
s = s.replace("'scripts/DK_Saw.lua', 'images/dkBaguette.png', 'images/dk_saw_alert.png', 'images/dkSawAssets/Animation.json', 'sounds/dkAlert1.ogg',",
              "'scripts/DK_Saw.lua', 'images/dkBaguette.png', 'images/dkSawWarning.png', 'sounds/alert.ogg',")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', len(s))
