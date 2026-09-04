# 参与 Peach

Peach 是单人自托管应用，维护规模很小。Issue 与 PR 都欢迎。小修（缺陷修复、文案、文档、测试）
直接提 PR；大改动——新页面、新连接器、改契约或数据层、被 ADR 涉及的方向——建议先开 issue
讨论，免得做完才发现与既定边界冲突。提交贡献即同意以 AGPL-3.0-or-later 授权。

## 开 Issue

- 缺陷：写清运行平台（Windows / macOS / Linux）、Python 版本、复现步骤、期望与实际行为，
  以及 `/healthz` 的返回。日志片段请先去掉路径、局域网地址和凭据。
- 需求：写清要解决的问题和你的使用场景。已知的开放需求见 [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md)，
  边界见 [`docs/adr/`](docs/adr/)；被 ADR 明确排除的方向（多用户、云托管、微服务、PostgreSQL）
  需要先讨论是否值得新立一份 ADR。
- 安全问题不要开公开 issue，走 [`SECURITY.md`](SECURITY.md)。

## 提 PR 之前

先读 [`AGENTS.md`](AGENTS.md)：它是开发边界与门槛的唯一入口，PR 评审也按它执行。
分支、暂存与提交的具体规则见 [`.claude/skills/peach-worktree/SKILL.md`](.claude/skills/peach-worktree/SKILL.md)，
其中三条最容易踩到：

- 不用 `git add .`、`git add -A`、目录路径或 glob，只暂存本次改动拥有的文件。
- 实现与它的测试在同一个提交里。
- 一个 PR 只做一件事，改动面写进 PR 模板的影响面那一项。

## 测试

每个平台只有一个测试入口：

```powershell
& .\scripts\test.ps1            # Windows
```

```bash
./scripts/test.sh               # macOS / Linux
```

局部改动跑对应功能域（`-Scope follow` / `follow`，可选域为 `follow`、`catalog`、`media`、
`sync`、`metadata`、`web`、`tooling`）；跨域、改迁移、改共享测试设施、改依赖或大面积改动跑默认
`full`。脚本自己定位虚拟环境并核对导入路径，请不要手工拼 venv 路径或另拼测试命令。
仓库使用标准库 `unittest`。

## 前端改动

`frontend/` 需要 Node 24 或更高版本。构建产物 `web/dist/` 进 Git——运行时没有 Node，
Python 服务与打包件直接读它。改了 `frontend/src` 就在同一个 PR 里跑
`npm --prefix frontend run build` 并提交 `web/dist/`，CI 的 `web-bundle` job 会核对产物与源码一致。
目录、样式表分区与挂载契约见 [`docs/FRONTEND.md`](docs/FRONTEND.md)。

## 文案

- 文档、注释、界面字串与测试名一律中文；代码标识、命令、协议名、库名保留英文。
- 只写最终状态：不写「改动前后」对比，也不留被否掉的做法。`tests/test_copy_final_state.py`
  是门槛，真实事故记录逐行加 `copy-lint-disable-line` 放行。
- 不提交媒体、账本、凭据、日志、构建缓存与个人坐标（局域网地址、主机名、账号名、个人目录）。
