import zipfile, json, hashlib, collections
P = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.30_OldInfant_20261118.zip'
z = zipfile.ZipFile(P)
ns = z.namelist()
print('items', len(ns), 'CRC', 'OK' if z.testzip() is None else 'BAD')

# 1) week 难度
for w in ['DK_Duet/weeks/dk-momo.json', 'DK_Duet/weeks/dk-miku.json']:
    d = json.loads(z.read(w).decode('utf-8-sig'))
    print(w, 'difficulties =', d.get('difficulties'))

# 2) 谱面文件 + 音符 + noteType + BOM
for s in ['double-kill', 'double-kill-miku']:
    for diff in ['old', 'hard', 'infant', 'god', 'god+']:
        n = f'DK_Duet/data/{s}/{s}-{diff}.json'
        if n not in ns:
            print(s, diff, 'MISSING'); continue
        b = z.read(n)
        bom = b.startswith(b'\xef\xbb\xbf')
        j = json.loads(b.decode('utf-8-sig'))
        secs = j.get('notes', [])
        tot = sum(len(x.get('sectionNotes', [])) for x in secs if isinstance(x, dict))
        types = collections.Counter()
        for sec in secs:
            for nt in sec.get('sectionNotes', []):
                if isinstance(nt, list) and len(nt) > 3:
                    types[str(nt[3])] += 1
        print(f'{s:18s} {diff:6s} BOM={bom} notes={tot} types={dict(types)}')

# 3) 新人声 md5
v = 'DK_Duet/songs/double-kill-miku/Voices.ogg'
print('voice md5', hashlib.md5(z.read(v)).hexdigest(), len(z.read(v)))

# 4) 难度图标
for n in ['DK_Duet/images/menudifficulties/old.png', 'DK_Duet/images/menudifficulties/infant.png']:
    print(n, len(z.read(n)), 'B' if n in ns else 'MISSING')
