# -*- coding: utf-8 -*-
"""Double Kill USTX：严格按原 MIDI 重建 White / Black 两轨音符。

- 音符 position / duration / tone 一律取自原 MIDI（division 96 -> USTX 480，x5）
- 不做 legato、不合并长音、不产生超长音符
- 歌词按同源假名工程 1:1 映射；'-' 及库里没有的别名改成「前一个有效音节」重复，
  保证每个音符都有采样（这才是固定位置静音的真因）
- MIDI 里的和弦重叠音分离到独立新轨（BF 唱 a），单轨内绝不重叠
- BF 原轨逐行不动
- 主文件与 -autosave 同步重建
"""
import os, re, json, glob, shutil, struct, collections, datetime
import yaml

MIDI = r'C:/Users/Administrator/Desktop/ustx/FNF/Double Kill Vocals (White-Black-Boyfriend).mid'
KANA = r'E:/UST_work/doublekill/Double Kill (Rareblin) - 3tracks - kana.ustx'
SINGERS = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/OpenUtau-win-x64/Singers'
TARGETS = [
    r'C:/Users/Administrator/Desktop/Double Kill (Rareblin) - 3tracks.ustx',
    r'C:/Users/Administrator/Desktop/Double Kill (Rareblin) - 3tracks-autosave.ustx',
]
BACKUP = r'E:/UST_work/doublekill/_backup_2026-11-08'
# 两份工程统一成这套（都是単独音/短先行発声，Default 音素器下裸假名 0 未命中）
UNIFORM = ['重音テト音声ライブラリー', '呗音ウタ_Defoko', 'BF']

# ---------- MIDI ----------

def vlq(d, i):
    v = 0
    while True:
        b = d[i]; i += 1; v = (v << 7) | (b & 0x7f)
        if not b & 0x80:
            return v, i


def read_midi(path):
    d = open(path, 'rb').read()
    hs = struct.unpack_from('>I', d, 4)[0]
    fmt, ntrk, div = struct.unpack_from('>HHH', d, 8)
    assert div == 96, div
    i = 8 + hs
    tracks = {}
    for t in range(ntrk):
        sz = struct.unpack_from('>I', d, i + 4)[0]
        j = i + 8; end = min(j + sz, len(d)); i = j + sz
        tick = 0; name = None; notes = []; on = {}; st = None
        while j < end:
            dt, j = vlq(d, j); tick += dt
            if j >= end: break
            b = d[j]
            if b == 0xff:
                j += 1; typ = d[j]; j += 1; ln, j = vlq(d, j); data = d[j:j+ln]; j += ln
                if typ == 0x03: name = data.decode('latin1', 'replace')
                continue
            if b in (0xf0, 0xf7):
                j += 1; ln, j = vlq(d, j); j += ln; continue
            if b & 0x80: st = b; j += 1
            if st is None: break
            hi = st & 0xf0
            if hi in (0x90, 0x80, 0xa0, 0xb0, 0xe0):
                if j + 1 >= end: break
                a, c = d[j], d[j+1]; j += 2
                if hi == 0x90 and c > 0: on.setdefault(a, []).append((tick, c))
                elif hi == 0x80 or (hi == 0x90 and c == 0):
                    if on.get(a): s = on[a].pop(0)[0]; notes.append((s, tick - s, a))
            elif hi in (0xc0, 0xd0): j += 1
            else: break
        tracks[name or str(t)] = sorted(notes)
    return tracks


# ---------- 声库别名 ----------

def aliases_of(singer):
    root = os.path.join(SINGERS, singer or '')
    al = set()
    if not os.path.isdir(root):
        return al
    for op in glob.glob(root + '/**/oto.ini', recursive=True):
        b = open(op, 'rb').read()
        txt = ''
        for enc in ('utf-8', 'shift_jis', 'cp932'):
            try:
                txt = b.decode(enc); break
            except Exception:
                pass
        for l in txt.splitlines():
            if '=' in l and ',' in l:
                al.add(l.split('=', 1)[1].split(',', 1)[0])
    return al


# ---------- 生成 note 文本块 ----------

def note_block(pos, dur, tone, lyric):
    q = json.dumps(lyric, ensure_ascii=False)
    return [
        '  - position: %d' % pos,
        '    duration: %d' % dur,
        '    tone: %d' % tone,
        '    lyric: %s' % q,
        '    pitch:',
        '      data:',
        '      - {x: 0, y: 0, shape: io}',
        '      - {x: %d, y: 0, shape: io}' % dur,
        '      snap_first: true',
        '    vibrato: {length: 0, period: 175, depth: 25, in: 10, out: 10, shift: 0, drift: 0, vol_link: 0}',
        '    tuning: 0',
        '    phoneme_expressions: []',
        '    phoneme_overrides: []',
    ]


def split_chords(notes):
    """主轨保留不重叠的音；和弦重叠音分离到另一轨。严格按时间顺序。"""
    main, chord = [], []
    last_end = -1
    for s, du, p in notes:
        if s < last_end:
            chord.append((s, du, p))
        else:
            main.append((s, du, p)); last_end = s + du
    return main, chord


# ---------- 主流程 ----------

def rebuild(path, midi, kana_map):
    raw = open(path, 'rb').read()
    bom = raw[:3] == b'\xef\xbb\xbf'
    txt = raw.decode('utf-8-sig')
    L = txt.replace('\r\n', '\n').split('\n')
    doc = yaml.safe_load(txt)

    singers = UNIFORM
    alias = [aliases_of(s) for s in singers[:2]]
    print('  统一 singers', singers, 'aliases', [len(a) for a in alias])

    # kana 歌词按 position 索引
    kparts = {vp['track_no']: {n['position']: n.get('lyric', '') for n in vp['notes']}
              for vp in kana_map['voice_parts']}

    # 生成两轨主音 + 和弦音
    plan = {}
    for ti, label in ((2, 'White'), (3, 'Black')):
        main, chord = split_chords(midi[label])
        km = kparts[ti - 2]
        al = alias[ti - 2]
        fallback = next((x for x in ('あ', 'a', 'よ', 'り') if x in al), 'あ')
        last_valid = fallback
        fixed = []
        for s, du, p in main:
            pos = s * 5
            ly = km.get(pos, '')
            if not ly or ly == '-' or ly not in al:
                ly = last_valid
            else:
                last_valid = ly
            fixed.append((pos, du * 5, p, ly))
        miss = sum(1 for _, _, _, ly in fixed if ly not in al)
        plan[ti - 2] = dict(main=fixed, chord=[(s * 5, du * 5, p) for s, du, p in chord])
        print('  %s: main %d (原 MIDI %d, 和弦分离 %d), 未命中 %d, maxdur %d'
              % (label, len(fixed), len(midi[label]), len(chord), miss,
                 max(x[1] for x in fixed)))

    chord_notes = sorted(plan[0]['chord'] + plan[1]['chord'])

    # ---- 定位 voice_parts / tracks ----
    vi = next(k for k, l in enumerate(L) if l.startswith('voice_parts:'))
    ti0 = next(k for k, l in enumerate(L) if l.startswith('tracks:'))
    vend = next((k for k in range(vi + 1, len(L))
                 if L[k] and not L[k].startswith(' ') and not L[k].startswith('-')), len(L))
    tend = vi

    part_starts = [k for k in range(vi + 1, vend) if L[k].startswith('- duration: ')]
    print('  parts at', part_starts[:5], 'voice_parts end', vend)
    assert len(part_starts) == 3, part_starts

    # 从后往前替换，避免行号漂移
    for idx in (1, 0):
        st = part_starts[idx]
        en = part_starts[idx + 1] if idx + 1 < len(part_starts) else vend
        ni = next(k for k in range(st, en) if L[k] == '  notes:')
        blocks = []
        for pos, dur, tone, ly in plan[idx]['main']:
            blocks.extend(note_block(pos, dur, tone, ly))
        L[ni + 1:en] = blocks
        print('  part%d 替换 %d 行 -> %d 行' % (idx, en - ni - 1, len(blocks)))

    # 重新定位（前两处改过行数）
    vi = next(k for k, l in enumerate(L) if l.startswith('voice_parts:'))
    tend = vi
    vend = next((k for k in range(vi + 1, len(L))
                 if L[k] and not L[k].startswith(' ') and not L[k].startswith('-')), len(L))
    part_starts = [k for k in range(vi + 1, vend) if L[k].startswith('- duration: ')]

    # BF 原轨文本（用于断言）
    bf_st = part_starts[2]
    bf_orig = L[bf_st:vend]

    # 追加第 4 个 voice part（和弦轨，BF 唱 a）
    dur_last = max(p + d for p, d, _ in chord_notes) if chord_notes else 0
    newpart = [
        '- duration: %d' % (dur_last + 480),
        '  name: Chord (BF)',
        '  comment: ""',
        '  track_no: 3',
        '  position: 0',
        '  notes:',
    ]
    for pos, dur, tone in chord_notes:
        newpart.extend(note_block(pos, dur, tone, 'a'))

    # 追加第 4 个 track（复制 BF track 结构）
    bf_track_st = next(k for k in range(ti0, tend)
                       if L[k].startswith('- singer:') and k > ti0 and
                       sum(1 for q in range(ti0, k) if L[q].startswith('- singer:')) == 2)
    bf_track_en = next((k for k in range(bf_track_st + 1, tend)
                        if L[k].startswith('- singer:')), tend)
    newtrack = []
    for l in L[bf_track_st:bf_track_en]:
        if l.startswith('  track_name:'):
            l = '  track_name: Chord (BF)'
        newtrack.append(l)

    # 歌手/音素器统一：两个工程完全一致，避免打开 autosave 又是另一套
    singer_i = 0
    for k in range(ti0, tend):
        if L[k].startswith('- singer:') and singer_i < 2:
            L[k] = '- singer: %s' % UNIFORM[singer_i]
            singer_i += 1
        if L[k].startswith('  phonemizer:') and k < bf_track_st:
            L[k] = '  phonemizer: OpenUtau.Core.DefaultPhonemizer'
    assert singer_i == 2, singer_i

    L[bf_track_en:bf_track_en] = newtrack
    # 插入位置因上面插行而偏移
    shift = len(newtrack)
    vend += shift
    vi = next(k for k, l in enumerate(L) if l.startswith('voice_parts:'))
    vend = next((k for k in range(vi + 1, len(L))
                 if L[k] and not L[k].startswith(' ') and not L[k].startswith('-')), len(L))
    L[vend:vend] = newpart

    # BF 原轨逐行断言
    vi2 = next(k for k, l in enumerate(L) if l.startswith('voice_parts:'))
    ps = [k for k in range(vi2 + 1, len(L)) if L[k].startswith('- duration: ')]
    assert len(ps) >= 4, ps
    bf_now = L[ps[2]:ps[3]]
    assert bf_now == bf_orig, 'BF 轨被改动！'
    print('  BF 轨逐行一致 OK, %d 行' % len(bf_orig))

    out = ('\r\n'.join(L))
    data = (b'\xef\xbb\xbf' if bom else b'') + out.encode('utf-8')
    open(path, 'wb').write(data)
    print('  写出', len(data), 'bytes')


def main():
    os.makedirs(BACKUP, exist_ok=True)
    midi = read_midi(MIDI)
    print('MIDI tracks', {k: len(v) for k, v in midi.items()})
    kana = yaml.safe_load(open(KANA, 'rb').read().decode('utf-8-sig'))
    stamp = datetime.datetime.now().strftime('%H%M%S')
    for p in TARGETS:
        print('===', os.path.basename(p))
        shutil.copy2(p, os.path.join(BACKUP, os.path.basename(p).replace('.ustx', '_before_midi_%s.ustx' % stamp)))
        rebuild(p, midi, kana)
    print('done')


if __name__ == '__main__':
    main()
