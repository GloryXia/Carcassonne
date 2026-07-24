# 区域拓扑数据规范

- 文档版本：0.2（草案；0.2 新增河流模块扩展：§3 河流行生效、§4 featureType 增加 river、§9 不变量补充、§13 新增）
- 状态：等待阶段 0 评审与逐块录入验证
- 关联：[规则引擎技术设计 §5](RULE_ENGINE_TECHNICAL_DESIGN.md)、[地块与扩展目录 §3](TILE_AND_EXPANSION_CATALOG.md)、[基础规则纲要 §3](GAME_RULES.md)

本文定义地块拓扑的**数据编码约定**，是 `content/schemas/tile-definition.schema.json` 的语义说明。规则引擎只消费符合本规范的数据；视觉上彼此靠近不代表逻辑连接，一切连接关系以本文编码为准。

## 1. 设计目标

- 地块拓扑完全由数据表达，规则引擎不硬编码任何具体图案。
- 编码结果对同一官方图案唯一确定，可复核、可生成测试。
- 支持基础游戏的单格地块，并为河流、多格地块和扩展符号预留空间。
- 所有字段使用整数、枚举和字符串，不使用浮点数，满足确定性要求。

## 2. 网格、方向与旋转

- 棋盘位置 `BoardPosition = (x, y)`，`x` 向东为正，`y` 向南为正，均为整数。
- 方向 `Direction ∈ {N, E, S, W}`。
- 旋转 `Rotation ∈ {North, East, South, West}`，表示地块**原始北边**放置后指向的棋盘方向。`North` 为未旋转。
- 每种图案声明 `distinctRotations`：在旋转对称下不等价的旋转数量。枚举合法放置时只枚举不等价旋转，但渲染和端口映射以实际旋转为准。
  - 4：无对称（多数地块）
  - 2：180° 旋转对称（如直路）
  - 1：90° 旋转对称（如十字路口、四面城、纯田野修道院）

旋转 `r` 将局部方向 `d` 映射为棋盘方向：`rotate(N,d)=d`；`East` 顺时针转 90°；`South` 转 180°；`West` 转 270°。端口在录入时永远以**未旋转方向**书写。

## 3. 边缘分区：三段式端口

每条外边缘划分为三个横向区带（zone），从地块中心朝外看：

```text
        N.left   N.center   N.right
          ┌──────┬──────┬──────┐
   W.right│      │      │      │E.left
 W.center │      │      │      │E.center
   W.left │      │      │      │E.right
          └──────┴──────┴──────┘
        S.right  S.center  S.left
```

- `left` / `right` 以**从中心朝该边缘外看**的左右为准。
- 不同地貌占用固定的区带组合：

| 地貌端口 | 占用区带 |
|---|---|
| 城市（城墙横贯整条边） | `left + center + right` |
| 道路（路面在边缘中央） | `center` |
| 田野 | 该边未被城市/道路/河流占用的其余区带 |
| 河流（v0.2 生效，见 §13） | `center`（同道路区带；语义由 §13 定义） |

- 边级地貌判定顺序（聚合统计与邻接匹配共用）：**city > river > road > field**。论证：城市恒占整边，与道路/河流不可能共存于同一边；道路与河流同占 `center` 亦不可能共边，故三者先后次序不影响判定结果，此序仅为约定（校验器 `validate_tiles.edge_terrain` 实现）。
- 相邻两块地块共享一条边时，端口按区带对接：**两侧同一区带位置的地貌必须相同**（城市对城市、道路对道路、田野对田野、河流对河流），否则放置非法。
- 对接时区带需要**镜像**：地块 A 的 `E.left` 接触地块 B（东侧邻居）的 `W.right`；`center` 对 `center`。

## 4. 区域段与内部连通

- 地块内部的逻辑区域用**区域段（segment）**表达。段是规则引擎的最小拓扑单元。
- 每个段声明：
  - `localSegmentId`：地块内唯一 ID（稳定字符串，如 `seg-road-1`）。
  - `featureType`：`field | road | city | garden | river`（`river` 为 v0.2 新增，语义见 §13）。
  - `ports`：该段触及边缘的 `{edge, zones}` 列表。
  - `symbols`：附着标志，如 `pennant`（盾徽）。
- **内部连通由段成员关系隐式表达**：一个段拥有多个端口，即表示这些端口在地块内部连通。例如直路地块只有一个含 `{E.center, W.center}` 两个端口的道路段；三岔路口只有一个含三个端口的道路段。
- 同一块地块上同类型的多个段表示**互不连接**的多个区域。例如直路地块有两个互不相连的田野段；十字路口有四个田野段。
- 田野可以绕过地块角落：一个田野段的端口列表可以跨越相邻边缘（含同一条边的 `left` 与 `right`），表示它在角部连续。跨地块的田野连接只通过共享边上的区带对接，**对角相邻不产生连接**。
- 段的完整连接区域（FeatureGraph 组件）由规则引擎在放置时按端口对接关系构建，见《规则引擎技术设计》§6。

## 5. 中心特征

`centerFeatures` 描述不通过边缘连接的中央区域：

- `monastery`：修道院。完成条件为周围八格被占满。
- `garden`：花园。计分同修道院，但只能由修道院长占用。

道路端口终止于中心特征时（如修道院带路地块），在道路段上标注 `endsAtCenter: true`；该端口参与道路完成判定。

## 6. 角色放置区

`meepleZones` 由段和中心特征派生，录入时显式写出以支持 UI 热点和碰撞检测：

| 区域类型 | 允许角色 | 基础游戏身份 |
|---|---|---|
| `road` 段 | `meeple` | 旅行者 |
| `city` 段 | `meeple` | 骑士 |
| `field` 段 | `meeple` | 农夫 |
| `monastery` | `meeple, abbot` | 僧侣 |
| `garden` | `abbot` | （修道院长） |

规则命令只使用 `localSegmentId` 或中心特征 ID 指定目标，不使用渲染坐标。

## 7. 地块定义字段

与《地块与扩展目录》§3 对齐，基础录入必须包含：

| 字段 | 说明 |
|---|---|
| `tileDefinitionId` | 稳定 ID，格式 `<catalog>.<mnemonic>`，如 `base-current.city-cap-road-straight` |
| `rulesetVersion` | 规则版本 ID，基础盒当前版为 `base-current` |
| `expansionId` | 所属包，基础盒为 `base` |
| `copiesInPool` | 抽取池中的数量（不含起始地块） |
| `startTileCopies` | 作为起始地块的数量，基础盒为 0 或 1 |
| `footprint.kind` | 基础地块为 `singleCell`；多格/半格预留 |
| `allowedRotations` | 允许的旋转，基础地块恒为全部四种 |
| `distinctRotations` | 旋转对称下不等价数量（1/2/4） |
| `segments` | 区域段列表（见 §4） |
| `centerFeatures` | 中心特征列表（见 §5） |
| `meepleZones` | 角色放置区（见 §6） |
| `placementTags` | 额外约束标签，如 `start-tile`、`river-source` |
| `sourceReference` | 官方来源（规则书页码或组件表） |
| `verificationStatus` | `待录入 / 已录入 / 已复核 / 已测试` |
| `visualAssetId` | 视觉资产引用，录入期可为 `null` |

## 8. 编码示例：起始地块

起始地块（城市在北，直路东西向，下称 `city-cap-road-straight`）的完整编码：

```json
{
  "tileDefinitionId": "base-current.city-cap-road-straight",
  "copiesInPool": 3,
  "startTileCopies": 1,
  "distinctRotations": 4,
  "segments": [
    { "localSegmentId": "seg-city-1", "featureType": "city",
      "ports": [{ "edge": "N", "zones": ["left", "center", "right"] }] },
    { "localSegmentId": "seg-road-1", "featureType": "road",
      "ports": [{ "edge": "E", "zones": ["center"] }, { "edge": "W", "zones": ["center"] }] },
    { "localSegmentId": "seg-field-1", "featureType": "field",
      "ports": [{ "edge": "E", "zones": ["left"] }, { "edge": "W", "zones": ["right"] }] },
    { "localSegmentId": "seg-field-2", "featureType": "field",
      "ports": [{ "edge": "S", "zones": ["left", "center", "right"] },
                { "edge": "E", "zones": ["right"] }, { "edge": "W", "zones": ["left"] }] }
  ]
}
```

注意两个田野段：`seg-field-1` 是城市与道路之间的东西向窄带，两个端口不相邻却属于同一段——这正是"视觉上分离不代表逻辑断开"的典型用例，应进入边界测试。

## 9. 完整性不变量（录入校验器必须检查）

1. 每条边的三个区带被且只被一个段覆盖（不重不漏）。
2. 城市端口恒占整边（三区带）；道路与河流端口恒占 `center`。
3. 段 ID 在地块内唯一；`meepleZones` 引用的段必须存在。
4. `copiesInPool + startTileCopies` 与目录清点一致；全部图案合计等于官方组件总数。
5. `distinctRotations` 与段端口集合的实际对称性一致。
6. 盾徽只能附着在城市段上。
7. 河流段不得被 `meepleZones` 引用（河流上不可部署随从，CAR p.27）。
8. 整盒聚合校验按目录独立进行（各盒口径互不并入）：
   - `base-current`：全部 72 块地块的边缘合计应满足田野 115、道路 94、城市 79（社区长期统计的交叉校验值；最终以锁定版官方组件表为准）。
   - `river-current`：全部 12 块地块的边缘合计应满足田野 15、道路 6、城市 5、河流 22（由 CAR Standard ver.7.3 p.267–269 The River 组件表逐块转写后汇总得出）。

## 10. 录入与复核流程

与《地块与扩展目录》§4.2 一致，每种图案按 `待录入 → 已录入 → 已复核 → 已测试` 推进：

1. 从锁定版官方组件表转写图案、数量与盾徽位置。
2. 按本规范编码端口与段，标记 `已录入`。
3. 第二名录入者独立重编码并逐字段比对（重点：田野段），一致后标记 `已复核`。
4. 每种不等价旋转自动生成放置合法性测试，官方示例转成场景测试后标记 `已测试`。

未达 `已复核` 的图案不得进入规则引擎的正式地块池。

## 11. 当前录入状态

`content/tiles/base-current.json` 已录入全部 24 种图案（72 块，含起始地块），整盒聚合校验通过（田野 115 / 道路 94 / 城市 79）。

前 8 种（37 块）为既有录入：纯田野修道院、修道院带路、直路、弯路、三岔路、十字路口、单城帽、单城帽直路（起始地块）。

### TASK-01 追加录入说明（16 种，35 块）

**来源与优先级执行情况**：

1. Z-Man 官方规则 PDF（README 基线链接）本机直连失败；经其镜像副本确认组件总述（72 块地形地块 + 深色背面起始块），但其组件页为整页插图，不含逐图案数量，无法单独作为逐图案来源。
2. Wikicarpedia 启用 Anubis 反爬验证，无法直接抓取，未使用。
3. 实际采用来源：**Complete Annotated Rules v4.0（Matthew Harper 编，HiG 授权翻译整理）p.16 基础盒 Tile Distribution 组件表**（dmediamom.com 镜像 PDF）。该页以扫描图逐图案列出数量；已提取全部 24 张地块扫描图逐一目检，确认边缘地貌、盾徽有无、城市连通/分割与道路走向。
4. 交叉核验：转写结果的聚合边缘统计与 russcon.org（Robert Gatliff 编制）的 C1 基础盒统计完全一致（田野 115 / 道路 94 / 城市 79；含城市地块 44 块、含道路地块 45 块亦一致）；盾徽图案共 6 种 10 枚，与 C1 基础盒公认盾徽总数一致。

**16 种图案清单**（ID / CAR 记号 / 数量）：

| tileDefinitionId | CAR 记号 | 数量 | 说明 |
|---|---|---|---|
| city-full-pennant | cccc | 1 | 四面城，带盾徽 |
| city-triple | cccf | 3 | 三面城 |
| city-triple-pennant | cccf+盾徽 | 1 | 三面城带盾徽 |
| city-triple-road | cccr | 1 | 三面城 + 单口路（路止于城门） |
| city-triple-road-pennant | cccr+盾徽 | 2 | 同上带盾徽 |
| city-corner | ccff 连通 | 3 | 邻边双城，角部连通 |
| city-corner-pennant | ccff 连通+盾徽 | 2 | 同上带盾徽 |
| city-corner-split | ccff 不连通 | 2 | 邻边两个互不连通城市 |
| city-corner-road-curve | ccrr | 3 | 邻边双城 + 弯路 |
| city-corner-road-curve-pennant | ccrr+盾徽 | 2 | 同上带盾徽 |
| city-tunnel | cfcf 连通 | 1 | 对边城市贯通（隧道城） |
| city-tunnel-pennant | cfcf 连通+盾徽 | 2 | 同上带盾徽（3 条种子场景引用） |
| city-opposite-split | cfcf 不连通 | 3 | 对边两个互不连通城市 |
| city-cap-road-curve-sw | cfrr | 3 | 单城帽 + 弯路（S+W 端口） |
| city-cap-road-curve-es | crrf | 3 | 单城帽 + 弯路（E+S 端口，与 cfrr 互为镜像） |
| city-cap-road-t | crrr | 3 | 单城帽 + 三岔路 |

**歧义与取舍记录**：

- **cfrr 与 crrr/crrf 手性**：单城帽弯路在盒中存在两个互为镜像的朝向（各 3 块），旋转不可互达，故拆为两个图案，ID 以道路端口方位后缀 `-sw` / `-es` 区分。
- **ccrr 田野分段**：扫描图显示弯路内侧角（S.right+W.left）为一段，城外两条窄带（S.left、W.right）被城市隔断、互不相连，故编码为三个田野段。
- **cccr 田野连通**：扫描图显示道路止于城门，路端两侧田野绕路端连通，编码为单一田野段（W.left+W.right）。
- **cfcf 两种不连通/连通变体**：连通变体（隧道城）城市为一段贯通 N–S，两侧田野分离；不连通变体两个城市各占一边，田野横贯 E–W 连通。扫描图确认不连通变体无盾徽。
- **cccc 盾徽**：扫描图确认唯一的四面城带盾徽，故 ID 定为 `city-full-pennant`。
- **CAR 页同纹多行**：CAR 组件表中同一记号出现多行时，以扫描图目检区分"无盾徽 / 带盾徽 / 城市不连通"变体，数量与各行一一对应如上表。
- 起始块唯一性不变：仅 `city-cap-road-straight`（startTileCopies=1）。

### TASK-02 追加录入说明（河流 10 种图案，12 块）

`content/tiles/river-current.json` 已录入 The River（River I，当前基础盒内置河流模块）全部 10 种图案 12 块，编码扩展见 §13。

**来源与核验**：

1. 规则事实：CAR Standard ver.7.3 p.27–28 河流规则全文（本地文本 `content/scenarios/sources/car-river-pages.txt`）。
2. 图案：CAR Standard ver.7.3 p.267–269 The River 组件表。已从本地原始 PDF（`content/scenarios/sources/carcassonne-rules-car.pdf`）提取全部扫描图，并结合页面内坐标重建表格行序后逐块目检（边缘地貌、城市连通/分割、道路桥梁、修道院归属）。
3. 交叉核验：聚合边缘统计 田野 15 / 道路 6 / 城市 5 / 河流 22，与 12×4=48 边自洽；`--expect-complete` 通过。

**已知不确定点的处理**：CAR p.27 图例显示河流块中存在修道院（cloister）但文本未指明归属块。经 p.268 "Farm, river, road, river / x1 (The River)" 扫描图目检，确认修道院位于该块北岸（道路经木桥跨河止于修道院），已据此录入 `river-current.monastery-road-bridge-river`。此为**单人目检结论**，按流程维持 `已录入` 状态，待 TASK-06 第二人独立复核确认。

**歧义与取舍记录**：

- CAR 四边记号未注明起始边与阅读方向：本目录约定**从 N 开始顺时针**映射；源头/湖泊块的唯一河流端口约定置于 S 边。官方朝向不影响玩法（旋转等价）。
- 组件表中的 "or" 变体经扫描图确认为同拓扑的印刷/图案变体（如 2014 版加绘葡萄园、羊等 Hills & Sheep 接口符号），各按一种朝向录入并在 `notes` 说明；扩展符号不录入。
- 同页出现的 The River II / GQ11 图案（如带修道院的直河块、城市跨河相连块）均不属于本目录，已在相关 `notes` 中标注以防混淆。

## 12. 预留

- 多格与半格地块：`footprint` 扩展为单元列表，端口相对各自单元书写。
- 扩展符号：`symbols` 与 `placementTags` 按扩展模块规范追加，不改变本文件既有编码语义。

## 13. 河流模块扩展（v0.2 新增）

本章为 The River（River I）模块的编码约定，与既有章节共同构成完整规范；既有编码语义不变（向后兼容，`base-current.json` 无需任何修改）。

### 13.1 river 边缘地貌

- `featureType: river` 为第四种边缘地貌。河流端口与道路一样恒占 `center` 区带（§3 表已生效）。
- 邻接匹配沿用区带对接规则：河流端口只能对接河流端口。
- 边级地貌判定顺序：**city > river > road > field**（论证见 §3；校验器与交叉校验器共用 `validate_tiles.edge_terrain`）。

### 13.2 河流段语义

- 河流段**不参与角色放置**（CAR p.27："Followers may not be deployed to the river"），`meepleZones` 不得引用河流段（不变量 §9.7）。
- 河流段**分割田野**（CAR 注释 42）：河流两侧的田野为互不连通的段，即使区带在角部相邻。
- 源头/湖泊块的田野**环绕源头/湖泊连通**（CAR 注释 39），编码为单一田野段。
- 随从可作为骑士/小偷/修士/农夫部署到河流块的城市/道路/修道院/田野特征上（CAR p.27），编码与基础块一致。

### 13.3 道路跨河（桥）

部分河流块上道路以**桥**跨越河流（扫描图确认：`city-cap-road-river-bridge`、`monastery-road-bridge-river`、`road-river-crossing-bridge`）。编码约定：桥仅为图案层次，**道路段与河流段在块内交叉但不连通**——段的连通性仍完全由段成员关系表达，无需额外字段。道路跨过河流后止于城门/修道院或继续至对边端口，按实际图案录入。

### 13.4 河流专用 placementTags

| 标签 | 含义 | 放置语义（规则引擎 TASK-04 实现） |
|---|---|---|
| `river-source` | 源头块 | 河流模块开局块，先于一切放置；`startTileCopies=1`、`copiesInPool=0` |
| `river-lake` | 湖泊块 | 河流收尾块，其余 10 块放完后放置 |
| `river-curve` | 弯河块 | 两个河流端口位于相邻边的块；用于 U 型回折禁止判定 |

**U 型回折禁止的数据表达**（CAR p.28 + 注释 43：仅**立即**回折被禁）：数据层只需识别弯河块，即 `river-curve` 标签（校验器断言该标签与"两河流端口相邻"严格一致）。放置规则本身（新放弯河块不得使其河流立即 180° 折返）属 TASK-04 规则引擎范围，本规范不展开。

### 13.5 河流目录级完整性断言（校验器实现）

`river-current` 目录在 `--expect-complete` 下除 §9.8 聚合边缘校验外，还需满足：

1. 源头块唯一且 `startTileCopies=1`、`copiesInPool=0`；湖泊块唯一且池中恰 1 块。
2. 源头/湖泊块恰有 1 个河流端口；其余图案每块恰有 2 个河流端口。
3. 弯河块必带 `river-curve`，直河块不得携带。
4. 合计 12 块（源头 1 + 湖泊 1 + 洗牌堆 10），边缘合计 田野 15 / 道路 6 / 城市 5 / 河流 22。

### 13.6 四边记号映射约定

CAR 组件表的四边地貌记号（如 "city, river, road, river"）未注明起始边与阅读方向。本目录约定**从 N 开始顺时针**映射为 N/E/S/W；记号中的 "or" 变体（同拓扑的印刷/图案差异）各按一种朝向录入，并在 `notes` 字段说明。该约定不影响玩法：官方地块朝向在规则下旋转等价。
