# -*- coding: utf-8 -*-
"""DK_Infant 唱者重标：按 old 谱（权威）逐时刻对齐，把 Infant 里标错的
Opponent 2 Sing / Both Opponents Sing / 空(第一对手) 全部改成「old 在这一刻的唱者」。

依据（用户 2026-11-21 20:36）：「照着 old 曲目，哪里是什么就什么。」
实测：old/hard/god/GOD+/easy/normal 与 old 逐时刻 100% 一致，只有 Infant 18% 不一致。
"""
import json, os, shutil, datetime, sys

MODS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
TOL_MS = 120            # 最近匹配容差
SINGER_TO_TYPE = {'M': '', 'T': 'Opponent 2 Sing', 'B': 'Both Opponents Sing'}
BACKUP = r'I:/_trash_ust_work/dk_singfix_' + datetime.datetime.now().strftime('%Y%m%d_%H%M%S')


def singer_of(typ):
    if typ == 'Both Opponents Sing':
        return 'B'
    if typ == 'Opponent 2 Sing':
        return 'T'
    return 'M'


def is_opponent(lane, must_hit, keys=4):
    return ((lane < keys) == must_hit) is False


def load(path):
    j = json.load(open(path, encoding='utf-8-sig'))
    return j, (j['song'] if isinstance(j.get('song'), dict) else j)


def build_ref(song):
    """old 谱 -> 按时间排序的 (ms, singer) 列表（仅对手音符）。"""
    ref = []
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            lane = int(n[1])
            if not is_opponent(lane, mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ.startswith('DK '):
                continue
            ref.append((float(n[0]), singer_of(typ)))
    ref.sort(key=lambda x: x[0])
    return ref


def singer_at(ref, t):
    """t 时刻正在唱的人：取时间 <= t+TOL 的最后一个参考音符。"""
    lo, hi = 0, len(ref) - 1
    best = None
    while lo <= hi:
        mid = (lo + hi) // 2
        if ref[mid][0] <= t + TOL_MS:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best is None:
        return 'M'
    # 若最近的参考点离得太远（>600ms），仍沿用（段落连续），但记录
    return ref[best][1]


def fix_one(path, ref, dry=False):
    j, song = load(path)
    changed = 0
    total = 0
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            lane = int(n[1])
            if not is_opponent(lane, mh):
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ.startswith('DK '):     # 特殊键类型不动
                continue
            total += 1
            want = SINGER_TO_TYPE[singer_at(ref, float(n[0]))]
            if typ != want:
                while len(n) <= 3:
                    n.append('')
                n[3] = want
                changed += 1
    if changed and not dry:
        os.makedirs(BACKUP, exist_ok=True)
        tag = os.path.basename(os.path.dirname(path)) + '__' + os.path.basename(path)
        shutil.copyfile(path, os.path.join(BACKUP, tag))
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(j, f, indent=1, ensure_ascii=False)
    return total, changed


def verify(path, ref):
    j, song = load(path)
    bad = 0
    total = 0
    for sec in song.get('notes', []):
        mh = sec.get('mustHitSection', True)
        for n in sec.get('sectionNotes', []):
            if len(n) < 2:
                continue
            typ = str(n[3]) if len(n) > 3 else ''
            if typ.startswith('DK '):
                continue
            if not is_opponent(int(n[1]), mh):
                continue
            total += 1
            if singer_of(typ) != singer_at(ref, float(n[0])):
                bad += 1
    return total, bad


def main():
    grand = 0
    for mod in MODS:
        if not os.path.isdir(mod):
            print('SKIP 不存在:', mod)
            continue
        print('==', mod)
        for s in SONGS:
            old_p = os.path.join(mod, 'data', s, s + '-old.json')
            if not os.path.isfile(old_p):
                print('   缺 old:', old_p); continue
            _, old_song = load(old_p)
            ref = build_ref(old_song)
            for diff in ['infant']:
                p = os.path.join(mod, 'data', s, '%s-%s.json' % (s, diff))
                if not os.path.isfile(p):
                    print('   缺谱:', p); continue
                total, changed = fix_one(p, ref)
                t2, bad = verify(p, ref)
                grand += changed
                print('   %-34s 对手音符 %-4d 改标 %-4d 校验不一致 %d' % (
                    os.path.basename(p), total, changed, bad))
    print('备份目录:', BACKUP)
    print('总计改标:', grand)


if __name__ == '__main__':
    if '--dry' in sys.argv:
        TOL_MS = TOL_MS
    main()
