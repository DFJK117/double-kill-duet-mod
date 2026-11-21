# -*- coding: utf-8 -*-
"""DK_Duet 谱面改造 v9：双方侧特殊键 + God 难度。

设计要点（全部对照引擎源码确认）：
  * Pe-1.0.4 规则：轨道 0-3 = 玩家侧(mustPress=true)，轨道 4-7 = 对手侧(mustPress=false)
  * 玩家侧音符漏按 -> 引擎调 Lua `noteMiss`          -> DK Warn 可用
  * 玩家侧音符命中 -> 引擎调 Lua `goodNoteHit`        -> DK Trap 可用
  * 对手侧音符命中 -> 引擎调 Lua `goodNoteHit`（opponentNoteHit 里 functionReturn='goodNoteHit'）
                                                          -> 对手侧 DK Trap 可用
  * 对手侧音符漏按 -> 引擎**不调** noteMiss（只对 mustPress 音符调）
                                                          -> 对手侧 DK Warn 需要 Lua 轮询自己判定

因此：
  * 玩家侧：Trap（新增）+ Warn（替换普通键）—— 双方都由引擎原生回调驱动
  * 对手侧：Trap（替换对手普通键）由 goodNoteHit 驱动
  * 对手侧：Warn 额外做一套「DK_God.lua 轮询判定」—— 音符过了判定线且没被打中即秒杀
"""
import json, os, random, shutil

TRAP = 'DK Trap'
WARN = 'DK Warn'

# ---- 数量配置 -----------------------------------------------------------
# hard 难度：适度（用户嫌少 -> 明显加量）
HARD_TRAP_PLAYER = 26     # 玩家侧陷阱键
HARD_WARN_PLAYER = 40     # 玩家侧警告牌
HARD_TRAP_OPP = 22        # 对手侧陷阱键

# god 难度：狂量
GOD_TRAP_PLAYER = 40
GOD_WARN_PLAYER = 60
GOD_TRAP_OPP = 34
GOD_WARN_OPP = 26         # 对手侧警告牌（靠 Lua 轮询判定）

TRAP_GAP = 4200           # 同类陷阱键最小间隔(ms)
WARN_GAP = 2600           # 同类警告牌最小间隔(ms)
START_MS = 12000          # 开场 12 秒不动
END_MS = 276000           # 结尾 4 秒不动

SEED = 20261116


# ---- 工具 ----------------------------------------------------------------
def _all_rows(chart):
    return [(n[0], n[1]) for sec in chart['notes'] for n in sec['sectionNotes']]


def _occupied(chart):
    """时刻 -> 已占用轨道集合（全谱）"""
    occ = {}
    for sec in chart['notes']:
        for n in sec['sectionNotes']:
            occ.setdefault(n[0], set()).add(n[1])
    return occ


def bucket_pick(cands, n, rng):
    """把时间轴切成 n 段，每段随机取一个候选 -> 全曲均匀分布"""
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


def _spread(cands, n, gap, rng, used_times):
    """从候选里挑 n 个：按时间顺序贪心，相邻间隔 >= gap，且不在 used_times 里。

    注意：间隔约束只对**相邻**两个生效（时间轴上真正需要隔开的是相邻两个），
    不能两两互斥 —— 否则均分取点时会因为远处点也冲突而大量落空。
    """
    pool = [c for c in cands if c[0] not in used_times and START_MS <= c[0] <= END_MS]
    if not pool or n <= 0:
        return []
    pool.sort(key=lambda c: c[0])
    # 目标间隔：让 n 个点尽量铺满整个区间
    t0, t1 = pool[0][0], pool[-1][0]
    need = min(gap, max(1.0, (t1 - t0) / float(n)))
    out = []
    last = None
    for c in pool:
        if last is not None and (c[0] - last) < need:
            continue
        out.append(c)
        last = c[0]
        if len(out) >= n:
            break
    # 不够就用随机补齐（放宽间隔到 gap/2）
    if len(out) < n:
        rest = [c for c in pool if c not in out]
        rng.shuffle(rest)
        for c in rest:
            if len(out) >= n:
                break
            if any(abs(c[0] - o[0]) < gap // 2 for o in out):
                continue
            out.append(c)
        out.sort(key=lambda c: c[0])
    return out


def _find_row(chart, si, t, lane):
    """在指定 section 里找到 (t, lane) 那一行"""
    for row in chart['notes'][si]['sectionNotes']:
        if row[0] == t and row[1] == lane:
            return row
    return None


# ---- 候选收集 ------------------------------------------------------------
def collect_candidates(chart):
    """返回 (player_chords, player_plain, opp_plain)

    player_chords: (t, si, free_lanes)  玩家侧和弦时刻及空闲轨道
    player_plain : (t, si, lane, row)   玩家侧无 noteType 的普通键
    opp_plain    : (t, si, lane, row)   对手侧无 noteType 的普通键
    """
    occ = _occupied(chart)
    p_chords, p_plain, o_plain = [], [], []
    for si, sec in enumerate(chart['notes']):
        bytime = {}
        for n in sec['sectionNotes']:
            bytime.setdefault(n[0], []).append(n)
        for t, ns in bytime.items():
            used = occ.get(t, set())
            pns = [n for n in ns if n[1] < 4]
            ons = [n for n in ns if n[1] >= 4]
            if len(pns) >= 2:
                free = [l for l in range(4) if l not in used]
                if free:
                    p_chords.append((t, si, free))
            for n in pns:
                if len(n) < 4:
                    p_plain.append((t, si, n[1], n))
            for n in ons:
                if len(n) < 4:
                    o_plain.append((t, si, n[1], n))
    p_chords.sort()
    p_plain.sort()
    o_plain.sort()
    return p_chords, p_plain, o_plain


# ---- 主改造 --------------------------------------------------------------
def patch_chart(chart, n_trap_p, n_warn_p, n_trap_o, n_warn_o, seed=SEED, label=''):
    """在 chart 上就地加双方侧特殊键。返回统计 dict。"""
    rnd = random.Random(seed)
    p_chords, p_plain, o_plain = collect_candidates(chart)

    used = set()          # 已占用时刻（避免 Trap/Warn 撞同一时刻）
    result = dict(trap_player=0, warn_player=0, trap_opp=0, warn_opp=0)

    # ① 玩家侧 Warn 先选（挑走一部分普通键）
    ws = _spread(p_plain, n_warn_p, WARN_GAP, rnd, used)
    warn_rows = []
    for t, si, lane, row in ws:
        row.append(WARN)
        warn_rows.append((t, si, lane))
        used.add(t)
        result['warn_player'] += 1

    # ② 玩家侧 Trap —— 两种来源：
    #    a) 和弦时刻**新增**到空闲轨道
    #    b) 玩家侧剩余普通键**原地替换**成 Trap（不占新轨道，也不新增音符行）
    #    两者合并才能把数量堆上去（god 难度要求 40 个）。
    cs = _spread(p_chords, min(n_trap_p, len(p_chords)), TRAP_GAP, rnd, used)
    trap_rows = []
    for t, si, free in cs:
        lane = free[rnd.randrange(len(free))]
        chart['notes'][si]['sectionNotes'].append([t, lane, 0, TRAP])
        trap_rows.append((t, si, lane))
        used.add(t)
        result['trap_player'] += 1

    # 剩余缺口用「普通键原地替换」补齐
    if result['trap_player'] < n_trap_p:
        need = n_trap_p - result['trap_player']
        plain_free = [x for x in p_plain if x[0] not in used]
        ts2 = _spread(plain_free, need, TRAP_GAP, rnd, used)
        for t, si, lane, row in ts2:
            row.append(TRAP)
            trap_rows.append((t, si, lane))
            used.add(t)
            result['trap_player'] += 1

    # ③ 对手侧 Trap —— 把对手普通键原地替换（命中即死，引擎会调 goodNoteHit）
    ts = _spread(o_plain, n_trap_o, TRAP_GAP, rnd, used)
    for t, si, lane, row in ts:
        row.append(TRAP)
        used.add(t)
        result['trap_opp'] += 1

    # ④ 对手侧 Warn —— 把对手普通键原地替换（靠 DK_God.lua 轮询判定）
    os_ = _spread(o_plain, n_warn_o, WARN_GAP, rnd, used)
    for t, si, lane, row in os_:
        row.append(WARN)
        used.add(t)
        result['warn_opp'] += 1

    if label:
        print('  %-22s 玩家侧 Trap %-3d Warn %-3d | 对手侧 Trap %-3d Warn %-3d'
              % (label, result['trap_player'], result['warn_player'],
                 result['trap_opp'], result['warn_opp']))
    return result


def dump(chart, path):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        json.dump(chart, f, ensure_ascii=False, indent=1)
    shutil.move(tmp, path)


def load(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def has_special(chart):
    for sec in chart['notes']:
        for n in sec['sectionNotes']:
            if len(n) > 3 and n[3] in (TRAP, WARN):
                return True
    return False


def count_special(chart):
    c = {TRAP: 0, WARN: 0}
    for sec in chart['notes']:
        for n in sec['sectionNotes']:
            if len(n) > 3 and n[3] in c:
                c[n[3]] += 1
    return c


def side_count(chart):
    c = {'p_trap': 0, 'p_warn': 0, 'o_trap': 0, 'o_warn': 0}
    for sec in chart['notes']:
        for n in sec['sectionNotes']:
            t = n[3] if len(n) > 3 else ''
            if n[1] < 4:
                if t == TRAP:
                    c['p_trap'] += 1
                elif t == WARN:
                    c['p_warn'] += 1
            else:
                if t == TRAP:
                    c['o_trap'] += 1
                elif t == WARN:
                    c['o_warn'] += 1
    return c


if __name__ == '__main__':
    import sys
    print('这是模块，由 apply_dk_god_v9.py 调用')
