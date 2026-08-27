@AGENTS.md

## Claude 专有：不要用内置的工作树机制

Claude Code 自带的工作树会建在 `.claude/worktrees/`，**本项目不用它**。工作树一律用
`scripts/agent_worktree.py create` 建在 `peach-worktrees/`，和 Codex 共用同一个目录。

理由是 2026-08-26 真实踩过的坑：内置工作树在分支被集成后会被回收，**目录却留在原地**，
变成主检出里一份长得一模一样的旧副本。在里面跑 git 全部作用于主检出的 master，而提示符、
文件列表看上去都没变。那一次的后果是我以为自己“还没推”，实际上提交已经被别的代理
在同一个 master 上推走了。

判据只有一条，别看目录名：

```bash
git rev-parse --show-toplevel
```

它如果等于 `peach-app`，你就在主检出里，不管当前目录叫什么。发现时立刻重建工作树再继续，
不要“先把手头这一点改完”。
