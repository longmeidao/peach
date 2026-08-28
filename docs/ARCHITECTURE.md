# 总体架构

## 产品形态

Peach 是逻辑前后端分离、部署仍为一个进程的 FastAPI 模块化单体。默认单用户、本地自托管；在线追更、外部元数据和可插拔 AI 是正式能力。未来远程访问通过 VPN/Tunnel，或 DDNS + 反代 + HTTPS；应用端口不直接裸露公网。

## 核心边界

1. **Ledger**：资产、行为、来源和知识的唯一真相源。SQLite 适合当前单用户规模。硬盘上的那份是权威副本，两台机器各持本地工作副本，由 `peach.sync` 做单写者复制：拉取、回写、冲突转只读，**不做多主合并**。
2. **API / 应用层**：FastAPI 承载页面、JSON、媒体响应和写入边界。
3. **平台层**：`peach.platform` 是账本路径与本机挂载点之间唯一的翻译层。账本只用 Windows 盘符记录路径，读取时按 `PEACH_DRIVE_MAP` 翻译到本机挂载点；没有挂载点的盘符落到不可达根，对应来源整体按脱盘处理。CloudDrive 在 Windows 是盘符、在 macOS 是 macFUSE 挂载点，差异全部收敛在这里。
4. **Media Engine**：FastAPI 只持有一个 `MediaEngine`。本地文件是原生后端；Stash 是公开协议适配器，再按扫描、元数据、预览、流媒体逐项替换。挂载网盘的已知时长原生 MP4 由 `stream-plan` 选择按时间生成的 HLS 片段，其他情况回退标准 Range。
5. **Web**：当前是无构建步骤的单页，保持移动端优先；不做 React 重写。
6. **AI Provider**：`InferenceProvider` 与 `AgentProvider` 分离。AI 只产出带来源和置信度的候选。
7. **Profile**：默认单用户，数据模型预留 user/profile，不引入完整账号体系。
8. **追更来源**：RSS/Atom 等成熟协议先归一化为只读候选；原始证据、复核和 ledger 写入分层。
9. **任务系统**：Peach 自己定义来源成本、磁盘闸门、进程归属、进度和来源证据；HTTP、调度、媒体探测、图片与协议解析使用成熟组件。
10. **HTTP / 搜索**：网络适配器默认共用长生命周期 HTTPX transport；FANBOX 公开 `post.info` 是有证据登记的窄例外，使用固定版本 `curl_cffi` 保留 Firefox TLS/HTTP2 传输特征，但不求解质询、不登录、不读取付费内容。作品全文搜索使用 SQLite FTS5 trigram，短查询保留 LIKE 回退。

## 数据流

```text
本地/网盘/在线来源 -> 索引/探测 -> ledger.db
                                  -> FastAPI -> Web/播放器
Stash ---------------- Media 适配器 --^
AI/外部元数据 -> 经复核的候选 -> ledger
```

## 明确不做

- 微服务、消息总线、PostgreSQL
- 重型前端框架迁移
- 抓取或保存 ChatGPT/Claude OAuth token
- 将 Stash 私有目录或 GPL 构建作为 Peach 的稳定打包依赖

关键取舍见 `docs/adr/`；Stash 的代码级证据见 `docs/STASH.md`。
复用/自研边界及旧脚本继任关系见 `docs/REUSE.md`。

## 运行数据目录

Windows 与 macOS 各自在内置盘持有代码、`peach-data`、`.venv` 和 worktree；外置盘只提供
`R:\media` / `/Volumes/RESOURCES/media`。代码与任务分支走私有 GitHub，worktree 目录本机重建；
账本走 Peach 单写者复制，其他运行数据按 durable artifact 与本机状态拆分，禁止整体同步。
Windows 内置盘环境、共享账本传输点、显式 writer/reader 和生成产物的跨机同步都已完成；
durable artifact 拆分仍待续，见 ADR-0017 与 `docs/STATUS.md`。三条链路各走各的：代码走 Git，
账本走 Peach 单写者复制，图片产物走 Syncthing 单向同步，互不兜底。

`peach-data` 与代码仓库刻意分离（Windows 为 `C:\Users\longm\Desktop\peach\peach-data`，
macOS 为 `~/Desktop/lmd.gg/peach/peach-data`，由 `PEACH_DATA_ROOT` 覆盖）：

- `database/`：SQLite 真相库。本地是工作副本，血缘记在同目录的 `ledger.db.sync.json`
- `generated/`：快照、海报、头像和厂牌 Logo
- `sources/`：浏览器、追更、盘点和导出等不可变原始输入
- `state/`：人工维护的本机状态和锁
- `secrets/`：仅本机保存的凭据材料
- `logs/`：当前运行日志
- `archive/`：历史迁移证据和备份
- `inbox/`：等待处理的临时导入
- `tools/`：FFmpeg 等本机托管运行时；二进制和许可证不进入 Git

以上是约定的分层，不是每台机器的实测形状。Mac 上 `generated` 是指向 `artifacts` 的符号链接，
另有 `review`、`tmp`，且 `archive`/`sources`/`tools` 指向外置盘。动手前以 `docs/STATUS.md` 为准。
