## Problem

字幕驱动快速路径已经限制重复分析并保护声音、字幕与完整句界，但开头和结尾的编辑意图仍主要是文字说明。必保源区间即使出现在成片中间也会通过，无法发现开头被铺垫挤走、结尾兑现后留下长尾的问题。不同题材套同一个反转模板也可能提前泄露答案或破坏人物情绪。

相关决定见 `../../implemented/simplification/2026-09-29-fast-path-with-editorial-gates.md`；本次延续紧凑编辑板，不新增模型轮次或独立策划文件。

## Decision

在写稿快速路径加入一份短模式指南：根据真实素材在冲突、身份/信息揭示、情感抉择、顺叙压缩之间选择，比较最多三个有源时间证据的开头，只落地一个方案。选择钩子、理解所需前提和本片兑现，避免关键词评分、假悬念、强制台词比例与固定切镜频率。

扩展现有 `clip_plan.json.required_evidence` 的可选 `opening` / `closing` 声明，引用已声明节点并分别给出最大开头铺垫/结尾余量。执行器在全部剪点吸附之后核对完整节点的实际输出位置，在预检与缓存复用前阻断错位。字段缺省沿用旧行为；不增加 API 或额外媒体扫描。选段校验不声称验证内容语义、混音或传播效果。

## Alternatives considered

- **统一高冲突倒叙、每几秒强制切镜**：最强理由是新 Agent 容易照模板快速执行。不用：情绪戏和信息揭示需要不同节奏，强制切镜会破坏反应、完整对白和因果。
- **只补文字指南**：最强理由是契约不变、改动最小。不用：计划宣称有开头钩子不代表实际剪点吸附与时长裁减后仍在开头。
- **增加一套评分器及多轮模型选优**：最强理由是能批量比较大量方案。不用：没有真实观看数据时分数容易被误当传播预测，并加重新 Agent 的耗时；现有编辑板与源区间校验足以承载本次改动。

## Consequences

收益：Agent 更容易按素材选结构；开头与结尾承诺绑定真实输出位置；复用现有 QC 且旧计划兼容。代价：边界余量需要结合完整表演设定，错误声明会要求重新选段；语义吸引力和观众表现仍需实际观看与发布数据确认。

## Validation

本次运行互相隔离的 pytest 进程，570 个不同用例通过，1 个符号链接用例因 Windows 缺少权限跳过；没有将此结果称为全仓库测试通过。

- `tests/cut/{test_narrative_selection,test_required_evidence_cli,test_pure_cut}.py`：149 passed、1 skipped。真实 FFmpeg 生成源文件并剪辑/解码；测得开头与结尾余量均 0.25 秒，收紧开头要求后缓存复用前阻断，旧媒体和修改时间保持不变。完整/局部副本、连续跨 clip、多源、错误引用、布尔/NaN/负数余量均覆盖。
- `tests/orchestrator/{test_creative_skill_contract,test_audio_routing,test_audio_policy_parity,test_media_command_encoding}.py`：85 passed。
- `tests/assemble/{test_pure_assemble,test_timeline}.py`：168 passed。
- `tests/voiceover/test_pure_voiceover.py`：46 passed。
- `tests/script`：117 passed。
- `tests/orchestrator/test_plugin_manifest.py`：5 passed（与已计入的 18 个 creative contract 用例一起再跑，输出 23 passed）。
- 受改动 Python 文件 compileall 和 git diff --check 通过。

测试源文件是生成的合成素材，不代表对新一部真实短剧的完整观看、缅甸语母语审稿或平台传播验证。模式是 Agent 创作策略；执行器只验证声明的源区间、位置和技术约束。
