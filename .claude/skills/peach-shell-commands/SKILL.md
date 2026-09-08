---
name: peach-shell-commands
description: 在写 PowerShell 或 Bash 命令、拼多行内容、用 rg 或 Python CLI、在测试里造临时目录，或命令报了看不懂的语法与编码错误时使用。
---

# 命令与路径的形态

最后复核：2026-09-08
证据来源：`tests/test_agent_worktree.py` 与 `tests/test_scripts.py` 里临时目录 `.resolve()`
和正斜杠路径的注释、`scripts/test.ps1` 与 `scripts/test.sh` 的编码约定、Git 历史里被
heredoc 转义损坏的那几次补丁。

## 何时使用

在这台机器上写任何 shell 命令之前。这些不是风格偏好，每一条都对应真实重犯过的失败；
违反后多数当场报错，少数（多行内容的转义）是静默损坏，那一类的核心判据留在 `AGENTS.md`。

## 按当前 shell 写

- PowerShell 的 `cat`、`ls`、`where` 是别名，语义与 Unix 同名命令不同；Bash 没有
  `Get-ChildItem`。写命令前先确定自己在哪个 shell 里。
- PowerShell 只用 `pwsh` 7.x。从 Bash 调用时加 `-NoProfile`。
- 默认单引号，需要展开才用双引号，有歧义时写 `${name}`。
- `rg` 的路径参数不含 `*`，要筛文件用 `-g`；退出码 1 表示无匹配，不是失败。
- Python CLI 加 `-X utf8`；PowerShell 读 UTF-8 日志显式加 `-Encoding utf8`。编码要在输出端
  固定，只给读取端指定编码挡不住乱码。

## 多行内容一律落盘

多行内容用写入工具或脚本文件落盘，再让命令读那个文件，不要用 heredoc。反斜杠会被吃掉一层，
换成带引号的定界符也挡不住所有情形，而损坏是静默的：命令照常退出 0，写进去的内容已经变形。
提交消息同理，写进临时文件再 `git commit -F`。

Windows 与 Git Bash 之间传路径时统一写正斜杠（`Path.as_posix()`）。`C:\Users\...` 落进
shell 脚本后反斜杠会被当成转义符吃掉，`exec` 拿到的是一个粘在一起的名字。Git Bash 也不按
shebang 找 Windows 上的 Python，解释器要显式写出来。

## PowerShell 变量与管道

- 变量必须用任务专属名称。禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 等系统变量的任何
  大小写变体。
- `foreach {}` 的结果先存进任务专属数组，再单独接管道格式化。禁止在闭合花括号后直接写管道。

## 测试里的临时目录

一律先 `.resolve()` 再喂给被测代码和断言。CI runner 的临时目录都是别名：macOS 的 `/var`
软链到 `/private/var`，Windows 的 `RUNNER~1` 短名展开成 `runneradmin`。开发机没有这层别名，
拿未 resolve 的路径断言只会在 CI 上红，本机怎么跑都是绿的。
