# -*- coding: utf-8 -*-
"""Subset simhei.ttf -> tiny dkCN.ttf containing only chars used by death-cause text + watermark."""
from fontTools import subset

SRC = r'C:/Windows/Fonts/simhei.ttf'
OUT = r'E:/UST_work/dk_miku/scripts/dkCN.ttf'

# Every string the Lua will render with this font.
LINES = [
    'DFJK117  GOD+',
    '死因：踩到陷阱，当场去世',
    '死因：漏按警告，当场去世',
    '死因：放过对手警告，当场去世',
    '死因：没躲开电锯，被劈了',
    '死因：血量耗尽',
    '按1快进5秒',
]
text = ''.join(LINES)
# safety: include full Chinese digit/punct set from the actual Lua escapes
text += '死因踩到陷阱漏按警告放过对手没躲开电锯被劈血量耗尽当场去世，：'
# also include full-width colon variant and digits/letters safety
text += '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz+ ：:·'

opts = subset.Options()
opts.no_hinting = True
opts.desubroutinize = True
opts.layout_features = ['*']
opts.name_IDs = ['*']
opts.name_legacy = True
opts.name_languages = ['*']

font = subset.load_font(SRC, opts)
subsetter = subset.Subsetter(options=opts)
subsetter.populate(text=text)
subsetter.subset(font)
subset.save_font(font, OUT, opts)

import os
print('OUT', OUT, os.path.getsize(OUT), 'bytes')
print('chars', len(set(text)))
