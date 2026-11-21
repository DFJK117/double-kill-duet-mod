# -*- coding: utf-8 -*-
"""DK_Duet 谱面改造：加两种自定义 type 按键。

玩家侧（轨道 0-3，Pe-1.0.4 规则）的音符：
  ① 'DK Trap' 陷阱键 —— 在和弦时刻**新增**少量，按到即死
  ② 'DK Warn' 警告牌 —— 把少量**正常键原地替换**，漏按即死

改的是 noteType（第 4 列），不改动段级 mustHitSection（会影响镜头），
也不动对手侧（轨道 4-7）。
"""
import json, os, random, sys, shutil

GAME = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
OUT = r'E:/UST_work/dk_miku/_godmode'

TRAP = 'DK Trap'
WARN = 'DK Warn'

N_TRAP = 12          # 新增陷阱键数量
TRAP_GAP = 6000      # 两个陷阱键最小间隔(ms)
N_WARN = 20          # 替换成警告牌的数量
WARN_GAP = 4000      # 两个警告牌最小间隔(ms)
START_MS = 15000     # 前 15 秒不改动（让玩家先熟悉）
END_MS = 270000      # 结尾 10 秒不改动

SEED = 20261115


def analyze(chart):
    """返回 (和弦候选, 普通玩家音符候选)
       和弦候选里的 free 轨道按**全谱**同一时刻占用情况算，避免同轨同刻重复。"""
    chords = []
    plain = []
    global_used = {}
    for sec in chart['notes']:
        for n in sec['sectionNotes']:
            global_used.setdefault(n[0], set()).add(n[1])
    for si, sec in enumerate(chart['notes']):
        bytime = {}
        for n in sec['sectionNotes']:
            if n[1] < 4:                      # 玩家侧
                bytime.setdefault(n[0], []).append(n)
        for t, ns in bytime.items():
            if len(ns) >= 2:                  # 和弦
                used = global_used.get(t, set())
                free = [l for l in range(4) if l not in used]
                if free:
                    chords.append((t, si, free))
            for n in ns:
                if len(n) < 4:                # 没有 noteType 的普通键
                    plain.append((t, si, n))
    chords.sort()
    plain.sort()
    return chords, plain


def bucket_pick(cands, n, rng):
    """把可用时间轴切成 n 段，每段随机取一个候选 -> 全曲均匀分布"""
    cands = [c for c in cands if START_MS <= c[0] <= END_MS]
    if not cands or n <= 0:
        return []
    t0, t1 = cands[0][0], cands[-1][0]
    span = max(1.0, (t1 - t0) / float(n))
    out = []
    for i in range(n):
        lo = t0 + i * span
        hi = t0 + (i + 1) * span
        bucket = [c for c in cands if lo <= c[0] < hi] if i < n - 1 else \
                 [c for c in cands if lo <= c[0] <= hi]
        if not bucket:
            continue
        out.append(bucket[rng.randrange(len(bucket))])
    return out


def pick_chords(chords, n, gap, rnd):
    out = []
    last = -10 ** 9
    for c in bucket_pick(chords, n * 2, rnd):
        if c[0] - last >= gap and all(abs(c[0] - o[0]) >= gap for o in out):
            out.append(c)
            last = c[0]
            if len(out) >= n:
                break
    return out


def pick_plain(plain, n, gap, avoid, rnd):
    avoid_set = set(avoid)
    cands = [p for p in plain if p[0] not in avoid_set]
    out = []
    for p in bucket_pick(cands, n * 2, rnd):
        if all(abs(p[0] - o[0]) >= gap for o in out):
            out.append(p)
            if len(out) >= n:
                break
    return out


def patch(path, label):
    with open(path, encoding='utf-8-sig') as f:
        chart = json.load(f)
    rnd = random.Random(SEED)
    chords, plain = analyze(chart)

    cs = pick_chords(chords, N_TRAP, TRAP_GAP, rnd)
    ws = pick_plain(plain, N_WARN, WARN_GAP, [c[0] for c in cs], rnd)

    # ① 新增陷阱键
    trap_added = []
    for t, si, free in cs:
        lane = free[rnd.randrange(len(free))]
        chart['notes'][si]['sectionNotes'].append([t, lane, 0, TRAP])
        trap_added.append((t, si, lane))

    # ② 普通键替换成警告牌
    warn_set = set()
    for t, si, n in ws:
        # 该音符所在行的位置
        for row in chart['notes'][si]['sectionNotes']:
            if row is n:
                row.append(WARN)
                warn_set.add((t, n[1]))
                break

    # 段级 mustHitSection 不动；统计
    pc = sum(1 for s in chart['notes'] for n in s['sectionNotes'] if n[1] < 4)
    print('=== %s (%s)' % (label, os.path.basename(path)))
    print('   玩家音符 %d -> %d；陷阱键 %d；警告牌 %d'
          % (pc - len(trap_added), pc, len(trap_added), len(warn_set)))
    print('   陷阱键时刻: %s' % ', '.join('%d(l%d)' % (t, l) for t, _, l in sorted(trap_added)))
    print('   警告牌时刻: %s' % ', '.join('%d(l%d)' % (t, l) for t, l in sorted(warn_set)))
    return chart


def dump(chart, path):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(chart, f, ensure_ascii=False, indent=1)
    shutil.move(tmp, path)


if __name__ == '__main__':
    targets = [
        (os.path.join(GAME, 'data/double-kill/double-kill-hard.json'), '桃音+Teto 版'),
        (os.path.join(GAME, 'data/double-kill-miku/double-kill-miku-hard.json'), '初音+Teto 版'),
    ]
    for path, label in targets:
        if not os.path.exists(path):
            print('跳过（不存在）', path)
            continue
        c = patch(path, label)
        dump(c, path)
        print('   已写入', path)
