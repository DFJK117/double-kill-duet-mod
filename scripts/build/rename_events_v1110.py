# -*- coding: utf-8 -*-
"""v11.10: chart events DK Saw -> Dodge Mechanic (original event name)."""
import os, json

ROOT = 'E:/UST_work/dk_miku'
G = 'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
DEPLOYS = [G, ROOT + '/DK_Dual', ROOT + '/DK_Miku']
SONGS = ['double-kill', 'double-kill-miku']
DIFFS = ['god', 'god+']

for d in DEPLOYS:
    for song in SONGS:
        for diff in DIFFS:
            p = os.path.join(d, 'data', song, song + '-' + diff + '.json')
            if not os.path.exists(p):
                print('MISS', p)
                continue
            txt = open(p, encoding='utf-8-sig').read()
            n = txt.count("'DK Saw'") + txt.count('"DK Saw"')
            if n:
                txt = txt.replace('DK Saw', 'Dodge Mechanic')
                open(p, 'w', encoding='utf-8', newline='').write(txt)
            # verify event count
            dd = json.loads(open(p, encoding='utf-8-sig').read())
            cnt = sum(1 for e in dd['events']
                      if e[1] and e[1][0][0] == 'Dodge Mechanic')
            print('renamed', os.path.relpath(p, d), n, '-> DM total', cnt)
