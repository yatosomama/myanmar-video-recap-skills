# Agent Note: 缅甸语旁白下保留原片背景声

Status: implemented

## Problem

字幕版 v6 的音轨只有一条 Edge TTS 缅甸语旁白。前一版为避免原剧配音和新旁白同时说话，把整条原片混合音轨都排除，结果旁白段落连音乐、环境声和音效也完全消失。用户指出旁白播放时没有原声。

## Decision

本次为该成片重新按 `edit_plan.json` 的入点和出点拼接 329 秒源音轨，并用 Demucs `htdemucs` 分为人声与非人声伴奏。依据 15 个旁白时间窗自动切换：旁白期间将原片混合音轨压到静音，只以 0.18 音量加入非人声 stem；旁白区间外以 0.70 音量恢复原片完整声音；每个旁白窗口边缘用 0.18 秒线性淡变。旁白保持原音量并通过 0.98 limiter 防削波。

成片：`E:\QC pass\September 2026\1.9.2026 QC pass\Myanmar recap - 090181 episodes 1-5\recap_090181_myanmar_episodes_1-5_v7.mp4`。Telegram 预览取输出时间 175 至 220 秒，压缩为 540×960、45 秒、3,312,837 字节，已成功发送（message ID 52）。完整成片与样片均已完整解码检查。

## Alternatives considered

- **旁白期间完全静音原片** — 最强理由：保证解说清晰，完全消除原片人声重叠。否：也会删掉用户指出缺失的配乐、环境声与音效。
- **旁白期间把原片混合音轨整体压低** — 最强理由：实现简单，能立即恢复背景氛围。否：原片对白仍会以较低音量与缅甸语旁白重叠，复现此前的混音投诉。

## Consequences

- **收益**：旁白下有原片背景氛围，停顿处能听见完整原声，同时不把原片对白直接混进旁白。
- **代价**：人声分离可能留下微弱人声残影或水声伪影；伴奏在旁白下固定为 0.18、间隙原片为 0.70，是针对这次素材的起始混音值，主观听感仍需用户试听确认。

关联先前的纯旁白选择：[`2026-09-27-myanmar-recap-profile.md`](../architecture/2026-09-27-myanmar-recap-profile.md)；字幕模糊与字幕时序：[`2026-09-27-burmese-narration-subtitles-and-source-blur.md`](2026-09-27-burmese-narration-subtitles-and-source-blur.md)。该混音修订仅针对本次交付，没有翻转 skill 的默认行为。
