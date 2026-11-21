# -*- coding: utf-8 -*-
p = 'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
s = open(p, encoding='utf-8').read()
s = s.replace("DK_Duet_FULL_v11.10_GODplus_20261116.zip", "DK_Duet_FULL_v11.11_GODplus_20261116.zip")
# tokens: legacy saw atlas no longer used
s = s.replace("'makeAnimatedLuaSprite', 'addAnimationByPrefix', 'makeFlxAnimateSprite',\n              'addAnimationBySymbol', 'dk_saw_alert', 'dkSawAssets', 'dkDodged',",
              "'makeAnimatedLuaSprite', 'addAnimationByPrefix', 'makeLuaSprite',\n              'dkBaguette', 'dk_saw_alert', 'dkDodged',")
s = s.replace("'alert', 'attack', 'timing1', 'timing2']:", "'alert', 'alertDouble', 'alertTriple', 'attack', 'timing1', 'timing2', 'timing3']:")
# timing / bell / black assertions
s = s.replace("ck('orig timing1 0.20', bool(_m) and abs(float(_m.group(1)) - 0.20) < 0.001)",
              "ck('v1111 timing1 0.30', bool(_m) and abs(float(_m.group(1)) - 0.30) < 0.001)")
s = s.replace("ck('orig timing2 0.30', bool(_j) and abs(float(_j.group(1)) - 0.30) < 0.001)",
              "ck('v1111 timing2 0.30', bool(_j) and abs(float(_j.group(1)) - 0.30) < 0.001)")
s = s.replace('ck(\'orig black 0.4\', "BLACK_TAG, 0.4, 0.3" in saw_script)\nck(\'orig alert x2\', saw_script.count("playSound, \'alert\'") == 2)',
              'ck(\'v1111 black 0.4\', "BLACK_TAG, 0.4, 0.3" in saw_script)\nck(\'v1111 black fullscreen other-cam\', "setObjectCamera, BLACK_TAG, \'other\'" in saw_script and "screenCenter, BLACK_TAG" in saw_script)\nck(\'v1111 three distinct bells\', saw_script.count("playSound, \'alert\'") == 1 and "playSound, \'alertDouble\'" in saw_script and "playSound, \'alertTriple\'" in saw_script)\nck(\'v1111 reaction >=300ms\', "timing3 = 0.32" in saw_script)\nck(\'v1111 baguette thrust+return\', "doTweenX, \'dkBagOutX\'" in saw_script and "doTweenX, \'dkBagInX\'" in saw_script)')
s = s.replace("ck('orig anim 1/2/dodge', \"'1'\" in saw_script and \"'2'\" in saw_script and \"'dodge'\" in saw_script)",
              "ck('v1111 anim 1/2/dodge', \"'1'\" in saw_script and \"'2'\" in saw_script and \"'dodge'\" in saw_script)")
# baguette png must exist in all three
s = s.replace("# 新素材 md5", "ck('baguette png game', os.path.getsize(os.path.join(G, 'images/dkBaguette.png')) > 10000)\n# 新素材 md5")
# pack inzip list
s = s.replace("'scripts/DK_Saw.lua', 'images/dk_saw_alert.png'", "'scripts/DK_Saw.lua', 'images/dkBaguette.png', 'images/dk_saw_alert.png'")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched', len(s))
