# 技术栈调研

- 调研日期：2026-07-23
- 状态：Node.js 方向已确认，精确依赖等待技术验证后锁定
- 目标平台：Windows 11 + WSL2 + 4K 电视 + iOS/Android 浏览器

## 1. 结论摘要

首阶段不使用 .NET。推荐验证以下组合：

| 层 | 推荐技术 | 原因 |
|---|---|---|
| 规则核心 | TypeScript 7 + Node.js 24 LTS | 与主机、协议和测试共用语言；强类型领域模型；可运行于 WSL2 和未来 Linux 服务 |
| 局域网主机 | Fastify 5 / Node.js | 提供 HTTP、静态文件、Schema 校验和健康检查，进程模型轻量 |
| 实时通信 | 标准 WebSocket + JSON | 浏览器和 Godot 都有原生客户端；协议不绑定 SignalR 或 Socket.IO |
| 手机控制器 | React 19.2 + TypeScript + Vite 8 | 移动浏览器支持好，构建结果可由本地主机直接提供 |
| Windows 3D | Godot 4.7.1 标准版 + GDScript | MIT 许可、无需 .NET、内建 WebSocket、glTF 管线和多档渲染器 |
| 本地存储 | SQLite + Node 数据库适配层 | 单文件、事务、无独立数据库服务，适合单主机事件日志与快照 |
| 测试 | Vitest + fast-check + 协议场景夹具 | 支持单元、性质、场景和确定性重放测试 |
| 运行环境 | WSL2 默认 NAT + Windows 端口转发 | Windows 与 WSL2 可以使用不同 IP，服务端接近未来 Linux 部署环境 |

当前版本快照：Node.js 24.18.0 LTS、Fastify 5.10.0、`ws` 8.21.1、TypeScript 7.0.2。正式工程不使用浮动版本，完成技术验证后以 `package.json`、`pnpm-lock.yaml` 和 Corepack 配置为准。

## 2. Node.js 与 TypeScript

Node.js 24 是当前 LTS 版本线，Node.js 26 在本次调研时仍为 Current，因此主机选择 Node.js 24，不追逐非 LTS 运行时。

规则核心与主机统一使用严格 TypeScript：

- `strict`、`noUncheckedIndexedAccess` 和 `exactOptionalPropertyTypes` 必须开启。
- 使用 ESM，不混用 CommonJS。
- 领域对象使用只读值、判别联合和品牌化 ID，避免到处传裸字符串。
- 规则核心不访问网络、SQLite、文件、系统时间或全局随机数。
- 规则数值限制在安全整数内；位运算和随机算法必须显式规范化为无符号 32 位结果。
- 规范序列化必须排序键和集合，不能依赖对象构造顺序生成状态指纹。
- CPU 密集型 AI 搜索放入 `worker_threads`，不能阻塞房间连接和心跳。

官方资料：

- [Node.js 发布状态](https://nodejs.org/en/about/previous-releases)
- [Node.js 24.18.0 LTS](https://nodejs.org/en/blog/release/v24.18.0)
- [TypeScript 项目内安装与锁定](https://www.typescriptlang.org/download/)
- [Node.js 稳定测试运行器](https://nodejs.org/api/test.html)

## 3. HTTP 主机：Fastify

Fastify 负责：

- 手机控制器静态文件
- 健康检查、引导、加入、快照和导出 HTTP API
- 请求体与响应体的 JSON Schema 校验
- 日志关联、消息大小、限流和错误边界
- WebSocket Upgrade 的认证入口

选择 Fastify 而不是引入更重的全栈框架，是为了让领域边界保持清楚。房间、规则、持久化和投影仍由独立包实现，不能写进路由处理器。

Fastify 5 支持 Node.js 20 及以上；目标 Node.js 24 位于其支持范围。具体 Fastify 小版本在 Spike 0 锁定。

官方资料：

- [Fastify 5 文档](https://fastify.dev/docs/v5.7.x/)
- [Fastify LTS 策略](https://fastify.dev/docs/latest/Reference/LTS/)
- [Fastify v5 迁移与 Node.js 要求](https://fastify.dev/docs/v5.0.x/Guides/Migration-Guide-V5/)

## 4. 实时通信：标准 WebSocket

首选 RFC 6455 WebSocket，不采用 SignalR，也不把 Socket.IO 协议作为必要层：

- 浏览器直接使用原生 `WebSocket`。
- Godot 标准版直接使用 `WebSocketPeer`。
- Node.js Host 使用 `ws` 或 `@fastify/websocket`；二者的准确组合由 Spike 2 决定。
- 负载首阶段为带版本的 JSON 文本帧。
- 心跳、认证、重连、幂等、事件补发和快照恢复由项目协议显式实现。

`ws` 只提供传输，不替项目承诺消息持久化。正式事件仍要先写入 SQLite，再广播；客户端通过事件序号发现缺口并请求补发或快照。

官方资料：

- [`ws` 官方仓库与心跳示例](https://github.com/websockets/ws)
- [Godot `WebSocketPeer`](https://docs.godotengine.org/en/stable/classes/class_websocketpeer.html)

## 5. Windows 3D：Godot 标准版

Godot 只负责 Windows 原生公共显示，不承载权威规则。使用标准版和 GDScript，避免安装或发布任何 .NET 运行时。

优点：

- MIT 许可和较轻的 Windows 发布流程。
- glTF/GLB 资产管线适合 Blender 与程序化素材。
- Forward+、Mobile、Compatibility 渲染器覆盖不同 Windows 硬件。
- 内建标准 WebSocket 客户端，可直接使用项目 JSON 协议。
- 显示进程重启不会影响 WSL2 内的权威对局。

风险：

- TypeScript 类型不能直接被 GDScript 引用，必须通过 JSON Schema、示例夹具和契约测试维持边界。
- 高级 VFX、AR 与商业工具生态弱于 Unity，仍需保留替换空间。
- 4K 大地图和长时间运行必须在目标 GPU 上实测。

官方资料：

- [Godot 官方发布档案](https://godotengine.org/download/archive/)
- [Godot Windows 导出](https://docs.godotengine.org/en/stable/tutorials/export/exporting_for_windows.html)
- [Godot 渲染器比较](https://docs.godotengine.org/en/stable/tutorials/rendering/renderers.html)
- [Godot MIT 许可](https://godotengine.org/license/)

## 6. 手机控制器

Controller Web 继续使用 React、TypeScript 与 Vite：

- 与 Host 和 Rules 共用协议类型及测试夹具。
- 生产构建是静态文件，运行时不需要单独的前端开发服务器。
- 页面、HTTP API 与 WebSocket 由同一个 Fastify Host 提供，维持同源。
- 真正的手机兼容范围以 iOS Safari、Android Chrome 实机测试为准。

官方资料：

- [React 当前版本](https://react.dev/versions)
- [Vite 指南与浏览器支持](https://vite.dev/guide/)
- [Vite 发布策略](https://vite.dev/releases)

## 7. SQLite 与 Node 适配层

数据库模型和“先提交、后广播”原则保持不变。Node.js 侧先验证两个驱动候选：

1. Node.js 24 内建 `node:sqlite`：依赖少并提供备份 API，但调研时仍标记为 Release Candidate。
2. `better-sqlite3`：成熟的同步事务 API，但包含原生扩展，需要验证 Node.js 24、WSL2 发布和升级兼容性。

选择标准：

- 事务和参数化 SQL 正确性
- WAL、`synchronous=FULL` 与受控检查点
- 一致备份能力
- 崩溃恢复结果
- 原生依赖和离线安装复杂度
- 六人局域网负载下对事件循环的影响

数据库访问封装在 `persistence-sqlite` 包内，规则和协议不得直接依赖具体驱动。活跃数据库继续放在 WSL2 ext4，不放在 `/mnt/c`。

官方资料：

- [Node.js `node:sqlite`](https://nodejs.org/download/release/latest-v24.x/docs/api/sqlite.html)
- [SQLite 官方概览](https://www.sqlite.org/about.html)
- [SQLite WAL](https://www.sqlite.org/wal.html)
- [SQLite 在线备份 API](https://www.sqlite.org/backup.html)

## 8. WSL2 主机

网络方案不因技术栈变化而改变：

- WSL2 使用默认 NAT 和独立 IP。
- Node.js Host 在 WSL2 内监听 `0.0.0.0:<hostPort>`。
- 手机访问 Windows 局域网 IP，由 Windows `portproxy` 转发到 WSL2 IP。
- Windows Launcher 每次启动查询 WSL2 IP 并刷新转发。
- 防火墙只开放选定游戏端口和局域网配置文件。
- Host、依赖和 SQLite 活跃文件位于 WSL Linux 文件系统。

官方资料：

- [WSL 网络](https://learn.microsoft.com/en-us/windows/wsl/networking)
- [WSL systemd](https://learn.microsoft.com/en-us/windows/wsl/systemd)
- [跨文件系统工作](https://learn.microsoft.com/en-us/windows/wsl/filesystems)

## 9. Windows Launcher

Launcher 不使用 .NET。首阶段采用 TypeScript/Node.js：

- Windows 侧随产品携带锁定的便携 Node.js 运行时，不要求用户预装开发环境。
- Launcher 调用 `wsl.exe`、`netsh` 和 Godot 可执行文件，完成 IP、转发、防火墙、健康检查和关闭流程。
- 先实现可双击启动的 CLI/轻量状态窗口；是否改用原生壳由打包 Spike 决定。
- WSL2 不可用时，可运行同一 Node.js Host 的 Windows x64 发布包作为降级后端。

## 10. Unity 与 Babylon.js 备选

- Unity 6.3 LTS：只有 AR 被提升为核心交付，或 Godot 4K 验证失败时才评估。Unity 不进入权威规则或 Node.js Host。
- Babylon.js：若 Godot 工作流受阻，可用相同 GLB 和 WebSocket 协议进行 4K 对照；它可以与 Controller 共用 TypeScript 工具链。

## 11. 当前开发机状态

调研时本工作区检测到：

- Node.js 22.22.1
- npm 10.9.4
- pnpm 10.15.1
- 尚未安装 Godot
- 尚未安装 Blender

项目目标是 Node.js 24 LTS，因此当前本机 Node.js 22 只用于文档和轻量检查，不作为正式运行基线。本轮不创建未经 Node.js 24、Windows/WSL2 和 Godot 验证的工程骨架。

## 12. 版本锁定原则

- `package.json` 的 `engines` 固定 Node.js 24 主版本范围。
- Corepack 固定 pnpm 版本并提交 `pnpm-lock.yaml`。
- TypeScript、Fastify、WebSocket、测试和数据库驱动固定精确版本。
- 审核依赖脚本、原生扩展、许可证和安全公告。
- Godot 记录精确编辑器版本和导出模板校验值。
- 生产分支不自动追随 `latest`；版本升级单独验证重放、协议与存档兼容性。

## 13. 推荐结果

推荐进入技术验证的组合是：

> Windows Godot 4.7.1 标准版显示端 + WSL2 NAT 中的 Node.js 24/TypeScript/Fastify Game Host + 标准 WebSocket/JSON + React 手机控制端 + SQLite。

首阶段不使用 .NET、ASP.NET Core 或 SignalR。最终依赖由 Node.js 24 构建、六手机连接、确定性重放、SQLite 崩溃恢复、Godot 4K 和 Windows 打包六项实测共同锁定。
