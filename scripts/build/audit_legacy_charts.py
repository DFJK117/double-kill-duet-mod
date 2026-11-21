import os, json, glob

paths = [
 r'I:/_trash_ust_work/dk_miku/_backup_PE_momo_20261114/data/double-kill/double-kill-hard.json',
 r'I:/_trash_ust_work/dk_miku/_backup_LE_momo_20261114/data/song data/double kill/double kill-hard.json',
 r'I:/NF-1.2.1h2/export/release/windows/bin/mods/VSImpostorLegacy_NVE/data/double-kill.json',
 r'E:/UST_work/dk_miku/DK_Miku/data/double-kill/double-kill-hard.json',
 r'E:/UST_work/dk_miku/DK_Miku/data/double-kill/double-kill.json',
 r'E:/UST_work/dk_miku/DK_Miku/data/double-kill-miku/double-kill-miku-hard.json',
 r'I:/_trash_ust_work/dk_miku/_backup_deployed_20261115_1346/data/double-kill/double-kill-hard.json',
 r'I:/_trash_ust_work/dk_miku/_backup_lua_v5_20261115/data/double-kill/double-kill-hard.json',
 r'I:/_trash_ust_work/dk_miku/_backup_god_v8_20261115/data/double-kill/double-kill-hard.json',
]

for p in paths:
    if not os.path.exists(p):
        print('MISSING', p); continue
    try:
        d = json.load(open(p, encoding='utf-8-sig'))
    except Exception as e:
        print('BADJSON', p, str(e)[:50]); continue
    song = d.get('song', {})
    if isinstance(song, str):
        head = ('str', song)
    else:
        head = song.get('player1'), song.get('player2')
    notes = d.get('notes', [])
    if not isinstance(notes, list):
        notes = []
    total = 0
    empty_secs = 0
    for sec in notes:
        if not isinstance(sec, dict):
            continue
        sn = sec.get('sectionNotes', [])
        if not isinstance(sn, list):
            sn = []
        total += len(sn)
        if not sn: empty_secs += 1
    nf = len(notes)
    print('%-70s notes=%5d secs=%3d empty=%3d p1/p2=%s' % (p, total, nf, empty_secs, head))
