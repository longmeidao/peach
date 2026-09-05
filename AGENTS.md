# Peach 智能体工作契约

本文件是 Codex 与 Claude 共用的唯一项目入口，只保留「每个任务都必须成立」的边界与索引。
它不是 README：`README.md` 讲这个项目是什么、怎么跑；本文件讲改动它之前必须先知道什么。
分层判据、写作规范与清退机制见 `docs/adr/0015-agent-context-layering.md`，不要默认追加到本文件。

面向用户阅读的 README、项目总览、状态、交接、复用清单、待办和 ADR 正文统一使用中文。
代码标识、命令、协议名、库名和无法准确翻译的专有名词保留英文；不要为了智能体处理方便混写英文叙述。
中文写作风格按用户级技能 tech-doc-style-chinese 执行；安装方式、项目覆盖与检查命令见 `docs/HANDOFF.md`。

本文件的风格与流程条目是好的默认，用户当场的指令可以覆盖它们。以下不在此列，必须在同一轮
拿到明确授权：写真实 ledger、不可逆删除、换掉生产入口（端口、主机、二进制或版本）、处理凭据与私钥。
重启托盘让已提交且测试通过的代码生效不在此列，直接重启并报告结果：用户不是一直盯着看，
为此逐次发问只会把修好的代码卡在工作区。这一条收窄了全局默认里的「重启一律先问」。
长跑批处理进行中要重启则仍需先问——那会打断的是任务，不是页面。
`agent_worktree.py prune --apply` 回收「分支已并入 master 且工作区干净」的工作树同样不在此列，
直接执行并报告：判定由脚本做，脏的和未合入的它本来就会拒收。这一条收窄「删除一律先问」。

## 术语表

同一件事只用一个词，回话时也用这些词，不要换成同义说法。

- **你**：正在读本文件并改动 Peach 的智能体（Codex 或 Claude）。**我 / 用户**：在这台机器上部署、使用并维护 Peach 的人；每个部署只有一人。 <!-- copy-lint-disable-line -->
- **ledger / 账本**：每台机器 `peach-data/database/ledger.db` 的本地工作副本，唯一真相源。**真相字段**：直接构成 ledger 断言的列。
- **候选 candidate**：带来源与置信度、未经复核的断言。只有用户复核后才 `approved`，工作者不得自行升级。
- **复核产物**：CSV 等可机读、可重放的中间结果；结论必须落在这里，不能只存在于对话。
- **实体 entity**：女优、厂牌、创作者、系列的规范身份；扁平 `asset_tag`、creator/studio 字段只是兼容投影。
- **表面 surface**：一次改动可能需要同时覆盖的位置（数据层、API、页面、契约、测试、文档）。
- **门槛**：由脚本、测试或 hook 强制的拒绝行为，区别于只写在文档里的提醒。
- **协调者 / 工作者**：主目录里负责集成和验收的一方 / 隔离工作树里负责执行的一方。
- **抽帧 / 接触表**：FFmpeg 采样帧 / 九宫格汇总图。**未取得**：取证失败的固定写法，不得用推测顶替。

## 必读顺序

先读 `README.md`、`docs/STATUS.md` 相关部分；按任务读取架构、复用与交接文档。实现遵循技能索引；部署读 `docs/OPERATIONS.md`，来源采集读 `docs/SOURCING.md`，架构决策读 `docs/adr/`。

## 技能索引

按需读取，不要预先全部展开。Claude 按 description 自动加载；Codex 在触发条件成立时直接读文件。

| 触发条件 | 文件 |
| --- | --- |
| 并行任务、创建工作树、暂存与提交、集成分支、回收工作树、顶层目录归置 | `.claude/skills/peach-worktree/SKILL.md` |
| 迁移、`--apply`、实体合并、批量删除等真实 ledger 写入 | `.claude/skills/peach-ledger-write/SKILL.md` |
| 改完界面、API、契约或文案后声明影响面 | `.claude/skills/peach-surfaces/SKILL.md` |
| 长跑批处理、刮削、限流、磁盘与流量预算 | `.claude/skills/peach-batch-jobs/SKILL.md` |
| JAV 封面、高清封面、缺封面、封面刮削、重探与来源比较 | `.claude/skills/peach-jav-cover-workflow/SKILL.md` |
| 模仿、参考或对齐外部产品的界面与行为 | `.claude/skills/peach-reference-evidence/SKILL.md` |
| 新增、修改或复核页面、控件、提示、数据面板与响应式布局 | `.claude/skills/peach-web-ui/SKILL.md` |
| 在 macOS 上开工、改路径解析或挂载判定、git status 与 diff 不一致 | `.claude/skills/peach-cross-platform/SKILL.md` |
| 新增或删除规则、文档、技能 | `.claude/skills/peach-context-rules/SKILL.md` |
| 新增、恢复或重写实现，尤其协议、解析器、抓取、媒体与基础设施 | `.claude/skills/peach-reuse-first/SKILL.md` |

## 工作规则

- `peach-app` is the only GitHub-synced tree. `peach-data`, `.venv`, build output, worktree directories, media and CloudDrive mounts never enter Git. Code, data and worktrees live on internal disks; external disks only supply media. See ADR-0017, and check `docs/STATUS.md` for the real mount shape before assuming a path exists.
- Ledger paths are always written in the Windows shape (`R:\Media\...`, `A:\...`, `B:\...`). `src/peach/platform.py` translates them to local mounts at read time; never rewrite the ledger to a POSIX shape, and never write `asset.path` from macOS.
- `peach-data/database/ledger.db` is the truth store. Tests use temporary databases only. A real migration requires a SQLite backup and before/after count checks; follow `peach-ledger-write` before any real write.
- Peach is a single-person self-hosted app: aggressively remove obsolete code and compatibility layers when the replacement is tested. Do not preserve dead interfaces merely for history; Git is the archive.
- Preserve real media, ledger rows, behavior history, credentials, network/firewall state, and unrelated long-running jobs.
- Inspect `git status` and the active listeners/processes before work. Never claim candidate code is production until the service has actually been switched and checked.
- Keep the architecture a FastAPI modular monolith with a separate web surface. Do not introduce microservices, PostgreSQL or a full multi-account system without a new ADR.
- The web surface moves to Vite + TypeScript + Preact islands by strangler migration (ADR-0022): new logic lands in `frontend/`, pages are replaced island by island, and there is no whole-app rewrite. Making the app installable by strangers follows the phases in ADR-0023.
- Ledger remains the core truth. The Stash adapter layer is deleted (ADR-0021); `src/peach/stash.py` survives only for the two offline import scripts. AI results are candidates with provenance/confidence, not direct truth-field mutations.
- User-confirmed corpus context: Peach contains consenting adults only. Labels such as `萝莉`、`学生`、`洛丽塔`、`制服`、`泄露` and `流出` are role-play, genre or marketing/source vocabulary, not evidence of age or consent. Do not skip cataloguing solely because those strings occur. If direct file evidence contradicts this, stop and report that evidence instead of inferring from a label.
- Do not create dated handoff documents. Update `docs/STATUS.md` for runtime facts, `docs/PRODUCT_BACKLOG.md` for open work and `docs/HANDOFF.md` for durable knowledge in the same change.
- 新增、恢复或重写实现前必须按 `peach-reuse-first` 依次检查当前树、`docs/REUSE.md`、Git 历史和成熟外部实现，并用真实输入做最小 POC；只有外部方案不满足已验证约束时才自研，并把例外写回复用清单。旧文件名不存在不等于能力缺失。
- When the user says to imitate, reference or align with another product, obtain current reproducible evidence first and register it per `peach-reference-evidence`. If evidence is unavailable, write `未取得`; do not ship a guessed approximation as a faithful reproduction.
- Never require the user to relay implementation details between agents. Put current facts in `docs/STATUS.md`, durable rules in `docs/HANDOFF.md`/`docs/REUSE.md`, procedures in a skill, and architecture decisions in an ADR.
- 复用既有入口与协议，不自研已有替代（含智能体用量与配额视图）：清单与例外见 `docs/REUSE.md`。截图与视觉验收的画面保护判据见 `docs/HANDOFF.md`。

## 门槛（由脚本、测试或 hook 拒绝，不是提醒）

- **测试入口**：每个平台只有一个，Windows `& .\scripts\test.ps1`，macOS/Linux `./scripts/test.sh`，只在当前隔离 worktree 根目录运行。局部改动跑对应功能域；跨域、迁移、共享测试设施、依赖、构建/发布或大面积改动跑默认 `full`。两者自动定位主项目 venv、强制 `PYTHONPATH=<当前 worktree>/src`、核对 `peach.__file__` 后运行 `unittest`；禁止手工拼接 venv 路径或调用 pytest。健康检查只使用 `/healthz`。
- **上下文预算**：入口文件与技能有行数、字节数和最长行三重预算，由 `scripts/check_context_budget.py` 与 `tests/test_context_budget.py` 强制。写不下就说明该内容属于 `docs/` 或某个技能，不是往本文件加行。
- **分层**：新增或删除规则前按 `peach-context-rules` 判层；本文件的技能索引必须与 `.claude/skills/` 一一对应，技能缺 frontmatter、name 不符或缺 `最后复核` 会被拒。
- **工作树**：并发改代码时主检出只做集成。每个智能体在 `scripts/agent_worktree.py create` 建于 `peach-worktrees/` 的隔离工作树里干活；提交前 `git rev-parse --show-toplevel` 必须不是主检出，工作者只交分支、从不自己合并。细节见 `peach-worktree`。
- **仓库卫生**：`.claude/worktrees/` 下不得留未在 `git worktree list` 注册的目录（`tests/test_repo_hygiene.py`）。不用 `git add .`、`git add -A`、目录路径或 glob，只暂存本任务拥有的文件再核对 `git diff --cached --name-status`；实现与它的测试原子提交。
- **文案只写最终状态**：界面字串、注释、docstring、测试名与文档不写改动前后对比，例外逐行加 `copy-lint-disable-line`（`tests/test_copy_final_state.py`）。
- **依赖策略**：Python 依赖精确固定版本，每个被 import 的外部模块要有声明的归属，前端清单与实际 vendored 路径一致，所有清单都进 Dependabot（`tests/test_dependency_policy.py`）。

## 常犯错误（没有自动拦截，都是真实重犯过的）

- 写命令前先分辨当前 shell，不混用语法：PowerShell 里 `cat`、`ls`、`where` 是别名，Bash 里没有 `Get-ChildItem`；需要 PowerShell 时用 `pwsh`（7.x），不回退 `powershell.exe`（5.1），从 Bash 调用加 `-NoProfile`。引号默认单引号，需要变量展开才用双引号，有歧义写 `${name}`；`rg` 不收含 `*` 的路径参数，筛选用 `-g`，退出码 1 是无匹配不是错误。多行内容一律用写入工具或脚本落盘，不用 heredoc——转义曾毁掉整个测试文件。
- PowerShell 变量必须使用任务专属名称；禁止声明 `$HOME`、`$home`、`$CODEX_HOME` 等系统变量的任何大小写变体。`foreach {}` 的结果先存入任务专属数组，再单独接管道格式化，禁止在闭合花括号后直接写管道。
- HTTPS 结论必须使用项目 CA 做严格校验；Schannel、浏览器或取证入口失败时，立即报告原始错误和未取得的验收面，不能改用 HTTP 成功来声称 HTTPS 已通过。
- UI 标签、身份、反馈状态和搜索推荐属于语义契约。修改时必须同时增加数据层测试和页面源测试，不能只改显示文本；推荐词上线前必须对真实 `/api/items` 验证至少一个命中，说明性后缀不得混入搜索词。
- 测试里的临时目录一律先 `.resolve()` 再喂给被测代码和断言。CI runner 的临时目录都是别名（macOS `/var` 软链到 `/private/var`，Windows `RUNNER~1` 短名展开成 `runneradmin`），开发机没有这层别名，拿未 resolve 的路径断言只会在 CI 上红。
- 本仓库最常见的缺陷是「只改了自己测试的那条路径」。收尾前按 `peach-surfaces` 逐项说明每个表面适用还是不适用，不要跳过不适用的项。
