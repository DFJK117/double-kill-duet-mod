# -*- coding: utf-8 -*-
import zipfile, re
p = 'E:/UST_work/dk_miku/DK_Duet_FULL_v11.6_GODplus_20261116.zip'
z = zipfile.ZipFile(p)
names = z.namelist()
print('=== OLD SAW SOUNDS IN v11.6 ===')
for n in names:
    if n.startswith('DK_Duet/sounds/') and any(k in n for k in ['alert', 'saw', 'dodge', 'hit']):
        print(' ', n, z.getinfo(n).file_size)
print()
print('=== OLD DK_Saw.lua ===')
raw = z.read('DK_Duet/scripts/DK_Saw.lua').decode('utf-8-sig')
print(raw[:3000])
print()
for pat in [r'local ALERT_GAP = ([0-9.]+)', r'local JUDGE_DELAY = ([0-9.]+)']:
    m = re.search(pat, raw)
    print(pat, '=>', m.group(1) if m else 'NOT FOUND')
print()
print('=== OLD playSound calls ===')
for line in raw.splitlines():
    if 'playSound' in line:
        print(' ', line.strip())
