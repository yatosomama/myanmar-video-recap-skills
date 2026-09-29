# Agent Note: 缅甸语字幕与旁白同步及片源字幕模糊

Status: implemented

## Problem

旁白字幕由文本字符数平均分配到整段 TTS 音频；这会忽略句间停顿、缅甸语组合字符和 TTS 尾部静音，导致声音结束后字幕还残留或字幕换行跟不上实际语速。片源字幕遮罩当前实现为半透明黑色 drawbox，并非旧样片记录的高斯模糊；因此原中文字幕可能仍透出，也没有机器门禁检查遮罩和解说字幕的呈现范围。

## Decision

Edge TTS 生成音频时同时保存它返回的逐词 WordBoundary 时间，旁白字幕把连续词边界匹配回原始缅甸语句子，再在句内拆成可读字幕行；其他 TTS 和边界不完整时保留显式估算回退，记录 timing source 供 QC 识别。缅甸语分句识别 `၊` / `။`，时长权重忽略组合标记。将原片字幕遮罩默认实现为可配置 sigma 的局部 `gblur`，只作用于测量带和旁白窗口，继续让原声对白窗口显示原片。视觉 QC 与文档明确记录真实滤镜、模糊带、字幕时间依据；目标素材在有字幕时必须明确测量带，不让 Agent 猜坐标。

Edge TTS 使用同一 Python 环境中的 `edge-tts` 包生成音频与逐词 sidecar，并在 `tts_meta.json` 记录声线。Edge 边界缺失、文本对齐失败或字幕行需要估算时，`visual_qc.json` 会阻断交付。测得字幕带的 Y 坐标通过合成器显式提供后才启用遮罩；QC 同时记录 `gblur`、遮罩区域和 sigma。

## Alternatives considered

- **继续按文字长度均分** — 最强理由：与 TTS provider 无关，快且不需要新工具。否：不能利用 Edge TTS 已提供的逐词时间，且标点停顿和尾静音会持续造成可见漂移。
- **把整段旁白当成一条字幕** — 最强理由：字幕结束可直接跟随音频段结束，不需要估算行内时间。否：长段会成为过长、多行的文字块，阅读节奏差。
- **在 `-vf` 中直接添加 `gblur`** — 最强理由：改动小且能调用 Gaussian blur。否：会模糊整帧画面，无法只处理字幕条带。

## Consequences

- **收益**：Edge TTS 默认路线的句子字幕结束点使用合成服务词级时间；缅甸语拆行遵守本地标点；中文字幕只在旁白窗口局部高斯模糊，原声对白窗口保留原画与原字幕。
- **代价**：Edge TTS 增加一份轻量边界 sidecar，旧缓存需要重新合成一次；非 Edge provider 仍会使用标注为估算的回退时间。局部模糊需要一次 split/crop/overlay 视频滤镜图，渲染成本略增。

关联已记录的样片字幕与遮罩目标：[`2026-09-27-burmese-narration-subtitles-and-source-blur.md`](../feature/2026-09-27-burmese-narration-subtitles-and-source-blur.md)。
