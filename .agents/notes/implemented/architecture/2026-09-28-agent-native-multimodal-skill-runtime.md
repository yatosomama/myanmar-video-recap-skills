## Problem

当前文档把通用视觉 API 的环境变量写成视频解说运行的前置条件。用户期望安装 skill 后，由宿主智能体直接调用自身可用的多模态能力理解视频和中文字幕，不额外配置模型服务商 API。

## Decision

Agent-native 运行模式是 skill 的默认入口：宿主多模态能力负责看视频或抽帧、结合 SRT 理解剧情并生成创作产物；后续剪辑/配音/合成由本仓库工具完成。`MULTIMODAL_*` 接口只用于独立 CLI / 自动化视觉分析，宿主完全不具备视频或图像输入能力时才提示此后端。此决定后续于 [2026-09-28 provider-agnostic VLM](2026-09-28-provider-agnostic-multimodal-vlm.md) 的 CLI 配置方案上作了默认入口调整；CLI provider 支持仍保留。

## Alternatives considered

- **要求所有宿主配置兼容 API** — 最强理由：脚本能自动化运行完整视觉分析且便于断点续跑。否决：这与用户希望 skill 直接使用宿主模型的调用方式相冲突，也会让无需外部 API 的 Agent 多一步凭证配置。

## Consequences

- **收益**：直接使用 skill 的 Agent 无需额外配置视觉模型 API；沿用其内置多模态能力和用户提供的 SRT。
- **代价**：不同宿主暴露的视频/图片能力不同；没有可视输入能力的宿主仍需配置可选兼容 API。脚本独立 CLI 自动理解路径仍需一个可访问的多模态 API。
