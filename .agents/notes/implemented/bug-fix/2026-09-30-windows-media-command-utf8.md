## Problem

本次回归中，FFmpeg 实际 loudnorm 测量在中文工作目录失败：子进程读取线程用系统 GBK 解码 UTF-8 日志，抛 UnicodeDecodeError，stderr 成为 None，后续解析触发 TypeError。剪辑预检也有同样警告。各阶段的独立 run_cmd 副本默认依赖系统编码，缅甸语/中文路径增加复现概率。

配置使用检查同时发现写稿的 api_url_source、multimodal_api_configured 和理解的 multimodal_api_configured 无读取者；只有编排器实际使用这些诊断字段。

## Decision

四个拥有 run_cmd 的媒体阶段显式默认 UTF-8、errors=replace，并保留调用方的编码覆盖。剪辑与合成的 FFmpeg 选项支持探测采用同样解码设置。子进程失败仍由 returncode 判断；非 UTF-8 诊断字节可替换，不改变媒体内容。测试包含真实 UTF-8/非法字节 stderr、显式覆盖和实际 FFmpeg 测量。两个阶段移除三个未使用的诊断字段，保留编排器的有效诊断。

## Alternatives considered

- **只在测试中设 PYTHONUTF8**：最强理由是最少代码就能让本机通过。不用：WorkBuddy 和其他 Agent 仍受系统编码影响，不能修复实际执行路径。
- **统一要求用户更改 Windows 系统语言**：最强理由是全环境一次生效。不用：Skill 应能在已有中文环境处理媒体，不应把本地执行错误转嫁给用户。

## Consequences

收益：中文/缅甸语路径的媒体诊断不会因 GBK 解码崩溃，音量测量可正常完成；未使用配置不再造成假配置表面。代价：第三方命令的非 UTF-8 日志会有替换字符，需要时调用方显式指定编码；外部代码若读取移除的未公开诊断字段需改读编排器。

## Validation

四个阶段各执行三项真实子进程测试（UTF-8 中缅文字、非法诊断字节、显式编码覆盖、非零退出），共 12 passed。真实 FFmpeg loudnorm 测量回归通过，剪辑用例不再出现 GBK 读取线程异常；配置使用检查与写稿全组回归通过。剪辑 CLI 测试显式设置子 Python 的 PYTHONUTF8，保证输出与捕获声明一致；符号链接测试仅在 Windows error 1314 时说明原因并跳过。
