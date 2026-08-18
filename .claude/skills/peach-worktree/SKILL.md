---
name: peach-worktree
description: 在用户说并行、开工作树、worktree、暂存、提交、ready、集成分支，或任何要写入 R:\peach-app 的代码任务开始时使用。
---

# 并行 worktree 与提交边界

最后复核：2026-08-17
证据来源：`docs/HANDOFF.md`「并行智能体与 Git 工作树」、`README.md`、ADR-0015。

## 何时使用

任何会写入 `R:\peach-app` 的代码任务。`R:\peach-app` 主目录只做集成，不做并行编辑。

## 流程

1. 协调者在主目录创建隔离工作树：

   ```powershell
   & .\.venv\Scripts\python.exe scripts\agent_worktree.py create --agent claude --task <task>
   ```

2. 工作者只在自己的工作树内编辑。工作树不复制 `.venv`。
3. 测试只用唯一入口，在当前工作树根目录运行：

   ```powershell
   & .\scripts\test.ps1
   ```

   脚本从 Git common directory 定位主项目 venv，强制 `PYTHONPATH=<当前工作树>\src`，
   核对 `peach.__file__` 后运行标准库 `unittest`。禁止手工拼接 venv 路径或调用 pytest。
4. 报告 `ready` 前先 rebase 到当前 `master` 并重跑测试；同文件冲突在工作者分支解决。
5. 协调者审核后运行 `integrate`。完成顺序不决定覆盖顺序。

## 暂存与提交

- 禁止 `git add .`、`git add -A`、目录路径或 glob。只暂存任务明确拥有的文件。
- 提交前用 `git diff --cached --name-status` 与任务边界逐条对照。干净的 `git status`
  不能证明归属正确。
- 实现与其测试必须原子提交。反例 `bba0b77`：测试被误判为本任务文件而进入提交，对应
  `probe.py` 未暂存，HEAD 出现「测试指向不存在实现」。

## 工作者禁止事项

自行 merge、执行 `--apply`、把候选标为 `approved`、修改迁移或 ADR、重启生产服务。
这些属于协调者。

## 已知陷阱

- 健康检查端点是 `/healthz`，不是 `/health`。
- PowerShell 变量必须用任务专属名称，禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 的任何大小写
  变体；`foreach {}` 结果先存入任务专属数组再单独接管道，禁止在闭合花括号后直接写管道。
- 2026-08-17 实测：在工具管道里直接 `python -m unittest discover` 全量运行会挂起或整会话
  输出消失（`test_jobs` 等极快退出的模块竞态最明显）。这是管道问题不是测试失败，但唯一
  可信入口仍是 `& .\scripts\test.ps1`。
