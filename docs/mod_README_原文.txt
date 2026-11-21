DFJK117 - Double Kill Duet | 单模组单曲目
============================================
玩家 BF / 第一对手 Miku(原白) / 第二对手 Teto(原黑)
音源、谱面事件(82 行) 沿用原曲。

谱面：用原版 hard 谱做模板换过，514 sections / 2800 notes，
      保留 DK_Duet 外壳(player1=bf / player2=momo / gfVersion=teto)，
      保留新谱的 noteType(Opponent 2 Sing x8)，events.json 仍是旧事件系统。

双人唱 & 另一对手独立唱：套用原包自带 lua
  custom_events/Both Opponents.lua / Opponent Two.lua  -> 和弦也是 Momo+Teto 双动作
  custom_notetypes/blackDuo.lua / Both Opponents Sing.lua / Opponent 2 Sing.lua / DuoSing.lua
第二对手出场：custom_events/Legacy.lua (black 淡入半透明 0.5 / not black 淡出)

双人 icon：images/icons/icon-momo-teto.png（内容已换 Miku+Teto） 与 icon-double-kill.png（内容相同）
  300x150 = normal 帧(左 150) + losing 帧(右 150)，不是左右各放一个人。
  每帧里 Momo(左下前景) + Teto(右上后景) 叠在一起，白色描边分隔，两个都看得见。
  icons.lua 里 specialIcon = 'momo-teto' 指向它。

超级 BOTPLAY / BOTPLAY Pro：scripts/BOTPLAY_Pro.lua
  开关 F4，或谱面事件 "BOTPLAY Pro"(1/on 开, 0/off 关, 空 切换)，F5 打印引擎输入字段。
  默认关闭。开启后自动按谱命中，走 game.goodNoteHit 真实计分(combo/health/accuracy)，
  同时写 keysPressed + 箭头 confirm + BF 动作 = 上报按键输入，CPU Controlled 保持 false。
  runHaxeCode 不可用时自动降级成兼容模式(cpuControlled + 强制显示 scoreTxt)。
  事件占位壳：custom_events/BOTPLAY Pro.lua

开场：黑幕 + 黑闪 + blackIntro + step144 闪光弹(白闪)，Teto 全程常驻不淡出。
  events.lua / NewLogic.lua，白屏过渡已取消。

署名：弹出的曲目信息全部改成 DFJK117；pack.json、week 名同为 DFJK117
删掉的：scripts/cray.lua「仙-星辰移植」、SUS_HUD.lua 里的「Vs Impostor Legacy! 1.0.3」
背景：cargo.png 木箱 TANK in a BOX -> DFJK117，左上角加 DFJK117 水印

【为什么 scripts/ 只放原本那一个全局脚本】
原包 9 个全局 lua + 2 个 hx 每首歌都执行：CustomVideos(缺视频)、
CustomGameOvers(缺 overLegacy 音效)、CustomDialogue(38KB 全曲对白)、
Complements.lua 甚至有语法错误 `or name 'bars'`。全塞进单曲模组必炸。
原始文件原样留在 _全局脚本_可选_不要放进scripts/ 供查阅，别直接拷进 scripts/。
（BOTPLAY_Pro.lua 是本项目自己写的，不占原包那 9 个的坑。）

【17:02 修订，以上旧描述以本段为准】
- 谱面「一人唱两 / 对面轨道跑到玩家轨道」已修：按 Psych 归属规则把
  1258 个音符归位，玩家固定 lane 0-3、对手固定 lane 4-7，全谱
  mustHitSection 统一 true；再按 events.json 的 Opponent Two /
  Both Opponents 时间段给 1040 个对手音符重打 noteType
  (Opponent 2 Sing 538 / Both Opponents Sing 510)，Teto 有独立音符。
  结果 514 节 / 2800 音，BF 1223 / 对手 1577。
- 开场：blackIntro（黑 impostor 从天而降的过渡动画）彻底删除，
  只保留黑幕 + 黑闪 + step144 闪光弹；Teto 全程常驻。
- Momo/Teto 站位拉近：cargo.json girlfriend [1490,630] -> [1400,680]，
  teto.json scale 0.5 -> 0.85 / position [-60,20] -> [-20,60]，
  实际横向间距约 100px（原 240+ 且大小差近 3 倍）。
- BOTPLAY Pro：开关 F4 -> **F1**，删掉全部 HUD 状态文字与 F5 诊断，
  脚本仍在 scripts/ 由模组自动加载，默认关闭、不显示任何状态。
- 双人 icon：去掉 4px 白描边，边缘白色雾边做去污染，
  靠角色自带黑描边 + 后景压暗区分；白色像素 6513 -> 739。
- USTX 交付副本：E:/UST_work/doublekill/Double Kill (Rareblin) - 3tracks - FINAL.ustx

【17:30 修订，以上旧描述以本段为准】
- 键位：A S J K。**DFJK117 是署名/名字，不是键位**。
- BOTPLAY Pro 重写为真·模拟按键上报：
  * press  -> game.keysPressed/keysHeld 置 true + game.keyPressed/onKeyPress/
             preKeyPress + Replay pressKey 帧 + frameData.push + inputUpload
  * hold   -> 按压 40~60ms 随机，中心随当前 acc 变化（acc 越高越短）；
             命中时机带 ±18ms 随机偏移，让 acc 真的会变化，不再永远 100%
  * release-> 清输入缓冲 + keyReleased + 箭头 playAnim('static')/playStatic
             回收，修掉「回收动画一直亮着」；长音自动延长到尾
  * 兜底 game.goodNoteHit 独立成核心段，分数/combo/health/acc 一定涨。
  * 老 hscript 不支持 try/catch，所以每个上报能力是独立一次 runHaxeCode，
    失败就 fail-once 关掉该能力，绝不会拖累命中段。
  * 按键映射可上传：事件 "BOTPLAY Pro Map" value1=A,S,J,K（4 个键名，
    逗号/分号/竖线分隔），或用 "BOTPLAY Pro" 的 value2；
    映射同时发布到 Lua 全局 bppKeyMap_0..3 / bppKeyMap 和引擎 game.bppKeyMap。
  * 事件 "BOTPLAY Pro Diag" 把各上报入口是否可用打到 debug 控制台（不占 HUD）。
  * 开关仍是 F1，默认关闭、不显示任何状态；CPU Controlled 保持 false。
- 镜头修复：上一轮把 514 段 mustHitSection 统一 true 修好了音符归属，
  但引擎 moveCamera 正靠这个字段切镜头，导致全程钉死 BF、看不到 Momo。
  **不改谱面**（改回去会让 false 段 lane 0-3 又判给对手，变回一人唱两），
  改为在 data/double-kill/NewLogic.lua 里内嵌【原版模板】514 段节奏表
  (BF 388 / Dad 126，共 65 次切换，逐位校验一致)，每帧按 curSection
  强制 cameraSetTarget('boyfriend'/'dad')，压住引擎的 moveCamera。
  音符归属完全不受影响。
- 备份：E:/UST_work/dk_duet/_backup_2026-11-08_1717/

=== 18:05 修订（覆盖上面 17:30 段里关于「上报」的描述）===
- 【开 BPP 闪退】17:41 / 17:53 两次 native crash 异常地址完全相同
  (RVA 0x226f07d，读空指针)：17:30 版往 game.replay.* / frameData /
  inputUpload / keyPressed / onKeyPress / preKeyPress / game.bppKeyMap
  写数据，非 replay 模式下 game.replay 为空，Lua 的 pcall 兜不住
  Haxe 层空指针，直接进程崩。以上调用**全部删除**，现在只保留两条
  验证过稳定的路径：
    game.keysPressed[L] / keysHeld[L]  = 写输入缓冲（真·按键上报层）
    game.goodNoteHit(note)            = 引擎真实命中入口（计分）
  「BOTPLAY Pro Diag」事件与引擎侧 bppKeyMap 字段一并移除；
  按键映射仍可通过 "BOTPLAY Pro Map" 上传到 Lua 全局 bppKeyMap_0..3。
  F1 开关 / A S J K / 40~60ms 随 acc / ±18ms 抖动 / 箭头回收 全部保留。
- 【一上来就合唱 / 各唱各的】17:02 曾给 1040 个对手音符强行打上
  "Opponent 2 Sing" / "Both Opponents Sing" noteType，远超原版模板的 8 个；
  现按原版模板逐音符还原 noteType 分布（2792 无 + 8 Opponent 2 Sing），
  合唱完全改由 events.json 的 Opponent Two / Both Opponents 开关驱动
  （第一个开关在 10790ms）。同时删掉 Opponent Two.lua 里每次事件遍历
  全部 notes 强设 noAnimation=false 的代码（会让每个对手音符都播唱歌动画）。
  开关关 = 只有 Momo 唱，开关开 = Momo + Teto 双唱。
- 【USTX 顺口 / 无换气 / 音符饱满】见 E:/UST_work/doublekill/ -FINAL.ustx。
  368 个长音 "+" 在重音テト/Defoko 单独音库里没有 alias（全是静音），
  是「唱着奇怪、中途换气」的真因。按用户认可的 141728 副本重做：长音
  并入前一音节 -> White 406 / Black 528，歌词全真假名、无长音符号，
  所有音符 duration 拉满到下一音符起点(gap=0)，alias 命中率 100%，
  4 轨、音高线拉平、BF 全 a 均保留。
- 备份：E:/UST_work/dk_duet/_backup_2026-11-08_1805/

===== 18:20 修订（上面 18:05 关于 USTX 与 BPP 的两段结论已作废）=====
- 【USTX 不渲染 / momo 白 teto 黑 / 禁止任何符号】
  18:05 版把 tracks 换成了 重音テト+呗音ウタ_Defoko 且音素器改成
  DefaultPhonemizer，还丢了 part 级 curves/masked_curves 字段、把
  pitch 点 x 写成等于 duration —— 这就是「直接不渲染」的原因。
  更关键：用户约定的对应关系一直是 **White -> 桃音モモ(Momo)、
  Black -> 重音テト(Teto)**，音素器是 JapanesePresampPhonemizer。
  Default 下才需要纯 alias，所以 18:05 那套「368 个 + 没采样」的
  诊断从根上就是错的：Presamp 会从纯假名生成 VCV alias（桃音モモ_Soft
  库里正是 "a あ"/"- よ" 这类），Teto 単独音库有 71 个平假名 alias。
  现以用户认可的 141728 副本为唯一基底重建（脚本
  E:/UST_work/doublekill/rebuild_ustx_1820.py）：
    * 3 轨：White 桃音モモ / Black 重音テト / BF，Presamp + Default
    * 368 个 "-" 长音块删除，时长并入【前一个】假名音符
      -> 歌词纯假名，零符号（无 + - * ー），一个音节一个长音符，
         读着顺口、不换气、不重新起音
    * gap>0 = 0、gap<0 = 0（饱满）；音高线仍全拉平；BOM+CRLF
    * White 406 / Black 528 / BF 1042 = 1976 音符，
      md5 450ea4fe669aa7a92bdeabd1d71af455
  「Chord (BF)」第 4 轨是后来加的，本次为回到可渲染基底未带回；
  需要的话从 _backup_2026-11-08_1820/ 里取回。
- 【BPP 闪退（箭头快到判定线时）】四次 crash（17:41 / 17:53 /
  18:06 / 18:17）RVA 全是 0x226f07d、read 0x0。hscript_source_preview
  依次是 try{game.keysPressed / game.bppKeyMap /
  game.keysPressed[1]=true;game.keysHeld[1]=true; —— 共同点是
  往 game 上不存在或为 null 的字段做下标写入，null[1]=true 在 Haxe
  层读空指针，Lua pcall 兜不住。崩溃时机 = 开 BPP 后第一个音符进
  判定窗口，所以看起来是「箭头快到底下就闪退」，不是按 F1 那一下。
  **现在一行 runHaxeCode 都没有**：
    * 自动打谱 + 真实计分 -> 引擎原生 cpuControlled（自己走 goodNoteHit）
    * 每帧抢回 scoreTxt（Complements.lua 会在 botplay 时隐藏它）
    * 按键上报 -> Lua 全局 bppKeyDown_N / bppKey_N / bppKeyMap
    * 箭头 press -> 40~60ms(随 acc) -> release 强制 static 回收
  F1 开关 / 无状态文字 / A S J K / BOTPLAY Pro Map 上传映射 全保留。
  【边界】引擎输入缓冲与 Replay 帧注入做不到（那条路必崩），
  Lua 层伪造不了 OS 级键盘事件；要 replay 录成真人按键流需改引擎源码。
- 【谱面脏数据】1040 个音符第 4 列是空字符串 noteType，已删掉恢复
  标准 3 列；1 个音符把 'Opponent Two' 塞进 sustain 长度列，已改 0。
  现 514 节 / 2800 音，noteType 仅 8 个 Opponent 2 Sing，lanes 0-7 不变。
- 备份：E:/UST_work/doublekill/_backup_2026-11-08_1820/

================================================================
【19:00 最终版 —— 以上各节均为历史记录，以本节为准】
================================================================
1) USTX 从 MIDI 全新重建，不再修补旧工程
   源：Desktop/ustx/FNF/Double Kill Vocals (White-Black-Boyfriend).mid
   脚本：E:/UST_work/doublekill/midi_rebuild_3tracks_1900.py
   **强制 3 轨**：White=桃音モモ / Black=重音テト / Boyfriend=BF
   音符数 555 / 747 / 1042，position/duration/tone 全部来自 MIDI，
   含 200->220 BPM tempo map 换算；和弦重叠音同起去重、前音截断，
   绝不生成第 4 轨。
   歌词全新写（能念的日文句子、全平假名、零符号），逐音节 1:1 对应
   MIDI 音符，每个音节都校验过声库别名存在（替换 0 个）。
   饱满：非句末音符延伸到下个音起点；换气：每个乐句末留 120 tick，
   共 73 / 116 个换气点。vibrato depth 5、音高线拉平。
   renderer 全轨 WORLDLINE-R（R1.1 缺 hnsep_240512 包，必崩）。
   交付：Desktop/Double Kill (Rareblin) - 3tracks.ustx 及同名
   autosave / FINAL 系列全部同步，另有
   E:/UST_work/doublekill/Double Kill (Rareblin) - MIDI重建3轨.ustx
   md5 89ae2a426f31a415980feb32a93a771c

2) 声库修复（这才是「Momo 不渲染」的真因）
   Singers/桃音モモ/oto.ini 原本 0 字节 -> 用同库 Soft 的 oto.ini 补齐，
   并转成 shift_jis（character.yaml 声明 shift_jis，UTF-8 字节会被
   解码成乱码，日志曾刷 198 条 Sound file missing）。
   254 个 wav 全部校验存在。没采样的同名备份库
   Singers/桃音モモ_Soft/character.yaml 已改名，不再抢桃音モモ这个名字。
   实测：Attach singer = 桃音モモ / 重音テト / BF，
   Sound file missing = 0，Failed to pre-render = 0，三轨 Phonemized，
   新增渲染片段 94 个、75 个非静音（平均 RMS 1165）。

3) BOTPLAY Pro v2（修「摆设」）
   旧版扫描条件 not wasGoodHit，而引擎 cpuControlled 会抢先把音符
   标成已命中 -> 计分 / acc / 按键上报整条链一次都没跑过。
   现改用自己的 seen 去重表；自己按判定偏差真实计分并 addScore，
   自算加权 acc（随命中浮动），icons.lua 在 BPP 开启时显示真实
   Score / Misses / Accuracy / Rank，不再是 N/A。
   逐次按键上报：bppKeyDown_N / bppKey_N / bppKeyHold_N /
   bppKeyCount / bppKeyEvent，外加 callOnLuas('onBPPKey', ...) 与
   triggerEvent('BOTPLAY Pro Key', ...)，外部脚本可直接订阅。
   仍 100% 纯 Lua、0 行 runHaxeCode（不会再触发 0x226f07d 空指针闪退）。
   F1 开关、无状态文字、A S J K、BOTPLAY Pro Map 上传映射全保留。
   边界不变：Lua 无法伪造 OS 级键盘 / 写引擎 Replay 帧。

4) 备份：E:/UST_work/doublekill/_backup_2026-11-08_1850/

================================================================
19:55 修订（USTX 修好版 + 谱面从旧谱重建 + 独唱/合唱分流）
================================================================

5) USTX「音符全消失」的根因与修复
   19:03 那版从 MIDI 全新生成，脚本里
       n[1] = max(60, end - n[0])   -- 把「结束时间」写成了「时长」
       dur  = b - a                 -- 又减了一次起点
   => dur = next_start - 2*start => 负数
   => OpenUtau 丢弃全部音符 =>「轨道在、音符全没了」，两轨一起崩
      所以听起来「两个都他妈一样」。
   现改用 OpenUtau 自己保存的原生工程作基底
   (OpenUtau-win-x64/Backups/Untitled-autosave.ustx)，
   duration / pitch.data / snap_first / shape 全部合法，
   且保留用户手动调过的内容（BF 轨音高 59/60、vibrato depth 5）。
   只改：歌词、句末换气（缩短 120 tick）、pitch 终点与 duration 同步。
   歌词换成能念的日文（全平假名、零符号）：
     白「よるのこえがきこえるよ まちのひかりがすこしだけ …」
     黑「うわさだけで きみのあしおとをきいてる …」
   逐音节校验声库可发声（Momo 142 个假名独立音 / Teto 每个假名
   有 aeiou 五种前接、句首只能用「う」），降级 0 个。

6) 谱面：用 mod 实际加载的旧谱重建
   基准 = mods/mods/data/double-kill/double-kill-hard.json
   （mods/mods/data/ 是这个 mod 运行时真正加载的目录；
     assets/data/ 只是素材目录）
   旧谱与本 mod 的 82 条 events 逐条完全一致 -> 同源。
   旧谱自带的正确信息，全部恢复：
     - 音符第 5 列归属标记（464 个）
     - 段级 mustHitSection 混合（True 132 / False 120）
     - 音符轨：0-3 玩家(bf)，4-7 对手
   之前 17:11 那版把音符换成另一套（玩家轨少 1058、对手轨多 1044），
   并把 126 个对手段的 mustHitSection 全改成 True
   -> 对面轨道的音符跑到玩家轨道，就是「BF 唱了对面的谱」。
   现：252 段 / 2070 音符 / 轨道 0-3: 270/269/237/282，
       4-7: 258/257/226/271 / 段级 mustHit True132 False120。

7) 「Teto 无法单独唱、一开就合唱」的根因与修复
   18:20 我把 1040 个 'Both Opponents Sing' 当成空值清掉了，
   谱面里只剩 8 个 'Opponent 2 Sing' -> Teto 根本没有独唱标记。
   现按旧谱 noteType 映射回来（全部落在对手轨 4-7）：
     'GF Sing'    417 -> 'Opponent 2 Sing'      Teto 独唱
     'blackDuo'   336 -> 'Both Opponents Sing'  Momo+Teto 合唱
     'No Animation' 3 -> 'No Animation'          不唱不动画
     其余对手音符无类型 -> 只有 Momo 唱
   时间点与 events 开关精确吻合：
     'Opponent Two'=1 @10790ms  <-> 首个 Opponent 2 Sing @10800ms
     'Both Opponents'=1 @58795ms <-> 首个 Both Opponents Sing @58800ms
   custom_notetypes 改成按 noteType 精确分流（对齐原 mod 权威实现）：
     Opponent 2 Sing      -> noAnimation = true   掐掉 Momo，Teto 独唱
     Both Opponents Sing  -> noAnimation = false  Momo 照唱 + Teto 也唱
     No Animation         -> noAnimation = true   不唱不动画
   custom_events/Opponent Two.lua、Both Opponents.lua 原来用事件开关
   做「全局双唱」，开关一开之后所有对手音符都两人合唱，
   把 Teto 独唱段也吃掉了 -> 现已移除双唱逻辑，只保留开关状态。
   玩家轨（0-3）音符一律不带 noteType；开头 0~10.8s 只有 Momo 唱，
   不会一上来就合唱。

8) 实测（19:43~19:55 真机 OpenUtau v0.1.576）
   Load project = 1，Phonemized = 3（三轨全部音素化成功）
   Failed to pre-render = 0，Sound file missing = 0，错误 0 条
   播放后新增渲染片段 41 个，全部非静音（平均 RMS 3013，最大 6445）
   USTX 841,822 B，md5 c51a1debb83a15a8a6a0351e8ec9b72d
   8 个路径同步（桌面主文件 / autosave / FINAL / VCV-autosave 等）
   DK_Duet.zip 21,105,215 B / 68 项 / CRC OK
   备份：E:/UST_work/doublekill/_backup_2026-11-08_1930/

================================================================
20:10 修订 —— 谱面基准彻底纠正（铺面问题的真正根因）

上一版（19:25~19:55）我拿 `mods/mods/data/double-kill/double-kill-hard.json`
当基准重建谱面，结论是错的。原因：

  modsList.txt 里 `mods|0` —— **那个 mod 是禁用的**，它的谱面根本不加载。
  真正在跑的是 `assets|1`，它提供：
      mods/assets/data/double-kill/double-kill-hard.json          (4P 原版, 2800 音符)
      mods/assets/data/double-kill/double-kill-hard-swapped.json (Nov 6 被改坏)
      mods/assets/data/double-kill/script.lua / events.json / info.txt
  引擎 debug 报告（debug/DK_Duet/hard/Double Kill.txt）证实：
  本次会话加载的是 assets 的角色与 shared 脚本 + DK_Duet 的 events.json，
  谱面目录来自 mods/DK_Duet/data/double-kill/。

本轮修的三件事：

1) `assets/.../double-kill-hard-swapped.json` 轨道字段类型损坏
   音符第 2 列被写成列表 [5]（引擎按整数读 noteData[1]）→ 2800 处全部改为整数。
   换轨逻辑本身是对的（0↔4 / 1↔5 / 2↔6 / 3↔7），保留不动。

2) DK_Duet 谱面基准换成正确的 4P→2P duet 转换
   正确基准 = `E:/UST_work/dk_duet/_backup_2026-11-08_1717/double-kill-hard.json`
   （该版由 assets 原版派生，转换规则已逐音符验证 0 违例）：
       段 514 / 音符 2800（与 assets 原版完全一致）
       玩家轨 0-3 = 1223 音符（BF）
       对手轨 4-7 = 1577 音符（Momo + Teto）
       转换规则：**只在原版 mustHitSection=False 的对手段里把 lane 0-3 ↔ 4-7 对调**
                   （对手段里"对手的音符"要落到对手轨；玩家段保持原样）
       noteType 只落在对手轨：
           Opponent 2 Sing      538  → 只有 Teto 唱（Momo 被 noAnimation 掐掉）
           Both Opponents Sing  510  → Momo + Teto 合唱
           (无类型)             529  → 只有 Momo 唱
   段级 mustHitSection 恢复为原版的 True 388 / False 126（之前被误设成全 True，
   那正是"镜头钉死 BF / 段级归属丢失"的来源）。

3) 交付
   谱面 121,353 B / md5 fa7616e1544ca52e9ff7c137251dc17e
   DK_Duet.zip 21,108,354 B / 68 项 / CRC OK
   备份：E:/UST_work/doublekill/_backup_2026-11-08_2010/
   （含改坏前的 DK_Duet 谱 + assets 两份原谱）



【2026-11-14 角色替换】Momo -> 初音未来（Vs Hatsune Miku 官方贴图）
文件名 momo* 一律沿用，谱面 player2 / lua specialIcon / week 图标名均未改动，
所以不会出现引用断裂；贴图、atlas 动画帧、血条图标、血条色、缩放全部换成 Miku。
原始 Momo 版本已整体备份到 E:/UST_work/dk_miku/_backup_PE_momo_20261114/。



【20261115_185235 单模组双曲】
weeks/dk-momo.json  -> double-kill        = Momo + Teto（恢复 11-14 原始 momo 贴图/角色）
weeks/dk-miku.json  -> double-kill-miku   = Miku + Teto（11-15 版）
两首歌各自独立的 data/<song>/ 脚本、songs/<song>/ 音频、双人 icon 与周目立绘。
共享：custom_events / custom_notetypes / characters / stages / scripts(BOTPLAY Pro v4)。
图标：Miku 单人改用旧的 300x150 两帧 icon；双人 icon 按 momo-teto 原版前后重叠构图合成。
构建脚本：E:/UST_work/dk_miku/build_dual_dk.py


==================== 更新日志 / CHANGELOG ====================
[2026-11-18] v11.32
  - 模组主页(主菜单)背景音改为 Double Kill Miku 的伴奏 (music/freakyMenu.ogg)
  - 难度: hard 改名 old (谱面内容不变); 新增 Infant 婴儿难度 (mods12 新版2800谱, 坐姿婴儿图标)
  - 空格躲避(dodge)动画强制播完, 命中音符的 sing 不再顶掉躲避动作
  - 保留 GOD / GOD+ 难度、黑黄资源、FLS 新人声 (md5 8f9ca277...)
[2026-11-18] v11.29
  - Double Kill Miku 人声替换为 FLS 原声 (支持和弦唱, 解决 OpenUTAU 断续)
[2026-11-16] v10
  - 难度资源分离: hard 用原版贴图, GOD 用黑黄贴图; Trap/Warn 特殊键机制
============================================================
