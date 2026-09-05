---
name: peach-worktree
description: 在用户说并行、工作树、暂存、提交、ready、集成、生产重启，或任何要写 Peach 代码的任务开始时使用。
---

# 并行 worktree 与提交边界

最后复核：2026-09-05
证据来源：`docs/HANDOFF.md`「并行智能体与 Git 工作树」、`README.md`、ADR-0015、ADR-0017。

## 何时使用

任何会写入当前机器 `peach-app` 的代码任务。主目录只做集成，不做并行编辑；worktree 本机重建，
不跨机器复制目录。

## 流程

1. 协调者在主目录创建隔离工作树：`& .\.venv\Scripts\python.exe scripts\agent_worktree.py create --agent claude --task <task>`。它建在 `peach-worktrees/`，Codex 和 Claude 共用这一个目录。**不要用 Claude Code 内置的工作树机制（`.claude/worktrees/`）**：它在分支被集成后会被回收，目录却留在原地。

2. 工作者只在自己的工作树内编辑。`create` 自动锁定工作树，成功集成后解锁；不复制 `.venv`。
3. 测试在当前工作树根目录运行：Windows `& .\scripts\test.ps1`，macOS/Linux `./scripts/test.sh`。默认 `auto` 按改动文件取影响域并集；文档及无改动检查 `checks`，未知影响面、共享测试设施、依赖、构建选 `full`。域清单唯一真相在 `scripts/test_runner.py`；局部调试可显式选域。
   两者契约相同：从 Git common directory 定位主项目 venv，强制 `PYTHONPATH=<当前工作树>/src`，
   核对 `peach.__file__` 后运行标准库 `unittest`。禁止手工拼接 venv 路径或调用 pytest。
   记录绑定完整代码内容、依赖环境和范围，24 小时有效；失败、验证期间改动使记录无效。
   有同环境全量基线时，`auto` 对比文件清单，只补跑新增差异的影响域；共享设施或未知文件仍跑全量。
   差异补测不延长全量基线有效期；版本号行单独变化归 tooling，包内其他逻辑变化仍按源码判断。
   相同状态复用记录；Windows `-Fresh`、POSIX 第二参数 `--fresh` 强制重跑；显式 `full` 总是实际执行。
4. `ready` 前将当前 `master` 纳入工作树并运行 `auto`。相同内容可复用记录；目标变化重算影响域。`ready` / `integrate` 拒绝缺记录、范围不足或目标分支未纳入的提交。
5. 协调者统一运行 `integrate`：锁内复查、合并固定提交、推进版本。锁忙就等待后重试，禁止直接 merge。同一批任务由协调者整理 `STATUS` 和版本，工作者按文件分工；共享文件安排顺序。版本号默认 `--bump auto`：改动碰到
   运行时输入才动，`feat`／破坏性标记／新迁移推 minor，其余推 patch（ADR-0012 修订）。
   它不打标签：发布走 `scripts/release_tag.py`，那是唯一入口。
   CI 与发布显式跑 `full`；合并完成不机械追加全量。耗时和慢测试记录在主目录 `build/agent-verification/`。
   记录和锁约束统一入口，不是权限隔离；直接 Git 或篡改记录仍可绕过，不能宣称绝对防绕过。

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

- **工作树会惄无声息地失效，目录却还在**。2026-08-26 实例：分支被集成后，
  `.claude/worktrees/<task>` 的注册消失，目录变成主检出里一份旧副本。提示符和文件列表看不出
  任何差别，但在里面跑的每一条 git 都作用于主检出的 master。后果不是报错而是假结论：
  那一轮里智能体一直报告「还没推」，实际上提交已经被另一个智能体的 push 顺带到了 origin。
  判据不看目录名，只看 `git rev-parse --show-toplevel`；等于 `peach-app` 就是在主检出里。
  实测入口：`git worktree list` 里没有你那一行，就是已经没了。
- 健康检查端点是 `/healthz`，不是 `/health`。
- Windows 源码改动生效时，禁止用 Computer Use 操作系统托盘。只用与托盘“重启服务”等价的项目命令；入口必须让现有托盘执行重启，或完整重启托盘并重新取得子服务所有权。直接强杀／另启 `.venv\Scripts\peach.exe` 会让 `_owned` 失真，不算等价；仓库缺少安全命令时先补入口，不能退回托盘 UI。
- PowerShell 变量必须用任务专属名称，禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 的任何大小写
  变体；`foreach {}` 结果先存入任务专属数组再单独接管道，禁止在闭合花括号后直接写管道。
- 工作者报 `ready` 前必须 rebase 到当前 `master`。落后十天的分支不要指望协调者去 merge：
  共享文件上你那一侧是旧的，冲突解错就会把已上线的修复回退掉。2026-08-25 清理时有 7 条
  这样的分支，最后是把各自独有的那几个文件移植到当前 master，而不是 merge 分支本体。

## 回收与顶层归置

工作树用完要回收：`python scripts/agent_worktree.py prune` 列出分支已并入 master 且工作区
干净的工作树，加 `--apply` 才真的删。回收全靠人想起来时，2026-08-29 手工清到 3 个，两天后长回 74 个、占 868 MB。 <!-- copy-lint-disable-line -->
脏的一律拒收并单独列出：分支已合入不等于工作区
里没东西，实测就有工作树的分支早已并入 master、里面却躺着一份成形的未提交改动。

一个工作树失败不影响其它工作树。Windows 上目录句柄常被别的进程占着，`git worktree remove`
报 Permission denied，而 git 已经把文件删光、注册也摘掉了：这种只按 `residue` 列出来等人清，
分支照样删；注册还在才进 `failed`，分支保留。看完 JSON 里的 `residue` 再手工 `rmdir`
那几个空目录。一失败就中止整轮的话，连跑 5 次才摘完 5 个工作树、分支一条没删（2026-09-01）。 <!-- copy-lint-disable-line -->

`prune` 保留锁定的活动工作树。不要手动解锁正在编辑的工作树；任务中止时先核对任务归属、
改动与提交，再决定是否解锁回收。

`Desktop\peach` 顶层只放 ADR-0017 定义的四个运行时目录加一个 `attic/`：

    peach-app  peach-data  peach-sync  peach-worktrees  attic

`peach-` 前缀专属那四个，不再新增；别的东西按性质进 `attic/` 的 `builds`／`evidence`／
`instances`／`tools`／`reviews`，目录名写成 `YYYYMMDD-主题`，顶层不放散落文件，
由 `test_repo_hygiene` 守住。这条规则只写在仓库外的 `../attic/README.md` 时，在 peach-app 里
干活的人根本看不到它，清完两天又堆回三个违规目录。 <!-- copy-lint-disable-line -->

`attic/` 不等于可以随便删：`instances/` 常带 100 MB 量级的 ledger 副本，`tools/` 的
`runtime.json` 会留 token。账本副本、复核产物和取证归档按 AGENTS.md 的保留清单对待，
删除要单独确认。
