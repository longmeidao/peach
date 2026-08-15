# ADR-0012：版本唯一来源与只检查更新边界

- 状态：Accepted
- 日期：2026-08-15

## 背景

Peach 曾同时在 `pyproject.toml`、`peach.__version__` 和 FastAPI 构造参数中保存版本，实际值
分别为 0.2.0、0.1.0 和 0.2.0。托盘“检查更新”直接在 Win32 消息线程运行 Git，再弹模态
MessageBox；仓库因 R: 盘所有权检查失败时只显示“无法读取”，确认框还会阻塞托盘交互。

主仓库目前没有 Git remote，并且 Codex/Claude 使用独立工作树。自动 pull 或覆盖工作树既不是
真实可用能力，也会破坏并行集成边界。

## 决策

- `src/peach/__init__.py::__version__` 是唯一版本来源；setuptools 通过 dynamic attr 生成包
  元数据，FastAPI health/OpenAPI 和托盘均读取同一值。
- 采用 pre-1.0 SemVer。修复升 patch；兼容功能升 minor；破坏性数据或接口变化升 minor，且
  必须同时有 ADR、正式迁移和验收。发布提交使用本地 `vX.Y.Z` tag。
- 托盘显示包版本、分支、八位提交、工作树状态和更新通道。所有 Git 读取显式传仓库级
  `safe.directory`，不修改用户的全局 Git 配置。
- 没有 `origin` 时报告“本地开发版、未配置更新源”。配置后，用户显式点击才在后台执行
  `git fetch --prune origin`，然后比较当前分支与 upstream 的 ahead/behind。
- 更新检查绝不 checkout、merge、pull、reset 或安装；发现更新只报告，由协调者按 worktree
  协议审核集成。
- 托盘正常动作只使用 pystray 非模态系统通知。Git、网络和比较工作不得运行在托盘消息线程。

## 已拒绝方案

- **继续手工同步三处版本字符串**：已经实际漂移，无法作为发布依据。
- **点击即 `git pull`**：会覆盖或冲突于用户和 agent 的在途修改。
- **自建更新服务器/安装器**：当前没有可发布制品和远程通道，属于虚假复杂度。
- **模态 MessageBox 报告普通状态**：会阻塞通知区消息循环，HiDPI 下还暴露缩放问题。

## 后果

0.2.1 起版本、API 和托盘一致；更新检查可真实区分未配置、最新、落后、领先和分叉，但保持
只读。将来有签名制品和稳定 remote 后，可在新 ADR 中增加下载/验签/原子切换，不能直接扩展
当前按钮为自动覆盖工作树。
