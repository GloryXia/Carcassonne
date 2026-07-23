# 技术验证计划

- 文档版本：0.1
- 状态：待执行
- 原则：先消除高风险假设，再创建正式工程骨架

## 1. 当前限制

当前工作区运行在 macOS，已检测到 Node.js 22 与 pnpm，但目标运行时是 Node.js 24 LTS，且没有 Godot 或 Blender。WSL2、Windows 防火墙、4K 电视和真实手机局域网必须在 Windows 目标机上验证，不能由 macOS 结果替代。

## 2. Spike 0：工具链与仓库基线

### 目标

- 确认精确 Node.js、pnpm、TypeScript、依赖和引擎版本可以共同构建。
- 建立最小可复现开发环境。

### 工作

- 在 WSL2 安装并锁定 Node.js 24 LTS、Corepack 与 pnpm。
- 在 Windows 准备同版本便携 Node.js 运行时。
- 在 Windows 安装 Godot 4.7.1 标准版及对应导出模板。
- 确认 TypeScript、Fastify、React 和 Vite 构建。
- 初始化 Git、忽略规则、版本锁定和基础 CI。
- 确认许可证记录方式。

### 通过标准

- 干净机器按照文档可以构建空 Node.js Host、空 Controller 和空 Godot/GDScript 客户端。
- 版本由锁文件或配置固定。
- CI 可以运行 TypeScript 类型检查、规则测试和 Web 测试。
- 依赖树、原生扩展、许可证与安装脚本均有记录。

## 3. Spike 1：WSL2 NAT 局域网

### 目标

验证 Windows、WSL2、Godot 和六部手机在不同 IP 下可靠连接。

### 工作

1. WSL2 保持默认 NAT。
2. 在 WSL2 内运行监听 `0.0.0.0` 的 Node.js/Fastify Host。
3. Launcher 使用 `wsl.exe -d <distro> hostname -I` 取得 WSL2 IPv4。
4. 动态建立 Windows `portproxy` 到 WSL2。
5. 创建只允许局域网配置文件和指定端口的防火墙规则。
6. Windows Godot/测试客户端连接 localhost 或 WSL2 IP。
7. iOS Safari、Android Chrome 扫码连接 Windows LAN IP。
8. 重启 WSL2，确认 IP 变化后 Launcher 能更新转发。

### 测试环境

- 家用路由器
- Windows 热点
- 有 VPN 与无 VPN
- 多网卡电脑
- 访客 Wi-Fi 或客户端隔离网络，用于确认失败提示

### 通过标准

- 六部手机可以同时加入并维持 60 分钟连接。
- WSL2 重启后无需用户手工修改 IP 或 netsh 规则。
- QR 始终使用手机可达的 Windows 地址。
- 关闭房间后端口转发和临时规则按设计清理。
- 无管理员权限时提供明确降级或安装引导。

### 失败回退

- Game Host 运行 Windows 原生构建。
- 或由 Windows 原生反向代理进程转发到 WSL2，而不是依赖全局 portproxy。

## 4. Spike 2：标准 WebSocket 协议

### 目标

验证标准 WebSocket 在 React、Godot/GDScript 和 WSL2 Node.js Host 之间的兼容性。

### 工作

- 使用 `ws` 或 `@fastify/websocket` 实现最小 Join、Seat、Heartbeat、Command、Event 和 Snapshot。
- 六个浏览器连接加入同一组。
- Godot 接收公共事件。
- 模拟消息重复、乱序、延迟和断线。
- 验证客户端退避重连、一次性 Socket Ticket 和席位恢复。
- 测量包大小、运行内存和发布兼容性。
- 验证最大消息、慢客户端、发送缓冲、心跳超时和异常 JSON。

### 通过标准

- 正式命令可以幂等重试。
- 丢失事件会触发增量补发或快照。
- Godot `WebSocketPeer` 可以稳定收发 JSON，并成功发布 Windows 构建。
- WebSocket 连接更换不改变席位。
- 私人负载不会广播到公共客户端。
- 服务端只暴露 RFC 6455，不要求 Godot 实现框架私有实时协议。

### 失败回退

保持消息 Schema 和标准 WebSocket，替换 Node.js 服务端 WebSocket 包；若 Fastify 插件集成有问题，则由 `ws` 直接接管同一个 HTTP Server 的 Upgrade。

## 5. Spike 3：确定性规则切片

### 目标

验证事件驱动规则核心和拓扑设计。

### 内容

- 10–20 块测试地块
- 道路、城市和田野段
- 两名玩家
- 地块旋转与合法放置
- 普通随从放置
- 完成道路和城市计分
- 固定随机洗牌
- 事件、快照和状态指纹

### 通过标准

- 10,000 次相同日志重放得到相同终局指纹。
- Node.js 24 在 WSL2 Linux、Windows 和 CI 上的结果一致。
- 拒绝命令不改变状态。
- 从多个快照点恢复得到相同终局。
- UI 不参与任何规则判断。

## 6. Spike 4：Node.js SQLite 崩溃恢复

### 目标

确认“先提交、后广播”及 WSL2 文件系统存储可以承受异常退出。

### 工作

- 实现最小 Event、Snapshot、Game 和 CommandResult 表。
- 对比 Node.js 24 `node:sqlite` 与 `better-sqlite3`，锁定一个驱动。
- 每次动作使用单事务。
- 在事务前、事务中、提交后广播前和快照中强杀 Host。
- 测试 WAL、同步级别和检查点。
- 使用所选驱动的 SQLite Online Backup API 导出到 Windows。
- 测量同步事务、快照压缩和备份对 Node.js 事件循环延迟的影响。

### 通过标准

- 已确认动作不会丢失或重复。
- 未提交动作不会出现在恢复状态。
- 最新快照损坏时可以退回上一快照。
- 备份文件可以独立打开并通过校验。
- 活跃数据库不需要放在 `/mnt/c`。
- 六个连接持续心跳时，数据库动作不得造成可感知的长时间事件循环停顿。

## 7. Spike 5：Godot 4K 棋盘

### 目标

验证 Godot 能在目标 Windows 硬件上显示长局地图。

### 场景

- 200 块占位地块
- 每块包含地表、道路、简单建筑和植被实例
- 6 种玩家角色
- 合法位置和区域轮廓
- 自动聚焦、全图和局部镜头
- 4K UI 与动态 3D 分辨率

### 测量

- Forward+、Mobile、Compatibility 渲染器
- Vulkan、D3D12 及回退行为
- 集成显卡与独立显卡
- 30/60 FPS、显存、内存和加载时间
- MultiMesh、LOD 和分区策略

### 通过标准

- 参考独立显卡达到稳定 4K UI / 60 FPS 目标。
- 参考集成显卡通过动态 3D 分辨率达到稳定 30 FPS。
- 地图扩大后文字、轮廓和当前区域仍清楚。
- 显示端重启不影响 Host 对局。

## 8. Spike 6：Godot 与 Babylon.js 显示对照

只有 Spike 5 达不到目标或开发工作流明显受阻时执行完整对照。

使用相同 GLB、相机和 200 地块场景比较：

- 4K 性能
- 包体和启动时间
- 资产迭代
- Shader/融合表现
- 崩溃隔离
- 全屏电视与输入
- 发布和更新复杂度

若两者接近，优先 Godot；只有 Web 方案在维护和性能上具有明确优势时才切换。

## 9. Spike 7：Windows Launcher 与打包

### 目标

验证普通用户可以启动整个系统，而不需要手工运行命令。

### 工作

- 使用 Windows 便携 Node.js 运行 Launcher
- 检测/启动 WSL2 发行版
- 动态端口与 portproxy
- 防火墙引导
- Host 健康检查
- Godot 启动和关闭
- 日志与诊断包
- 原生 Host 降级
- Windows 睡眠、恢复和重启

### 通过标准

- 双击一次即可出现可扫码房间。
- 无 WSL2、无权限、端口冲突和网络隔离都有明确提示。
- 正常关闭不会留下失效转发规则或损坏数据库。
- 异常退出后下次启动能够恢复。

## 10. Spike 8：手机交互

### 目标

验证手机网页是可用的聚会控制器。

### 设备

- 不同尺寸 iPhone/Safari
- Android/Chrome
- 横屏、竖屏和系统字体放大
- 低电量模式和后台切换

### 通过标准

- 扫码到加入席位的中位时间不超过 10 秒。
- 地块位置、旋转、角色和跳过不需要复杂手势。
- 当前玩家切后台并返回后恢复原状态。
- 44–48 dp 触控目标和颜色替代提示通过人工检查。

## 11. Spike 9：AR Lite

不阻塞基础开发。规则和 3D 资产稳定后验证：

- GLB/场景资产在手机 AR 中的比例和性能
- 单设备平面放置
- 地图规模和遮挡
- 公共锚点的候选方式

若 AR 需要 Unity 原生客户端，再单独评估 Unity 6.3 LTS 和 AR Foundation，不改变 TypeScript Rules Core 或 Node.js Game Host。

## 12. 决策门禁

强制完成 Spike 0–5 与 Spike 7 后召开技术决策检查。Spike 6 只在 Godot 验证失败或工作流明显受阻时执行；Spike 8 属于手机交互阶段，Spike 9 属于后续 AR 阶段，不阻塞本次技术门禁。

- WSL2 NAT + portproxy 是否达到零手工维护？
- 标准 WebSocket 是否同时适合 React 和 Godot，并能稳定恢复？
- 规则重放是否跨平台确定？
- SQLite 是否满足崩溃恢复？
- Godot 是否满足 4K 性能？
- Windows Launcher 是否能完成免手工启动、诊断、转发清理和原生 Host 降级？

全部通过后，复核 D-014 的已确认技术方向；将 D-015 从“提议”改为“已确认”，或用新的决策记录替换未通过的方案，再创建正式产品工程。

## 13. 结果记录模板

每个 Spike 记录：

- 日期、提交和依赖版本
- 目标硬件、系统和网络
- 测试步骤和原始数据
- 通过/失败项
- 已知限制
- 截图、日志或录像位置
- 结论和对 ADR 的影响

不能只用“感觉流畅”或“基本可用”作为技术决策依据。
