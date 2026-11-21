# -*- coding: utf-8 -*-
"""DK 唱者对齐 old —— 修正版（v4，2026-11-21 20:48）

关键纠正：本引擎是 4P 轨道布局，**轨道 0-3 = BF（玩家），4-7 = 对手**，
与 mustHitSection 无关（实测 old：mustHit=True 段音符几乎全在 0-3，
mustHit=False 段几乎全在 4-7）。之前用 mustPress 公式判侧是错的。

对齐规则（用户：「照着 old 曲目，哪里是什么就什么」）：
  * 段落一一对应（514=514，mustHitSection/lengthInSteps 全同）
  * old 该段对手音符唱者统一 -> infant 该段对手音符全部改成同一类型
  * old 该段本身混唱（仅 4 段）-> 按该段内最近时间点继承 old 那个音符的唱者
  * old 该段没有对手音符 -> 继承最近有内容的段
  * 轨道 0-3（BF）一个都不碰；'DK Trap' / 'DK Warn' 不动
  * 无 type 的音符写成 3 元素 [time, lane, sus]（与 old 一致）
"""
import json, os, shutil, datetime
from collections import Counter

MODS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
TARGETS = ['-infant']
BACKUP = r'I:/_trash_ust_work/dk_sing_v4_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
KEEP = ('DK Trap', 'DK Warn')
T2S = {'': 'M', 'Opponent 2 Sing': 'T', 'Both Opponents Sing': 'B'}
S2T = {'M': '', 'T': 'Opponent 2 Sing', 'B': 'Both Opponents Sing'}
OPP_MIN_LANE = 4          # 4P 布局：4-7 是对手


def load(p):
    j = json.load(open(p, encoding='utf-8-sig'))
    return j, (j['song'] if isinstance(j.get('song'), dict) else j)


def opp_notes(sec):
    out = []
    for n in sec.get('sectionNotes', []):
        if len(n) < 2:
            continue
        lane = int(n[1])
        if lane < OPP_MIN_LANE:
            continue
        typ = str(n[3]) if len(n) > 3 else ''
        if typ in KEEP:
            continue
        out.append((float(n[0]), lane, typ))
    return out


def old_sections(song):
    """每段：[(t, singer)] 与统一唱者（None=混唱/空）"""
    secs = []
    for sec in song.get('notes', []):
        seq = [(t, lane, T2S.get(typ, 'M')) for t, lane, typ in opp_notes(sec)]
        uniq = {s for _, _, s in seq}
        uniform = seq[0][2] if len(uniq) == 1 else None
        secs.append((seq, uniform))
    # 空段继承
    last = None
    for i, (seq, uni) in enumerate(secs):
        if uni is None and not seq:
            secs[i] = (seq, last)
        else:
            last = uni if uni else last
    nxt = None
    for i in range(len(secs) - 1, -1, -1):
        seq, uni = secs[i]
        if uni is None and not seq:
            secs[i] = (seq, nxt)
        else:
            nxt = uni if uni else nxt
    return secs


def pick_for(sec_ref, t, lane):
    """段落内某时刻该由谁唱：同轨道优先（不同轨 +200ms 罚分），再按时间最近。"""
    seq, uni = sec_ref
    if not seq:
        return uni or 'M'
    if uni:
        return uni
    def cost(x):
        dt = abs(x[0] - t)
        return dt + (0.0 if x[1] == lane else 200.0)
    return min(seq, key=cost)[2]


def retag(path, ref_secs):
    j, song = load(path)
    changed = 0
    for k, sec in enumerate(song.get('notes', [])):
        ref = ref_secs[k] if k < len(ref_secs) else ([], 'M')
        for n in sec.get('sectionNotes', []):
            if len(n) < 2 or int(n[1]) < OPP_MIN_LANE:
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ in KEEP:
                continue
            want = S2T[pick_for(ref, float(n[0]), int(n[1]))]
            if want == '':
                if len(n) > 3 or typ != '':
                    del n[3:]
                    changed += 1
            else:
                if typ != want:
                    while len(n) <= 3:
                        n.append('')
                    n[3] = want
                    changed += 1
    if changed:
        os.makedirs(BACKUP, exist_ok=True)
        shutil.copyfile(path, os.path.join(BACKUP, os.path.basename(os.path.dirname(path)) + '__' + os.path.basename(path)))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
    return changed


def verify(path, ref_secs):
    j, song = load(path)
    mixed = 0
    wrong = 0
    for k, sec in enumerate(song.get('notes', [])):
        seq = [T2S.get(typ, 'M') for t, lane, typ in opp_notes(sec)]
        if len(set(seq)) > 1:
            mixed += 1
        ref = ref_secs[k] if k < len(ref_secs) else ([], 'M')
        if seq and ref[1] and set(seq) != {ref[1]}:
            wrong += 1
    return mixed, wrong


def main():
    total = 0
    for mod in MODS:
        if not os.path.isdir(mod):
            print('SKIP', mod); continue
        print('==', mod)
        for s in SONGS:
            old_p = os.path.join(mod, 'data', s, s + '-old.json')
            _, old_song = load(old_p)
            ref_secs = old_sections(old_song)
            for d in TARGETS:
                p = os.path.join(mod, 'data', s, s + d + '.json')
                if not os.path.isfile(p):
                    continue
                ch = retag(p, ref_secs)
                mixed, wrong = verify(p, ref_secs)
                total += ch
                print('   %-34s 改标 %-4d 段内混唱 %-2d 与old统一段不符 %d' % (
                    os.path.basename(p), ch, mixed, wrong))
    print('备份:', BACKUP)
    print('总改标:', total)


if __name__ == '__main__':
    main()
