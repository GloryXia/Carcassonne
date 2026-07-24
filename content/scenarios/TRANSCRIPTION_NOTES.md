# 场景转写笔记（TASK-03）

来源基线：

- Z-Man Games 官方《Carcassonne Rulebook English》（©2016，6 页）：`https://cdn.svc.asmodee.net/production-unboxnowcom/uploads/sites/13/2022/02/Carcassonne-EN.pdf`
- Z-Man Games 官方《Carcassonne v3 Supplemental Rulesheet》（2 页）：`https://cdn.svc.asmodee.net/production-zman/uploads/2024/09/carcassonne_v3_supplement_en.pdf`
- Complete Annotated Rules（CAR）Standard ver. 7.3，334 页，作为历史图例和交叉核对来源；本地核查缓存位于已被 Git 忽略的 `sources/`，不随仓库分发。

2026-07-24 已对官方基础规则和补充规则逐页提取文本，并渲染补充规则 p.1–2 核查农夫与修道院长图例。

## 版本口径核查（重要结论）

CAR 7.3（2014-12）基础游戏计分与当前规则口径（C3/2015+）**一致**：

- p.15 注释 19 明确：C1 早期的"小城规则"（2 块城只值 2 分）**已废弃**，"small cities are now scored in the same way as every other city"——即 2 分/段 + 2 分/盾徽，与当前口径相同。
- 道路 1 分/块、完成城 2 分/段 + 2 分/盾徽、修道院 1+8、农夫 3 分/已完成城、并列全分、终局未完成 1 分/段 + 1 分/盾徽——逐项与 `content/rulesets/base-current.json` 一致。

因此本目录场景未做任何版本调整。

## 关于"盘面为等价转写构造"

CAR 示例的数值在文本中明确（如 "RED scores 8 points (three city segments and one pennant)"），但示例图片为位图无法机器提取精确盘面。凡标题/说明标注"等价转写构造"的场景：数值直接引用官方示例，盘面由转写者按地块拓扑等价构造，均通过 `validate_content.py` 的邻接合法性实算与盒内块数约束。复核时建议对照 CAR 原图确认盘面等价性。

## 场景清单与出处

| scenarioId | 数值出处 | kind | 说明 |
|---|---|---|---|
| road-complete-3pt-between-monasteries | CAR p.14 "RED scores 3 points" | official-example | 两端终止于修道院（修道院是道路终止点） |
| road-complete-4pt | CAR p.14 "RED scores 4 points" | official-example | 同上，4 块 |
| city-complete-8pt-pennant | CAR p.15 "RED scores 8 points (three city segments and one pennant)" | official-example | 隧道城（cfcf+盾徽）加两城帽 |
| city-complete-8pt-no-pennant | CAR p.15 "RED scores 8 points (four city segments, no pennants)" | official-example | 三面城块 + 三城帽封口，验证无盾徽 4 段=8 分 |
| city-tie-10pt-both-score-full | CAR p.15 "BLUE and RED both score the full 10 points…a draw!" | official-example | 三面城带盾徽（4 段+1 盾徽=10 分），并列双方全分 |
| city-tie-8pt-both-score-full | CAR p.15 并列条款 | derived | 补充：隧道城布局下的并列 |
| monastery-complete-9pt | CAR p.16 "RED scores 9 points" | official-example | 环形盘面（直路+弯块围 3×3） |
| field-farmer-3pt-one-city | CAR p.15–16 农夫 3 分/城规则 | derived | 田经城帽田野段接壤 1 个完成城 |
| field-farmer-6pt-two-cities | 同上 | derived | 一田多城：田经 (-1,0) 隧道城东田野段接壤第二城（注：隧道城两侧田野互不相连，仅东侧段属该田） |
| field-split-by-road-two-farms | CAR p.16–17 田分割规则 | derived | 直路将一块上的田分为南北两段（seg-field-1/seg-field-2），北田接壤城得 3 分、南田 0 分 |
| endgame-incomplete-road-3pt | CAR p.18 "RED scores 3 points for the incomplete road" | official-example | 一端终止于修道院、一端开敞 |
| endgame-incomplete-cloister-5pt | CAR p.18 "自身 1 + 每邻居 1"（FAQ：5 邻居=6 分） | derived | 4 邻居 → 5 分 |
| endgame-incomplete-city-3pt-pennant | CAR p.18 终局 1 分/段 + 1 分/盾徽 | derived | 盾徽终局仍计分 |
| endgame-city-majority-loser-scores-zero | CAR p.18 "GREEN scores 8…BLACK scores nothing, since GREEN has more knights" | derived | 2 骑士 vs 1 骑士，多数方得 4 分（3 段+1 盾徽）、少数方 0 分 |
| deployment-road-occupied-rejected | Z-Man 基础规则 p.3 已占用道路示例 | official-example | 新放地块已接入有随从道路，第二名道路随从部署被拒绝 |
| abbot-recall-6pt | Z-Man v3 补充规则 p.2 "score 6 points" | official-example | 官方图为花园；当前目录未拆分花园插画，按规则等价转写为有 5 个邻块的修道院 |
| abbot-complete-monastery-9pt | Z-Man v3 补充规则 p.2 完成修道院/花园 9 分条款 | official-clarification | 8 邻块完成，修道院长得 9 分并返回供应区 |

## 已知限制与处理结论

1. **Schema 扩展**：为消除原先无法表达的缺口，场景动作新增 `place-piece`、`reclaim-abbot`，期望新增 `actionAccepted`、`rejectionCode`；该变更属于完成 TASK-03 所必需的契约演进，TASK-04 应直接消费这些断言。
2. **花园数据粒度**：`base-current.json` 当前按拓扑合并图案，没有把花园插画拆成独立定义。官方 6 分图例因此以规则明确允许、计分完全相同的修道院作等价盘面；待地块目录按插画变体拆分后可替换为花园原图转写，数值和动作断言不变。
3. CAR p.14 的“T 型路口各方向均为独立道路”缺少独立计分数值，属于引擎拓扑单元测试，不伪造为计分场景。

## 盒内块数约束核查

各场景相互独立（各自构造盘面），单场景内用量已核对不超盒内数量：city-tunnel×1、city-tunnel-pennant×2、city-triple(-pennant)×1、city-cap ≤4、monastery×1、monastery-road ≤2、road-straight ≤4、road-curve ≤4，均在 72 块盒存量内。
