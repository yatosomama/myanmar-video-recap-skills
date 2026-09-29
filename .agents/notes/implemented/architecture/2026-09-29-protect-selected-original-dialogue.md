# Agent Note: 将必留原声对白接入渲染门禁

Status: implemented

## Problem

创作规约要求每拍填写 `audio_owner` 并留住精彩原对白，但装配器只读取 `narration.json` 的旁白时间和 `original_subtitles.json` 的字幕文本，不消费视听板的声音归属。旁白若覆盖对白，默认混音会静音原片，成片仍可能成功发布而丢失预期的对白高光。不同 Agent 因而可能反复返工。

## Decision

标准 narration 工作流要求提供 output-time `original_subtitles.json`，其中每一条都是明确要让观众听见且可显示字幕的对白高光；无高光时写空数组。recap 在合成/配音前校验文件存在且为数组，并把 `--require-original-dialogue-plan` 传给装配器。装配器校验条目、片长边界、实际 TTS 落点和原声淡入保护时间；对白高光作为安全原声交接点，且会阻止 duck bridge 合并穿过这段对白。冲突报错包含条目和时间，修正计划后重跑同一 work_dir。

## Alternatives considered

- **继续只在 skill 提示词里要求 audio_owner** — 最强理由：无代码变动，对创作自由影响最小。否：渲染器无法消费视听板，遇到漏写或时间重叠时仍会静音对白并发布成片。
- **自动把所有字幕对白都设为必留** — 最强理由：无需 Agent 另选高光，所有源对白都有机会保留。否：源字幕包含大量普通台词，墙到墙原声会破坏解说节奏，且剪后重复或裁切字幕无法代表真正要保留的对白。

## Consequences

- **收益**：声音归属成为机器可验证的渲染前置条件；保留对白与旁白冲突时不再静默吞掉对白后交付。
- **收益**：缅甸语本地化规则在编排器目录内有独立副本，单独导入该 Skill 时不依赖另一个 Skill 的文件路径。
- **代价**：标准 narration 渲染多一个必需产物；无保留对白时也要显式写 `[]`。对白和旁白时间需要以成片 output timeline 校准；本地化参考副本需要随上游修订同步维护。

关联旁白默认静音原片的实现：[`2026-09-29-mute-source-under-myanmar-narration.md`](../../implemented/bug-fix/2026-09-29-mute-source-under-myanmar-narration.md)。
