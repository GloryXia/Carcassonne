# TASK-02：河流 12 块编码扩展与录入

## 背景

当前规则盒（C3 口径基础盒）内含河流模块：12 块河流地块用于替代标准起始块开局。`content/rulesets/base-current.json` 已声明引用 `content/tiles/river-current.json`（contributesTiles=12），但该文件尚不存在，交叉校验器因此产生一条警告。

河流与基础地块的差异：引入了第四种边缘地貌 **river（河流）**，且有特殊放置约束（河流不得直接回折 / U 型急转；源头开局、湖泊收尾）。这些约束当前 Schema 与拓扑规范都未覆盖。

## 输入

- `docs/TILE_TOPOLOGY_SPEC.md`（现有三段式编码）
- `content/schemas/tile-definition.schema.json`、`content/schemas/ruleset-manifest.schema.json`
- `tools/content-validator/validate_tiles.py`（聚合边缘统计目前只认 field/road/city）
- 官方来源：Z-Man 农夫/河流/修道院长补充规则 PDF（README「规则资料基线」有链接）；Wikicarpedia 河流图案表（人工查阅）

## 交付物

1. `docs/TILE_TOPOLOGY_SPEC.md` 扩展章节：river 边缘地貌的编码方式（建议复用三段式，river 端口占 center，与 road 类似）、河流专用标记（`riverSource` / `riverLake` 或 placementTags）、U 型回折禁止的形式化表达。**这是对规范的受控演进，需在章节内注明版本变更。**
2. `content/schemas/tile-definition.schema.json` 相应扩展（featureType 增加 river 等）。
3. `content/tiles/river-current.json`：12 块完整录入，`verificationStatus=已录入`，带来源。
4. `tools/content-validator/validate_tiles.py` 扩展：识别 river 地貌、河流目录的边缘统计口径（河流盒独立统计，不并入基础盒 288 边校验值）。
5. `tools/content-validator/validate_content.py` 无需改动的，说明理由；需要改动的，一并改。

## 验收标准

- `python tools/content-validator/validate_tiles.py content/tiles/river-current.json` 通过（河流目录的完整性断言方式由你在工具中定义，并在任务回报中说明）。
- `python tools/content-validator/validate_tiles.py content/tiles/base-current.json --expect-complete` 不受影响，仍全绿。
- `python tools/content-validator/validate_content.py` 中 river-current.json 缺失警告消失。
- 河流 12 块的图案与官方补充规则组件表一致（源头 1、湖泊 1、其余 10）。

## 依赖门禁

建议 TASK-01 完成后开始（共享 Schema/校验器演进避免冲突），但不强制。

## 约束

- 规范扩展保持向后兼容：已有 8 种基础图案的 JSON 不得因此失效。
- U 型回折禁止属于**放置规则**，本任务只需在数据层表达足够信息（如弯道方向标签），放置校验逻辑属于 TASK-04 规则引擎范围。
- 严禁凭记忆编造 12 块图案；逐块对照官方来源。
