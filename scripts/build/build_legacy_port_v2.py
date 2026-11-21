# -*- coding: utf-8 -*-
"""
把 NF 的 DK_Duet 正确移植到 VS Impostor Legacy 1.1.2（老 PE 结构）。

【关键教训 2026-11-21】
上一版 build_nve_port.py 把 NVE 新结构(charts/ + audio/)套到老 PE 引擎，
exe 字符串里 'charts/' 出现 0 次、'data/' 出现 30 次 -> 引擎回退到 assets 原版资源，
表现为「点进去还是原版 double kill」。本版按遗产版真实规则重建：

  * 谱面: content/<mod>/songs/<song>/data/normal.json   (老 PE 默认难度, 无后缀难度 = normal)
  * 音乐: content/<mod>/songs/<song>/Inst.ogg + Voices.ogg (直接在 song 根, 不是 audio/)
  * 歌名绝不能撞原版: 原版已有 assets/songs/double-kill -> 本 mod 改名
       momo 版 -> double-kill-duo-momo
       miku 版 -> double-kill-duo-miku
     否则 week 里同名 song 会顶掉原版(double kill 变成本 mod 或反过来)。
  * week: content/<mod>/data/weeks/*.json, 老 PE 5 元素格式:
       songs: [["显示名","图标名",[r,g,b],"背景/portrait"," composer", ...]]
       字段 section/storyName/weekName/weekBefore/startUnlocked/hideStoryMode/hideFreeplay/node
       不是 NVE 的 weekCharacters/weekBackground/freeplayColor/difficulties
  * 角色: content/<mod>/data/characters/*.json (树形 data/, 已对)
  * 舞台: content/<mod>/data/stages/<name>.json + <name>.hx (平铺, 不是 <name>/data.json)
  * notetype: 遗产版用 data/notetypes/<type>.txt (空占位) + stage/event 脚本处理,
       原版引擎源码已内建 'Opponent 2 Sing'/'Both Opponents Sing' 的 note.owner 切换
       (见 assets/data/stages/cargo.hx 的 opponentNoteHitPre), 无需 lua。

谱面 song 字段保持源谱原值; chart 内容原样保留(老 PE 本来就吃这种 3/4 元素 note)。
难度: 用户明确「默认旧版」-> 每个 song 只产 data/normal.json = 源 old 谱。

幂等: 每次从 SRC 重建 DEST。备份走 I 盘。
"""
import os, json, shutil, time, sys

SRC = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\windows\mods\DK_Duet'
GAME = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
DEST = os.path.join(GAME, 'content', 'DK_Duet')

# 改名映射: 源 song 目录名 -> 遗产版 song 目录名(避免撞原版 double-kill)
RENAME = {
    'double-kill': 'double-kill-duo-momo',
    'double-kill-miku': 'double-kill-duo-miku',
}
# 显示名
# 注意: 遗产版用显示名 sanitize 定位 song 目录(空格->-, 非法字符删除)。
# 显示名必须 sanitize 后 === 目录名, 否则引擎找不到谱 -> 回退原版。
# "Double Kill (Momo & Teto)" 会变成 "double-kill-(momo---teto)" 匹配不上, 故用纯字母数字。
DISPLAY = {
    'double-kill-duo-momo': 'Double Kill Duo Momo',
    'double-kill-duo-miku': 'Double Kill Duo Miku',
}
# 每首歌的 data/normal.json 来源(源 data/<dir>/ 下的文件)
OLD_CHART = {
    'double-kill': 'double-kill-old.json',
    'double-kill-miku': 'double-kill-miku-old.json',
}


def jload(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def jdump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def build():
    t0 = time.time()
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
        print('清空旧 DEST')
    os.makedirs(DEST, exist_ok=True)

    # ---- 1. meta.json (mod 描述) ----
    jdump({
        'name': 'DFJK117 - Double Kill Duet (Momo/Miku & Teto)',
        'description': 'BF vs Momo/Miku + Teto 双人对唱。谱面=旧版(old)。',
        'global': False,
        'windowTitle': 'VS Impostor Legacy - Double Kill Duet',
    }, os.path.join(DEST, 'meta.json'))

    # ---- 2. songs/<new>/{Inst.ogg, Voices.ogg, data/normal.json, info.txt} ----
    total_notes = 0
    for src_song, new_song in RENAME.items():
        sdir = os.path.join(DEST, 'songs', new_song)
        data_dir = os.path.join(sdir, 'data')
        os.makedirs(data_dir, exist_ok=True)

        # 音乐: 直接在 song 根
        saudio = os.path.join(SRC, 'songs', src_song)
        for af in ['Inst.ogg', 'Voices.ogg']:
            sp = os.path.join(saudio, af)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(sdir, af))
            else:
                print('  MISS audio', src_song, af)

        # 谱面: 源 old 谱 -> data/normal.json
        sp = os.path.join(SRC, 'data', src_song, OLD_CHART[src_song])
        if not os.path.isfile(sp):
            print('  MISS chart', sp)
            continue
        obj = jload(sp)
        s = obj['song'] if isinstance(obj.get('song'), dict) else obj
        s = dict(s)
        s['song'] = DISPLAY[new_song]   # song 字段=显示名, 老 PE 惯例
        # 去掉 NVE-only 字段, 保留老 PE 字段
        s.pop('format', None)
        jdump({'song': s}, os.path.join(data_dir, 'normal.json'))
        nnotes = sum(len(sec.get('sectionNotes', [])) for sec in s.get('notes', []))
        total_notes += nnotes
        print('song', new_song, 'notes=', nnotes)

        # info.txt (遗产版 freeplay 用)
        with open(os.path.join(sdir, 'info.txt'), 'w', encoding='utf-8') as f:
            f.write(DISPLAY[new_song] + '\nComposer: DFJK117\nCharter: DFJK117')

    print('total notes:', total_notes)

    # ---- 3. week: data/weeks/*.json (老 PE 5 元素格式) ----
    # songs 条目: ["显示名","图标名",[r,g,b],"背景portrait","composer"]
    weeks = {
        'dk-duo-momo.json': {
            'songs': [[DISPLAY['double-kill-duo-momo'], 'momo-teto', [200, 180, 220], 'momo', 'DFJK117']],
            'section': 'story',
            'storyName': 'DFJK117', 'weekName': 'Double Kill - Momo & Teto',
            'weekBefore': 'week3', 'startUnlocked': True,
            'hideStoryMode': False, 'hideFreeplay': False,
            'node': {'parent': 'week3', 'direction': 'north'},
        },
        'dk-duo-miku.json': {
            'songs': [[DISPLAY['double-kill-duo-miku'], 'miku-teto', [200, 180, 220], 'miku', 'DFJK117']],
            'section': 'story',
            'storyName': 'DFJK117', 'weekName': 'Double Kill - Miku & Teto',
            'weekBefore': 'week3', 'startUnlocked': True,
            'hideStoryMode': False, 'hideFreeplay': False,
            'node': {'parent': 'week3', 'direction': 'south'},
        },
    }
    for wf, w in weeks.items():
        jdump(w, os.path.join(DEST, 'data', 'weeks', wf))

    # ---- 4. 角色: data/characters/*.json (源角色 json 原样, 已兼容老 PE) ----
    cdir = os.path.join(SRC, 'characters')
    cnum = 0
    os.makedirs(os.path.join(DEST, 'data', 'characters'), exist_ok=True)
    if os.path.isdir(cdir):
        for f in os.listdir(cdir):
            if f.endswith('.json'):
                shutil.copy2(os.path.join(cdir, f), os.path.join(DEST, 'data', 'characters', f))
                cnum += 1
    print('characters:', cnum)

    # ---- 5. 舞台: data/stages/cargo.json + cargo.hx (平铺) ----
    # 用遗产版自带 cargo 结构基底 + 源 cargo 的位置数据, 关键是不能丢 stage 脚本里的
    # opponentNoteHitPre(noteType -> gf/dad) 与 onEvent(Opponent Two/Both Opponents)。
    game_cargo = os.path.join(GAME, 'assets', 'data', 'stages', 'cargo.json')
    src_cargo = os.path.join(SRC, 'stages', 'cargo.json')
    stdir = os.path.join(DEST, 'data', 'stages')
    os.makedirs(stdir, exist_ok=True)
    # 舞台 json 用遗产版基底 (位置/flags 是遗产版引擎认的字段)
    if os.path.isfile(game_cargo):
        shutil.copy2(game_cargo, os.path.join(stdir, 'cargo.json'))
    elif os.path.isfile(src_cargo):
        shutil.copy2(src_cargo, os.path.join(stdir, 'cargo.json'))
    # stage 脚本: 遗产版内建 cargo.hx 已实现双对手 noteType 分流, 直接镜像一份到 mod
    # (不镜像会 fallback 到 assets 原版 cargo.hx, 效果相同; 镜像只为自包含)
    game_cargo_hx = os.path.join(GAME, 'assets', 'data', 'stages', 'cargo.hx')
    if os.path.isfile(game_cargo_hx):
        shutil.copy2(game_cargo_hx, os.path.join(stdir, 'cargo.hx'))
    print('stage: cargo.json + cargo.hx')

    # ---- 6. notetypes 空占位 (.txt, 遗产版读它做注册) ----
    ntdir = os.path.join(DEST, 'data', 'notetypes')
    os.makedirs(ntdir, exist_ok=True)
    for nt in ['Opponent 2 Sing', 'Both Opponents Sing', 'No Animation',
               'DK Trap', 'DK Warn', 'Alt Animation']:
        with open(os.path.join(ntdir, nt + '.txt'), 'w', encoding='utf-8') as f:
            f.write('Functionality: legacy noteType placeholder')

    # ---- 7. images 镜像(角色立绘/图标/menu) ----
    img_src = os.path.join(SRC, 'images')
    img_num = 0
    if os.path.isdir(img_src):
        for root, dirs, files in os.walk(img_src):
            rel = os.path.relpath(root, img_src)
            out = os.path.join(DEST, 'images', rel) if rel != '.' else os.path.join(DEST, 'images')
            os.makedirs(out, exist_ok=True)
            for f in files:
                if '.bak' in f or f.endswith(('.ogg1', '.ogg3')) or '原版' in f:
                    continue
                shutil.copy2(os.path.join(root, f), os.path.join(out, f))
                img_num += 1
    print('images:', img_num)

    # ---- 8. sounds/fonts 镜像 ----
    for d in ['sounds', 'fonts', 'music']:
        sd = os.path.join(SRC, d)
        if os.path.isdir(sd):
            for root, dirs, files in os.walk(sd):
                rel = os.path.relpath(root, sd)
                out = os.path.join(DEST, d, rel) if rel != '.' else os.path.join(DEST, d)
                os.makedirs(out, exist_ok=True)
                for f in files:
                    if '.bak' in f:
                        continue
                    shutil.copy2(os.path.join(root, f), os.path.join(out, f))

    # ---- 9. modsList.txt: 确保启用且置顶 ----
    ml = os.path.join(GAME, 'modsList.txt')
    lines = []
    if os.path.isfile(ml):
        with open(ml, encoding='utf-8-sig') as f:
            lines = [l.strip() for l in f if l.strip()]
    lines = [l for l in lines if not l.startswith('DK_Duet|')]
    lines.insert(0, 'DK_Duet|1')
    with open(ml, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('modsList:', lines)

    # ---- 10. 安装说明 ----
    with open(os.path.join(DEST, '安装说明.txt'), 'w', encoding='utf-8') as f:
        f.write(
            'DK Duet - VS Impostor Legacy 1.1.2 (老 PE 结构)\n'
            '================================================\n'
            '安装位置: content/DK_Duet/  (modsList.txt 已启用 DK_Duet|1)\n\n'
            '改了什么:\n'
            '  - 谱面放 songs/<song>/data/normal.json (老 PE 默认难度=旧版 old)\n'
            '  - 音乐放 songs/<song>/ 根目录 (Inst.ogg / Voices.ogg)\n'
            '  - 歌名改名: double-kill -> double-kill-duo-momo / double-kill-duo-miku\n'
            '    (不顶掉原版 Double Kill, 两首都可选)\n'
            '  - week 用老 PE 5 元素格式, section=story\n\n'
            '唱者: noteType 决定 (Opponent 2 Sing = Teto 独唱, Both Opponents Sing = 合唱),\n'
            '      遗产版内建 cargo.hx 的 opponentNoteHitPre 已实现。\n'
        )

    print('DONE %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    build()
