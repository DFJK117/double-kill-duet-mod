# -*- coding: utf-8 -*-
"""
v11.33 修复（2026-11-19 20:15）
用户反馈：
  1) 开 bpp 直接取消回收动画
  2) F2 快速回收不生效，必须开 bpp 才有
  3) F3 要独立开启（DK_Push 本来独立，确认不动）

根因：
  - F2 的快速回收动作 recycleLane() 只在 bpp 自动打谱命中流程 doRelease() 里调用。
    不开 bpp（手动打谱）时按 F2 只切了 recycleMode 变量，箭头回收不经过 recycleLane
    -> F2 看起来"不生效、必须开 bpp"。
  - 开 bpp 时 TURBO 档 frameRate=240 + resetAnim=0.001，confirm 一帧播完 -> 像"取消动画"。

修复：
  - BOTPLAY_Pro.lua tick()：在 `if not enabled then return end` 之前插入"独立回收扫描"，
    不开 bpp 时也按当前档位处理玩家 4 轨 confirm -> F2 独立生效。
  - recycleLane()：enabled(开 bpp) 时走正常速度，保留完整回收动画；TURBO 快速档
    只用于手动打谱（F2）。
  - DK_Push.lua 不动（F3 已独立）。

写正本 DK_Miku，同步 DK_Dual 与游戏 DK_Duet，打包 v11.33 ZIP。
"""
import os, shutil, zipfile, hashlib, datetime

ROOT   = r'E:/UST_work/dk_miku'
SRC    = os.path.join(ROOT, 'DK_Miku', 'scripts', 'BOTPLAY_Pro.lua')
GAME   = r'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet/scripts/BOTPLAY_Pro.lua'
DUAL   = os.path.join(ROOT, 'DK_Dual', 'scripts', 'BOTPLAY_Pro.lua')
BK     = r'I:/_trash_ust_work/dk_bpp_backup_20261119_2015'
ZIP    = os.path.join(ROOT, 'DK_Duet_FULL_v11.33_BPPIndependent_20261119.zip')
PREFIX = 'DK_Duet/'

os.makedirs(BK, exist_ok=True)

def md5(p):
    h = hashlib.md5()
    with open(p, 'rb') as f:
        for c in iter(lambda: f.read(1 << 20), b''):
            h.update(c)
    return h.hexdigest()

# 0) 备份三处原文件
for tag, p in [('DK_Miku', SRC), ('DK_Dual', DUAL), ('game_DK_Duet', GAME)]:
    d = os.path.join(BK, tag + '_BOTPLAY_Pro.lua')
    if not os.path.exists(d):
        shutil.copy2(p, d)
        print('BACKUP', tag, md5(p))

t = open(SRC, encoding='utf-8').read()
orig = t

# 1) 头部版本注释
t = t.replace(
    '--  BOTPLAY Pro (bpp)  v6      DK_Duet / NovaFlare Engine',
    '--  BOTPLAY Pro (bpp)  v7      DK_Duet / NovaFlare Engine\n'
    '--  v7(2026-11-19): F2 快速回收独立于 bpp(手动打谱也生效);\n'
    '--      开 bpp 时保留完整回收动画(不再被 TURBO 压成 1 帧=取消)。')

# 2) 独立回收扫描：插在 enabled 门控之前
OLD_GATE = """    if not enabled then return end
    ensureScoreVisible()
"""
NEW_GATE = """    -- v7: F2 快速回收独立于 bpp —— 不开 bpp(手动打谱)时也按当前档位处理玩家 4 轨回收。
    --     这样 F2 不再"必须开 bpp 才有"；开/关 bpp 都不影响 F2 的回收速度控制。
    if not enabled then
        for L = 0, 3 do
            local base = 'playerStrums.members[' .. L .. ']'
            local an = gp(base .. '.animation.curAnim.name', '')
            if an == 'confirm' then
                if recycleMode == 'TURBO' then
                    sp(base .. '.animation.curAnim.frameRate', TURBO_FPS)
                    sp(base .. '.resetAnim', 0.001)
                else
                    sp(base .. '.animation.curAnim.frameRate', 24)
                    sp(base .. '.resetAnim', 0.12)
                end
            end
        end
        return
    end
    ensureScoreVisible()
"""
assert OLD_GATE in t, 'gate anchor not found'
t = t.replace(OLD_GATE, NEW_GATE, 1)

# 3) recycleLane：开 bpp 走正常速度，TURBO 只给手动打谱
OLD_RL = """local function recycleLane(L)
    local base = 'playerStrums.members[' .. L .. ']'
    if recycleMode == 'TURBO' then
        pcall(setProperty, base .. '.animation.curAnim.frameRate', TURBO_FPS)
        pcall(setProperty, base .. '.resetAnim', 0.001)
    else
        -- 常速：恢复引擎默认帧率，让 confirm 按 24fps 正常播完后再回收
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
        pcall(setProperty, base .. '.resetAnim', 0.12)
    end
end
"""
NEW_RL = """local function recycleLane(L)
    local base = 'playerStrums.members[' .. L .. ']'
    -- v7: 开 bpp 时保留完整回收动画(24fps 正常播完)，不再被 TURBO 压成 1 帧≈取消。
    --     TURBO 快速档改由上面的独立扫描在"不开 bpp"时执行，专供手动打谱。
    if enabled then
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
        pcall(setProperty, base .. '.resetAnim', 0.12)
    elseif recycleMode == 'TURBO' then
        pcall(setProperty, base .. '.animation.curAnim.frameRate', TURBO_FPS)
        pcall(setProperty, base .. '.resetAnim', 0.001)
    else
        pcall(setProperty, base .. '.animation.curAnim.frameRate', 24)
        pcall(setProperty, base .. '.resetAnim', 0.12)
    end
end
"""
assert OLD_RL in t, 'recycleLane anchor not found'
t = t.replace(OLD_RL, NEW_RL, 1)

assert t != orig, 'no change'
open(SRC, 'w', encoding='utf-8', newline='\n').write(t)
print('PATCHED SRC', md5(SRC), len(t.splitlines()), 'lines')

# 4) 同步到 DK_Dual 与游戏目录
for tag, p in [('DK_Dual', DUAL), ('game_DK_Duet', GAME)]:
    shutil.copy2(SRC, p)
    print('SYNC', tag, md5(p))

# 5) 校验函数完整
for p in [SRC, DUAL, GAME]:
    s = open(p, encoding='utf-8').read()
    assert 'v7: F2 快速回收独立于 bpp' in s
    assert "if an == 'confirm' then" in s
    assert '-- v7: 开 bpp 时保留完整回收动画' in s
print('VERIFY all 3 copies OK')

# 6) 打包 v11.33（以游戏 DK_Duet 目录为源，前缀 DK_Duet/）
srcmod = os.path.dirname(os.path.dirname(GAME))  # .../mods/DK_Duet
if os.path.exists(ZIP):
    os.remove(ZIP)
n = 0
with zipfile.ZipFile(ZIP, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for root, _, files in os.walk(srcmod):
        for fn in files:
            fp = os.path.join(root, fn)
            z.write(fp, PREFIX + os.path.relpath(fp, srcmod))
            n += 1
with zipfile.ZipFile(ZIP) as z:
    bad = z.testzip()
print('ZIP', ZIP)
print('items', n, 'size', os.path.getsize(ZIP), 'crc', 'OK' if bad is None else bad)
print('md5', md5(ZIP))
