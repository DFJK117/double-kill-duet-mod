# -*- coding: utf-8 -*-
"""
把 NF 的 DK_Duet mod 正确移植到 VS Impostor Legacy 1.1.2 (Nightmare Vision Engine)。

依据 NVE 官方源码 (NMVTeam/NightmareVision) + 官方 NMV-Base-Game 样例:
  - MODS_DIRECTORY = 'content'  -> mod 必须放 content/<name>/
  - Paths.mods(key) = 'content/' + key
  - chart:  Paths.json('$song/charts/${difficulty}') = songs/<song>/charts/<diff>.json
            且要求 {"song":{...}} 外壳, format 必须是 nmv2 (psych_v1 会被判不兼容抛错)
  - audio:  有 songs/<song>/audio/ 目录 -> audio/Inst.ogg + audio/Voices.ogg
  - week:   data/weeks/*.json 自动扫描(无需 weekList), 目录用 data/weeks/
  - 角色:   data/characters/*.json
  - stage:  data/stages/<name>/{data.json,script.hx}
  - noteType 脚本: data/notetypes/<type>.hx (只认 hx/hxs/hscript, 不认 lua)
            唱歌类 noteType (Opponent 2 Sing / Both Opponents Sing) 引擎原生, 无需脚本
  - modsList.txt: <name>|1 启用, 位于游戏根目录

幂等: 每次从 SOURCE 重建 DEST。
"""
import os, json, shutil, sys, time

SRC = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\windows\mods\DK_Duet'
GAME = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
DEST = os.path.join(GAME, 'content', 'DK_Duet')
WRONG = os.path.join(GAME, 'mods', 'DK_Duet')

DIFF_ORDER = ['easy', 'normal', 'hard', 'old', 'infant', 'god', 'god+']
SONGS = ['double-kill', 'double-kill-miku']


def jload(p):
    with open(p, encoding='utf-8-sig') as f:
        return json.load(f)


def jdump(obj, p):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def chart_to_nve(src_json, diff_key):
    """源谱(扁平) -> NVE chart({"song":..., format=nmv2})"""
    j = jload(src_json)
    s = j['song'] if isinstance(j.get('song'), dict) else j
    s = dict(s)  # copy
    # 关键: psych_v1_convert 会被 NVE Chart.checkFormat 判为 PSYCH 而拒绝
    s['format'] = 'nmv2'
    # 统一 section 字段: sectionBeats 已有, 去掉 lengthInSteps 由引擎补
    for sec in s.get('notes', []):
        if 'sectionBeats' not in sec and 'lengthInSteps' in sec:
            sec['sectionBeats'] = sec['lengthInSteps'] / 4.0
    return {'song': s}


def build():
    t0 = time.time()
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
        print('清空旧 DEST')
    os.makedirs(DEST, exist_ok=True)

    # ---- 1. meta.json ----
    meta = {
        'name': 'DFJK117 - Double Kill Duet (Momo/Miku & Teto)',
        'description': 'BF vs Momo/Miku + Teto 双人对唱谱。难度: old / Infant / GOD / GOD+。唱者由 noteType 决定(引擎原生)。',
        'global': False,
        'windowTitle': 'VS Impostor Legacy - Double Kill Duet',
    }
    jdump(meta, os.path.join(DEST, 'meta.json'))

    # ---- 2. weeks: data/weeks/*.json (NVE 3元素 song 格式) ----
    count_week = 0
    for wf in ['dk-momo.json', 'dk-miku.json']:
        sp = os.path.join(SRC, 'weeks', wf)
        if not os.path.isfile(sp):
            continue
        w = jload(sp)
        songs = []
        for entry in w.get('songs', []):
            disp, sid = entry[0], entry[1]
            color = entry[2] if len(entry) > 2 and isinstance(entry[2], list) else [200, 180, 220]
            songs.append([disp, sid, color])  # NVE: [显示名, id, color]
        nw = {
            'songs': songs,
            'weekCharacters': w.get('weekCharacters', ['momo', 'teto', '']),
            'weekBackground': w.get('weekBackground', 'yellow'),
            'storyName': w.get('storyName', 'DFJK117'),
            'weekName': w.get('weekName', wf),
            'weekBefore': w.get('weekBefore', 'tutorial'),
            'freeplayColor': w.get('freeplayColor', [200, 180, 220]),
            'startUnlocked': w.get('startUnlocked', True),
            'hiddenUntilUnlocked': w.get('hiddenUntilUnlocked', False),
            'hideStoryMode': w.get('hideStoryMode', False),
            'hideFreeplay': w.get('hideFreeplay', False),
            'difficulties': [d.strip() for d in w.get('difficulties', 'old,Infant,GOD,GOD+').split(',') if d.strip()],
        }
        jdump(nw, os.path.join(DEST, 'data', 'weeks', wf))
        count_week += 1
    print('weeks:', count_week)

    # ---- 3. 角色: data/characters/*.json ----
    cdir = os.path.join(SRC, 'characters')
    cnum = 0
    os.makedirs(os.path.join(DEST, 'data', 'characters'), exist_ok=True)
    if os.path.isdir(cdir):
        for f in os.listdir(cdir):
            if f.endswith('.json'):
                shutil.copy2(os.path.join(cdir, f), os.path.join(DEST, 'data', 'characters', f))
                cnum += 1
    print('characters:', cnum)

    # ---- 4. stage: data/stages/cargo/{data.json,script.hx} ----
    st_src = os.path.join(SRC, 'stages', 'cargo.json')
    if os.path.isfile(st_src):
        stdir = os.path.join(DEST, 'data', 'stages', 'cargo')
        os.makedirs(stdir, exist_ok=True)
        shutil.copy2(st_src, os.path.join(stdir, 'data.json'))
        lua = os.path.join(SRC, 'stages', 'cargo.lua')
        if os.path.isfile(lua):
            # NVE 不认 lua -> 不复制(舞台脚本失效但静态舞台可用)
            pass
    print('stage: cargo')

    # ---- 5. songs/<song>/{charts,audio,meta.json} ----
    total_charts = 0
    total_notes = 0
    for song in SONGS:
        sdir = os.path.join(DEST, 'songs', song)
        charts_dir = os.path.join(sdir, 'charts')
        audio_dir = os.path.join(sdir, 'audio')
        os.makedirs(charts_dir, exist_ok=True)
        os.makedirs(audio_dir, exist_ok=True)

        # charts: 源 data/<song>/<song>[-<diff>].json
        for diff in DIFF_ORDER:
            if diff == 'normal':
                fn = song + '.json'          # 无后缀 = Normal(默认)
            else:
                fn = song + '-' + diff + '.json'
            sp = os.path.join(SRC, 'data', song, fn)
            if not os.path.isfile(sp):
                print('  MISS chart', fn)
                continue
            obj = chart_to_nve(sp, diff)
            out_name = diff.lower() + '.json'
            jdump(obj, os.path.join(charts_dir, out_name))
            total_charts += 1
            total_notes += len(obj['song'].get('notes', [])) and sum(
                len(sec.get('sectionNotes', [])) for sec in obj['song']['notes'])

        # audio: Inst.ogg + Voices.ogg
        saudio = os.path.join(SRC, 'songs', song)
        for af in ['Inst.ogg', 'Voices.ogg']:
            sp = os.path.join(saudio, af)
            if os.path.isfile(sp):
                shutil.copy2(sp, os.path.join(audio_dir, af))
            else:
                print('  MISS audio', song, af)

        # song meta.json
        smeta = {
            'songName': song,
            'displayName': 'Double Kill' + (' (Miku & Teto)' if 'miku' in song else ' (Momo & Teto)'),
            'composers': ['DFJK117'],
            'charters': ['DFJK117'],
            'freeplayColor': '#C8B4DC',
            'difficulties': [d.capitalize() if d not in ('god+',) else 'GOD+' for d in DIFF_ORDER],
        }
        jdump(smeta, os.path.join(sdir, 'meta.json'))
        print('song', song, 'done')
    print('charts:', total_charts, 'notes:', total_notes)

    # ---- 6. images: 直接镜像(角色立绘/图标/stage 背景) ----
    img_src = os.path.join(SRC, 'images')
    img_num = 0
    if os.path.isdir(img_src):
        for root, dirs, files in os.walk(img_src):
            rel = os.path.relpath(root, img_src)
            out = os.path.join(DEST, 'images', rel) if rel != '.' else os.path.join(DEST, 'images')
            os.makedirs(out, exist_ok=True)
            for f in files:
                # 排除备份垃圾
                if '.bak' in f or f.endswith(('.ogg1', '.ogg3')) or '原版' in f:
                    continue
                shutil.copy2(os.path.join(root, f), os.path.join(out, f))
                img_num += 1
    print('images:', img_num)

    # ---- 7. sounds/music (若有) ----
    for d in ['sounds', 'music', 'fonts', 'shaders']:
        sd = os.path.join(SRC, d)
        if os.path.isdir(sd):
            dd = os.path.join(DEST, d)
            for root, dirs, files in os.walk(sd):
                rel = os.path.relpath(root, sd)
                out = os.path.join(dd, rel) if rel != '.' else dd
                os.makedirs(out, exist_ok=True)
                for f in files:
                    shutil.copy2(os.path.join(root, f), os.path.join(out, f))

    # ---- 8. modsList.txt ----
    ml = os.path.join(GAME, 'modsList.txt')
    lines = []
    if os.path.isfile(ml):
        with open(ml, encoding='utf-8-sig') as f:
            lines = [l.strip() for l in f if l.strip()]
    # 保留其它 mod, 确保 DK_Duet 启用且在最前(优先级)
    lines = [l for l in lines if not l.startswith('DK_Duet|')]
    lines.insert(0, 'DK_Duet|1')
    with open(ml, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    print('modsList:', lines)

    # ---- 9. 删除放错位置的 mods/DK_Duet ----
    if os.path.isdir(WRONG):
        bk = r'I:\_trash_ust_work\dk_wrong_mods_dir_20261121'
        os.makedirs(bk, exist_ok=True)
        dst_bk = os.path.join(bk, 'DK_Duet')
        if os.path.isdir(dst_bk):
            shutil.rmtree(dst_bk)
        shutil.move(WRONG, dst_bk)
        print('已移走错误目录 mods/DK_Duet ->', dst_bk)

    print('DONE %.1fs' % (time.time() - t0))


if __name__ == '__main__':
    build()
