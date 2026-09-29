---
name: video-understanding
user-invocable: false
description: >
 把视频分析为结构化理解索引：场景检测、ASR 转写、逐场景 VLM 观察、静音窗口、融合时间线和写作 brief。
 用于理解、索引或总结视频，也作为后续创作前的分析阶段。输入视频文件；输出 scenes.json、
 asr_result.json、vlm_analysis.json、silence_periods.json、timeline_fusion.json、agent_narration_brief.md。
 触发词：视频理解、视频分析、视频索引、video understanding、analyze video、看懂视频。
---

## 1. 定位

本技能把源视频转成 Agent 与下游阶段可读取的理解索引。它的创作角色是**素材观察员 / 场记**，不是导演：

- 先观察，再解释；事实与推断分开。
- 除了“发生了什么”，还要让下游看见知识、权力、目标、关系或情绪在哪一刻变化。
- 标出由谁的 POV 承载变化、哪个反应或表演不可替代，以及哪里存在完整台词/动作的自然剪辑边界。
- 证据不足时保留不确定性，不制造戏剧结论。

## 2. 处理阶段

以下是完整结构化 CLI 流程及输出契约；Agent-native 的默认快速档只生成上一节列出的最小交接产物，避免重复产出完整 sidecar。

1. **场景检测**：写 `scenes.json`，包含切点、时长和废片段过滤结果。
2. **抽帧**：为视觉分析提取代表帧。
3. **ASR（可选）**：通过已配置的 ASR provider 写粗分段对白 `asr_result.json`，并写
   `asr_timing_evidence.json` 说明可用性、有限时间精度与文本修正来源。
4. **静音检测**：写 `silence_periods.json`，标注安静窗口与 `has_speech`。
5. **VLM 观察**：写 `vlm_analysis.json`，包含场景描述、深层分析和 `frame_facts`。
6. **时间线融合与创作 brief**：写 `timeline_fusion.json`、`asr_writing_chunks.json` 和 `agent_narration_brief.md`。

各阶段只有在输出产物与 provenance sidecar 同时匹配当前视频及影响结果的设置时才会复用；`--force` 强制重算。

## 3. 环境要求

**由 Agent 调用本技能时，默认使用当前宿主自己的多模态视觉能力理解视频或抽取帧，不要求用户配置模型 API。** 读取并使用用户提供的中文字幕；字幕支持剧情/对白判断，但动作、人物出入和剪点必须用画面核实。只有用户要求独立 CLI/自动化运行，或宿主没有视觉能力时，才走可配置视觉 API 后端；该后端需支持 OpenAI-compatible Chat Completions `image_url` 输入，旧 `MIMO_API_KEY` / `MIMO_API_URL` 配置仍兼容。CLI 提供可信字幕时用 `--skip-asr` 跳过转写；需要识别无字幕对白时，另行配置 ASR provider。`--mimo-video-overview` 是保留旧名的专用整段视频 API 选项。

### Agent-native 快速档

多集短剧默认先按字幕时间戳粗筛剧情候选，不给每个场景都写单独长描述。先批量读各集字幕、时长和已有场景切点；将每集候选画面缩成联系表一次浏览，重点围绕转折、爆点、人物首次出现、关键动作和结尾悬念。只有准备选入成片的候选段及其两侧接点才回看连续画面/原声。快速档的理解交接只需 `source_subtitle_notes.md` + 一份带时间证据的 `agent_narration_brief.md` + 候选段联系表；用户要求完整机器索引、长片调查或脚本 CLI 时，再生成 §5 全部索引文件。

不可以因为画面稀疏而凭字幕臆造动作，也不能让粗筛删掉承载表演的留白。字幕与画面冲突、关键动作发生在采样间隙、字幕时间戳不可靠时，只对相应时间窗加密抽帧或播放原段；不要全片提高采样率。

### Agent-native 完整索引模式

用户要求完整机器索引时，读取全部中文字幕并实际检查视频。宿主可直接读视频时按时间线观察；否则先用 ffmpeg 检测场景并抽取代表帧，再用宿主的图像理解能力分析。输出本技能 §5 所列的理解文件，字幕作为对白/剧情依据，画面帧作为动作/表演/人物位置依据；将画面事实和剧情推断分开记录。整个流程不需要 `MULTIMODAL_API_*` 或 ASR API。

### 独立 CLI / 自动化模式

脚本化理解才需要配置视觉 API：

```bash
# ffmpeg: brew install ffmpeg | apt install ffmpeg | choco install ffmpeg
export MULTIMODAL_API_URL=https://api.openai.com/v1
export MULTIMODAL_API_KEY=your-api-key  # 本地免密服务可省略
export MULTIMODAL_MODEL=your-vision-model
```

该 endpoint 需支持 OpenAI-compatible Chat Completions `image_url` 输入；旧 `MIMO_API_KEY` / `MIMO_API_URL` 仍兼容。CLI 提供可信字幕时用 `--skip-asr` 跳过转写；需要识别无字幕对白时，另行配置 ASR provider。`--mimo-video-overview` 是保留旧名的专用整段视频 API 选项。

若 `work_dir/background_research.json` 存在，本技能会把剧情梗概和角色名折入 VLM 上下文；`--context` 可补充一条简短提示。

下面的 `scripts/...` 均相对于本技能目录。若执行器从仓库根目录启动，请给脚本路径加上本技能的绝对目录。

## 4. 运行命令

以下命令仅用于独立 CLI / 自动化运行。Agent-native 模式按上文理解步骤直接产出索引，不调用此 CLI 视觉 API。

```bash
python3 scripts/understand.py <video> --work-dir <work_dir> \
  [--context "节目名/角色名"] [--scene-threshold 0.1] [--skip-asr] [--mimo-video-overview] [--force]
```

## 5. 输出契约

| 文件 | 内容 |
|------|------|
| `scenes.json` | 场景切点、起止时间与时长 |
| `asr_result.json` | `[{start, end, text}]` 时间戳对白 |
| `asr_timing_evidence.json` | ASR 可用性状态、粗窗口精度、glossary 前后文本，以及它所描述的源视频/音频/结果文件（路径存在性 + size/mtime） |
| `vlm_analysis.json` | 逐场景描述、深层分析与 `frame_facts` |
| `silence_periods.json` | `[{start, end, duration, has_speech}]` 安静窗口 |
| `timeline_fusion.json` | VLM、ASR 与静音信息的统一时间线 |
| `asr_writing_chunks.json` | 按句界和场景切分的 ASR 写作块 |
| `agent_narration_brief.md` | Agent 首先阅读的创作简报 |

后续写作阶段根据创作简报与索引制定方案并写 `narration.json`。

## 6. 参考资料

- 背景调研：`references/research-guide.md`，产出 `background_research.json`。
- JSON 结构：`references/data-schema.md`。

## 7. 能力边界

- 不写解说词，也不做解说评分；只负责生成理解索引与创作简报。
- 不编造信号无法支持的剧情；当 ASR / VLM 过薄时输出素材警告。
- ASR 的 `start/end` 是固定分片形成的**粗窗口**，不是词级对齐；空文本只表示原因未知，
  不能当作已证实静音。`asr_timing_evidence.json` 的状态字段见 `references/data-schema.md`。
