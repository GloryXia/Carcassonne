# 持久化设计

- 文档版本：0.1
- 状态：建议设计
- 首阶段存储：WSL2 ext4 中的 SQLite

## 1. 目标

- 每个已确认动作在广播前可靠保存。
- Windows、WSL2 或显示端异常退出后可以恢复。
- 同一事件日志可以重放出相同终局状态。
- 支持多个未完成对局、完成历史和本地玩家档案。
- 数据模型可以迁移到未来公网数据库。

## 2. 非目标

- 首阶段不实现云同步。
- 不实现公网账号密码存储。
- 不让手机直接访问数据库文件。
- 不把 SQLite 文件放到网络共享中供多主机同时打开。

## 3. 数据库位置

WSL2 模式建议：

```text
/var/lib/carcassonne/carcassonne.db
/var/lib/carcassonne/backups/
/var/lib/carcassonne/exports/
```

- 活跃数据库位于 WSL2 Linux 文件系统。
- 不直接放在 `/mnt/c`。
- Windows 只通过 Game Host API 读取游戏数据。
- 导出到 Windows 前，使用 SQLite Backup API 生成一致副本。

SQLite WAL 要求所有数据库使用进程位于同一主机，符合单个 WSL2 Game Host 的模型。官方参考：[SQLite WAL](https://www.sqlite.org/wal.html)

## 4. 建议表

### 4.1 `schema_migrations`

| 字段 | 说明 |
|---|---|
| `version` | 单调递增迁移版本 |
| `name` | 迁移名称 |
| `applied_at_utc` | 诊断时间 |
| `checksum` | 迁移脚本校验值 |

### 4.2 `local_profiles`

| 字段 | 说明 |
|---|---|
| `profile_id` | 稳定本地玩家 ID |
| `display_name` | 本地显示名 |
| `preferred_color` | 偏好颜色，可空 |
| `settings_json` | 玩家设置，不含秘密凭据 |
| `created_at_utc` | 创建时间 |
| `updated_at_utc` | 修改时间 |
| `future_account_id` | 未来绑定公网账号，可空 |

### 4.3 `games`

| 字段 | 说明 |
|---|---|
| `game_id` | 对局 ID |
| `room_id` | 创建该局的房间 ID |
| `status` | Setup、Active、Finished、Abandoned |
| `ruleset_id` | 规则集 ID |
| `ruleset_hash` | 内容与模块哈希 |
| `protocol_version` | 创建时协议版本 |
| `revision` | 当前规则修订号 |
| `last_event_sequence` | 最后提交事件序号 |
| `state_fingerprint` | 当前状态规范哈希 |
| `created_at_utc` | 诊断时间 |
| `updated_at_utc` | 诊断时间 |
| `finished_at_utc` | 完成时间，可空 |

### 4.4 `game_seats`

| 字段 | 说明 |
|---|---|
| `game_id` | 对局 ID |
| `seat_id` | 席位 ID |
| `seat_index` | 官方回合顺序 |
| `profile_id` | 本地档案，可空 |
| `controller_type` | Human、AI、HostFallback |
| `player_color` | 玩家颜色 |
| `final_score` | 完成后分数，可空 |
| `final_rank` | 完成后名次，可空 |

WebSocket 连接和临时连接 ID 不属于永久席位记录。

### 4.5 `game_events`

| 字段 | 说明 |
|---|---|
| `game_id` | 对局 ID |
| `event_sequence` | 对局内单调递增序号 |
| `game_revision` | 该事务完成后的修订号 |
| `event_type` | 稳定事件代码 |
| `event_schema_version` | 事件负载版本 |
| `payload_json` | UTF-8 JSON 负载 |
| `command_id` | 触发命令，可空 |
| `seat_id` | 触发席位，可空 |
| `state_fingerprint_after` | 应用该批事件后的状态指纹 |
| `created_at_utc` | 诊断时间 |

主键为 `(game_id, event_sequence)`。`command_id` 在对应设备/对局范围内建立唯一约束，以支持幂等。

### 4.6 `game_snapshots`

| 字段 | 说明 |
|---|---|
| `snapshot_id` | 快照 ID |
| `game_id` | 对局 ID |
| `event_sequence` | 快照覆盖到的事件序号 |
| `game_revision` | 规则修订号 |
| `snapshot_schema_version` | 快照格式版本 |
| `ruleset_hash` | 快照对应规则内容 |
| `state_fingerprint` | 状态指纹 |
| `compression` | None 或 Brotli 等明确算法 |
| `payload_blob` | 完整权威状态 |
| `created_at_utc` | 诊断时间 |

### 4.7 `command_results`

保存有限时间或有限数量的近期命令结果：

- 命令 ID
- 设备会话 ID
- 客户端命令序号
- 接受或拒绝
- 对应修订和事件范围
- 安全错误码

用于重复提交返回原结果。完成对局封存时可以裁剪无长期价值的拒绝结果。

### 4.8 `completed_game_summaries`

- 终局规则集、席位、分数、名次和胜利者
- 开始、结束和终止原因
- 首尾状态指纹
- 录像是否完整
- 可选的人类可读摘要

终局摘要是查询优化，不替代事件日志。

## 5. 动作事务

正式命令处理：

```text
接收并认证命令
  → 获取单局串行锁
  → 读取当前 revision 和必要状态
  → 检查幂等记录
  → Rules Core 验证并产生事件
  → 开始 SQLite 事务
  → 插入事件
  → 更新 games revision、sequence、fingerprint
  → 按策略写快照
  → 保存命令结果
  → 提交事务
  → 释放单局锁
  → 广播正式事件
```

如果数据库提交失败，不广播正式事件。若提交成功但广播前进程退出，客户端重连后从数据库取得缺失事件。

## 6. 快照策略

建议在以下时机写快照：

- 创建对局并完成准备后
- 每固定数量的正式命令或事件后
- 回合边界达到设定间隔时
- 启用扩展的复杂选择完成后
- 进入最终计分前
- 完成对局后
- 正常关闭前

具体间隔通过性能测试确定。事件日志不能因为已有快照就立即删除；保留策略需要保证完整录像和规则审计。

## 7. 快照格式

首阶段建议：

- 使用项目内版本化 Snapshot Schema 将权威状态序列化为 UTF-8 JSON
- UTF-8 字节后可选 Brotli 压缩
- 在负载外保存 Schema、规则集和压缩版本
- 未知快照版本不得静默反序列化

状态指纹来自单独的规范序列化，而不是压缩后的快照字节。

## 8. 恢复

1. 读取 `games` 当前元数据。
2. 加载不超过最后事件序号的最新有效快照。
3. 验证快照规则集哈希和状态指纹。
4. 按序应用快照之后的事件。
5. 每批或最终验证状态指纹。
6. 若成功，将游戏恢复为可连接状态。
7. 若失败，保持只读并生成诊断包，不猜测修复。

显示端和手机状态全部从恢复后的权威状态重新投影。

## 9. WAL 与同步

候选设置：

- `journal_mode=WAL`
- `foreign_keys=ON`
- `busy_timeout` 使用明确值
- `synchronous=FULL` 作为规则动作耐久性基线
- 在空闲、对局结束和备份前执行受控检查点

最终值需要通过 WSL2 断电/强杀测试和性能测量决定。不能为了极小延迟牺牲已确认动作的恢复语义。

## 10. Node.js 数据库访问

- 首阶段使用 `persistence-sqlite` TypeScript 包和显式参数化 SQL。
- Spike 4 在 Node.js 24 内建 `node:sqlite` 与 `better-sqlite3` 中选择并锁定一个实现；领域层不得直接导入驱动。
- 单个 Host 进程是唯一写者。
- 不让 Godot 直接读取数据库。
- 读取查询需要短事务，避免阻塞 WAL 检查点。
- 所有 SQL 参数化。
- 数据库迁移在 Host Ready 之前完成。
- 同步驱动的每个事务必须足够短；备份、压缩、录像导出和 AI 搜索不得长期阻塞 Node.js 事件循环。

## 11. 备份与导出

### 11.1 自动备份

- 完成对局后创建一致备份。
- 保留有限数量的轮换备份。
- 在磁盘不足时停止创建新对局并给出明确提示，不静默删除活动对局。

### 11.2 Windows 导出

1. Host 通过已选 Node.js 驱动调用 SQLite Online Backup API，在 WSL2 内生成一致数据库或单局导出。
2. 关闭备份连接。
3. 将已完成的备份文件复制到 Windows 用户数据目录。
4. 生成校验值和元数据。

不要直接复制活动中的 `.db`、`-wal` 和 `-shm` 组合。

### 11.3 WSL 级备份

用户还可以使用 `wsl --export` 备份发行版，但这不是单局导出功能的替代品。

## 12. 迁移

- 每个迁移有唯一版本、名称和校验值。
- 迁移只能向前自动执行。
- 迁移前先生成一致备份。
- 已发布事件负载不可原地改义。
- 新代码需要通过旧事件与旧快照升级测试。
- 不能读取的旧规则内容需要与应用一起保留或提供明确迁移工具。

## 13. 隐私与安全

- 本地临时昵称属于本地档案数据。
- 席位恢复令牌不进入永久事件日志。
- 诊断导出默认脱敏设备令牌和网络地址。
- 私人游戏状态可以存在权威快照，但按权限生成录像视图。
- 未来账号凭据存储在独立身份系统，不塞入本地游戏事件表。

## 14. 容错场景

必须测试：

- 事务写入过程中终止 Host
- 事务提交后、广播前终止 Host
- 写快照过程中终止 Host
- WAL 检查点期间终止 WSL2
- 磁盘空间耗尽
- 数据库只读或权限错误
- 最新快照损坏但旧快照有效
- 某个事件负载损坏
- WSL2 IP 改变但数据库保持完整
- Windows 睡眠后继续对局

## 15. 公网迁移

未来使用服务器数据库时保留：

- Game、Seat、Event、Snapshot 和 Summary 领域模型
- 单局命令串行化
- 先提交后广播
- 规则集哈希和状态指纹
- 幂等命令结果

需要替换的是物理数据库、分布式锁、对象存储和保留策略，而不是规则事件语义。
