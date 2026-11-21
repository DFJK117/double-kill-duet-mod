# -*- coding: utf-8 -*-
"""v11.32 完整部署到三处：先备份旧目录到 I 盘，再从 zip 覆盖"""
import zipfile, os, shutil, hashlib, time

ZIP = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.32_MenuBGM_20261118.zip'
BK  = r'I:/_trash_ust_work/deploy_backup_20261118_1920'
TARGETS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Miku',
    r'E:/UST_work/dk_miku/DK_Dual',
]
PREFIX = 'DK_Duet/'
os.makedirs(BK, exist_ok=True)

z = zipfile.ZipFile(ZIP)
members = [n for n in z.namelist() if n.startswith(PREFIX)]

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

for i, tgt in enumerate(TARGETS):
    tag = ['game_DK_Duet', 'DK_Miku', 'DK_Dual'][i]
    # 1) 备份旧目录到 I 盘（只备份一次）
    bdst = os.path.join(BK, tag)
    if not os.path.exists(bdst):
        shutil.copytree(tgt, bdst)
        print('BACKUP', tag, '->', bdst)
    # 2) 从 zip 覆盖解压（去掉 DK_Duet/ 前缀）
    written = 0
    for n in members:
        rel = n[len(PREFIX):]
        if not rel:
            continue
        dst = os.path.join(tgt, rel.replace('/', os.sep))
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        data = z.read(n)
        # 若目标已存在且内容相同则跳过写入（减少改动），不同则覆盖
        if os.path.exists(dst) and md5(dst) == hashlib.md5(data).hexdigest():
            continue
        with open(dst, 'wb') as f:
            f.write(data)
        written += 1
    print('DEPLOY', tag, 'written', written, 'of', len(members))

# 3) 核验三处关键项
print('\n=== VERIFY ===')
checks = {
    'week diff': 'weeks/dk-miku.json',
    'infant icon': 'images/menudifficulties/infant.png',
    'infant chart': 'data/double-kill/double-kill-infant.json',
    'old chart': 'data/double-kill/double-kill-old.json',
    'menu bgm': 'music/freakyMenu.ogg',
    'pack desc': 'pack.json',
    'DK_Fun dodge': 'scripts/DK_Fun.lua',
}
for tgt in TARGETS:
    print('--', tgt)
    import json
    w = os.path.join(tgt, 'weeks', 'dk-miku.json')
    j = json.load(open(w, encoding='utf-8-sig'))
    print('   difficulties =', j.get('difficulties'))
    for k, rel in checks.items():
        if k == 'week diff':
            continue
        p = os.path.join(tgt, rel)
        print('   %-14s %s' % (k, 'OK' if os.path.exists(p) else 'MISSING'))
    bgm = os.path.join(tgt, 'music', 'freakyMenu.ogg')
    inst = os.path.join(tgt, 'songs', 'double-kill-miku', 'Inst.ogg')
    print('   bgm==mikuInst', md5(bgm) == md5(inst))
    pk = json.load(open(os.path.join(tgt, 'pack.json'), encoding='utf-8-sig'))
    print('   desc has Infant:', 'Infant' in pk.get('description', ''))
print('\nDONE')
