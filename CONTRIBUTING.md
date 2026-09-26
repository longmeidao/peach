# 参与 Peach

Issues and pull requests are welcome. Small fixes (bugs, copy, documentation, tests) can go straight to a PR; large changes — new pages, new connectors, contract or data-layer changes, anything an ADR covers — should be discussed in an issue first. Read [`AGENTS.md`](AGENTS.md) before opening a PR: it is the single entry point for development rules, and reviews follow it. Each platform has exactly one test entry point: `& .\scripts\test.ps1` on Windows and `./scripts/test.sh` on macOS/Linux. By submitting a contribution you agree to license it under AGPL-3.0-or-later. The rest of this document is in Chinese.

Peach 是单人自托管应用，由一个人维护。欢迎提 Issue 和 PR。

- 小修（修缺陷、改文案、补文档、补测试）可以直接提 PR。
- 大改动（新页面、新连接器、改接口约定或数据层、涉及 ADR 的方向）请先开 issue 讨论，免得做完才发现和既定设计冲突。

提交贡献即表示同意以 AGPL-3.0-or-later 授权。

## 开 Issue

- **报缺陷**：写清运行平台（Windows / macOS / Linux）、Python 版本、复现步骤、期望结果和实际结果，并附上 `/healthz` 的返回。贴日志前先去掉路径、局域网地址和凭据。
- **提需求**：写清要解决什么问题、在什么场景下用。已知的开放需求在 [`docs/PRODUCT_BACKLOG.md`](docs/PRODUCT_BACKLOG.md)，设计边界在 [`docs/adr/`](docs/adr/)。ADR 明确排除的方向（多用户、云托管、微服务、PostgreSQL）需要先讨论值不值得新立一份 ADR。
- **安全问题**：不要开公开 issue，按 [`SECURITY.md`](SECURITY.md) 私下报告。

## 提 PR 之前

先读 [`AGENTS.md`](AGENTS.md)，它是开发规则的唯一入口，PR 评审也按它执行。分支、暂存与提交的细则见 [`.claude/skills/peach-worktree/SKILL.md`](.claude/skills/peach-worktree/SKILL.md)。最容易踩到的三条：

1. 不用 `git add .`、`git add -A`、目录路径或通配符，只暂存这次改动的文件。
2. 实现和它的测试放在同一个提交里。
3. 一个 PR 只做一件事，并在 PR 模板的「影响面」表里逐项说明（数据层、API、页面、接口约定、测试、文档），不适用的也写出来。

## 测试

每个平台只有一个测试入口：

```powershell
& .\scripts\test.ps1            # Windows
```

```bash
./scripts/test.sh               # macOS / Linux
```

不带参数时按改动的文件自动选测试范围，判断不了就跑全量。也可以手动指定范围，例如 `-Scope follow`（macOS/Linux 写 `./scripts/test.sh follow`），可选 `follow`、`catalog`、`media`、`sync`、`metadata`、`web`、`tooling` 等。跨多个范围、改数据库迁移、改共享测试设施、改依赖或大面积改动时，请用 `full` 跑全量。

脚本会自己找到虚拟环境并核对导入路径，不要手动拼 venv 路径或另写测试命令。测试框架是标准库 `unittest`。

## 前端改动

`frontend/` 需要 Node 24 或更高版本。

运行 Peach 时不需要 Node，Python 服务和安装包直接读取构建好的 `web/dist/`，所以它要提交进 Git。改了 `frontend/src` 后，在同一个 PR 里运行 `npm --prefix frontend run build` 并提交 `web/dist/`；CI 的 `web-bundle` 任务会检查构建结果和源码是否一致。目录结构与样式约定见 [`docs/FRONTEND.md`](docs/FRONTEND.md)。

## 提交说明与变更日志

- 提交主题按 Conventional Commits 写，例如 `feat:`、`fix:`、`perf:`、`docs:`、`refactor:`。
- 破坏性变化在主题里加 `!`，或写 `BREAKING CHANGE:` 脚注。
- PR 不用改 [`CHANGELOG.md`](CHANGELOG.md)。维护者发布时用 `python scripts/changelog.py` 按提交起草，再改成使用者读得懂的话；每个 PR 各改一次只会互相冲突。

## 文案

- 文档、注释、界面文字和测试名一律用中文；代码标识、命令、协议名和库名保留英文。
- 只写现在的状态，不写「改动前后」的对比，也不保留被否掉的做法。`tests/test_copy_final_state.py` 会检查这一条；确实需要记录的事故原文，逐行加 `copy-lint-disable-line` 放行。
- 不要提交媒体、数据库、凭据、日志、构建缓存和个人信息（局域网地址、主机名、账号名、个人目录）。
