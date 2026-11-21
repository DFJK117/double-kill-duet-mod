# -*- coding: utf-8 -*-
"""把 NF 的 DK_Duet mod 适配到 Impostor Legacy 1.1.2（PE 0.6.3 定制/NVE 内核）。

遗产版差异：
  - noteType 目录 = data/notetypes/*.hscript（非 custom_notetypes/*.lua）
  - week 目录    = data/weeks/*.json（非 weeks/*.json）
  - 无 Lua 支持（exe 中 .lua=0 / .hscript=193）→ GOD 特殊键脚本不生效（保留文件，静态说明）
策略：双路径共存（原目录保留 + 遗产版目录补一份），modsList.txt 启用。
"""
import os, shutil, json, sys

ROOT = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
MOD  = os.path.join(ROOT, 'mods', 'DK_Duet')
MODSLIST = os.path.join(ROOT, 'modsList.txt')
MODNAME = 'DK_Duet'

def log(*a): print('[adapt]', *a)

def copy_if(src, dst):
    if not os.path.isfile(src):
        log('MISS', src); return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst); return True

# 1) week 双路径：weeks/*.json -> data/weeks/*.json
weeks_src = os.path.join(MOD, 'weeks')
weeks_dst = os.path.join(MOD, 'data', 'weeks')
n = 0
for f in os.listdir(weeks_src):
    if f.lower().endswith('.json'):
        copy_if(os.path.join(weeks_src, f), os.path.join(weeks_dst, f)); n += 1
log('week 复制到 data/weeks:', n)

# 2) noteType 双路径：遗产版引擎原生支持 Opponent 2 Sing / Both Opponents Sing，
#    放空 .hscript/.txt 占位与原版 assets/data/notetypes 一致（= 用引擎内置逻辑）
nt_dst = os.path.join(MOD, 'data', 'notetypes')
os.makedirs(nt_dst, exist_ok=True)
for name in ['Opponent 2 Sing', 'Both Opponents Sing', 'Opponent Two', 'GF Sing', 'No Animation']:
    for ext in ('.hscript', '.txt'):
        p = os.path.join(nt_dst, name + ext)
        if not os.path.exists(p):
            open(p, 'wb').close()
log('noteType 占位写到 data/notetypes:', len(os.listdir(nt_dst)), '文件')

# 3) modsList.txt 启用（保留其它条目）
lines = []
if os.path.isfile(MODSLIST):
    with open(MODSLIST, encoding='utf-8-sig', errors='replace') as fh:
        lines = [l.strip() for l in fh if l.strip()]
out, found = [], False
for l in lines:
    if l.split('|')[0].strip() == MODNAME:
        out.append(MODNAME + '|1'); found = True
    else:
        out.append(l)
if not found:
    out.insert(0, MODNAME + '|1')
with open(MODSLIST, 'w', encoding='utf-8', newline='\n') as fh:
    fh.write('\n'.join(out) + '\n')
log('modsList.txt:', repr('\n'.join(out)))

# 4) 静态验证：谱面引用的角色/音频/图片是否齐全
def fmt(s):
    s = str(s).lower().replace(' ', '-')
    for c in '~&\\;:<>#': s = s.replace(c, '-')
    for c in '.,\'"%?!': s = s.replace(c, '')
    return s

missing = []
for song in ['double-kill', 'double-kill-miku']:
    d = os.path.join(MOD, 'data', song)
    for f in os.listdir(d):
        if not f.endswith('.json') or 'events' in f: continue
        try:
            j = json.load(open(os.path.join(d, f), encoding='utf-8-sig'))
            s = j['song'] if isinstance(j.get('song'), dict) else j
        except Exception as e:
            missing.append((f, 'JSON 解析失败', str(e))); continue
        # 音频目录（按谱内 song 字段）
        snd = fmt(s.get('song') or song)
        inst = os.path.join(MOD, 'songs', snd, 'Inst.ogg')
        if not os.path.isfile(inst): missing.append((f, '缺音频', inst))
        # 角色 json
        for k in ('player1', 'player2', 'gfVersion'):
            ch = s.get(k)
            if ch and not os.path.isfile(os.path.join(MOD, 'characters', fmt(ch) + '.json')):
                missing.append((f, '缺角色 '+k, ch))

log('静态引用检查：缺失', len(missing))
for m in missing[:30]: log('  ', m)
log('DONE')
