# TASK-01：基础盒剩余 16 种图案录入

## 背景

规则与数据基础设施已就位（`docs/TILE_TOPOLOGY_SPEC.md`、`content/schemas/tile-definition.schema.json`、`tools/content-validator/validate_tiles.py`）。基础盒 72 块共 24 种图案（含起始块），当前 `content/tiles/base-current.json` 已录入 8 种 37 块作为格式范例，**剩余 16 种 35 块待录入**。

已录入的 8 种（可直接对照学习格式）：
monastery×4、monastery-road×2、road-straight×8、road-curve×9、road-t×4、road-x×1、city-cap×5、city-cap-road-straight×3+1（起始块）。

## 输入

- 编码规范：`docs/TILE_TOPOLOGY_SPEC.md`（三段式边缘区带、段/端口/中心特征/meepleZones、§9 七条不变量）
- Schema：`content/schemas/tile-definition.schema.json`
- 范例：`content/tiles/base-current.json`
- 图案来源（按优先级）：
  1. Z-Man 官方规则书组件页（README「规则资料基线」有链接）
  2. Wikicarpedia 基础盒图案总表（注意：站点有反爬，建议人工查阅后转写，不要爬虫）
  3. 任何社区来源必须与官方组件表交叉一致才可采用，并记入 `sourceReference`

## 交付物

1. 更新后的 `content/tiles/base-current.json`：24 种图案、72 块完整。
2. 每个新图案的 `verificationStatus` 标 `已录入`，`sourceReference` 指向实际使用的来源。
3. 录入说明：追加到 `docs/TILE_TOPOLOGY_SPEC.md` §11（哪些来源用于转写、有无歧义图案及取舍）。

## 验收标准（全部必须满足）

```bash
python tools/content-validator/validate_tiles.py content/tiles/base-current.json --expect-complete
# 必须输出：地块 72 块；田野 115 / 道路 94 / 城市 79；校验通过。
python tools/content-validator/validate_content.py
# city-tunnel-pennant 相关警告必须消失（场景依赖它）
```

- `base-current.city-tunnel-pennant`（N、S 双边城市 + 盾徽，CFCF 布局）必须录入——3 条种子场景引用它。
- 整盒边缘校验值（田野 115 / 道路 94 / 城市 79，每边单一地貌口径）是 russcon 社区对 C1 基础盒的统计，已核验可信；若转写结果与之不符，**优先怀疑转写错误**，逐图案复查后再怀疑校验值。
- 起始块唯一（startTileCopies=1，仅 city-cap-road-straight）。

## 依赖门禁

无。可在本机直接执行。

## 约束

- 严禁凭记忆编造图案分布；每种图案必须来自上述来源之一的实际查阅。
- 不修改 Schema、校验器、拓扑规范正文（§11 追加除外）。
- 河流 12 块**不在**本任务范围（见 TASK-02）。
