# Agent Note: 缅甸语旁白未讲完时原片声音提前恢复

Status: implemented

## Problem

上一轮 v8 混音接入较慢的 15 段旁白整轨，但原片音量恢复时刻沿用了原生 +25% 快版的字幕时长。首段慢版语音时长 15.408 秒，快版窗口只有 11.376 秒，所以源对白在旁白尾音前恢复。

## Decision

本次复用此前的 Edge TTS `my-MM-ThihaNeural` 原生 +25% 分段音频。旁白每段按实际 WAV 文件长度与段落输出起点放置，旁白窗口在文件结束后延迟 0.25 秒恢复完整源音轨；窗口前后保留 0.05/0.25 秒保护区。旁白下只混入 Demucs 非人声伴奏，空隙处恢复原片音轨。未叠加 `atempo`；所有旁白只做 1.03 倍轻微升调和 +5 dB 增益，再由 0.95 limiter 限峰。缅甸语参考文档要求源音轨交接跟随变速及音高处理后的实际 WAV 长度，不能用字幕 cue 截止时间代替。

完整 v9 为 329 秒 1080×1920；480p 压缩版为 16,239,364 bytes。两份输出均完整解码通过；抽查首段尾音（约 10.8 秒）与首段结束后的原声空隙（约 12 秒），字幕仍在模糊带中央，源声音恢复晚于旁白文件末尾。

文件：
- `E:\QC pass\September 2026\1.9.2026 QC pass\Myanmar recap - 090181 episodes 1-5\recap_090181_myanmar_episodes_1-5_v9.mp4`
- `E:\QC pass\September 2026\1.9.2026 QC pass\Myanmar recap - 090181 episodes 1-5\090181_myanmar_episodes_1-5_v9_480p.mp4`

## Alternatives considered

- **继续使用慢版并把所有源声恢复点统一延后** — 最强理由：不需更换现有语音文件。否：静态延长无法对应不同片段的实际语音长度，也不符合用户喜欢的前次较快试听。
- **在原生 +25% 上再加 atempo 提速** — 最强理由：旁白会更短，给原片留更多空间。否：历史记录确认二次 atempo 会使旁白听起来发硬，因此沿用已试听认可的原生速度。
- **用字幕 cue 结束时间控制 ducking** — 最强理由：字幕时间轴现成且容易取得。否：字号拆句、字幕时长和 TTS 实际尾音不总是同一时钟，已经造成过早恢复；本次直接读取每段最终音频长度。

## Consequences

- **收益**：完整源对白不会在旁白尾音前抢入；原生快版 voice 与既有字幕时钟一致；轻微升调不会改变段落时长；所有段落仍保留配乐/环境声与间隙原声。
- **代价**：音高变化虽小仍是主观听感选择，需用户设备试听确认；分段 TTS 再生成或重新变速后必须重新计算所有交接点。Telegram 在先前交付尝试中连接超时，本次成片保存在本地。

关联防止双重变速的既有决定：[`2026-09-27-myanmar-recap-v4-double-tempo.md`](2026-09-27-myanmar-recap-v4-double-tempo.md)，背景声交接配置：[`2026-09-28-myanmar-recap-original-bed-under-narration.md`](../feature/2026-09-28-myanmar-recap-original-bed-under-narration.md)。
