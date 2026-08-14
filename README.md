# Peach

Peach（蜜桃）是一个单用户、本地优先的个人媒体系统：统一索引本地/网盘/在线资产，记录真实消费反馈，并逐步提供搜索、推荐和追更。

当前界面以作品、女优、厂牌、创作者和系列实体为导航：名字进入带简介、别名和渠道链接的资料页，内容标签才直接叠加筛选。“稍后看”和“喜欢/为什么喜欢”使用独立 profile 数据，不和“看过/不喜欢”混用；用户原始偏好说明是本机真相，AI 以后只能提出可审核的归一化候选。

## 边界

- 项目代码：`R:\peach-app`
- 真实数据：`R:\peach-data`
- 本地媒体：`R:\media`
- 网盘挂载：`A:\`、`B:\`
- 真相数据库：`R:\peach-data\database\ledger.db`
- Stash：过渡期可替换 adapter，不是真相源

项目仓库不保存媒体、数据库、凭据、快照、封面或运行日志。

`R:\peach-data` 使用固定分层：`database` 保存真相库，`generated` 保存可再生成的视觉资产，`sources` 保存原始分析输入，`state` 保存人工维护状态，`secrets` 保存本机凭据材料，`logs` 保存运行记录，`archive` 保存历史备份，`inbox` 是临时下载落地区，`tools` 保存不进入 Git 的本机运行时工具。

## 结构

```text
peach-app/
├─ src/peach/        FastAPI、Media Engine、迁移和 Provider 边界
├─ web/index.html    当前无构建步骤的前端
├─ migrations/       有版本和校验和的 SQLite 迁移
├─ scripts/          仍在使用的运维/索引命令
├─ tests/            全隔离测试
├─ docs/             架构、状态、交接和 ADR
├─ AGENTS.md         Codex/Claude 共用工作契约
└─ CLAUDE.md         Claude 自动导入 AGENTS.md
```

## 开发

```powershell
cd R:\peach-app
& py -3.14 -m venv .venv
& .\.venv\Scripts\python.exe -m pip install -e .
& .\.venv\Scripts\python.exe -m unittest discover -s tests -p 'test_*.py' -v
& .\.venv\Scripts\peach.exe migrate status
& .\.venv\Scripts\peach.exe serve --port 8900
```

`serve` 默认只监听 `127.0.0.1:8900`。公网、反代、HTTPS 和认证属于后续部署阶段，不在开发命令中隐式开启。

需要本机 TLS 时同时提供证书和私钥；二者应放在 `R:\peach-data\secrets`，不要提交 Git：

```powershell
& .\.venv\Scripts\peach.exe serve --host 0.0.0.0 --port 443 `
  --mdns-address 192.168.50.162 `
  --ssl-certfile R:\peach-data\secrets\tls\peach.crt `
  --ssl-keyfile R:\peach-data\secrets\tls\peach.key
```

证书必须包含实际访问名（例如 `peach.local`）并被客户端信任；启用 TLS 时 mDNS 自动发布 HTTPS。

本机局域网不使用 Let's Encrypt。项目提供可重复执行的本地 CA + 服务器证书生成脚本；默认只写
`R:\peach-data\secrets\tls`，`-TrustCurrentUser` 只把 CA 加入当前 Windows 用户的信任库：

```powershell
& .\scripts\setup_local_tls.ps1 -Address 192.168.50.162 -TrustCurrentUser
```

每台访问设备都必须单独信任 `peach-local-ca.crt`，只需安装一次，证书续签仍可沿用同一 CA：

- macOS：把 CA 拖入“钥匙串访问”的“登录”或“系统”钥匙串，双击后在“信任”中将 SSL
  设为始终信任。Apple 官方步骤：<https://support.apple.com/guide/keychain-access/kyca11871/mac>。
- iPhone/iPad：先安装 CA 描述文件，再进入“设置 → 通用 → 关于本机 → 证书信任设置”，
  为该根证书开启完全信任。Apple 官方步骤：<https://support.apple.com/en-us/102390>。
- 只传 `peach-local-ca.crt`。绝不传 `peach-local-ca.key`、`peach.key` 或整个 `tls` 目录。

如果不愿在设备上安装本地 CA，继续使用 `http://peach.local`。浏览器无法在不信任 CA 的
前提下把自签 HTTPS 变成无警告连接；Let's Encrypt 也不会签发 `.local`。

当前运行态与下一任务只看 [`docs/STATUS.md`](docs/STATUS.md)；跨 Codex/Claude 的固定接手方式只看 [`docs/HANDOFF.md`](docs/HANDOFF.md)。
准备新增、恢复或替换实现前，必须查 [`docs/REUSE.md`](docs/REUSE.md)，避免按旧文件名重复造轮子。

## 批处理安全边界

`scripts/scrape_codes.py` 默认只把番号发送到已声明的元数据源并写复核 CSV；只有 `--apply` 才写 ledger。`scripts/clean_names.py` 默认只生成改名计划；`--apply` 会先备份 SQLite，并在数据库更新失败时把文件名回滚。两者导入模块时均无副作用，测试不得使用真实路径。

`/api/providers` 是无副作用 capability health；`/api/providers/opencode-go/models` 只在显式访问时拉取 OpenCode Go 的公开模型清单，不发送推理请求或读取本机 CLI 凭据。

在线追更从 `FeedAdapter` 的 RSS/Atom 候选发现开始：只有显式调用才联网，支持条件请求和有界读取，当前不会自动写 ledger。
