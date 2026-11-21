# -*- coding: utf-8 -*-
"""逐项验证 DK_Duet 移植到 Impostor Legacy 的完整性（PE 路径解析规则）。"""
import os, json, glob
from collections import Counter

ROOT = r'E:\UGUSDTIOUIYSRGIUUHSRGIH\Downloads\vs-impostor-legacy-1.1.2\VS IMPOSTOR LEGACY 1.1.2'
MOD  = os.path.join(ROOT, 'mods', 'DK_Duet')

def fmt(s):
    s = str(s).lower().replace(' ', '-')
    for c in '~&\\;:<>#': s = s.replace(c, '-')
    for c in '.,\'"%?!': s = s.replace(c, '')
    return s

def load(p):
    j = json.load(open(p, encoding='utf-8-sig'))
    return j['song'] if isinstance(j.get('song'), dict) else j

errs, warns = [], []
# 1) modsList 启用
ml = open(os.path.join(ROOT,'modsList.txt'),encoding='utf-8').read()
assert 'DK_Duet|1' in ml, 'modsList 未启用'
print('OK modsList.txt 已启用 DK_Duet')

# 2) 逐谱面
charts = [p for p in glob.glob(os.path.join(MOD,'data','*','*.json'))
          if 'events' not in os.path.basename(p) and os.path.basename(os.path.dirname(p)) not in ('weeks','notetypes')]
tot_notes = 0
for p in charts:
    rel = os.path.relpath(p, MOD)
    try: s = load(p)
    except Exception as e: errs.append((rel,'JSON坏',str(e))); continue
    n = sum(len(sec.get('sectionNotes',[])) for sec in s.get('notes',[]))
    tot_notes += n
    if n==0: warns.append((rel,'0音符'))
    # 音频：谱内 song -> songs/<fmt>/Inst.ogg
    song = s.get('song')
    inst = os.path.join(MOD,'songs',fmt(song or ''),'Inst.ogg')
    if not os.path.isfile(inst):
        errs.append((rel,'缺Inst',fmt(song or '')+'/Inst.ogg'))
    # 角色
    for k in ('player1','player2','gfVersion'):
        ch = s.get(k)
        if not ch: continue
        cj = os.path.join(MOD,'characters',fmt(ch)+'.json')
        if not os.path.isfile(cj): errs.append((rel,'缺角色'+k,ch)); continue
        try: c = json.load(open(cj,encoding='utf-8-sig'))
        except: errs.append((rel,'角色JSON坏',ch)); continue
        img = c.get('image'); hc = c.get('healthicon')
        if img and not (os.path.isfile(os.path.join(MOD,'images',img+'.png')) or os.path.isfile(os.path.join(ROOT,'assets','images',img+'.png'))):
            errs.append((rel,'缺角色图',img))
        if hc and not (os.path.isfile(os.path.join(MOD,'images','icons','icon-'+hc+'.png')) or os.path.isfile(os.path.join(ROOT,'assets','images','icons','icon-'+hc+'.png'))):
            errs.append((rel,'缺icon','icon-'+hc+'.png'))
print('OK 谱面 %d 个 / 总音符 %d'%(len(charts),tot_notes))

# 3) week 双路径 + 歌曲名能解析到谱面
for w in glob.glob(os.path.join(MOD,'weeks','*.json')):
    b=os.path.basename(w)
    assert os.path.isfile(os.path.join(MOD,'data','weeks',b)), 'week 双路径缺失 '+b
    j=json.load(open(w,encoding='utf-8-sig'))
    for entry in j.get('songs',[]):
        name=entry[0]
        # 引擎按 difficulty 拼文件名；至少要有无后缀主谱
        main=os.path.join(MOD,'data',fmt(name),fmt(name)+'.json')
        if not os.path.isfile(main):
            warns.append((b,'week歌曲无主谱',name))
print('OK week 双路径齐备')

# 4) noteType 双路径
for name in ['Opponent 2 Sing','Both Opponents Sing']:
    assert os.path.isfile(os.path.join(MOD,'data','notetypes',name+'.hscript')), '缺 noteType '+name
    assert os.path.isfile(os.path.join(MOD,'custom_notetypes',name+'.lua')), '缺原 noteType lua '+name
print('OK noteType 双路径齐备')

# 5) 唱者分流正确性（infant 段9 全 Opponent 2 Sing，lane>=4）
for song in ['double-kill','double-kill-miku']:
    p=os.path.join(MOD,'data',song,song+'-infant.json')
    s=load(p)
    seq=[str(n[3]) if len(n)>3 else '' for n in s['notes'][9]['sectionNotes'] if int(n[1])>=4]
    ok = seq and all(x=='Opponent 2 Sing' for x in seq)
    print('OK' if ok else 'WARN', song, 'infant 段9 对手类型:', Counter(seq))
    if not ok: warns.append((song,'段9唱者不一致',str(Counter(seq))))

print('\n=== 错误 %d ==='%len(errs))
for e in errs[:40]: print(' ERR',e)
print('=== 警告 %d ==='%len(warns))
for w in warns[:40]: print(' WARN',w)
print('\nRESULT:', 'PASS' if not errs else 'FAIL')
