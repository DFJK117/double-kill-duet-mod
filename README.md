# Double Kill Duet — FNF 三人双人对唱模组（完整开源）

**⬇️ 成品下载：[Releases 页面](../../releases)**（各引擎版本的完整 zip，下载后按说明放进对应游戏）

基于 Vs Impostor 的 `Double Kill` 曲目深度改造的 FNF 模组。原曲是 BF vs Black Impostor 的对唱，本项目把它扩展成 **Momo / Miku 与 Teto 的双人轮唱 + 合唱**，并加了 Infant / GOD / GOD+ 多难度、DK Trap / DK Warn 特殊机制、BOTPLAY Pro 模拟按键、评分贴图、输入 HUD 等大量定制。这是从 2026-11-08 到 11-21 连续迭代 30+ 版本的最终成果，全部源码与构建脚本开源于此。

## ⭐ 核心技术：唱者分流（这是整个项目最难的部分）

FNF 标准引擎只有 BF / Dad / GF 三个角色槽，"两个对手轮流唱"没有原生支持。本项目的解法：

- **轨道布局**：Legacy / NVE 是 4P 布局——`lane 0-3 = BF`、`lane 4-7 = 对手`，**与 `mustHitSection` 无关**（这是最容易被误判的点，`mustHitSection` 在 4P 下不决定归属）。
- **noteType 分流**：
  - `''`（空 type）= 第一对手 Momo/Miku 唱
  - `Opponent 2 Sing` = 第二对手 Teto 独唱
  - `Both Opponents Sing` = 两人合唱
  - 遗产版靠 stage 脚本的 `opponentNoteHitPre` + `note.owner = gf` 把第二对手音符路由到 GF 槽（Teto）
- ** Infant 谱对齐**：以 `*-old.json` 为权威，按**段索引**（old 与 infant 514 段一一对应）重标 infant 对手侧（lane≥4）音符；old 自己混唱的段按「同轨道优先 + 时间最近」继承；lane 0-3 一律不碰。修了 695 个音符，三副本同步。
- 实现见 `scripts/build/fix_sing_v4.py`（最终版分流算法）、`scripts/legacy/cargo-duo-*.hx`（遗产版 stage 路由）、`scripts/nf/DK_*.lua`（NF 机制脚本）。

## 版本谱系（哪个是哪个）

| 版本 / 包 | 引擎 | 说明 |
|---|---|---|
| `DK_Duet_FULL_v11.33_BPPIndependent` | NovaFlare Engine | **功能最全的最终版**：GOD+/Infant 多难度、DK Trap/Warn、BOTPLAY Pro、评分贴图、输入 HUD、BPPIndependent |
| `DK_Duet_Dual` / `DK_Miku` | NF / Kade | Miku 版三副本（游戏侧 + dk_miku/DK_Dual + DK_Miku），md5 对齐 |
| `DK_Duet_Lua_v5~v10` | Psych / Kade | 早期纯 Lua 机制版（GOD v8→v10 演进） |
| `DK_Duet_遗产版_assets直装` | VS Impostor Legacy 1.1.2 | 遗产版最终方案：以新增文件装进 `assets/`，独立 stage 修图标硬编码（详见下节） |
| `DK_Duet_Legacy版_移植包` | Leather Engine / Legacy | 中期移植包 |
| `DK_Duet_NVE遗产版_移植包` | NVE | 曾被误套 NVE `charts/` 新结构（失败尝试，保留供参考） |

### 遗产版移植的踩坑记录（血泪，值得看）

VS Impostor Legacy 1.1.2 的 exe 是魔改老 Codename 引擎：`charts/` 字符串出现 **0 次**、`data/` 30 次——它是老 PE 结构（音乐在 song 根、谱面在 `songs/<歌>/data/normal.json`）。标准 NVE 的 `charts/`+`audio/` 结构、mod 的 `content/`+`meta.json`+`modsList.txt` 机制在这个引擎上都不生效。最终确定解：**不碰 mod 机制，把内容以纯新增文件装进引擎必读的 `assets/`**（新歌名 `double-kill-duo-{momo,miku}` 不顶原版），配独立 stage `cargo-duo-{momo,miku}.hx` 修掉原版 `cargo.hx` 里写死的 `changeIcon('double-kill'/'black'/'white')`。实现见 `scripts/build/deploy_into_assets.py`。

## 目录结构

```
scripts/nf/        NF 引擎的 Lua 机制脚本（DK_God/DK_Saw/DK_Death/BOTPLAY_Pro/DK_InputHUD 等）
scripts/legacy/    遗产版 stage 脚本（cargo-duo-momo/miku.hx，唱者路由 + 图标修复）
scripts/build/     全部构建 / 验证 / 修复脚本（109 个，含各版本演进）
docs/              模组原版 README 与说明
```

## 使用

各 zip 是完整的模组目录或安装说明包，按引擎放进对应位置：
- **NF / Kade / PE**：整目录放进 `mods/`，在 `modsList.txt` 启用。
- **遗产版 Legacy 1.1.2**：按 `DK_Duet_遗产版_assets直装` 包内的文件结构，把新增文件放进游戏的 `assets/`（不覆盖任何原版文件）。

详细历史说明见 `docs/mod_README_原文.txt`。

## 作者与致谢

作者 **DFJK117**。曲目原作者 Rareblin（Double Kill），Vs Impostor 原作者，Momo / Teto / Miku 声库原作者。本项目为个人非商业改造，仅供学习交流。

## License

MIT（本项目改造部分）；原曲与角色素材版权归各自原作者所有。
