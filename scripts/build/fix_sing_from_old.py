# -*- coding: utf-8 -*-
"""以 old 谱为唯一权威，重标所有难度（hard/easy/normal/infant/god/god+/无后缀）的唱者类型。

规则（用户 2026-11-21 20:36「你要么就照着 old 曲目。哪里是什么就什么」）：
  1) old 里 (时间, 轨道) 存在的音符 -> 原样复制 old 的 noteType（''/'Opponent 2 Sing'/'Both Opponents Sing'）
  2) old 里没有该 (时间, 轨道) 的音符 -> 取 old 在该时刻「正在唱的人」（时间 <= t 的最后一个对手音符）
  3) 'DK Trap' / 'DK Warn' 等特殊键类型一律不动
"""
import json, os, shutil, datetime

MODS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
BACKUP = r'I:/_trash_ust_work/dk_sing_from_old_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
TOL_MS = 120
KEEP_TYPES = ('DK Trap', 'DK Warn')


def load(p):
    j = json.load(open(p, encoding='utf-8-sig'))
    return j, (j['song'] if isinstance(j.get('song'), dict) else j)


def is_opp(lane, mh, keys=4):
    return ((lane < keys) == mh) is False


def tkey(t):
    return round(float(t), 3)


def build_old_index(song):
    idx = {}          # (t, lane) -> type
    series = []       # [(t, type)] 按时排序，仅对手侧
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            lane = int(n[1])
            if not is_opp(lane, mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            idx[(tkey(n[0]), lane)] = typ
            series.append((float(n[0]), typ))
    series.sort(key=lambda x: x[0])
    return idx, series


def singer_at(series, t):
    lo, hi, best = 0, len(series) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= t + TOL_MS:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return series[best][1] if best is not None else ''


def retag(path, idx, series):
    j, song = load(path)
    changed = exact = fallback = 0
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            lane = int(n[1])
            if not is_opp(lane, mh):
                continue
            old_typ = str(n[3]) if len(n) > 3 else ''
            if old_typ in KEEP_TYPES:
                continue
            hit = idx.get((tkey(n[0]), lane))
            if hit is not None:
                want = hit
                exact += 1
            else:
                want = singer_at(series, float(n[0]))
                fallback += 1
            if old_typ != want:
                while len(n) <= 3:
                    n.append('')
                n[3] = want
                changed += 1
    if changed:
        os.makedirs(BACKUP, exist_ok=True)
        shutil.copyfile(path, os.path.join(BACKUP, os.path.basename(os.path.dirname(path)) + '__' + os.path.basename(path)))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
    return changed, exact, fallback


def verify(path, idx, series):
    j, song = load(path)
    bad_exact = bad_time = 0
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            lane = int(n[1])
            if not is_opp(lane, mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ in KEEP_TYPES:
                continue
            hit = idx.get((tkey(n[0]), lane))
            if hit is not None:
                if typ != hit:
                    bad_exact += 1
            else:
                if typ != singer_at(series, float(n[0])):
                    bad_time += 1
    return bad_exact, bad_time


def main():
    total_changed = 0
    for mod in MODS:
        if not os.path.isdir(mod):
            print('SKIP', mod); continue
        print('==', mod)
        for s in SONGS:
            old_p = os.path.join(mod, 'data', s, s + '-old.json')
            if not os.path.isfile(old_p):
                print('   缺 old', old_p); continue
            _, old_song = load(old_p)
            idx, series = build_old_index(old_song)
            diffs = ['', '-hard', '-normal', '-easy', '-infant', '-god', '-god+']
            for d in diffs:
                p = os.path.join(mod, 'data', s, s + d + '.json')
                if not os.path.isfile(p):
                    continue
                ch, ex, fb = retag(p, idx, series)
                b1, b2 = verify(p, idx, series)
                total_changed += ch
                print('   %-34s 改标 %-4d（精确匹配 %d / 时刻兜底 %d） 校验: 与old不同 %d / 兜底错 %d'
                      % (os.path.basename(p), ch, ex, fb, b1, b2))
    print('备份:', BACKUP)
    print('总改标:', total_changed)


if __name__ == '__main__':
    main()
