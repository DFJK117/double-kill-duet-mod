# -*- coding: utf-8 -*-
p = 'E:/UST_work/dk_miku/scripts/verify_and_pack_v11.py'
s = open(p, encoding='utf-8').read()
s = s.replace("OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.9_GODplus_20261116.zip'",
              "OUT = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.10_GODplus_20261116.zip'")
s = s.replace("'DK Saw'", "'Dodge Mechanic'")
s = s.replace("'DK Saw'\" in saw_script and \"'Dodge Mechanic'", "'Dodge Mechanic'\" in saw_script and \"'DK Saw'")
open(p, 'w', encoding='utf-8', newline='\n').write(s)
print('patched; DK Saw refs left:', s.count("'DK Saw'"), '| DM refs:', s.count("'Dodge Mechanic'"))
