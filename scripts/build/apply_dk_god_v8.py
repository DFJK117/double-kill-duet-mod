# -*- coding: utf-8 -*-
"""DK_Duet v8 部署：黑+黄手主题 / 两个自定义 type 按键 / GOD 模式。

做四件事：
  1. 角色图集重着色（黑身 + 黄手 + 话筒原色）覆盖到三处目录
  2. 新增两个自定义 note 皮肤（dk_trap / dk_warn）与 GOD 徽章
  3. 新增 DK_God.lua + 两个 custom_notetypes，并给 DK_Push.lua 加 GOD 免疫
  4. 谱面改造：和弦上加陷阱键 + 少量普通键换成警告牌
最后跑校验 + 打包 zip。
"""
import json, os, shutil, sys, zipfile, hashlib, io

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import patch_charts_god as PC
import recolor_characters as RC

WORK = r'E:/UST_work/dk_miku'
GOD = r'E:/UST_work/dk_miku/_godmode'
STAGE = GOD + '/stage'
ASSETS = GOD + '/assets'
TARGETS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
BACKUP = WORK + '/_backup_god_v8_20261115'
ZIP = WORK + '/DK_Duet_Lua_v8_20261115.zip'

CHECKS = []


def ck(name, ok, detail=''):
    CHECKS.append((name, bool(ok), detail))
    print(('  PASS  ' if ok else '  FAIL  ') + name + (('  | ' + str(detail)) if detail != '' else ''))
    return ok


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(65536), b''):
            h.update(b)
    return h.hexdigest()


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


# ---------------------------------------------------------------
def backup():
    src = TARGETS[0]
    if os.path.exists(BACKUP):
        print('备份已存在，跳过（保持原始版本作为对比基准）:', BACKUP)
        return
    shutil.copytree(src, BACKUP, ignore=shutil.ignore_patterns('*.bak*', '_bak*'))
    print('备份 ->', BACKUP)


def push_assets():
    """重着色图集 + 新贴图"""
    for tag in ('miku', 'momo', 'teto', 'bf', 'bfdefeat'):
        cfg = RC.CFG[tag]
        rel = 'images/characters/' + cfg['png']
        src = GOD + '/recolored_%s.png' % tag
        for t in TARGETS:
            copy(src, os.path.join(t, rel))
    for name in ('dk_trap.png', 'dk_trap.xml', 'dk_warn.png', 'dk_warn.xml', 'dk_god_badge.png'):
        for t in TARGETS:
            copy(os.path.join(ASSETS, name), os.path.join(t, 'images', name))
    print('已推送：重着色图集 x4 + note 皮肤 x2 + GOD 徽章')


def push_lua():
    files = [
        ('scripts/DK_God.lua', 'scripts/DK_God.lua'),
        ('custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.lua'),
        ('custom_notetypes/DK Trap.txt', 'custom_notetypes/DK Trap.txt'),
        ('custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.lua'),
        ('custom_notetypes/DK Warn.txt', 'custom_notetypes/DK Warn.txt'),
    ]
    for s, d in files:
        for t in TARGETS:
            copy(os.path.join(STAGE, s), os.path.join(t, d))
    # DK_Push.lua：GOD 模式下不推血
    OLD = "    if not enabled then return end\n"
    NEW = ("    if not enabled then return end\n"
           "    -- GOD 模式免疫推条（DK_God.lua 写入 dkGodMode）\n"
           "    local okGod, godVal = pcall(getVar, 'dkGodMode')\n"
           "    if okGod and godVal == true then return end\n")
    for t in TARGETS:
        p = os.path.join(t, 'scripts/DK_Push.lua')
        with open(p, encoding='utf-8') as f:
            txt = f.read()
        if 'dkGodMode' not in txt:
            if OLD not in txt:
                print('  !! DK_Push.lua 未找到锚点:', p)
                continue
            txt = txt.replace(OLD, NEW, 1)
            with open(p, 'w', encoding='utf-8', newline='\n') as f:
                f.write(txt)
    print('已推送：DK_God.lua + 2 个 custom_notetypes(+txt) + DK_Push GOD 免疫')


def push_charts():
    for t in TARGETS:
        for rel, label in (('data/double-kill/double-kill-hard.json', '桃音+Teto'),
                           ('data/double-kill-miku/double-kill-miku-hard.json', '初音+Teto')):
            p = os.path.join(t, rel)
            if not os.path.exists(p):
                continue
            with open(p, encoding='utf-8-sig') as f:
                cur = json.load(f)
            if any(len(n) > 3 and n[3] == 'DK Trap'
                   for s in cur['notes'] for n in s['sectionNotes']):
                print('  跳过（已改造）', rel)
                continue
            chart = PC.patch(p, label)
            PC.dump(chart, p)
    print('已改造两首曲的谱面')


# ---------------------------------------------------------------
def validate():
    print('\n=== 校验 ===')
    game = TARGETS[0]
    # 1) 图集尺寸与原版一致（XML 不变，坐标必须对齐）
    for tag in ('miku', 'momo', 'teto', 'bf', 'bfdefeat'):
        cfg = RC.CFG[tag]
        orig = os.path.join(BACKUP, 'images/characters', cfg['png'])
        new = os.path.join(game, 'images/characters', cfg['png'])
        from PIL import Image
        so = Image.open(orig).size
        sn = Image.open(new).size
        ck('%s 图集尺寸不变 %s' % (tag, so), so == sn, '%s vs %s' % (so, sn))
    # 2) 角色图集确实变了
    for tag in ('miku', 'momo', 'teto', 'bf', 'bfdefeat'):
        cfg = RC.CFG[tag]
        o = md5(os.path.join(BACKUP, 'images/characters', cfg['png']))
        n = md5(os.path.join(game, 'images/characters', cfg['png']))
        ck('%s 图集已重着色' % tag, o != n)
    # 3) 新资源就位
    for rel in ('images/dk_trap.png', 'images/dk_trap.xml', 'images/dk_warn.png', 'images/dk_warn.xml',
                'images/dk_god_badge.png', 'scripts/DK_God.lua',
                'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.txt',
                'custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.txt'):
        ck('存在 %s' % rel, os.path.exists(os.path.join(game, rel)))
    # 4) note 皮肤 XML 帧名必须是引擎要的四个前缀
    import xml.etree.ElementTree as ET
    for base in ('dk_trap', 'dk_warn'):
        root = ET.parse(os.path.join(game, 'images', base + '.xml')).getroot()
        names = [t.get('name') for t in root.iter('SubTexture')]
        need = [c + '0000' for c in ('purple', 'blue', 'green', 'red')]
        ck('%s.xml 帧名齐全 %s' % (base, need), all(nm in names for nm in need),
           '实际 %d 帧' % len(names))
        png = os.path.join(game, 'images', base + '.png')
        from PIL import Image
        im = Image.open(png)
        ck('%s.png 尺寸 %s' % (base, im.size), im.size[0] > 0 and im.mode == 'RGBA', str(im.size))
    # 5) 谱面：两种 type 的音符数量与位置
    for rel in ('data/double-kill/double-kill-hard.json',
                'data/double-kill-miku/double-kill-miku-hard.json'):
        with open(os.path.join(game, rel), encoding='utf-8-sig') as f:
            c = json.load(f)
        traps, warns, player = [], [], 0
        for si, sec in enumerate(c['notes']):
            for n in sec['sectionNotes']:
                if n[1] < 4:
                    player += 1
                    if len(n) > 3 and n[3] == 'DK Trap':
                        traps.append((n[0], n[1]))
                    elif len(n) > 3 and n[3] == 'DK Warn':
                        warns.append((n[0], n[1]))
                else:
                    ck_ok = (len(n) <= 3 or n[3] in ('Opponent 2 Sing', 'Both Opponents Sing'))
                    if not ck_ok:
                        ck('%s 对手侧未混入新 type' % rel, False, str(n))
        ck('%s 陷阱键 %d 个' % (rel.split('/')[1], len(traps)), len(traps) == PC.N_TRAP, len(traps))
        ck('%s 警告牌 %d 个' % (rel.split('/')[1], len(warns)), len(warns) == PC.N_WARN, len(warns))
        ck('%s 玩家音符全部在轨道0-3' % rel.split('/')[1],
           all(l < 4 for _, l in traps + warns))
        ck('%s 段级 mustHitSection 混合保留' % rel.split('/')[1],
           len(set(s['mustHitSection'] for s in c['notes'])) == 2)
        # 陷阱键不能与其它音符同轨同时
        allrows = [(n[0], n[1]) for s in c['notes'] for n in s['sectionNotes']]
        with open(os.path.join(BACKUP, rel), encoding='utf-8-sig') as f:
            oc = json.load(f)
        orows = [(n[0], n[1]) for s in oc['notes'] for n in s['sectionNotes']]
        dup_now = len(allrows) - len(set(allrows))
        dup_old = len(orows) - len(set(orows))
        ck('%s 未新增同轨同刻重复(原谱已有%d)' % (rel.split('/')[1], dup_old),
           dup_now == dup_old, '现 %d' % dup_now)
    # 6) Lua 无 hscript / runHaxeCode
    for rel in ('scripts/DK_God.lua', 'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Warn.lua',
                'scripts/DK_Push.lua'):
        with open(os.path.join(game, rel), encoding='utf-8') as f:
            t = f.read()
        code = '\n'.join(l for l in t.splitlines() if not l.strip().startswith('--'))
        ck('%s 无 runHaxeCode' % rel, 'runHaxeCode' not in code)
    with open(os.path.join(game, 'scripts/DK_God.lua'), encoding='utf-8') as f:
        g = f.read()
    ck('DK_God.lua 注册 goodNoteHit', 'function goodNoteHit' in g)
    ck('DK_God.lua 注册 noteMiss', 'function noteMiss' in g)
    ck('DK_God.lua 有 F4 开关', "GOD_KEY   = 'F4'" in g)
    ck('DK_God.lua 写 dkGodMode', "sv('dkGodMode'" in g)
    with open(os.path.join(game, 'scripts/DK_Push.lua'), encoding='utf-8') as f:
        pu = f.read()
    ck('DK_Push.lua 有 GOD 免疫', 'dkGodMode' in pu)
    # 7) 三处一致性
    for rel in ('characters/bf.json', 'scripts/DK_God.lua',
                'images/characters/miku_assets.png', 'images/dk_trap.png',
                'data/double-kill/double-kill-hard.json'):
        hs = set(md5(os.path.join(t, rel)) for t in TARGETS)
        ck('三处一致 %s' % rel, len(hs) == 1, '%d 个不同' % len(hs))

    fail = [n for n, ok, _ in CHECKS if not ok]
    print('\n=== 汇总: %d 项, 失败 %d 项 ===' % (len(CHECKS), len(fail)))
    for f in fail:
        print('  !! ' + f)
    return 1 if fail else 0


def pack():
    files = [
        'scripts/DK_God.lua', 'scripts/DK_Push.lua',
        'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.txt',
        'custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.txt',
        'images/dk_trap.png', 'images/dk_trap.xml',
        'images/dk_warn.png', 'images/dk_warn.xml', 'images/dk_god_badge.png',
        'images/characters/miku_assets.png', 'images/characters/momo_assets.png',
        'images/characters/teto-2026.png', 'images/characters/cuphead/BoyFriend_ICCuphead.png',
        'images/characters/bf/defeatBf-normal.png',
        'data/double-kill/double-kill-hard.json',
        'data/double-kill-miku/double-kill-miku-hard.json',
    ]
    if os.path.exists(ZIP):
        os.remove(ZIP)
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in files:
            p = os.path.join(TARGETS[0], rel)
            if os.path.exists(p):
                z.write(p, 'DK_Duet/' + rel)
    bad = zipfile.ZipFile(ZIP).testzip()
    print('打包 -> %s  (%d 项, %d B, CRC %s)'
          % (ZIP, len(zipfile.ZipFile(ZIP).namelist()), os.path.getsize(ZIP),
             'OK' if bad is None else bad))


if __name__ == '__main__':
    backup()
    push_assets()
    push_lua()
    push_charts()
    rc = validate()
    pack()
    sys.exit(rc)
