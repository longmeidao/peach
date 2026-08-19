# Peach 智能体工作契约

本文件是 Codex 与 Claude 共用的唯一项目入口，只保留「每个任务都必须成立」的边界与索引。
它不是 README：`README.md` 讲这个项目是什么、怎么跑；本文件讲改动它之前必须先知道什么。
分层判据、写作规范与清退机制见 `docs/adr/0015-agent-context-layering.md`；新增规则前先按
`.claude/skills/peach-context-rules/SKILL.md` 判断该写在哪一层，不要默认追加到本文件。

面向用户阅读的 README、项目总览、状态、交接、复用清单、待办和 ADR 正文统一使用中文。
代码标识、命令、协议名、库名和无法准确翻译的专有名词保留英文；不要为了智能体处理方便混写英文叙述。
中文写作风格按用户级技能 tech-doc-style-chinese 执行；安装方式、项目覆盖与检查命令见 `docs/HANDOFF.md`。

本文件的风格与流程条目是好的默认，用户当场的指令可以覆盖它们。以下不在此列，必须在同一轮
拿到明确授权：写真实 ledger、不可逆删除、换掉生产入口（端口、主机、二进制或版本）、处理凭据与私钥。
重启托盘让已提交且测试通过的代码生效不在此列，直接重启并报告结果：用户不是一直盯着看，
为此逐次发问只会把修好的代码卡在工作区。这一条收窄了全局默认里的「重启一律先问」。
长跑批处理进行中要重启则仍需先问——那会打断的是任务，不是页面。

## 术语表

同一件事只用一个词，回话时也用这些词，不要换成同义说法。

- **你**：正在读本文件并改动 Peach 的智能体（Codex 或 Claude）。**我 / 用户**：Peach 的唯一使用者兼维护者。 <!-- copy-lint-disable-line -->
- **ledger / 账本**：`R:\peach-data\database\ledger.db`，唯一真相源。**真相字段**：直接构成 ledger 断言的列。
- **候选 candidate**：带来源与置信度、未经复核的断言。只有用户复核后才 `approved`，工作者不得自行升级。
- **复核产物**：CSV 等可机读、可重放的中间结果；结论必须落在这里，不能只存在于对话。
- **实体 entity**：女优、厂牌、创作者、系列的规范身份；扁平 `asset_tag`、creator/studio 字段只是兼容投影。
- **表面 surface**：一次改动可能需要同时覆盖的位置（数据层、API、页面、契约、测试、文档）。
- **门槛**：由脚本、测试或 hook 强制的拒绝行为，区别于只写在文档里的提醒。
- **协调者 / 工作者**：主目录里负责集成和验收的一方 / 隔离工作树里负责执行的一方。
- **抽帧 / 接触表**：FFmpeg 采样帧 / 九宫格汇总图。**未取得**：取证失败的固定写法，不得用推测顶替。

## 必读顺序

1. `README.md`
2. `docs/STATUS.md`
3. `docs/ARCHITECTURE.md`
4. `docs/REUSE.md`
5. `docs/HANDOFF.md`
6. Relevant ADRs under `docs/adr/`

## 技能索引

按需读取，不要预先全部展开。Claude 按 description 自动加载；Codex 在触发条件成立时直接读文件。

| 触发条件 | 文件 |
| --- | --- |
| 并行任务、创建工作树、暂存与提交、集成分支 | `.claude/skills/peach-worktree/SKILL.md` |
| 迁移、`--apply`、实体合并、批量删除等真实 ledger 写入 | `.claude/skills/peach-ledger-write/SKILL.md` |
| 改完界面、API、契约或文案后声明影响面 | `.claude/skills/peach-surfaces/SKILL.md` |
| 长跑批处理、刮削、限流、磁盘与流量预算 | `.claude/skills/peach-batch-jobs/SKILL.md` |
| 模仿、参考或对齐外部产品的界面与行为 | `.claude/skills/peach-reference-evidence/SKILL.md` |
| 在 macOS 上开工、改路径解析或挂载判定、git status 与 diff 不一致 | `.claude/skills/peach-cross-platform/SKILL.md` |
| 新增或删除规则、文档、技能 | `.claude/skills/peach-context-rules/SKILL.md` |

## 工作规则

- `peach-app` is code and documentation. `peach-data`, the local media root, and the two CloudDrive mounts are runtime data or mounted media and must never be copied into Git. Windows: `R:\peach-app`, `R:\peach-data`, `R:\media`, `A:\`, `B:\`. macOS: `~/Desktop/lmd.gg/peach/peach-app`, `~/Desktop/lmd.gg/peach/peach-data`, `/Volumes/RESOURCES/media`, `~/Desktop/IMSL/Pikpak`, `~/Desktop/IMSL/115`.
- Ledger paths are always written in the Windows shape (`R:\Media\...`, `A:\...`, `B:\...`). `src/peach/platform.py` translates them to local mounts at read time; never rewrite the ledger to a POSIX shape, and never write `asset.path` from macOS.
- `peach-data/database/ledger.db` is the truth store. Tests use temporary databases only. A real migration requires a SQLite backup and before/after count checks; follow `peach-ledger-write` before any real write.
- The project is an early personal project: aggressively remove obsolete code and compatibility layers when the replacement is tested. Do not preserve dead interfaces merely for history; Git is the archive.
- Preserve real media, ledger rows, behavior history, credentials, network/firewall state, and unrelated long-running jobs.
- Inspect `git status` and the active listeners/processes before work. Never claim candidate code is production until the service has actually been switched and checked.
- Keep the architecture a FastAPI modular monolith with a separate web surface. Do not introduce microservices, PostgreSQL, a React rewrite, or a full multi-account system without a new ADR.
- Ledger remains the core truth. Stash is a replaceable Media Engine adapter. AI results are candidates with provenance/confidence, not direct truth-field mutations.
- User-confirmed corpus context: Peach contains consenting adults only. Labels such as `萝莉`、`学生`、`洛丽塔`、`制服`、`泄露` and `流出` are role-play, genre or marketing/source vocabulary, not evidence of age or consent. Do not skip cataloguing solely because those strings occur. If direct file evidence contradicts this corpus-level context, stop and report the specific evidence instead of inferring from a label.
- Do not create dated handoff documents. Update `docs/STATUS.md` for current runtime/next work and `docs/HANDOFF.md` for durable operating knowledge as part of the same change.
- Before adding or restoring an implementation, check `docs/REUSE.md`, the current tree and Git history. A missing legacy filename does not prove the capability is missing. Update the reuse register when the decision changes.
- When the user says to imitate, reference or align with another product, obtain current reproducible evidence first and register it per `peach-reference-evidence`. If evidence is unavailable, write `未取得`; do not ship a guessed approximation as a faithful reproduction.
- Never require the user to relay implementation details between agents. Put current facts in `docs/STATUS.md`, durable rules in `docs/HANDOFF.md`/`docs/REUSE.md`, procedures in a skill, and architecture decisions in an ADR.
- During concurrent code work, the main `peach-app` checkout is integration-only. Each agent works in an isolated Git worktree; a worker commits its branch and reports it ready, but never merges itself. Details in `peach-worktree`.
- Never use `git add .`, `git add -A`, a directory path, or a glob in an agent checkout. Stage only the exact files owned by the task, then inspect `git diff --cached --name-status`. Implementation and its tests must be committed atomically.
- Run the verification commands in `README.md` before committing relevant changes: `scripts/test.ps1` on Windows, `scripts/test.sh` on macOS. Both entry points must stay green; a change that only passes on one platform is not done.
- Reuse existing usage surfaces and protocols. T3 Code/CodexBar cover historical token and API-equivalent cost views; official provider quota endpoints cover live remaining windows. Do not build another session-log cost scanner or depend on T3 Code's private localhost API.

## 防止重复错误的硬门槛

- PowerShell 变量必须使用任务专属名称；禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 等系统变量的任何大小写变体。`foreach {}` 的结果先存入任务专属数组，再单独接管道格式化，禁止在闭合花括号后直接写管道。
- 测试只在当前隔离 worktree 根目录运行，唯一入口是 `& .\scripts\test.ps1`。脚本自动定位主项目 venv、强制 `PYTHONPATH=<当前 worktree>\src`、核对 `peach.__file__`，再运行 `unittest`；禁止手工拼接 venv 路径或调用 pytest。健康检查只使用 `/healthz`。
- HTTPS 结论必须使用项目 CA 做严格校验；Schannel、浏览器或取证入口失败时，立即报告原始错误和未取得的验收面，不能改用 HTTP 成功来声称 HTTPS 已通过。
- UI 标签、身份、反馈状态和搜索推荐属于语义契约。修改时必须同时增加数据层测试和页面源测试，不能只改显示文本；推荐词上线前必须对真实 `/api/items` 验证至少一个命中，说明性后缀不得混入搜索词。
- 本仓库最常见的缺陷是「只改了自己测试的那条路径」。收尾前按 `peach-surfaces` 逐项说明每个表面适用还是不适用，不要跳过不适用的项。
- 入口与技能有行数预算，由 `scripts/check_context_budget.py` 和 `tests/test_context_budget.py` 强制执行。写不下就说明该内容属于 `docs/` 或某个技能，不是往本文件加行。
