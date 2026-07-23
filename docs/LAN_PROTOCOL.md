# 局域网协议

- 文档版本：0.1
- 状态：协议草案
- 候选传输：Fastify HTTP + 标准 WebSocket
- 首阶段编码：JSON

## 1. 原则

- 领域命令和事件独立于 Fastify、`ws` 或具体路由实现。
- Game Host 是唯一权威节点。
- 连接不是身份；席位令牌和设备会话才是身份上下文。
- 正式命令可幂等重试。
- 客户端通过修订号和事件序号恢复。
- 同一 Host 提供 Controller Web 和 API，保持同源。

## 2. 地址

- 手机页面：`http://<windows-lan-ip>:<port>/join/<roomCode>`
- HTTP API：`/api/v1/...`
- 实时端点：`/ws/v1/game`
- 健康检查：`/health/live`、`/health/ready`

生产公网阶段切换为 HTTPS/WSS，不改变领域消息。

## 3. 协议版本

每个 WebSocket 消息使用同一个顶层信封：

- `protocolVersion`
- `messageType`
- `messageId`
- `correlationId`，仅响应消息使用，指向请求的 `messageId`
- `instanceId`
- `roomId`
- `gameId`，开局前可空
- `sentAt`，RFC 3339 UTC 时间，仅用于诊断，不参与规则顺序
- `payload`

除 `correlationId` 和开局前的 `gameId` 外，其余字段必填。消息类型特有字段只能放入 `payload`，不能在不同实现中随意提升到顶层。

`protocolVersion` 使用 `major.minor`：

- 主版本不同则拒绝连接。
- 次版本新增可忽略字段时允许兼容。
- 字段删除、改义或类型变化必须提升主版本。

## 4. HTTP 引导

建议端点：

### `GET /health/live`

进程存在且能够响应。

### `GET /health/ready`

数据库、规则内容和实时端点已准备。

### `GET /api/v1/bootstrap`

返回实例名、协议版本、公开房间状态和实时端点。

### `POST /api/v1/rooms/{roomCode}/join-requests`

提交临时昵称、设备 ID 和一次性二维码令牌，返回待批准的 Join Request ID。

### `GET /api/v1/join-requests/{id}`

轮询批准结果。批准后返回短期设备会话凭据；席位恢复令牌通过安全响应单独下发。

### `GET /api/v1/games/{gameId}/snapshot`

按设备权限返回公共或玩家快照，需要有效设备会话。

### `POST /api/v1/socket-tickets`

使用设备会话申请高熵、一次性、短时效的 WebSocket Ticket。浏览器随后连接 `/ws/v1/game?ticket=<ticket>`；Host 在 Upgrade 时消费票据并立即使其失效。日志必须删除查询参数，避免把票据写入诊断文件。

## 5. 身份与令牌

### 5.1 Join Token

- 编码在二维码或加入链接中
- 高熵、短期、可一次性使用
- 只允许创建 Join Request
- 房间关闭后立即失效

### 5.2 Device Session Token

- 代表一台已批准设备
- 绑定房间、设备 ID 和权限
- 短期，可刷新
- 不能作为排位账号凭据

### 5.3 Seat Resume Token

- 代表恢复指定席位的能力
- 不在大屏、URL、日志或二维码中显示
- 手机本地保存
- 房主重新分配席位后立即轮换

WebSocket 连接对象和临时连接 ID 只能用于当前进程路由，不能恢复身份。

## 6. 命令信封

正式命令建议包含：

```json
{
  "protocolVersion": "1.0",
  "messageType": "CommitTilePlacement",
  "messageId": "client-generated-id",
  "instanceId": "host-instance-id",
  "roomId": "room-id",
  "gameId": "game-id",
  "sentAt": "2026-07-23T08:00:00.000Z",
  "payload": {
    "seatId": "seat-id",
    "clientCommandSequence": 42,
    "expectedGameRevision": 108,
    "tileInstanceId": "tile-instance-id",
    "position": { "x": 3, "y": -2 },
    "rotation": "East"
  }
}
```

`messageId` 和 `clientCommandSequence` 用于幂等与诊断，`expectedGameRevision` 防止在过期状态上操作。

## 7. 命令结果

成功：

```json
{
  "protocolVersion": "1.0",
  "messageType": "CommandAccepted",
  "messageId": "host-message-id",
  "correlationId": "client-generated-id",
  "instanceId": "host-instance-id",
  "roomId": "room-id",
  "gameId": "game-id",
  "sentAt": "2026-07-23T08:00:00.050Z",
  "payload": {
    "gameRevision": 109,
    "firstEventSequence": 301,
    "lastEventSequence": 304
  }
}
```

失败：

```json
{
  "protocolVersion": "1.0",
  "messageType": "CommandRejected",
  "messageId": "host-message-id",
  "correlationId": "client-generated-id",
  "instanceId": "host-instance-id",
  "roomId": "room-id",
  "gameId": "game-id",
  "sentAt": "2026-07-23T08:00:00.050Z",
  "payload": {
    "errorCode": "RULE_TILE_EDGES_MISMATCH",
    "currentGameRevision": 108,
    "safeDetails": {
      "conflictingDirection": "North"
    }
  }
}
```

拒绝结果本身不推进规则修订号。

## 8. 正式事件

事件信封：

```json
{
  "protocolVersion": "1.0",
  "messageType": "TilePlaced",
  "messageId": "host-event-message-id",
  "instanceId": "host-instance-id",
  "roomId": "room-id",
  "gameId": "game-id",
  "sentAt": "2026-07-23T08:00:00.060Z",
  "payload": {
    "eventSequence": 302,
    "gameRevision": 109,
    "rulesetHash": "sha256:...",
    "tileInstanceId": "tile-instance-id",
    "position": { "x": 3, "y": -2 },
    "rotation": "East"
  }
}
```

事件在数据库事务提交后广播。客户端按 `eventSequence` 应用；遇到缺口立即停止增量应用并请求同步。

## 9. 状态投影

主机维护三类输出：

- `PublicGameView`：大屏和所有玩家可见。
- `SeatGameView`：公共视图加指定席位的私人信息和合法动作。
- `HostAdminView`：设备、网络和房间管理，不自动包含其他席位秘密。

每类视图包含：

- `gameRevision`
- `lastEventSequence`
- `rulesetHash`
- `viewSchemaVersion`

禁止把完整权威状态发送到浏览器再依靠 CSS 隐藏。

## 10. 预览

预览不是正式命令：

- `GetLegalTilePlacements`
- `PreviewTilePlacement`
- `GetLegalPieceActions`
- `InspectFeature`

预览响应包含基于哪个 `gameRevision` 计算。状态变化后，旧预览自动失效。

大屏的半透明效果可以立即播放预览；只有收到正式事件后才播放不可逆的落子和计分动画。

## 11. 重连

1. 客户端使用 Device Session 或 Seat Resume Token 重新认证。
2. 提交最后应用的 `eventSequence` 和当前视图版本。
3. 主机判断是否能发送缺失事件。
4. 若事件已裁剪、视图版本变化或差距过大，则发送完整权限投影快照。
5. 客户端替换本地投影，验证序号后恢复交互。

Controller Web 和 Godot 自行退避重连；以上流程负责恢复身份、事件和游戏视图。

## 12. 幂等

- 每台设备的正式命令序号单调递增。
- 主机保存最近命令 ID 和结果。
- 收到重复命令时返回原结果，不再次调用规则核心。
- 收到小于已确认序号但未找到记录的命令时，返回协议错误并要求同步。
- 预览请求无需写入幂等表。

## 13. 并发

- 单场对局的正式命令串行处理。
- 不同房间可以并行。
- 同一席位多个连接只能有一个主控制连接；其他连接只读或被新连接替换。
- 秘密同时选择先分别持久化提交状态，再在所有人完成后产生统一揭示事件。

## 14. 局域网安全

- 首阶段不传输账号密码和支付信息。
- 同源提供页面、API 和实时端点，不启用宽泛 CORS。
- 验证 `Origin`、消息大小、频率和 JSON 深度。
- 加入需要高熵令牌和房主批准。
- 默认只开放单个 TCP 端口。
- Windows 防火墙只允许局域网配置文件和指定端口。
- 所有令牌从日志中脱敏。
- WebSocket Server 设置明确的握手超时、最大帧、连接数、空闲时间和发送缓冲上限。
- 浏览器不能可靠暴露协议级 Ping/Pong，因此同时定义轻量应用级 `Heartbeat`/`HeartbeatAck` 消息。

当前 Chrome 对局域网访问引入权限控制；由本地主机直接导航并维持同源可以减少公共网站跨域访问本地网络的问题，但仍必须在目标 Chrome/Safari 版本上实测。

官方参考：[Chrome Local Network Access](https://developer.chrome.com/blog/local-network-access)

## 15. 错误分类

- `AUTH_*`：令牌、设备、席位权限
- `ROOM_*`：房间状态、人数、批准
- `PROTOCOL_*`：版本、格式、序号、大小
- `RULE_*`：回合、地块、角色和选择
- `PERSISTENCE_*`：提交、恢复和只读故障
- `HOST_*`：维护、关闭和内部故障

客户端只展示安全错误；内部异常详情进入诊断日志。

## 16. 传输实现边界

Node.js Host 首先验证 `ws` 与 `@fastify/websocket` 的组合。无论最终使用哪个包：

- 保留全部 HTTP 引导、消息信封、命令、事件和重连语义。
- 对客户端只暴露标准 RFC 6455 WebSocket，不暴露框架私有协议。
- 客户端自行实现应用级心跳、退避重连和快照恢复。
- 更换服务端 WebSocket 包不得修改 Rules Core 或数据库事件格式。

## 17. 协议测试

- 主版本不兼容拒绝
- 未知可选字段向前兼容
- 过期修订号拒绝
- 重复命令只执行一次
- 事件丢失触发快照
- 六部手机同时重连
- 私人字段不出现在公共视图
- 更换 WebSocket 连接不改变席位
- Host 提交后广播前崩溃，重连仍能得到事件
- 异常大消息和高频请求被限制
