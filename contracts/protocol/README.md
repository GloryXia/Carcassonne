# 局域网协议契约（draft）

本目录是 `docs/LAN_PROTOCOL.md` 0.1 的机器可校验草案，不代表协议冻结。信封遵循协议 `1.0` 的 `major.minor` 策略：主版本不同必须拒绝；次版本只可新增可忽略字段；删除、改义或改变字段类型必须提升主版本。

消息族按用途拆分为 `lobby`、`session`、`turn`、`display`、`heartbeat`。每份 fixture 以 `.valid.json` 或 `.invalid.json` 标明预期，运行：

```bash
python3 tools/contract-validator/validate_contracts.py
```

契约只覆盖协议文档已经明确的字段。文档尚未规定各房间/会话消息的完整 payload，因此草案只约束已定义的信封、正式命令/结果/事件、投影版本、重连序号和心跳相关字段；后续新增字段应先更新协议文档。

## 建议新增、待协议评审的名称

以下消息名是为把文档中的流程变成可引用契约而提出的名称，原协议只描述了语义，没有正式命名，不能视为已经冻结：

- `JoinRequestPending`、`JoinRequestApproved`
- `ResumeSession`、`SessionResumed`
- `PublicGameView`、`SeatGameView`、`HostAdminView`（沿用文档中的投影类型名作为消息名）

`Heartbeat`、`HeartbeatAck`、`CommitTilePlacement`、`CommandAccepted`、`CommandRejected`、`TilePlaced` 已由协议文档明确给出。
