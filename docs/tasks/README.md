# 任务文档索引

本目录存放可交付给独立开发 agent 执行的任务文档。每个任务自包含：背景、输入、交付物、验收标准、依赖门禁与约束。

## 任务一览

| 任务 | 标题 | 类型 | 依赖 | 门禁 |
|------|------|------|------|------|
| [TASK-01](TASK-01-base-tile-transcription.md) | 基础盒剩余 16 种图案录入 | 内容数据 | 无 | 无 |
| [TASK-02](TASK-02-river-tiles.md) | 河流 12 块编码扩展与录入 | 内容数据 + 规范扩展 | TASK-01（建议，不强制） | 无 |
| [TASK-03](TASK-03-official-scenarios.md) | 官方示例全量场景转写 | 内容数据 | TASK-01 | 无 |
| [TASK-04](TASK-04-rules-core-slice.md) | rules-core TypeScript 垂直切片 | 工程开发 | TASK-01、TASK-03（种子场景即可起步） | **Spike 0/3 通过 + Node 24 环境** |
| [TASK-05](TASK-05-protocol-contracts.md) | 局域网协议契约包草案 | 工程开发 | 无 | 无 |
| [TASK-06](TASK-06-validator-diff-mode.md) | 校验器双人复核 diff 模式 | 工具开发 | 无 | 无 |

## 当前交付状态（2026-07-24）

- TASK-01：已录入 24 种、72 块基础地块，完整性校验通过。
- TASK-02：已录入 10 种、12 块河流地块，完整性校验通过。
- TASK-03：已录入 17 个计分、部署与修道院长场景；官方页码齐全，Schema 表达缺口已补齐，交叉校验通过。
- TASK-04：已完成 TypeScript 规则核心垂直切片；17 个内容场景、严格类型检查与 10,000 次确定性重放测试通过。原平台门禁已由 D-016 调整。
- TASK-05：契约 Schema、fixtures 和离线校验器已交付，待协议评审。
- TASK-06：地块语义 diff、复核工作流和构造性测试已交付。

## 依赖图

```
TASK-01 ──→ TASK-03 ──→ TASK-04（场景测试驱动规则引擎验收）
   │                        ↑
TASK-02 ─────────────────────┘（河流并入目录后引擎需支持）
TASK-06 ──→ 支撑 TASK-01/02/03 的"已复核"升级流程
TASK-05（独立，与规则工作并行）
```

## 执行 agent 通用约束

1. **工作区**：所有操作在仓库根目录 `/Users/xiachao/Desktop/developer/code/Carcassonne` 内进行；目标开发环境是 Windows + WSL2 + Node 24，内容/工具类任务在本机完成即可，工程类任务注意门禁。
2. **数据诚实**：任何地块图案、数量、规则数值必须有明确来源（官方规则书 / 官方组件表 / 已核验的社区统计），**严禁凭记忆补全**。来源写入 `sourceReference`。
3. **验证纪律**：修改 `content/` 后必须运行：
   - `python tools/content-validator/validate_tiles.py content/tiles/base-current.json`（地块目录）
   - `python tools/content-validator/validate_content.py`（交叉引用与场景合法性）
   - 完整盒校验：`python tools/content-validator/validate_tiles.py content/tiles/base-current.json --expect-complete`
4. **verificationStatus 四级**：`待录入 → 已录入 → 已复核 → 已测试`。录入者只能标"已录入"；"已复核"需第二人独立复核（见 TASK-06）；"已测试"需引擎场景测试通过。
5. **不擅自修改**：`docs/DECISIONS.md`、`docs/TECHNICAL_SPIKES.md` 的门禁结论、`docs/TILE_TOPOLOGY_SPEC.md` 的编码规则。发现矛盾时记录在任务回报中，由项目负责人裁决。
6. **语言**：文档与提交信息使用中文；标识符、字段名使用英文。
7. **拓扑编码**：地块图案一律按 `docs/TILE_TOPOLOGY_SPEC.md` 的三段式边缘区带编码，Schema 见 `content/schemas/tile-definition.schema.json`。

双人复核的具体操作见 [`tools/content-validator/REVIEW_WORKFLOW.md`](../../tools/content-validator/REVIEW_WORKFLOW.md)。
