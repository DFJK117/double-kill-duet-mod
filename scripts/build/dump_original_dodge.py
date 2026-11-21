# -*- coding: utf-8 -*-
import zipfile
z = zipfile.ZipFile('I:/mods.zip')
hits = [n for n in z.namelist() if 'dodge' in n.lower() and n.lower().endswith('.lua')]
print('hits:', len(hits))
for n in hits:
    print('===', n, '===')
    raw = z.read(n)
    print(raw.decode('utf-8-sig', errors='replace')[:12000])
    print()
