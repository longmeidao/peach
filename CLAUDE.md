@AGENTS.md

## Claude 专有：不要用内置的工作树机制

工作树一律用 `scripts/agent_worktree.py create` 建在 `peach-worktrees/`，不用 Claude Code
内置的 `.claude/worktrees/`：分支集成后它会被回收，目录却留在原地，成了主检出里一份看不出
区别的旧副本，在里面跑 git 全部作用于主检出的 master。判据只有一条，别看目录名：
`git rev-parse --show-toplevel` 等于 `peach-app` 就是在主检出里，立刻重建工作树再继续。
残留目录由 `tests/test_repo_hygiene.py` 的 `BuiltInWorktreeTests` 拦住。
