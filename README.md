# Carcassonne 数字桌游项目

> 当前状态：需求、规则与技术设计阶段；Node.js/TypeScript 技术方向已经确认，等待目标 Windows/WSL2 环境验证，尚未进入功能开发。

本项目计划制作一套机制优先的数字拼图桌游系统。第一阶段以 Windows 电脑作为局域网权威主机，通过 4K 电视展示公共棋盘，玩家使用手机浏览器作为个人控制器。系统首先准确实现当前官方基础规则，并为扩展、互联网服务、3D 表现和 AR 保留演进空间。

`Carcassonne` 目前是项目工作名称。若项目未来公开或商业发行，产品名称、美术、规则文本和相关知识产权需要另行评估；项目自产的视觉素材不得直接复刻官方素材。

## 已确认的优先级

1. 规则与计分正确性
2. 主机权威与状态一致性
3. 手机控制器和聚会交互
4. 基础画面可读性与性能
5. 3D、美术、声音和特效升级
6. AR 与公网服务

## 首阶段目标

- Windows 主机可完全离线创建并恢复局域网对局。
- 4K 电视显示公共 3D 棋盘、计分和当前回合。
- iOS、Android 手机通过二维码加入并操作自己的席位。
- 基础游戏支持官方的 2–5 人。
- 启用第六套玩家组件的规则集支持官方的 2–6 人。
- 基础规则、农夫、河流和修道院长均有明确的规则模块与测试用例。
- 真人和 AI 使用同一套确定性规则引擎。
- 手机断线、Windows 应用重启后可以恢复对局。
- 协议和数据模型能够在未来将权威主机迁移到公网服务器。

## 文档索引

- [产品需求](docs/PRODUCT_REQUIREMENTS.md)
- [基础规则纲要](docs/GAME_RULES.md)
- [地块与扩展目录](docs/TILE_AND_EXPANSION_CATALOG.md)
- [交互与大屏设计](docs/INTERACTION_AND_DISPLAY.md)
- [局域网架构](docs/LAN_ARCHITECTURE.md)
- [技术栈调研](docs/TECH_STACK_RESEARCH.md)
- [实现架构](docs/IMPLEMENTATION_ARCHITECTURE.md)
- [规则引擎技术设计](docs/RULE_ENGINE_TECHNICAL_DESIGN.md)
- [局域网协议](docs/LAN_PROTOCOL.md)
- [持久化设计](docs/PERSISTENCE_DESIGN.md)
- [技术验证计划](docs/TECHNICAL_SPIKES.md)
- [游戏模式与未来在线服务](docs/ONLINE_AND_GAME_MODES.md)
- [视觉、素材与 AR 方向](docs/VISUAL_AND_AR_DIRECTION.md)
- [实施与验收路线](docs/DELIVERY_PLAN.md)
- [决策日志](docs/DECISIONS.md)

## 规则资料基线

- [Hans im Glück 当前基础游戏页](https://www.hans-im-glueck.de/en/game/carcassonne/)
- [Z-Man 当前基础规则 PDF](https://images.zmangames.com/filer_public/24/b9/24b924f3-b7d0-464f-9d1d-618bd01e38a0/carcassonne_v3_rulesheet_en_revised_ab.pdf)
- [Z-Man 农夫、河流和修道院长补充规则 PDF](https://images.zmangames.com/filer_public/39/ae/39aecf66-33ea-48a1-a53a-fcb885cb084b/carcassonne_v3_supplement_en_fixed_jan_20.pdf)
- [Hans im Glück 2025 扩展更新公告](https://www.hans-im-glueck.de/en/?news=a-new-carcassonne-world)
- [Hans im Glück 当前扩展目录](https://www.hans-im-glueck.de/unsere-spiele/carcassonne-erweiterungen/)
- [Hans im Glück 当前小扩展目录](https://www.hans-im-glueck.de/unsere-spiele/carcassonne-mini-erweiterungen/)

技术选型文档中的版本信息以 2026-07-23 的官方资料为准。进入开发后，实际依赖版本由仓库锁文件和技术决策记录确定，不自动追随最新版。

任何实现都不得只依赖本文档的摘要。每个规则模块进入开发前，必须重新核对对应版本的官方规则、组件清单和官方示例。
