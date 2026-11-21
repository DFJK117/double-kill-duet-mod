import os, hashlib

A = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
B = r'E:/UST_work/dk_miku/DK_Miku'
C = r'E:/UST_work/dk_miku/DK_Dual'

def files(d):
    m = {}
    for r, ds, fs in os.walk(d):
        for f in fs:
            p = os.path.join(r, f)
            rel = os.path.relpath(p, d).replace(os.sep, '/')
            m[rel] = hashlib.md5(open(p, 'rb').read()).hexdigest()
    return m

a, b, c = files(A), files(B), files(C)
for name, x, y in [('DK_Duet vs DK_Miku', a, b), ('DK_Duet vs DK_Dual', a, c), ('DK_Miku vs DK_Dual', b, c)]:
    onlyx = sorted(set(x) - set(y))
    onlyy = sorted(set(y) - set(x))
    diff = sorted(k for k in set(x) & set(y) if x[k] != y[k])
    print('===', name, '===')
    print('  只在前:', onlyx[:15], 'count', len(onlyx))
    print('  只在后:', onlyy[:15], 'count', len(onlyy))
    print('  内容不同:', len(diff))
    for k in diff[:40]:
        print('    ', k, x[k][:8], y[k][:8])
