# -*- coding: utf-8 -*-
"""v11.32 = v11.31 基底 + 主页背景音(miku伴奏) + pack.json/README 更新日志"""
import zipfile, hashlib, os, shutil, io

BASE = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.31_DodgeLock_20261118.zip'
OUT  = r'E:/UST_work/dk_miku/DK_Duet_FULL_v11.32_MenuBGM_20261118.zip'

# 更新日志（模组详情显示 = pack.json description）
DESC = ("BF vs {Momo / Miku} + Teto | 2 Songs | "
        "[2026-11-18 更新] 难度: hard改名old + 新增Infant婴儿难度(坐姿婴儿图标); "
        "空格躲避动画强制播完(不被连打顶掉); 主页背景音=Double Kill Miku伴奏; "
        "保留 GOD/GOD+ 与 FLS 原声")

CHANGELOG = """
==================== 更新日志 / CHANGELOG ====================
[2026-11-18] v11.32
  - 模组主页(主菜单)背景音改为 Double Kill Miku 的伴奏 (music/freakyMenu.ogg)
  - 难度: hard 改名 old (谱面内容不变); 新增 Infant 婴儿难度 (mods12 新版2800谱, 坐姿婴儿图标)
  - 空格躲避(dodge)动画强制播完, 命中音符的 sing 不再顶掉躲避动作
  - 保留 GOD / GOD+ 难度、黑黄资源、FLS 新人声 (md5 8f9ca277...)
[2026-11-18] v11.29
  - Double Kill Miku 人声替换为 FLS 原声 (支持和弦唱, 解决 OpenUTAU 断续)
[2026-11-16] v10
  - 难度资源分离: hard 用原版贴图, GOD 用黑黄贴图; Trap/Warn 特殊键机制
============================================================
"""

zin = zipfile.ZipFile(BASE)
names = zin.namelist()
# miku 伴奏
inst = zin.read('DK_Duet/songs/double-kill-miku/Inst.ogg')
print('miku Inst.ogg', len(inst), hashlib.md5(inst).hexdigest()[:12])

n = 0
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as z:
    for it in zin.infolist():
        data = zin.read(it.filename)
        if it.filename == 'DK_Duet/pack.json':
            import json
            j = json.loads(data.decode('utf-8-sig'))
            j['description'] = DESC
            data = json.dumps(j, ensure_ascii=False, indent=1).encode('utf-8')
            print('pack.json description updated')
        elif it.filename == 'DK_Duet/README.txt':
            data = data + ('\n' + CHANGELOG).encode('utf-8')
            print('README changelog appended')
        z.writestr(it, data)
        n += 1
    # 新增主页背景音
    z.writestr('DK_Duet/music/freakyMenu.ogg', inst)
    n += 1
    print('added DK_Duet/music/freakyMenu.ogg')

z = zipfile.ZipFile(OUT)
bad = z.testzip()
print('OUT', os.path.basename(OUT))
print('items', n, 'size', os.path.getsize(OUT))
print('CRC', 'OK' if bad is None else bad)
print('md5', hashlib.md5(open(OUT, 'rb').read()).hexdigest())
# 校验
assert z.read('DK_Duet/music/freakyMenu.ogg') == inst
assert 'Infant' in z.read('DK_Duet/pack.json').decode('utf-8-sig')
assert 'freakyMenu' not in z.read('DK_Duet/weeks/dk-miku.json').decode('utf-8-sig')
print('VERIFY OK: freakyMenu==miku Inst, desc has Infant, week untouched')
