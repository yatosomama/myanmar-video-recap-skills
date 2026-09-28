# Agent Note: 多模态视觉模型配置兼容层

## Problem

缅甸语独立版的面向用户说明仍把视频理解绑定到单一模型品牌，运行配置也只识别该供应商的密钥、模型名和 `api-key` 请求头。仅改 README 会让用户误以为任意多模态模型可直接接入，实际却无法配置。

## Decision

逐场景图像理解支持通用 OpenAI-compatible Chat Completions 配置：`MULTIMODAL_API_URL`、`MULTIMODAL_API_KEY`、`MULTIMODAL_MODEL`。通用配置使用标准 Bearer 认证和图像 `image_url` 格式，不注入供应商专有 thinking 参数；旧 MiMo 环境变量仍作为向后兼容回退。README 和技能入口说明兼容性要求；提供可信字幕时可通过 `--skip-asr` 跳过转写。专用整段视频接口、ASR 和 TTS 继续使用各自的 provider 适配器。

## Alternatives considered

- **只在 README 把品牌名替换成“多模态模型”** — 最强理由是改动小、立即满足对外定位；但运行时仍会把请求发到固定供应商，承诺不实，因此同时添加通用配置和请求格式。
- **把每家模型 API 都做成独立适配器** — 最强理由是能覆盖更多原生协议；但本次没有足够的供应商清单与账户/请求样例，先提供常见的 OpenAI-compatible 视觉接口契约。

## Consequences

- **收益**：使用 OpenAI-compatible vision endpoint 的托管或本地模型可驱动逐帧分析；旧配置继续兼容；显式中文字幕工作流可跳过 ASR。
- **代价**：原生协议不兼容的多模态模型不能只靠模型名直接接入；用户仍需配置可访问的视觉 API。没有字幕时，ASR 仍需要支持的 ASR provider。整段视频 URL 的专用模式、TTS provider 标识和历史产物名不在本次重命名范围内。

## Follow-up

此笔记记录的 API 配置解决的是独立 CLI 后端。Agent 调用 skill 时改为默认使用宿主内置视觉能力，见 [Agent-native multimodal skill runtime](2026-09-28-agent-native-multimodal-skill-runtime.md)。
