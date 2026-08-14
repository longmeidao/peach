# Peach

Peach（蜜桃）是一个单用户、本地优先的个人媒体系统：统一索引本地/网盘/在线资产，记录真实消费反馈，并逐步提供搜索、推荐和追更。

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

当前运行态与下一任务只看 [`docs/STATUS.md`](docs/STATUS.md)；跨 Codex/Claude 的固定接手方式只看 [`docs/HANDOFF.md`](docs/HANDOFF.md)。
