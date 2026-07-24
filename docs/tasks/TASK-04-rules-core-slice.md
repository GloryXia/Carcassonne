# TASK-04：rules-core TypeScript 垂直切片

## 背景

项目第一个工程任务：建立 TypeScript 规则引擎（rules-core）的最小垂直切片。这是一个**受门禁任务**——项目文档明确规定，未经技术验证不得搭建工程骨架。

规则引擎设计见 `docs/RULE_ENGINE_TECHNICAL_DESIGN.md`（§17 定义了最小切片范围，动手前必读全文）；验收数据来自 `content/` 下的地块目录与场景测试（数据驱动，引擎不硬编码任何图案或计分数值）。

## 门禁（由 D-016 于 2026-07-24 调整）

项目负责人已明确：Node 版本不作为本任务门禁，大屏客户端允许 macOS。当前使用 Node.js 22 开发；Spike 0/3、Windows/WSL2 与跨平台黄金向量改为后续部署验证，不阻塞规则核心实现。依据见 D-016。

## 输入

- `docs/RULE_ENGINE_TECHNICAL_DESIGN.md`（§17 最小切片）
- `docs/TILE_TOPOLOGY_SPEC.md`、`content/schemas/tile-definition.schema.json`
- `content/tiles/base-current.json`（TASK-01 后为完整 72 块）
- `content/scenarios/*.json`（TASK-03 后为全量官方示例）
- `content/rulesets/base-current.json`（计分参数注入来源）

## 交付物

1. `packages/rules-core/`（或按架构文档约定的目录）：TypeScript 库，纯函数/无副作用风格，按 RULE_ENGINE_TECHNICAL_DESIGN 的模块划分实现最小切片：
   - 地块目录与规则集清单加载（JSON Schema 校验）
   - 放置合法性检查（边缘匹配、随从部署规则）
   - 特征完成检测（道路/城市/修道院）
   - 计分（含并列全分、盾徽、终局规则，参数全部来自 ruleset manifest）
2. 场景测试运行器：读取 `content/scenarios/*.json`，对每个场景执行 given→when→expect 断言，作为单元测试接入测试框架。
3. `package.json` / `tsconfig.json` / 测试脚本，`npm test` 一条命令跑全部。

## 验收标准

- `npm test` 全绿，其中场景测试覆盖 `content/scenarios/` 全部条目（TASK-03 完成前允许对引用未录入图案的场景 skip 并显式列出）。
- 引擎代码中**不出现**任何具体图案 ID、计分数字字面量（全部来自 content 数据）。
- 类型检查严格模式（strict）无错误。

## 依赖门禁

- 门禁：已由 D-016 解除；当前最低 Node.js 22。
- 数据依赖：TASK-01（完整目录）、TASK-03（全量场景）。种子场景已存在，可先行起步，但完成判定以全量为准。

## 约束

- 不引入架构文档之外的依赖；每个新依赖在回报中说明理由。
- 引擎 API 设计服从 RULE_ENGINE_TECHNICAL_DESIGN 的接口约定；有出入时记录，不擅自偏离。
- 本任务只到规则引擎切片：不做网络、持久化、UI。
