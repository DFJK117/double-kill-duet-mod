# -*- coding: utf-8 -*-
"""在两首 God 谱面撒入 DK Saw 事件（GOD+ 锯子）。hard 谱面不动。

事件格式：[strumTime(ms), [['DK Saw', value1, value2]]]
  value1 = 方向：left（右->左，默认）/ right / both
  value2 = 数量：1/2/3/4

节奏设计（BPM 200，一的拍=300ms，一小节=1.2s）：
  30s~90s  每 8 秒一条，单锯，方向交替
  90s~180s 每 6 秒一条，单/双锯
  180s~270s 每 4.5 秒一条，双/三锯，偶有四锯
  270s~尾  每 5 秒一条，双锯收尾
避开已有事件时刻 ±200ms；两首曲用相同节奏（谱面结构一致）。
"""
import os, json

G = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
ROOTS = [G, r'E:/UST_work/dk_miku/DK_Dual', r'E:/UST_work/dk_miku/DK_Miku']
SONGS = ['double-kill', 'double-kill-miku']


def gen_times():
    out = []
    t = 30000.0
    while t < 282000:
        if t < 90000:
            step, maxn = 8000, 1
        elif t < 180000:
            step, maxn = 6000, 2
        elif t < 270000:
            step, maxn = 4500, 3
        else:
            step, maxn = 5000, 2
        idx = len(out)
        # 数量分布：前期单锯；中期单/双；后期双/三，每 7 条来一次四锯
        if maxn == 1:
            n = 1
        elif maxn == 2:
            n = 1 if idx % 3 == 0 else 2
        else:
            if idx % 7 == 6:
                n = 4
            elif idx % 2 == 0:
                n = 2
            else:
                n = 3
        # 方向：交替 left/right，每 5 条来一次 both
        if idx % 5 == 4:
            d = 'both'
        elif idx % 2 == 0:
            d = 'left'
        else:
            d = 'right'
        out.append((t, d, n))
        t += step
    return out


def patch(path):
    raw = open(path, 'rb').read()
    d = json.loads(raw.decode('utf-8-sig'))
    evs = d['events']
    # 已有事件时刻（避开 ±200ms）
    used = [e[0] for e in evs]
    plan = gen_times()
    added = []
    for (t, dr, n) in plan:
        if any(abs(t - u) < 200 for u in used):
            continue
        evs.append([t, [['DK Saw', dr, str(n)]]])
        used.append(t)
        added.append((t, dr, n))
    evs.sort(key=lambda e: e[0])
    d['events'] = evs
    # 保持原 BOM/缩进风格：用 utf-8-sig + indent=1（Psych 常见），但为最小改动用紧凑
    out = json.dumps(d, ensure_ascii=False, indent=1)
    open(path, 'w', encoding='utf-8-sig', newline='').write(out)
    return added


def main():
    for root in ROOTS:
        for s in SONGS:
            p = os.path.join(root, 'data', s, s + '-god.json')
            if not os.path.exists(p):
                print('MISS', p)
                continue
            added = patch(p)
            print('%s  +%d saws  %s' % (p, len(added), os.path.getsize(p)))
            if root == ROOTS[0]:
                print('  first:', added[:3], 'last:', added[-2:])


if __name__ == '__main__':
    main()
