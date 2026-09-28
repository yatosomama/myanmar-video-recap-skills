# Agent Note: 缅甸语解说字幕与片源字幕模糊

Status: implemented

## Problem

前五集合成版已有缅甸语解说音轨，但没有随解说显示的字幕。原片画面底部已烧录缅甸语对白字幕，不能作为单独字幕轨开关；直接在相同位置叠加解说字幕会互相遮挡，放在人物脸部附近又会影响剧情画面。

## Decision

本次导出采用单独的解说字幕时间轴：按标点和阅读宽度把旁白段落拆成短句，在原片开头起按句序逐段显示，使用 Myanmar Text 字体放在竖屏底部安全区。原片硬字幕所在画面带（1080×1920 画面的 y=1190 至 1460）使用高斯模糊（sigma=36）遮盖；不改动人物脸部及口型区域。成片音轨仅保留 Edge TTS 缅甸语旁白，不混入原片混合音轨。

导出文件：`E:\QC pass\September 2026\1.9.2026 QC pass\Myanmar recap - 090181 episodes 1-5\recap_090181_myanmar_episodes_1-5_v6.mp4`。45 秒压缩预览为 `090181_myanmar_subtitle_sample_v6_45s_540p.mp4`，已发送到用户指定的 Telegram 对话。ASS 时间轴 sidecar 为 `narration_my_v6.ass`。

## Alternatives considered

- **把解说字幕叠在原片硬字幕位置** — 最强理由：延续原片字幕视觉位置，观众阅读视线移动较少。否：两套文字会重叠，原片字幕无法独立关闭。
- **把解说字幕放在人物中部** — 最强理由：能避开底部烧录字幕并保留较多字幕空间。否：会遮住人物表情和口型；因此字幕放在画面下方，模糊只作用于原硬字幕带。

## Consequences

- **收益**：旁白文字与语音按时间逐句同步，原片硬字幕不再与解说字幕打架；人物脸和说话口型仍清楚可见；原片配音不会与新旁白混响。
- **代价**：模糊带覆盖字幕背景所在的整条窄区域，画面下方背景细节会一起变软；硬字幕是画面像素，不能在不影响其背后画面的情况下单独移除；解说字幕已烧录进 MP4，修改时需重渲染。

参考：[`2026-09-27-myanmar-recap-v4-double-tempo.md`](../bug-fix/2026-09-27-myanmar-recap-v4-double-tempo.md)、[`2026-09-27-myanmar-recap-profile.md`](../architecture/2026-09-27-myanmar-recap-profile.md)。
