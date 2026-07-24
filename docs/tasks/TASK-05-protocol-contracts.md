# TASK-05：局域网协议契约包草案

## 背景

主机（Windows/Node 权威端）、Godot 显示端、手机浏览器控制器三方通过局域网协议通信。`docs/LAN_PROTOCOL.md` 已定义消息信封与协议族，但目前是散文描述，没有机器可校验的契约。本任务产出协议契约包：JSON Schema + 消息夹具，供三端共享，未来接 CI 契约测试。

## 输入

- `docs/LAN_PROTOCOL.md`（信封、消息族、版本策略——动手前必读全文）
- `docs/LAN_ARCHITECTURE.md`（拓扑与生命周期）
- 参考风格：`content/schemas/*.json`（JSON Schema 2020-12）

## 交付物

1. `contracts/protocol/` 目录（新目录，不混入 content/）：
   - `envelope.schema.json`：消息信封（协议版本、消息类型、会话/席位标识、序号、时间戳等，字段以 LAN_PROTOCOL.md 为准）；
   - 各消息族的 Schema： lobby / session / turn / display / heartbeat 等（以协议文档实际划分为准）；
   - `fixtures/`：每类消息至少 2 个合法示例 + 1 个非法示例（应被 Schema 拒绝）。
2. `tools/contract-validator/`（或并入现有 content-validator 工具链）：校验 fixtures 合法/非法断言的脚本。
3. 协议版本号策略说明：写入 `contracts/protocol/README.md`，与 LAN_PROTOCOL.md 的版本条款一致。

## 验收标准

- 全部合法 fixtures 通过 Schema；全部非法 fixtures 被拒绝（脚本输出断言结果，退出码非零即失败）。
- 契约字段与 LAN_PROTOCOL.md 逐条对应；任何文档未定义的字段需在回报中标注为"建议新增"，不得静默加入。
- 发现协议文档内部矛盾时，记录在回报中，不擅自取舍。

## 依赖门禁

无。纯数据/Schema 工作，本机可完成。

## 约束

- 这是**草案**：产出供项目负责人评审，不承诺冻结；文件头注明 draft 状态。
- 不实现任何收发代码；契约先行，实现在后续任务。
- JSON Schema draft 2020-12，风格与 content/schemas 保持一致。
