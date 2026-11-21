# -*- coding: utf-8 -*-
"""
v10.4：修复 God 难度 SHIFT(attack) / 空格(hey) 不播放动作。
根因：God 角色名 bf-god/miku-god/momo-god/teto-god 不在 DK_Fun.lua 的
      HEY_ANIM / ATTACK_ANIM 映射表里 —— attack 退回 'hey'、hey 无 specialAnim 锁。
修复：
  1) 加 baseChar() 后缀归一化，-god 等难度后缀自动映射到基础角色名查表
  2) 两个表显式补全 God 角色名（双保险）
  3) playHey 与 playAttack 一样设 specialAnim=true + heyTimer=0 + holdTimer=0
"""
import os

ROOTS = [
    'E:/UST_work/dk_miku/DK_Dual',
    'E:/UST_work/dk_miku/DK_Miku',
    'E:/UGUSDTIOUIYSRGIUUHSRGIH/Downloads/windows/mods/DK_Duet',
]
REL = 'scripts/DK_Fun.lua'

OLD_TABLE = """-- curCharacter -> hey 动画名（都来自 characters/*.json 的真实 name）
local HEY_ANIM = {
    ['bf']               = 'hey',
    ['bf-ic']            = 'hey',
    ['bf-defeat-normal'] = 'hey',
    ['miku']             = 'hey',
    ['momo']             = 'hey',
    ['teto']             = 'hey',
    ['teto-cozy']        = 'hey',
}

-- curCharacter -> attack 动画名；表外的角色（Miku/Momo/Teto）没有 attack，
-- 退回 hey，避免向引擎请求不存在的动画名。
local ATTACK_ANIM = {
    ['bf']    = 'attack',
    ['bf-ic'] = 'attack',
}
local function attackAnimFor(cc)
    if cc and ATTACK_ANIM[cc] then return ATTACK_ANIM[cc] end
    return 'hey'
end
"""

NEW_TABLE = """-- curCharacter -> hey 动画名（都来自 characters/*.json 的真实 anim 字段）
-- God 难度角色名带 -god 后缀，靠 baseChar() 归一化后复用基础表；
-- 这里也显式列出 God 名做双保险。
local HEY_ANIM = {
    ['bf']               = 'hey',
    ['bf-ic']            = 'hey',
    ['bf-defeat-normal'] = 'hey',
    ['miku']             = 'hey',
    ['momo']             = 'hey',
    ['teto']             = 'hey',
    ['teto-cozy']        = 'hey',
    ['bf-god']           = 'hey',
    ['bf-defeat-normal-god'] = 'hey',
    ['miku-god']         = 'hey',
    ['momo-god']         = 'hey',
    ['teto-god']         = 'hey',
}

-- curCharacter -> attack 动画名；表外的角色（Miku/Momo/Teto）没有 attack，
-- 退回 hey，避免向引擎请求不存在的动画名。
local ATTACK_ANIM = {
    ['bf']               = 'attack',
    ['bf-ic']            = 'attack',
    ['bf-god']           = 'attack',   -- God 难度玩家：Indie Cross 31 帧挥拳
}

-- 难度后缀归一化：'bf-god' -> 'bf'、'miku-god' -> 'miku'、
-- 'bf-defeat-normal-god' -> 'bf-defeat-normal'。只剥末尾一个 -后缀。
local function baseChar(cc)
    if not cc then return nil end
    local s = tostring(cc)
    local b = s:gsub('%-[%w_]+$', '')
    return b
end

local function heyAnimFor(cc)
    if not cc then return 'hey' end
    if HEY_ANIM[cc] then return HEY_ANIM[cc] end
    local b = baseChar(cc)
    if b and HEY_ANIM[b] then return HEY_ANIM[b] end
    return 'hey'
end

local function attackAnimFor(cc)
    if not cc then return 'hey' end
    if ATTACK_ANIM[cc] then return ATTACK_ANIM[cc] end
    local b = baseChar(cc)
    if b and ATTACK_ANIM[b] then return ATTACK_ANIM[b] end
    return 'hey'
end
"""

OLD_HEY = """        local anim = 'hey'
        local okc, cc = pcall(getProperty, c .. '.curCharacter')
        if okc and cc and HEY_ANIM[cc] then anim = HEY_ANIM[cc] end
        pcall(playAnim, c, anim, true)
        sp(c .. '.holdTimer', 0)
"""

NEW_HEY = """        local okc, cc = pcall(getProperty, c .. '.curCharacter')
        local anim = heyAnimFor(okc and cc or nil)
        -- 与 attack 相同的「先播后锁」：playAnim 内部会清 specialAnim，
        -- 必须播完立刻重新锁住，否则 Character.update 的 dance 会把 hey 顶掉。
        pcall(playAnim, c, anim, true)
        sp(c .. '.specialAnim', true)
        sp(c .. '.heyTimer', 0)
        sp(c .. '.holdTimer', 0)
"""

cnt = 0
for root in ROOTS:
    p = os.path.join(root, REL)
    if not os.path.exists(p):
        print('SKIP (missing)', p)
        continue
    raw = open(p, encoding='utf-8').read()
    if 'baseChar' in raw and 'bf-god' in raw and 'hit' not in OLD_HEY:
        pass
    new = raw
    if OLD_TABLE in new:
        new = new.replace(OLD_TABLE, NEW_TABLE)
    if OLD_HEY in new:
        new = new.replace(OLD_HEY, NEW_HEY)
    if new == raw:
        if 'local function baseChar' in raw and "['bf-god']           = 'attack'" in raw:
            print('= already fixed', root)
        else:
            print('! PATTERN NOT FOUND', root)
        continue
    open(p, 'w', encoding='utf-8', newline='').write(new)
    print('+ fixed', root)
    cnt += 1

print('modified files:', cnt)
