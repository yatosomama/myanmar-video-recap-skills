## Problem

中英文 README 的实际安装命令仍指向上游 zenstory-ai/video-recap-skills，插件元数据仍描述中文解说和固定 MiMo。新 Agent 按说明安装会得到原版，而不是当前改好的缅甸语版本。

## Decision

两份 README 的安装、克隆和维护入口指向已存在的公开仓库 yatosomama/myanmar-video-recap-skills。插件元数据说明 Agent 多模态、中文字幕、Burmese Edge TTS 和适应剧情的模式；保留已用插件/marketplace 名称以及原作者归属，版本更新到 0.6.1。历史 issue 和原项目致谢继续链接上游；安装路径测试核对此改版地址。

## Alternatives considered

- **保留上游安装命令并只说明这是改版**：最强理由是保持原文与上游同步。不用：说明不能改变实际安装来源，会丢失用户需要的缅甸语行为。

## Consequences

收益：新 Agent 获得已修改的版本，插件介绍与行为一致。代价：此前安装原版的用户需更换来源，不能只刷新原版仓库。

## Validation

5 个插件清单/安装说明测试通过，检查清单字段、版本与 CHANGELOG 一致、改版 homepage、Burmese Edge TTS 描述以及中英文安装地址。未调用宿主执行实际插件安装，不能以清单测试代替 WorkBuddy 的实际导入测试。
