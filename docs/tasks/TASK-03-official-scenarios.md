# TASK-03：官方示例全量场景转写

## 背景

规则引擎的验收测试采用数据驱动：把官方规则书的每个印刷示例转写成 given/when/expect 场景 JSON，引擎必须全部跑绿。种子文件 `content/scenarios/base-current-official-examples.json` 已有 5 条（8 分完成城、3 分完成路、9 分修道院、并列全分、终局未完成城），但只是子集，且 official-example 条目缺页码。

## 输入

- Schema：`content/schemas/scenario.schema.json`
- 种子场景：`content/scenarios/base-current-official-examples.json`
- 完整地块目录（依赖 TASK-01 完成后的 `content/tiles/base-current.json`）
- 官方来源：Z-Man 基础规则书 PDF + 农夫/河流/修道院长补充规则 PDF（README「规则资料基线」有链接）

## 交付物

1. 扩充 `content/scenarios/base-current-official-examples.json`（必要时可拆分为多个场景目录文件）：覆盖规则书与补充规则中**每一个**计分、放置、随从部署示例，包括但不限于：
   - 道路、城市（含盾徽）、修道院各计分示例；
   - 农夫/田野计分示例（当前种子完全缺失，优先级最高）；
   - 部署合法性示例（不可放置随从的已占用特征等）；
   - 终局计分示例；
   - 修道院长召回计分示例（补充规则）。
2. 每条场景补全 `sourceReference.page`（消除现有的缺页码警告）。
3. 转写笔记：每个示例的原始页码、图示布局与你坐标系转写的对应关系，附在场景文件同目录的 `TRANSCRIPTION_NOTES.md`，供复核者对照。

## 验收标准

- `python tools/content-validator/validate_content.py` 通过，且无 official-example 缺页码警告、无未录入图案警告（即场景引用的图案必须在 TASK-01 后的完整目录中）。
- 每个场景盘面通过邻接合法性校验（校验器已自动执行）。
- 场景坐标系：x 向东、y 向北；rotation 顺时针 0/90/180/270。转写时以规则书图示朝向为 rotation=0 的参考，允许整体旋转，但必须自洽。
- 农夫场景至少 3 条（含一条一田多城、一条被道路/城市分割的田野）。

## 依赖门禁

- **依赖 TASK-01**（场景引用的图案必须已录入，否则只能停留在警告状态）。

## 约束

- 数值必须来自规则书印刷示例原文；推导型场景（kind=derived）单独标注并在笔记中写明推导链条。
- 原约束要求不修改 Schema 与校验器；执行中确认部署拒绝与修道院长召回无法表达。经项目负责人要求继续完成 TASK-03 后，已作最小契约演进，新增 `place-piece`、`reclaim-abbot` 及对应结果断言，变更理由与兼容边界记录在 `TRANSCRIPTION_NOTES.md`。
