# -*- coding: utf-8 -*-
"""DK_Duet v10：把 hard 与 God 两套资源彻底拆开。

v9 的两处污染：
  ① hard 谱面被塞了 88 个特殊键（本该干净）；
  ② 角色贴图全局共用，hard 也被套上黑黄皮。

v10 设计（不用 Lua 换皮，纯两套资源 + 谱面按难度指向不同角色名）：
  * hard  : 恢复备份原版（彩色图集 / 原角色名 / 0 特殊键）
  * God   : 黑黄图集独立命名 *_god.png；新建 *-god.json 角色定义指向它们；
            God 谱面 player1/player2/gfVersion 改成 *-god 角色名
  * 特殊键规则（用户明确）：
      - DK Trap（按到即死） = 只加在【和弦的空闲轨道】上（附加键，玩家可不按）
      - DK Warn （漏按即死） = 只【替换普通键】（玩家必须按，漏了才死）
      - 双方侧（轨道 0-3 玩家 / 4-7 对手）都要有
      - 严禁把 Trap 放到普通键上（那是必死无解）

用法：python apply_dk_god_v10.py
"""
import os, sys, json, shutil, hashlib, zipfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import patch_charts_god_v9 as P9

GOD = r'E:/UST_work/dk_miku/_godmode'
BACK = r'E:/UST_work/dk_miku/_backup_god_v8_20261115'
PKG = r'E:/UST_work/dk_miku'
TARGETS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
ZIP = PKG + '/DK_Duet_Lua_v10_20261116.zip'

# 角色：原名 -> (原图集相对路径, God 重着色输出文件名, God 图集新名, God 角色名)
# 角色 json 的 image 字段 = 'characters/' + 图集相对 images/characters 的路径（不含扩展名）
ROLES = {
    'bf':    ('cuphead/BoyFriend_ICCuphead', 'recolored_bf.png',        'cuphead/BoyFriend_ICCuphead_god', 'bf-god'),
    'momo':  ('momo_assets',                  'recolored_momo.png',      'momo_assets_god',                 'momo-god'),
    'teto':  ('teto-2026',                    'recolored_teto.png',      'teto-2026_god',                   'teto-god'),
    'miku':  ('miku_assets',                  'recolored_miku.png',      'miku_assets_god',                 'miku-god'),
    'bfdefeat': ('bf/defeatBf-normal',        'recolored_bfdefeat.png',  'bf/defeatBf-normal_god',          'bf-defeat-normal-god'),
}
# 谱面里实际引用的玩家/对手/GF 角色 -> God 映射
CHART_ROLE_MAP = {'bf': 'bf-god', 'momo': 'momo-god', 'miku': 'miku-god', 'teto': 'teto-god'}

# 8 个 icon（原名 -> 重着色输出）
ICONS = ['bf', 'momo', 'teto-cozy', 'miku', 'momo-teto', 'miku-teto', 'double-kill', 'surprise']

# 特殊键数量（只产 God 谱面）—— 用户要求两种各 200 起步
# Trap 受和弦时刻硬上限约束（玩家165/对手90），取满即约 255
# Warn 替换普通键，池子大（玩家1223/对手529），可堆到 250/220
GOD_TRAP_PLAYER = 200  # 和弦空闲轨道新增（实际约165，取满所有和弦）
GOD_WARN_PLAYER = 260  # 替换普通键（玩家）
GOD_TRAP_OPP    = 200  # 对手和弦空闲轨道（实际约90，取满）
GOD_WARN_OPP    = 220  # 替换普通键（对手）
TRAP_GAP_V10 = 0       # Trap 不设间隔（和弦时刻有限，全取）
WARN_GAP_V10 = 500     # Warn 间隔压低以取够数量


def cp(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)


def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def build_god_roles():
    """生成 God 专用图集 *_god.png + 角色 json *-god.json（指向 God 图集与 God icon）。"""
    made = []
    for old_name, (rel, recol_file, god_rel, god_name) in ROLES.items():
        src = os.path.join(GOD, recol_file)
        assert os.path.exists(src), '缺重着色图: ' + src
        # 角色 json 以原名为模板
        jsrc = os.path.join(BACK, 'characters', _json_name(old_name) + '.json')
        c = json.load(open(jsrc, encoding='utf-8'))
        c['image'] = 'characters/' + god_rel
        # healthicon：God 版用独立 icon 名（<原icon>-god）
        if c.get('healthicon'):
            c['healthicon'] = c['healthicon'] + '-god'
        outj = os.path.join(GOD, 'stage', 'characters', god_name + '.json')
        os.makedirs(os.path.dirname(outj), exist_ok=True)
        with open(outj, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(c, f, ensure_ascii=False, indent=1)
        made.append((god_name + '.json', outj))
        made.append((god_rel.split('/')[-1] + '.png', src))   # 落盘时按 god_rel 定位
    return made


def _json_name(old):
    return {'bfdefeat': 'bf-defeat-normal'}.get(old, old)


def god_char_rel(god_rel):
    """God 图集在 images/characters 下的相对路径（含 .png）"""
    return god_rel + '.png'


def push_assets():
    """三处目录：God 资源新增；hard 原图保持备份原样（覆盖回彩色）。"""
    for t in TARGETS:
        chdir = os.path.join(t, 'images', 'characters')
        # ① 恢复原版彩色图集（hard 用）
        for old_name, (rel, _) in [(k, (v[0], v[1])) for k, v in ROLES.items()]:
            src = os.path.join(BACK, 'images', 'characters', rel + '.png')
            if os.path.exists(src):
                cp(src, os.path.join(chdir, rel + '.png'))
        # ② God 黑黄图集（God 用，独立文件名）
        for old_name, (rel, recol, god_rel, god_name) in ROLES.items():
            src = os.path.join(GOD, recol)
            cp(src, os.path.join(chdir, god_rel + '.png'))
        # ③ icon：原版彩色恢复 + God 黑黄独立命名
        idir = os.path.join(t, 'images', 'icons')
        for n in ICONS:
            src = os.path.join(BACK, 'images', 'icons', 'icon-' + n + '.png')
            if os.path.exists(src):
                cp(src, os.path.join(idir, 'icon-' + n + '.png'))
            gsrc = os.path.join(GOD, 'recolored_icon-' + n + '.png')
            if os.path.exists(gsrc):
                cp(gsrc, os.path.join(idir, 'icon-' + n + '-god.png'))
        # ④ God 角色 json
        jdir = os.path.join(t, 'characters')
        for old_name, (rel, recol, god_rel, god_name) in ROLES.items():
            src = os.path.join(GOD, 'stage', 'characters', god_name + '.json')
            cp(src, os.path.join(jdir, god_name + '.json'))


def _collect_opp_chords(chart):
    """对手侧和弦：同刻 >=2 个对手键，返回 (t, si, free_lanes 4-7)。"""
    occ = P9._occupied(chart)
    out = []
    for si, sec in enumerate(chart['notes']):
        bytime = {}
        for n in sec['sectionNotes']:
            bytime.setdefault(n[0], []).append(n)
        for t, ns in bytime.items():
            ons = [n for n in ns if n[1] >= 4]
            if len(ons) >= 2:
                used = occ.get(t, set())
                free = [l for l in range(4, 8) if l not in used]
                if free:
                    out.append((t, si, free))
    out.sort()
    return out


def patch_god(chart, label):
    """God 谱面改造：Trap 只加和弦空闲轨道；Warn 只替换普通键；双方侧。"""
    rnd = __import__('random').Random(P9.SEED)
    p_chords, p_plain, o_plain = P9.collect_candidates(chart)
    o_chords = _collect_opp_chords(chart)
    used = set()
    res = dict(trap_player=0, warn_player=0, trap_opp=0, warn_opp=0)

    # ① Trap 玩家：只在和弦空闲轨道新增（严禁替换普通键）
    #    顺序放最前：和弦时刻不可再生，避免被 Warn 先占走
    for t, si, free in P9._spread(p_chords, GOD_TRAP_PLAYER, TRAP_GAP_V10, rnd, used):
        lane = free[rnd.randrange(len(free))]
        chart['notes'][si]['sectionNotes'].append([t, lane, 0, P9.TRAP])
        used.add(t); res['trap_player'] += 1

    # ② Trap 对手：只在对手和弦空闲轨道新增（严禁替换普通键）
    for t, si, free in P9._spread(o_chords, GOD_TRAP_OPP, TRAP_GAP_V10, rnd, used):
        lane = free[rnd.randrange(len(free))]
        chart['notes'][si]['sectionNotes'].append([t, lane, 0, P9.TRAP])
        used.add(t); res['trap_opp'] += 1

    # ③ Warn 玩家：替换普通键（玩家必须按，漏了才死）
    for t, si, lane, row in P9._spread(p_plain, GOD_WARN_PLAYER, WARN_GAP_V10, rnd, used):
        row.append(P9.WARN); used.add(t); res['warn_player'] += 1

    # ④ Warn 对手：替换对手普通键（DK_God.lua 轮询判定）
    for t, si, lane, row in P9._spread(o_plain, GOD_WARN_OPP, WARN_GAP_V10, rnd, used):
        row.append(P9.WARN); used.add(t); res['warn_opp'] += 1

    # 角色名 -> God 版
    for k in ('player1', 'player2', 'gfVersion'):
        if chart.get(k) in CHART_ROLE_MAP:
            chart[k] = CHART_ROLE_MAP[chart[k]]

    print('  %-20s 玩家 Trap %-3d Warn %-3d | 对手 Trap %-3d Warn %-3d | 角色 %s/%s/%s'
          % (label, res['trap_player'], res['warn_player'], res['trap_opp'], res['warn_opp'],
             chart.get('player1'), chart.get('player2'), chart.get('gfVersion')))
    return res


def push_charts():
    songs = ['double-kill', 'double-kill-miku']
    for t in TARGETS:
        for song in songs:
            # hard：从备份原版恢复（0 特殊键，原角色名）
            src = os.path.join(BACK, 'data', song, song + '-hard.json')
            cp(src, os.path.join(t, 'data', song, song + '-hard.json'))
            # god：从备份原版派生
            c = P9.load(src)
            patch_god(c, song)
            P9.dump(c, os.path.join(t, 'data', song, song + '-god.json'))
    # weeks difficulties 保持 hard,god
    for t in TARGETS:
        for w in ('dk-momo.json', 'dk-miku.json'):
            p = os.path.join(t, 'weeks', w)
            if os.path.exists(p):
                c = json.load(open(p, encoding='utf-8-sig'))
                c['difficulties'] = 'hard,god'
                with open(p, 'w', encoding='utf-8', newline='\n') as f:
                    json.dump(c, f, ensure_ascii=False, indent=1)


def push_scripts():
    """推 God 逻辑脚本、noteType 配置与皮肤。脚本/配置在 stage/，皮肤在 assets/。"""
    stage = os.path.join(GOD, 'stage')
    assets = os.path.join(GOD, 'assets')
    from_stage = [
        'scripts/DK_God.lua',
        'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.txt',
        'custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.txt',
    ]
    from_assets = [
        ('dk_trap.png', 'images/dk_trap.png'), ('dk_trap.xml', 'images/dk_trap.xml'),
        ('dk_warn.png', 'images/dk_warn.png'), ('dk_warn.xml', 'images/dk_warn.xml'),
        ('dk_god_badge.png', 'images/dk_god_badge.png'),
    ]
    # icons.lua：按难度选双人 icon（God 用黑黄版）
    from_data = ['data/double-kill/icons.lua', 'data/double-kill-miku/icons.lua']
    for t in TARGETS:
        for rel in from_stage:
            cp(os.path.join(stage, rel), os.path.join(t, rel))
        for rel in from_data:
            cp(os.path.join(stage, rel), os.path.join(t, rel))
        for src_name, rel in from_assets:
            cp(os.path.join(assets, src_name), os.path.join(t, rel))


def validate():
    ok = [0]; bad = [0]
    def ck(name, cond, info=''):
        if cond: ok[0] += 1
        else:
            bad[0] += 1
            print('  FAIL %s %s' % (name, info))

    for t in TARGETS:
        tag = os.path.basename(t)
        # hard 谱面：0 特殊键、原角色名
        for song in ('double-kill', 'double-kill-miku'):
            c = P9.load(os.path.join(t, 'data', song, song + '-hard.json'))
            cnt = P9.count_special(c)
            ck(tag + ' ' + song + ' hard 无 Trap', cnt['DK Trap'] == 0, str(cnt))
            ck(tag + ' ' + song + ' hard 无 Warn', cnt['DK Warn'] == 0, str(cnt))
            ck(tag + ' ' + song + ' hard 用原角色', c.get('player1') in CHART_ROLE_MAP.values() or c.get('player1') in ('bf',), str(c.get('player1')))
            # God 谱面：双方侧 Trap/Warn 齐全、角色指向 God
            g = P9.load(os.path.join(t, 'data', song, song + '-god.json'))
            sc = P9.side_count(g)
            trap_total = sc['p_trap'] + sc['o_trap']
            warn_total = sc['p_warn'] + sc['o_warn']
            ck(tag + ' ' + song + ' god Trap合计>=200', trap_total >= 200, str(sc))
            ck(tag + ' ' + song + ' god Warn合计>=200', warn_total >= 200, str(sc))
            ck(tag + ' ' + song + ' god 双方Trap', sc['p_trap'] > 0 and sc['o_trap'] > 0, str(sc))
            ck(tag + ' ' + song + ' god 双方Warn', sc['p_warn'] > 0 and sc['o_warn'] > 0, str(sc))
            ck(tag + ' ' + song + ' god 用God角色', all(g.get(k, '').endswith('-god') for k in ('player1','player2','gfVersion')),
               str([g.get(k) for k in ('player1','player2','gfVersion')]))
            # Trap 不得出现在普通键上：每个 Trap 时刻该轨道必须是和弦（同刻同侧>=2键）
            badtrap = 0
            for sec in g['notes']:
                bytime = {}
                for n in sec['sectionNotes']:
                    bytime.setdefault(n[0], []).append(n)
                for tt, ns in bytime.items():
                    for n in ns:
                        if len(n) > 3 and n[3] == 'DK Trap':
                            side = [x for x in ns if (x[1] < 4) == (n[1] < 4)]
                            if len(side) < 2:
                                badtrap += 1
            ck(tag + ' ' + song + ' god Trap全在和弦', badtrap == 0, '非和弦Trap=%d' % badtrap)
        # God 角色 json / 图集存在
        for old, (rel, recol, god_rel, god_name) in ROLES.items():
            ck(tag + ' God角色json ' + god_name, os.path.exists(os.path.join(t, 'characters', god_name + '.json')))
            ck(tag + ' God图集 ' + god_rel, os.path.exists(os.path.join(t, 'images', 'characters', god_rel + '.png')))
        # 原图集仍在（hard 用）
        for old, (rel, recol, god_rel, god_name) in ROLES.items():
            src = os.path.join(BACK, 'images', 'characters', rel + '.png')
            if os.path.exists(src):
                target_md5 = md5(src)
                ck(tag + ' 原图集保留 ' + rel,
                   md5(os.path.join(t, 'images', 'characters', rel + '.png')) == target_md5)
        # icon：原版 + God 版都在
        for n in ICONS:
            ck(tag + ' icon原版 ' + n, os.path.exists(os.path.join(t, 'images', 'icons', 'icon-' + n + '.png')))
            ck(tag + ' iconGod ' + n, os.path.exists(os.path.join(t, 'images', 'icons', 'icon-' + n + '-god.png')))
        # icons.lua 按难度切双人 icon
        for song in ('double-kill', 'double-kill-miku'):
            ic = open(os.path.join(t, 'data', song, 'icons.lua'), encoding='utf-8').read()
            ck(tag + ' ' + song + ' icons难度切换',
               "difficultyName == 'god'" in ic and "-god' end" in ic)
    print('\n校验汇总: 通过 %d / 失败 %d' % (ok[0], bad[0]))
    return bad[0] == 0


def pack():
    names = []
    # 谱面 4 套 + weeks
    for song in ('double-kill', 'double-kill-miku'):
        for d in ('hard', 'god'):
            names.append('DK_Duet/data/%s/%s-%s.json' % (song, song, d))
    for w in ('dk-momo.json', 'dk-miku.json'):
        names.append('DK_Duet/weeks/' + w)
    for song in ('double-kill', 'double-kill-miku'):
        names.append('DK_Duet/data/%s/icons.lua' % song)
    # God 角色 json
    for old, (rel, recol, god_rel, god_name) in ROLES.items():
        names.append('DK_Duet/characters/' + god_name + '.json')
        names.append('DK_Duet/images/characters/' + god_rel + '.png')
    for n in ICONS:
        names.append('DK_Duet/images/icons/icon-' + n + '-god.png')
    # 脚本与皮肤
    for rel in ['scripts/DK_God.lua', 'custom_notetypes/DK Trap.lua', 'custom_notetypes/DK Trap.txt',
                'custom_notetypes/DK Warn.lua', 'custom_notetypes/DK Warn.txt',
                'images/dk_trap.png', 'images/dk_trap.xml', 'images/dk_warn.png', 'images/dk_warn.xml',
                'images/dk_god_badge.png']:
        names.append('DK_Duet/' + rel)
    base = TARGETS[0]
    with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED) as z:
        for rel in names:
            p = os.path.join(base, rel.split('/', 1)[1])
            assert os.path.exists(p), '打包缺文件: ' + p
            z.write(p, rel)
    z = zipfile.ZipFile(ZIP)
    print('打包 %s: %d 项 / %d B / CRC %s / md5 %s'
          % (os.path.basename(ZIP), len(z.namelist()), os.path.getsize(ZIP),
             z.testzip(), md5(ZIP)))


def main():
    # 先刷新 dk_trap 图集（新椭圆光环箭头）到 assets/，push_scripts 会推到三处
    print('== 0. 重建 Trap 椭圆光环皮肤 ==')
    import apply_dk_god_v9 as V9
    V9.build_trap_skin()
    print('== 1. 生成 God 角色定义 ==')
    made = build_god_roles()
    for n, p in made:
        print('  ', n)
    print('== 2. 推送资源（原图恢复 + God 图独立） ==')
    push_assets()
    print('== 3. 推送谱面（hard 还原 / god 重建） ==')
    push_charts()
    print('== 4. 推送脚本与皮肤 ==')
    push_scripts()
    print('== 5. 校验 ==')
    if not validate():
        print('校验未通过，不打包'); sys.exit(1)
    print('== 6. 打包 ==')
    pack()


if __name__ == '__main__':
    main()
