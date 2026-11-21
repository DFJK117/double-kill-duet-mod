import os, shutil, json, hashlib

OUT = r'I:/_trash_ust_work/legacy_recovery_20261118'
os.makedirs(OUT, exist_ok=True)

# 找到的所有遗产 double kill 谱面
sources = {
 'PE_DK_hard_2800':   r'I:/_trash_ust_work/dk_miku/_backup_PE_momo_20261114/data/double-kill/double-kill-hard.json',
 'PE_DK_events':      r'I:/_trash_ust_work/dk_miku/_backup_PE_momo_20261114/data/double-kill/events.json',
 'LE_DK_hard_empty':  r'I:/_trash_ust_work/dk_miku/_backup_LE_momo_20261114/data/song data/double kill/double kill-hard.json',
 'NVE_DK_empty':      r'I:/NF-1.2.1h2/export/release/windows/bin/mods/VSImpostorLegacy_NVE/data/double-kill.json',
 'CURRENT_DK_hard':   r'E:/UST_work/dk_miku/DK_Miku/data/double-kill/double-kill-hard.json',
 'CURRENT_DK_godp':   r'E:/UST_work/dk_miku/DK_Miku/data/double-kill/double-kill-god+.json',
 'CURRENT_DK_main':   r'E:/UST_work/dk_miku/DK_Miku/data/double-kill/double-kill.json',
 'CURRENT_MIKU_hard': r'E:/UST_work/dk_miku/DK_Miku/data/double-kill-miku/double-kill-miku-hard.json',
 'CURRENT_MIKU_godp': r'E:/UST_work/dk_miku/DK_Miku/data/double-kill-miku/double-kill-miku-god+.json',
}

def chart_stat(p):
    try:
        j = json.load(open(p, encoding='utf-8-sig'))
    except Exception as e:
        return 'BADJSON:' + str(e)[:30]
    notes = j.get('notes', [])
    n = sum(len(s.get('sectionNotes', [])) for s in notes if isinstance(s, dict))
    ev = 0
    for s in notes:
        if isinstance(s, dict):
            ev += len(s.get('sectionEvents', []) or [])
    # noteTypes
    types = {}
    for s in notes:
        if isinstance(s, dict):
            for note in s.get('sectionNotes', []) or []:
                if isinstance(note, list) and len(note) > 3:
                    t = str(note[3]); types[t] = types.get(t, 0) + 1
    return 'notes=%d events=%d types=%s' % (n, ev, types)

manifest = []
for key, p in sources.items():
    if not os.path.exists(p):
        print('MISSING', key, p); continue
    b = open(p, 'rb').read()
    md5 = hashlib.md5(b).hexdigest()
    dst = os.path.join(OUT, key + '.json')
    shutil.copy2(p, dst)
    stat = chart_stat(p)
    print('%-20s %9d B md5=%s %s' % (key, len(b), md5[:12], stat))
    manifest.append((key, len(b), md5, stat))

with open(os.path.join(OUT, 'MANIFEST.txt'), 'w', encoding='utf-8') as f:
    f.write('遗产谱面找回 2026-11-18\n')
    for key, sz, md5, stat in manifest:
        f.write('%-20s %9d B md5=%s %s\n' % (key, sz, md5, stat))
print('ARCHIVED ->', OUT)
