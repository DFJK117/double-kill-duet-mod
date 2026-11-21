# -*- coding: utf-8 -*-
"""DK 唱者按「段落」对齐 old（v3，2026-11-21 20:45）

上一版按 (时间,轨道) 逐音符对：婴儿谱是削谱重排，音符时间/轨道与 old 不同，
几乎全部落空 -> 兜底规则在段内乱跳 -> 出现「一段里一半 Opponent 2 Sing 一半空 type」。
本节拍：infant 与 old **段数/段序/mustHitSection/BPM 完全一致（514 段）**，
所以直接按段索引取 old 该段的主导唱者，整段统一。

唱者 -> noteType：M(第一对手)='' ; T(Teto)='Opponent 2 Sing' ; B(合唱)='Both Opponents Sing'
未标 type 的音符按 old 风格写成 3 元素 [time, lane, sus]。
'DK Trap' / 'DK Warn' 一律不动。
"""
import json, os, shutil, datetime
from collections import Counter

MODS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
TARGETS = ['-infant', '']          # 需要重标的难度（其余已与 old 一致）
BACKUP = r'I:/_trash_ust_work/dk_sing_section_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
KEEP = ('DK Trap', 'DK Warn')
T2S = {'': 'M', 'Opponent 2 Sing': 'T', 'Both Opponents Sing': 'B'}
S2T = {'M': '', 'T': 'Opponent 2 Sing', 'B': 'Both Opponents Sing'}


def load(p):
    j = json.load(open(p, encoding='utf-8-sig'))
    return j, (j['song'] if isinstance(j.get('song'), dict) else j)


def is_opp(lane, mh, keys=4):
    return ((lane < keys) == mh) is False


def section_singers(song):
    """每个段落的对手侧唱者序列（按出现顺序）。"""
    out = []
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        seq = []
        for n in sec.get('sectionNotes', []):
            if len(n) < 2 or not is_opp(int(n[1]), mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ in KEEP:
                continue
            seq.append(T2S.get(typ, 'M'))
        out.append(seq)
    return out


def dominant_per_section(seqs):
    """每段主导唱者；空段向前（再向后）继承最近段。"""
    dom = []
    for seq in seqs:
        if not seq:
            dom.append(None)
            continue
        cnt = Counter(seq)
        best = max(cnt.values())
        # 并列时取该段里最先出现的那个，保证与原谱观感一致
        pick = next(s for s in seq if cnt[s] == best)
        dom.append(pick)
    # 空段继承
    last = None
    for i, d in enumerate(dom):
        if d is None:
            dom[i] = last
        else:
            last = d
    nxt = None
    for i in range(len(dom) - 1, -1, -1):
        if dom[i] is None:
            dom[i] = nxt
        else:
            nxt = dom[i]
    return [d or 'M' for d in dom]


def retag_sections(path, dom):
    j, song = load(path)
    changed = 0
    for k, sec in enumerate(song.get('notes', [])):
        mh = sec.get('mustHitSection', True)
        want_singer = dom[k] if k < len(dom) else 'M'
        want_type = S2T[want_singer]
        for n in sec.get('sectionNotes', []):
            if len(n) < 2 or not is_opp(int(n[1]), mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ in KEEP:
                continue
            if typ == want_type and not (want_type == '' and len(n) > 3):
                continue
            if want_type == '':
                del n[3:]                    # 与 old 一致：无 type 只写 3 元素
            else:
                while len(n) <= 3:
                    n.append('')
                n[3] = want_type
            changed += 1
    if changed:
        os.makedirs(BACKUP, exist_ok=True)
        shutil.copyfile(path, os.path.join(BACKUP, os.path.basename(os.path.dirname(path)) + '__' + os.path.basename(path)))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
    return changed


def main():
    total = 0
    for mod in MODS:
        if not os.path.isdir(mod):
            print('SKIP', mod); continue
        print('==', mod)
        for s in SONGS:
            old_p = os.path.join(mod, 'data', s, s + '-old.json')
            _, old_song = load(old_p)
            dom = dominant_per_section(section_singers(old_song))
            for d in TARGETS:
                p = os.path.join(mod, 'data', s, s + d + '.json')
                if not os.path.isfile(p):
                    continue
                ch = retag_sections(p, dom)
                # 校验：每段唱者必须唯一，且等于 old 该段主导
                jj, ss = load(p)
                seqs = section_singers(ss)
                mixed = [i for i, seq in enumerate(seqs) if len(set(seq)) > 1]
                wrong = [i for i, seq in enumerate(seqs) if seq and set(seq) != {dom[i]}]
                total += ch
                print('   %-34s 改标 %-4d 段内混唱 %d 与old段落不同 %d' % (
                    os.path.basename(p), ch, len(mixed), len(wrong)))
                if mixed or wrong:
                    print('      混唱段:', mixed[:8], '错段:', wrong[:8])
    print('备份:', BACKUP)
    print('总改标:', total)


if __name__ == '__main__':
    main()
