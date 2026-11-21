# v11.5：把所有 DK Saw 事件规范成"单锯 + 从左边(left)"——按用户明确要求
# 只改 GOD / GOD+ 谱面的 DK Saw 事件 v1/v2，不碰其它事件、不碰 notes、不碰 hard。
import json, os

ROOTS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
DIFFS = ['god', 'god+']

for root in ROOTS:
    for song in SONGS:
        for diff in DIFFS:
            p = os.path.join(root, 'data', song, '%s-%s.json' % (song, diff))
            if not os.path.exists(p):
                print('SKIP', p)
                continue
            raw = open(p, encoding='utf-8-sig').read()
            d = json.loads(raw)
            n = 0
            for ev in d.get('events', []):
                if ev[1] and ev[1][0][0] == 'DK Saw':
                    ev[1][0][1] = 'left'   # 方向：从左边出现
                    ev[1][0][2] = '1'      # 数量：单锯
                    n += 1
            # indent=1 是 Psych 原生格式
            out = json.dumps(d, ensure_ascii=False, indent=1)
            open(p, 'w', encoding='utf-8', newline='').write(out)
            print('NORM', root.split('/')[-1], song, diff, 'saws=', n)
