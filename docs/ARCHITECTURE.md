# Architecture

## Product shape

Peach 是逻辑前后端分离、部署仍为一个进程的 FastAPI 模块化单体。默认单用户、本地自托管；在线追更、外部元数据和可插拔 AI 是正式能力。未来远程访问通过 VPN/Tunnel，或 DDNS + 反代 + HTTPS；应用端口不直接裸露公网。

## Core boundaries

1. **Ledger**：资产、行为、来源和知识的唯一真相源。SQLite 适合当前单用户规模。
2. **API/application**：FastAPI 承载页面、JSON、媒体响应和写入边界。
3. **Media Engine**：本地文件为原生 backend；Stash 先作为 adapter，再按扫描、元数据、预览、流媒体逐项替换。
4. **Web**：当前是无构建步骤的单页，保持移动端优先；不做 React 重写。
5. **AI providers**：`InferenceProvider` 与 `AgentProvider` 分离。AI 只产出带 provenance/confidence 的候选。
6. **Profiles**：默认单用户，数据模型预留 user/profile，不引入完整账号体系。

## Data flow

```text
local/network/online sources -> index/probe -> ledger.db
                                           -> FastAPI -> web/player
Stash ----------------------- Media adapter --^
AI/external metadata -> reviewed candidates -> ledger
```

## Non-goals

- 微服务、消息总线、PostgreSQL
- 重型前端框架迁移
- 抓取或保存 ChatGPT/Claude OAuth token
- 将 Stash 私有目录或 GPL 构建作为 Peach 的稳定打包依赖

关键取舍见 `docs/adr/`；Stash 的代码级证据见 `docs/STASH.md`。

## Runtime data layout

`R:\peach-data` is intentionally separate from the repository:

- `database/`: SQLite truth store
- `generated/`: snapshots, posters, avatars and logos
- `sources/`: immutable/raw browser, follow, inventory and export inputs
- `state/`: curated local state and locks
- `secrets/`: local-only secret material
- `logs/`: current operational logs
- `archive/`: historical migration evidence and backups
- `inbox/`: transient imports awaiting processing
