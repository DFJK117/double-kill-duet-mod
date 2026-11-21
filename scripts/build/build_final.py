# -*- coding: utf-8 -*-
"""DK 单模组单曲目 + 署名/水印 + USTX 歌词重构（BF 轨禁改）。"""
import os, re, json, shutil, subprocess, hashlib, datetime
from PIL import Image, ImageDraw, ImageFont

SRC = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/mods'
COZY = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/Monochrome_Cozy'
OUT = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet'
USTX = r'C:/Users/Administrator/Desktop/Double Kill (Rareblin) - 3tracks.ustx'
SINGERS = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/OpenUtau-win-x64/Singers'
SIGN = 'DFJK117'

def cp(rel, dst=None, base=SRC):
    s = os.path.join(base, rel)
    if not os.path.exists(s): raise FileNotFoundError(s)
    d = os.path.join(OUT, dst or rel)
    os.makedirs(os.path.dirname(d), exist_ok=True)
    shutil.copy2(s, d); return d

def put(rel, text, crlf=True):
    d = os.path.join(OUT, rel); os.makedirs(os.path.dirname(d), exist_ok=True)
    t = text.replace('\r\n', '\n').replace('\n', '\r\n') if crlf else text
    open(d, 'w', encoding='utf-8', newline='').write(t); return d

def putb(rel, data):
    d = os.path.join(OUT, rel); os.makedirs(os.path.dirname(d), exist_ok=True)
    open(d, 'wb').write(data); return d

def jload(p): return json.load(open(p, encoding='utf-8-sig'))

os.makedirs(OUT, exist_ok=True)   # 重复执行直接覆盖，不产生垃圾目录

# =====================================================================
# A. 单模组单曲目
# =====================================================================
cp('songs/double-kill/Inst.ogg'); cp('songs/double-kill/Voices.ogg')
cp('stages/cargo.json'); cp('stages/cargo.lua')
for f in os.listdir(os.path.join(SRC, 'images/stages/airship/double-kill')):
    if f != 'cargo.png': cp('images/stages/airship/double-kill/' + f)

# --- 曲目脚本：原样套用自带 lua（只改双人 icon 名 + gf 半透明保持）
for f in ('NewLogic.lua', 'events.lua', 'events.json'):
    cp('data/double-kill/' + f)
ic = open(os.path.join(SRC, 'data/double-kill/icons.lua'), encoding='utf-8-sig').read()
ic = ic.replace("local specialIcon = 'double-kill'", "local specialIcon = 'momo-teto'")
put('data/double-kill/icons.lua', ic)

# --- 谱面：只换两个角色，note Type 一个不动（自带 GF Sing / blackDuo 套用）
chart = jload(os.path.join(SRC, 'data/double-kill/double-kill-hard.json'))
chart['player2'] = 'momo'      # 原白
chart['gfVersion'] = 'teto'    # 原黑（第二对手）
putb('data/double-kill/double-kill-hard.json',
     json.dumps(chart, ensure_ascii=False, separators=(',', ':')).encode('utf-8'))

# --- 角色
for f in ('bf.json', 'bf-defeat-normal.json'): cp('characters/' + f)
for f in ('BOYFRIEND.png', 'BOYFRIEND.xml', 'defeatBf-normal.png', 'defeatBf-normal.xml'):
    cp('images/characters/bf/' + f)

momo = jload(os.path.join(COZY, 'characters/momo-cozy.json'))
momo['healthicon'] = 'momo'          # 原值 icon-momo 会去找 icon-icon-momo.png
putb('characters/momo.json', json.dumps(momo, ensure_ascii=False, indent=1).encode('utf-8'))
for f in ('momo_assets.png', 'momo_assets.xml'): cp('images/characters/' + f, base=COZY)
cp('images/icons/icon-momo.png', base=COZY)

teto_src = jload(os.path.join(COZY, 'characters/teto-cozy.json'))
a = {x['anim']: x for x in teto_src['animations']}
def mk(anim_name, src_anim, loop=False):
    x = dict(a[src_anim]); x['anim'] = anim_name; x['loop'] = loop; return x
anims = [mk(n, 'idle', n == 'idle') for n in
         ('idle', 'danceLeft', 'danceRight', 'sad', 'scared', 'hurt', 'combo50')]
anims += [mk('cheer', 'hey'), mk('hey', 'hey')]
anims += [mk(k, k) for k in ('singLEFT', 'singDOWN', 'singUP', 'singRIGHT')]
teto = {'animations': anims, 'image': 'characters/teto-2026', 'healthicon': 'teto-cozy',
        'healthbar_colors': [233, 120, 145], 'position': [-60, 20], 'camera_position': [0, 0],
        'scale': 0.5, 'flip_x': False, 'sing_duration': 4, 'no_antialiasing': False,
        'vocals_file': '', '_editor_isPlayer': False}
putb('characters/teto.json', json.dumps(teto, ensure_ascii=False, indent=1).encode('utf-8'))
for f in ('teto-2026.png', 'teto-2026.xml'): cp('images/characters/' + f, base=COZY)
cp('images/icons/icon-teto-cozy.png', base=COZY)

# --- 双人合成 icon：Momo 左半 + Teto 右半（两帧 300x150）
im1 = Image.open(os.path.join(COZY, 'images/icons/icon-momo.png')).convert('RGBA')
im2 = Image.open(os.path.join(COZY, 'images/icons/icon-teto-cozy.png')).convert('RGBA')
out = Image.new('RGBA', (300, 150))
for fr in (0, 1):
    out.paste(im1.crop((fr * 150, 0, fr * 150 + 75, 150)), (fr * 150, 0))
    out.paste(im2.crop((fr * 150 + 75, 0, fr * 150 + 150, 150)), (fr * 150 + 75, 0))
out.save(os.path.join(OUT, 'images/icons/icon-momo-teto.png'))
cp('images/icons/icon-double-kill.png')   # 原版双人 icon 也留着

# --- 自带 lua：套用，不自造
for f in ('Both Opponents.lua', 'Opponent Two.lua', 'Reactor Beep.lua',
          'flash.lua', 'Camera Set Target.lua', 'Add Cam Zoom.lua'):
    cp('custom_events/' + f)
for f in ('blackDuo.lua', 'Both Opponents Sing.lua', 'Opponent 2 Sing.lua', 'DuoSing.lua'):
    cp('custom_notetypes/' + f)

# --- 补齐谱面用到但原包没有实现的事件（只做显示层，不重复播动画）
put('custom_events/Legacy.lua', '''-- Legacy: 叫出/收起第二对手(Teto)，半透明显示；唱歌动作由自带 lua 负责
function onEvent(name, v1, v2)
    if name ~= 'Legacy' then return end
    if v1 == 'black' or v1 == 'kill' then
        doTweenAlpha('dkSecond', 'gf', 0.5, 0.5, 'linear')
    elseif v1 == 'not black' then
        doTweenAlpha('dkSecond', 'gf', 0, 0.5, 'linear')
    end
end
''')
put('custom_events/Extra Cam Zoom.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Extra Cam Zoom' then return end
    setProperty('camGame.zoom', getProperty('camGame.zoom') + (tonumber(v1) or 0.02))
    if v2 ~= nil and v2 ~= '' then
        setProperty('camHUD.zoom', getProperty('camHUD.zoom') + (tonumber(v2) or 0))
    end
end
''')
put('custom_events/Add Camera Zoom.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Add Camera Zoom' then return end
    if v1 ~= nil and v1 ~= '' then setProperty('camGame.zoom', getProperty('camGame.zoom') + (tonumber(v1) or 0)) end
    if v2 ~= nil and v2 ~= '' then setProperty('camHUD.zoom', getProperty('camHUD.zoom') + (tonumber(v2) or 0)) end
end
''')
put('custom_events/Set Cams.lua', '''function onEvent(name, v1, v2)
    if name ~= 'Set Cams' then return end
    local t = string.lower(v1 or '')
    if t == 'bf' or t == 'b' then cameraSetTarget('boyfriend')
    elseif t == 'dad' or t == 'd' then cameraSetTarget('dad')
    elseif t == 'gf' or t == 'g' then cameraSetTarget('gf') end
end
''')

# --- 全局脚本：只带曲目信息（全改 DFJK117）；"仙-星辰移植"/版本号脚本不加载 = 删掉
task = open(os.path.join(SRC, 'scripts/CustomTaskSong.lua'), encoding='utf-8-sig').read()
task = re.sub(r'\{("|\')(.+?)\1\s*,\s*("|\').*?\3\s*\}',
              lambda m: '{%s%s%s, "%s"}' % (m.group(1), m.group(2), m.group(1), SIGN),
              task, flags=re.S)
put('scripts/CustomTaskSong.lua', task)
cp('impostor/pita.lua')
opt = os.path.join(OUT, '_全局脚本_可选_不要放进scripts'); os.makedirs(opt, exist_ok=True)
for f in os.listdir(os.path.join(SRC, 'scripts')):
    shutil.copy2(os.path.join(SRC, 'scripts', f), os.path.join(opt, f))

# --- week / pack
putb('weeks/dk-duet.json', json.dumps({
    'songs': [['double-kill', 'momo-teto', [200, 180, 220]]],
    'hiddenUntilUnlocked': False, 'hideFreeplay': False, 'weekBackground': 'yellow',
    'difficulties': 'hard', 'weekCharacters': ['', '', ''], 'storyName': SIGN,
    'weekName': 'Double Kill Duet', 'hideStoryMode': False,
    'weekBefore': 'tutorial', 'startUnlocked': True,
}, ensure_ascii=False, indent=1).encode('utf-8'))
putb('pack.json', json.dumps({'name': SIGN + ' - Double Kill Duet',
    'description': 'BF vs Momo + Teto | Single Song', 'restart': True,
    'runsGlobally': False, 'color': [200, 180, 220]},
    ensure_ascii=False, indent=1).encode('utf-8'))

# --- 背景：木箱 "TANK in a BOX" -> DFJK117 + 左上角水印
bg = Image.open(os.path.join(SRC, 'images/stages/airship/double-kill/cargo.png')).convert('RGBA')
px = bg.load()
# 文字是偏蓝灰的深色；用木箱棕覆盖这些像素（保留木纹/边框）
wood = (176, 120, 70, 255)
for y in range(165, 365):
    for x in range(880, 1115):
        r, g, b, a = px[x, y]
        if b > r + 6 and b > g + 2 and max(r, g, b) < 165:
            px[x, y] = wood
font_path = os.path.join(SRC, 'fonts/vcr.ttf')
big = ImageFont.truetype(font_path, 44)
small = ImageFont.truetype(font_path, 30)
d = ImageDraw.Draw(bg, 'RGBA')
d.text((898, 235), SIGN, font=big, fill=(58, 74, 90, 255))
# 水印：左上留白区
d.text((24, 22), SIGN, font=small, fill=(70, 60, 80, 120))
d.text((26, 24), SIGN, font=small, fill=(255, 255, 255, 105))
bg.save(os.path.join(OUT, 'images/stages/airship/double-kill/cargo.png'))

put('README.txt', '''%s - Double Kill Duet | 单模组单曲目
============================================
玩家 BF / 第一对手 Momo(原白) / 第二对手 Teto(原黑)
音源、谱面事件(82 行)、音符 Type 全部沿用原曲，未改一个音符。

双人唱 & 另一对手独立唱：全部套用原包自带 lua
  custom_events/Both Opponents.lua / Opponent Two.lua
  custom_notetypes/blackDuo.lua / Both Opponents Sing.lua / Opponent 2 Sing.lua / DuoSing.lua
第二对手出场：custom_events/Legacy.lua (black 淡入半透明 0.5 / not black 淡出)
双人合成 icon：images/icons/icon-momo-teto.png（icons.lua 里 specialIcon 指向它）

署名：弹出的曲目信息全部改成 %s；pack.json、week 名同为 %s
删掉的：scripts/cray.lua「仙-星辰移植」、SUS_HUD.lua 里的「Vs Impostor Legacy! 1.0.3」
背景：cargo.png 木箱 TANK in a BOX -> %s，左上角加 %s 水印

【为什么 scripts/ 只放一个】
原包 9 个全局 lua + 2 个 hx 每首歌都执行：CustomVideos(缺视频)、
CustomGameOvers(缺 overLegacy 音效)、CustomDialogue(38KB 全曲对白)、
Complements.lua 甚至有语法错误 `or name 'bars'`。全塞进单曲模组必炸。
原始文件原样留在 _全局脚本_可选_不要放进scripts/ 供查阅，别直接拷进 scripts/。
''' % (SIGN, SIGN, SIGN, SIGN, SIGN))

print('[A] 模组完成 ->', OUT)

# =====================================================================
# B. USTX 歌词重构（BF 轨禁改）
# =====================================================================
raw = open(USTX, 'rb').read()
bom = raw.startswith(b'\xef\xbb\xbf')
text = raw.decode('utf-8-sig').replace('\r\n', '\n')
L = text.split('\n')
orig_bf_lines = []
backup = os.path.join(r'E:/UST_work/doublekill/_backup_2026-11-08',
                      'Double Kill (Rareblin) - 3tracks_before_rebuild.ustx')
shutil.copy2(USTX, backup)

# 1) 音素器：只改前两个 track（JapanesePresamp -> Default），BF 那行不动
n_ph = 0
for k, line in enumerate(L):
    if line.strip().startswith('phonemizer: OpenUtau.Plugin.Builtin.JapanesePresampPhonemizer'):
        L[k] = line.replace('OpenUtau.Plugin.Builtin.JapanesePresampPhonemizer',
                            'OpenUtau.Core.DefaultPhonemizer')
        n_ph += 1
print('[B] 音素器改默认:', n_ph, '轨')

# 2) 定位 voice_parts 下每个 note 块
vp = next(k for k, l in enumerate(L) if l.startswith('voice_parts:'))
blocks = []           # (start, end, track_no, position, duration, lyric)
track_no = -1
starts = []
for k in range(vp, len(L)):
    l = L[k]
    m = re.match(r'^  track_no: (\d+)', l)
    if m: track_no = int(m.group(1))
    if re.match(r'^  - position: \d+', l):
        starts.append((k, track_no))
# 块结束必须截断在 voice part 边界，否则删尾块会连下一个 part 的头一起吞掉
part_starts = [k for k in range(vp + 1, len(L)) if re.match(r'^- ', L[k])]
bounds = sorted(set([x[0] for x in starts] + part_starts + [len(L)]))
for idx, (st, tn) in enumerate(starts):
    en = min(x for x in bounds if x > st)
    seg = L[st:en]
    pos = int(re.search(r'position: (\d+)', seg[0]).group(1))
    dur = next((int(re.search(r'duration: (\d+)', x).group(1))
                for x in seg if re.match(r'^    duration: \d+', x)), 0)
    lyr = next((x.split('lyric: ', 1)[1].strip().strip("'") for x in seg
                if re.match(r'^    lyric: ', x)), '')
    blocks.append([st, en, tn, pos, dur, lyr])
    if tn == 2: orig_bf_lines.extend(L[st:en])

print('[B] note 块', len(blocks), '| BF 块', sum(1 for b in blocks if b[2] == 2))

# 3) 合并 "-" 长音进前一个音符，并重算 duration 为「到下一个保留音符」= 100%% 连唱
remove, newdur = set(), {}
for tn in (0, 1):
    bs = [b for b in blocks if b[2] == tn]
    keep = [b for b in bs if b[5] not in ('-', '', 'R', 'r')]
    for b in bs:
        if b not in keep: remove.add(b[0])
    tail = bs[-1][3] + bs[-1][4]          # 原轨最后一个音符的结束位置（含被合并的长音）
    for i, b in enumerate(keep):
        nxt = keep[i + 1][3] if i + 1 < len(keep) else tail
        newdur[b[0]] = max(nxt - b[3], 120)
    print('    track%d: %d -> %d 音符（合并长音 %d 个）' % (tn, len(bs), len(keep), len(bs) - len(keep)))

# 4) 生成新文本：BF 轨整块原样；track0/1 删块或改 duration
by_start = {b[0]: b for b in blocks}
line_owner = {}
for b in blocks:
    for q in range(b[0] + 1, min(b[1], len(L))):
        line_owner[q] = b
outL, skip_until = [], -1
for k, line in enumerate(L):
    if k < skip_until: continue
    b = by_start.get(k)
    if b is not None and k in remove:
        skip_until = b[1]; continue
    if re.match(r'^    duration: \d+', line):
        owner = line_owner.get(k)
        if owner is not None and owner[0] in newdur:
            outL.append('    duration: %d' % newdur[owner[0]]); continue
    outL.append(line)
new_text = '\n'.join(outL)
if bom: new_text = '\ufeff' + new_text
open(USTX, 'wb').write(new_text.replace('\n', '\r\n').encode('utf-8'))

# 5) 校验
import yaml, glob, collections
d = yaml.safe_load(open(USTX, 'rb').read().decode('utf-8-sig'))
bf_after = [n for p in d['voice_parts'] if p.get('track_no') == 2 for n in p['notes']]
bf_before = [n for p in yaml.safe_load(open(backup, 'rb').read().decode('utf-8-sig'))['voice_parts']
             if p.get('track_no') == 2 for n in p['notes']]
print('[B] BF 轨音符完全一致:', bf_before == bf_after, '| 音符数', len(bf_after))
print('[B] 音素器:', [t.get('phonemizer') for t in d['tracks']])
for p in d['voice_parts']:
    ns = sorted(p['notes'], key=lambda n: n['position'])
    gaps = sum(1 for i in range(1, len(ns)) if ns[i]['position'] > ns[i-1]['position'] + ns[i-1]['duration'])
    dash = sum(1 for n in ns if n['lyric'] in ('-', '', 'R', 'r'))
    print('    %s: %d 音符, 空隙 %d, 长音残块 %d' % (p['name'], len(ns), gaps, dash))
    if p.get('track_no') in (0, 1):
        folder = '重音テト音声ライブラリー' if p['track_no'] == 0 else '呗音ウタ_Defoko'
        al = set()
        for f in glob.glob(os.path.join(SINGERS, folder, '**', 'oto.ini'), recursive=True):
            b = open(f, 'rb').read()
            for e in ('utf-8', 'shift_jis', 'cp932'):
                try: t = b.decode(e); break
                except Exception: t = ''
            for x in t.splitlines():
                if '=' in x and ',' in x: al.add(x.split('=', 1)[1].split(',', 1)[0])
        miss = collections.Counter(n['lyric'] for n in ns if n['lyric'] not in al)
        print('       %s 别名 %d | 未命中 %d %s' % (folder, len(al), sum(miss.values()), dict(miss.most_common(8))))

# 6) modsList：禁用原大包，启用单曲模组
ml = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/modsList.txt'
shutil.copy2(ml, ml + '.bak_dkduet')
lines = open(ml, encoding='utf-8-sig').read().splitlines()
lines = [('mods|0' if x.strip() == 'mods|1' else x) for x in lines]
if not any(x.startswith('DK_Duet|') for x in lines): lines.append('DK_Duet|1')
open(ml, 'w', encoding='utf-8', newline='\r\n').write('\n'.join(lines) + '\n')
print('[B] modsList 已切换（备份 .bak_dkduet）')
print('\n全部完成')
