# -*- coding: utf-8 -*-
"""新建 GOD+ 独立难度：week 加 GOD+、两首曲复制 -god+ 谱面、icons 认 GOD+、补难度图。

幂等。三处目录同步：DK_Duet(游戏) / DK_Dual / DK_Miku。
formatToSongPath('GOD+') == 'god+'，故谱面文件名 = <song>-god+.json。
"""
import json, shutil, os
from PIL import Image, ImageDraw, ImageFont

ROOTS = [
    r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
    r'E:/UST_work/dk_miku/DK_Dual',
    r'E:/UST_work/dk_miku/DK_Miku',
]
SONGS = ['double-kill', 'double-kill-miku']
WEEKS = ['dk-momo.json', 'dk-miku.json']
FONT = r'C:/Windows/Fonts/arialbd.ttf'


def make_diff_png(text, path, fill, outline):
    """仿 menudifficulties 风格：粗体描边字，透明底。"""
    font = ImageFont.truetype(FONT, 58)
    probe = Image.new('RGBA', (10, 10), (0, 0, 0, 0))
    d = ImageDraw.Draw(probe)
    bb = d.textbbox((0, 0), text, font=font, stroke_width=3)
    w = bb[2] - bb[0] + 20
    h = bb[3] - bb[1] + 16
    im = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    dr = ImageDraw.Draw(im)
    dr.text((10 - bb[0], 8 - bb[1]), text, font=font, fill=fill,
            stroke_width=3, stroke_fill=outline)
    im.save(path)
    return im.size


for root in ROOTS:
    name = root.replace('\\', '/').split('/')[-1]

    # 1) week: difficulties 加 GOD+
    for wf in WEEKS:
        p = os.path.join(root, 'weeks', wf)
        with open(p, encoding='utf-8-sig') as f:
            d = json.load(f)
        diffs = [x.strip() for x in (d.get('difficulties') or '').split(',') if x.strip()]
        for want in ('GOD', 'GOD+'):
            if want not in diffs:
                diffs.append(want)
        d['difficulties'] = ','.join(diffs)
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
        print(name, wf, 'difficulties=', d['difficulties'])

    # 2) 谱面: -god.json -> -god+.json（含 DK Saw 事件）
    for s in SONGS:
        src = os.path.join(root, 'data', s, f'{s}-god.json')
        dst = os.path.join(root, 'data', s, f'{s}-god+.json')
        with open(src, encoding='utf-8-sig') as f:
            d = json.load(f)
        with open(dst, 'w', encoding='utf-8') as f:
            json.dump(d, f, indent=1, ensure_ascii=False)
        saw = sum(1 for e in d['events'] if e[1] and e[1][0][0] == 'DK Saw')
        print(name, f'{s}-god+.json', 'saw=', saw)

    # 3) icons.lua: GOD+ 也走 god icon
    for s in SONGS:
        p = os.path.join(root, 'data', s, 'icons.lua')
        txt = open(p, encoding='utf-8').read()
        old = "if difficultyName == 'GOD' or difficultyName == 'god' then"
        new = "if difficultyName == 'GOD' or difficultyName == 'god' or difficultyName == 'GOD+' then"
        if old in txt:
            txt = txt.replace(old, new)
            open(p, 'w', encoding='utf-8', newline='').write(txt)
            print(name, s, 'icons GOD+ OK')

    # 4) 难度图 GOD / GOD+（放 mod 本地 images，mod 优先于 assets）
    md = os.path.join(root, 'images', 'menudifficulties')
    os.makedirs(md, exist_ok=True)
    sz1 = make_diff_png('GOD', os.path.join(md, 'god.png'),
                        (255, 220, 40, 255), (30, 20, 0, 255))
    sz2 = make_diff_png('GOD+', os.path.join(md, 'god+.png'),
                        (255, 90, 60, 255), (60, 8, 8, 255))
    print(name, 'god.png', sz1, 'god+.png', sz2)

print('DONE')
