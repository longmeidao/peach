# Peach 智能体工作契约

本文件是 Codex 与 Claude 共用的唯一项目入口。

面向用户阅读的 README、项目总览、状态、交接、复用清单、待办和 ADR 正文统一使用中文。
代码标识、命令、协议名、库名和无法准确翻译的专有名词保留英文；不要为了智能体处理方便混写英文叙述。

修改项目前，按顺序阅读：

1. `README.md`
2. `docs/STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REUSE.md`
5. `docs/HANDOFF.md`
6. Relevant ADRs under `docs/adr/`

工作规则：

- `R:\peach-app` is code and documentation. `R:\peach-data`, `R:\media`, `A:\` and `B:\` are runtime data or mounted media and must never be copied into Git.
- `R:\peach-data\database\ledger.db` is the truth store. Tests use temporary databases only. A real migration requires a SQLite backup and before/after count checks.
- The project is an early personal project: aggressively remove obsolete code and compatibility layers when the replacement is tested. Do not preserve dead interfaces merely for history; Git is the archive.
- Preserve real media, ledger rows, behavior history, credentials, network/firewall state, and unrelated long-running jobs.
- Inspect `git status` and the active listeners/processes before work. Never claim candidate code is production until the service has actually been switched and checked.
- Keep the architecture a FastAPI modular monolith with a separate web surface. Do not introduce microservices, PostgreSQL, a React rewrite, or a full multi-account system without a new ADR.
- Ledger remains the core truth. Stash is a replaceable Media Engine adapter. AI results are candidates with provenance/confidence, not direct truth-field mutations.
- User-confirmed corpus context: Peach contains consenting adults only. Labels such as `萝莉`、`学生`、`洛丽塔`、`制服`、`泄露` and `流出` are role-play, genre or marketing/source vocabulary, not evidence of age or consent. Do not skip cataloguing solely because those strings occur. If direct file evidence contradicts this corpus-level context, stop and report the specific evidence instead of inferring from a label.
- Do not create dated handoff documents. Update `docs/STATUS.md` for current runtime/next work and `docs/HANDOFF.md` for durable operating knowledge as part of the same change.
- Before adding or restoring an implementation, check `docs/REUSE.md`, the current tree and Git history. A missing legacy filename does not prove the capability is missing. Update the reuse register when the decision changes.
- When the user says to imitate, reference or align with another product, obtain current reproducible evidence first: live behavior plus DOM/CSS/source/bundle where available, or exact screenshot measurements when source is unavailable. Record the URL/version/hash and intentional Peach deviations in `docs/HANDOFF.md`. If evidence is unavailable, write `未取得`; do not ship a guessed approximation as a faithful reproduction.
- Never require the user to relay implementation details between agents. Put current facts in `docs/STATUS.md`, durable rules in `docs/HANDOFF.md`/`docs/REUSE.md`, and architecture decisions in an ADR.
- During concurrent code work, `R:\peach-app` is integration-only. Each agent must create and edit an isolated Git worktree with `scripts/agent_worktree.py create`; a worker commits its branch and reports it ready, but never merges itself merely because it finished last.
- Never use `git add .`, `git add -A`, a directory path, or a glob in an agent checkout. Stage only the exact files owned by the task, then inspect `git diff --cached --name-status`. Tests belong to the implementation they exercise: never stage a test when the corresponding implementation is outside the task or unstaged.
- A clean `git status` is not proof of correct ownership. Before commit, compare the staged path list with the task boundary and run the relevant tests from that same worktree. The coordinator alone integrates ready branches, resolves same-file conflicts and restarts production.
- Run the verification commands in `README.md` before committing relevant changes.
- Reuse existing usage surfaces and protocols. T3 Code/CodexBar cover historical token and API-equivalent cost views; official provider quota endpoints cover live remaining windows. Do not build another session-log cost scanner or depend on T3 Code's private localhost API.

防止重复错误的硬门槛：

- PowerShell 变量必须使用任务专属名称；禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 等系统变量的任何大小写变体。`foreach {}` 的结果先存入任务专属数组，再单独接管道格式化，禁止在闭合花括号后直接写管道。
- 测试只在当前隔离 worktree 根目录运行，先设置 `PYTHONPATH=<worktree>\src` 并核对 `peach.__file__`；唯一入口是 `python -m unittest discover -s tests -p 'test_*.py' -v`。禁止调用 pytest，健康检查只使用 `/healthz`。
- HTTPS 结论必须使用项目 CA 做严格校验；Schannel、浏览器或取证入口失败时，立即报告原始错误和未取得的验收面，不能改用 HTTP 成功来声称 HTTPS 已通过。
- UI 标签、身份、反馈状态和搜索推荐属于语义契约。修改时必须同时增加数据层测试和页面源测试，不能只改显示文本；推荐词上线前必须对真实 `/api/items` 验证至少一个命中，说明性后缀不得混入搜索词。
