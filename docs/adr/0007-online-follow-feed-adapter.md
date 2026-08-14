# ADR-0007：在线追更首先复用 RSS/Atom 协议

- 状态：Accepted
- 日期：2026-08-14

## 背景

Peach 把在线追更列为正式能力，但尚无 connector。直接从站点 HTML、私有接口或浏览器状态开始，会把站点易变结构、认证、抓取和 ledger 写入耦合在一起。

## 决策

- 第一类追更 connector 复用 RSS 2.0/Atom 公开协议，由 `FeedAdapter` 统一输出稳定候选 DTO。
- 网络请求只能由显式调用触发；服务启动、health 和普通浏览均不自动联网。
- adapter 支持 ETag/Last-Modified 条件请求、15 秒超时、5 MiB 有界读取，以及 RSS enclosure/Atom enclosure 媒体候选。
- URL 只允许无内嵌凭据的绝对 HTTP(S) 地址；凭据不得写入 URL、日志或 ledger。
- adapter 只发现候选，不自动写 ledger 真相。`FeedSnapshotStore` 把不可变原始响应与规范化旁车存入 `peach-data/sources/follow`，把条件请求游标存入 `peach-data/state/follow`；后续通过带 source/provenance/review 的导入边界写入。
- 无 feed 的站点以后实现独立 connector；不得把站点专用 HTML 规则塞进通用 feed adapter。

## 后果

Peach 获得可测试、低耦合的首个在线追更边界，并复用成熟协议；具体 feed 配置、调度和 reviewed import 仍需下一阶段实现。当前没有对真实站点发起追更请求，也没有修改 ledger。

## 拒绝方案

- 服务启动时自动轮询所有来源。
- 用浏览器 Cookie 或 URL 内嵌账号密码抓取。
- 解析结果直接创建/覆盖资产。
- 为首个 connector 引入独立抓取服务或消息队列。
