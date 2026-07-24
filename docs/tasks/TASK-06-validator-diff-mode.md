# TASK-06：校验器双人复核 diff 模式

## 背景

内容数据（地块图案、场景）采用四级验证：`待录入 → 已录入 → 已复核 → 已测试`。"已复核"要求第二人**独立**从官方来源再录入一遍，两份结果一致才可信——这是桌游数据防错的关键流程（单人转写 24 种图案极易出错）。当前 `tools/content-validator/validate_tiles.py` 只校验单份文件，缺少 diff 能力。

## 输入

- `tools/content-validator/validate_tiles.py`、`validate_content.py`
- `docs/TILE_TOPOLOGY_SPEC.md`（§验证等级语义）

## 交付物

1. `validate_tiles.py` 新增 diff 模式：
   ```bash
   python tools/content-validator/validate_tiles.py content/tiles/base-current.json \
       --diff content/tiles/review/base-current.second-pass.json
   ```
   - 逐图案比对：segments/ports/zones/symbols/centerFeatures/meepleZones/copiesInPool/distinctRotations 的语义等价（允许字段顺序、JSON 键序差异；localSegmentId 命名允许不同，但端口集合签名必须一致——可复用文件内已有的 segment_signature 思路）。
   - 输出：一致图案清单 + 差异图案逐项 diff（人类可读）。
2. 第二录入者工作流说明：追加到 `docs/tasks/README.md` 或单独 `tools/content-validator/REVIEW_WORKFLOW.md`——独立录入→diff→一致后双方把 verificationStatus 升"已复核"。
3. 对 `validate_content.py` 的场景 diff 可选（如时间允许）：场景语义等价比对。

## 验收标准

- 自比对（同一份文件 diff 自己）输出零差异。
- 构造性测试：人为改动一个图案的端口/数量，diff 必须检出并指明位置。
- 现有功能回归：`validate_tiles.py` 常规模式与 `--expect-complete`、`validate_content.py` 行为不变。

## 依赖门禁

无。

## 约束

- 纯 Python 标准库（与现有工具一致），不引第三方依赖。
- 语义等价而非文本等价：JSON 键序、数组顺序不应产生误报；但段端口集合、区带、数量必须严格一致。
- 不改四级验证的语义，只提供工具支撑。
