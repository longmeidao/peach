# Peach 智能体工作契约

本文件是 Codex 与 Claude 共用的唯一项目入口，只保留「每个任务都必须成立」的边界与索引。
`README.md` 讲项目与运行方式；本文件讲改动前的约定。
分层判据、写作规范与清退机制见 `docs/adr/0015-agent-context-layering.md`，不要默认追加到本文件。

面向用户阅读的 README、项目总览、状态、交接、复用清单、待办和 ADR 正文统一使用中文。
代码标识、命令、协议名、库名和无法准确翻译的专有名词保留英文；不要为了智能体处理方便混写英文叙述。
中文写作风格按用户级技能 tech-doc-style-chinese 执行；安装方式、项目覆盖与检查命令见 `docs/HANDOFF.md`。
回复用日常语言讲清结果、原因、处理和验证，技术细节按需展开；结尾保留「我做了什么」「你需要做什么」。

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
- **影响面 surface**：一次改动可能需要同时覆盖的位置（数据层、API、页面、契约、测试、文档）。
- **门槛**：由脚本、测试或 hook 强制的拒绝行为，区别于只写在文档里的提醒。
- **协调者 / 工作者**：主目录里负责集成和验收的一方 / 隔离工作树里负责执行的一方。
- **抽帧 / 九宫格**：FFmpeg 采样帧 / 九帧拼成的汇总图。**未取得**：取证失败的固定写法，不得用推测顶替。

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
| 写 PowerShell 或 Bash 命令、拼多行内容、测试里造临时目录 | `.claude/skills/peach-shell-commands/SKILL.md` |
| 新增或删除规则、文档、技能 | `.claude/skills/peach-context-rules/SKILL.md` |
| 新增、恢复或重写实现，尤其协议、解析器、抓取、媒体与基础设施 | `.claude/skills/peach-reuse-first/SKILL.md` |

## 工作规则

- `peach-app` is the only GitHub-synced tree; data, worktrees, build output, media and CloudDrive mounts stay out of Git. Real paths and mount shape: ADR-0017 and `docs/STATUS.md`.
- Ledger paths are always written in the Windows shape (`R:\Media\...`, `A:\...`, `B:\...`). `src/peach/platform.py` translates them at read time; never rewrite the ledger to a POSIX shape, and never write `asset.path` from macOS.
- `peach-data/database/ledger.db` is the truth store and tests use temporary databases only; any real write follows `peach-ledger-write`. AI results are candidates with provenance and confidence, never direct truth-field mutations.
- Preserve real media, ledger rows, behavior history, credentials, network/firewall state, and unrelated long-running jobs.
- Inspect `git status` and the active listeners/processes before work. Never claim candidate code is production until the service has actually been switched and checked.
- Peach is a single-person self-hosted app: remove obsolete code and compatibility layers once the replacement is tested. Git is the archive, so dead interfaces are not kept for history.
- The architecture is settled in ADRs — modular monolith and disk boundaries (0017), Stash adapter closed (0021), frontend strangler migration into `frontend/` (0022), distribution phases (0023). Changing any of them takes a new ADR, not a commit.
- User-confirmed corpus context: Peach contains consenting adults only. Labels such as `萝莉`、`学生`、`洛丽塔`、`制服`、`泄露` and `流出` are role-play, genre or marketing vocabulary, not evidence of age or consent. Do not skip cataloguing solely because those strings occur. If direct file evidence contradicts this, stop and report that evidence instead of inferring from a label.
- Do not create dated handoff documents. Update `docs/STATUS.md` for runtime facts, `docs/PRODUCT_BACKLOG.md` for open work and `docs/HANDOFF.md` for durable knowledge in the same change.
- Never require the user to relay implementation details between agents: facts go to `docs/STATUS.md`, durable rules to `docs/HANDOFF.md`/`docs/REUSE.md`, procedures to a skill, decisions to an ADR.
- 复用优先：新增、恢复或重写实现按 `peach-reuse-first` 依次查当前树、`docs/REUSE.md`、Git 历史与成熟外部实现，旧文件名不存在不等于能力缺失；对齐外部产品先按 `peach-reference-evidence` 取到可复现证据，取不到写 `未取得`，不拿猜测冒充复现。

## 门槛（由脚本、测试或 hook 拒绝，不是提醒）

- **测试入口**：Windows `& .\scripts\test.ps1`、macOS/Linux `./scripts/test.sh`，在当前隔离 worktree 根目录运行。`auto` 按域选测，共享设施、实际依赖和未知面用 `full`；CI 见 `docs/TESTING.md`。入口优先当前树 venv，核对 `PYTHONPATH` 与 `peach.__file__`；禁止另拼测试命令。`ready` / `integrate` 拒收无有效记录的分支；集成事务互斥。健康检查只用 `/healthz`。
- **上下文预算**：入口文件与技能有行数、字节数和最长行三重预算，由 `scripts/check_context_budget.py` 与 `tests/test_context_budget.py` 强制。写不下就说明该内容属于 `docs/` 或某个技能，不是往本文件加行。
- **分层**：新增或删除规则前按 `peach-context-rules` 判层；本文件的技能索引必须与 `.claude/skills/` 一一对应，技能缺 frontmatter、name 不符或缺 `最后复核` 会被拒。
- **工作树**：并发改代码时主检出只做集成。每个智能体在 `scripts/agent_worktree.py create` 建于 `peach-worktrees/` 的隔离工作树里干活；提交前 `git rev-parse --show-toplevel` 必须不是主检出，工作者只交分支、从不自己合并。细节见 `peach-worktree`。
- **仓库整洁**：`.claude/worktrees/` 下不得留未在 `git worktree list` 注册的目录（`tests/test_repo_hygiene.py`）。不用 `git add .`、`git add -A`、目录路径或 glob，只暂存本任务拥有的文件再核对 `git diff --cached --name-status`；实现与它的测试原子提交。交付提交须署名（`scripts/co_author.py`）。
- **文案只写最终状态**：界面字串、注释、docstring、测试名与文档不写改动前后对比，例外逐行加 `copy-lint-disable-line`（`tests/test_copy_final_state.py`）。
- **依赖策略**：Python 依赖精确固定版本，每个被 import 的外部模块要有声明的归属，前端清单与实际 vendored 路径一致，所有清单都进 Dependabot（`tests/test_dependency_policy.py`）。

## 常犯错误（没有自动拦截，都是真实重犯过的）

- 改文件用编辑工具直接改，不要先写一个一次性补丁脚本再执行它。规则约束的是「改文件这件事怎么做」，不是某一门语言：禁掉 Python 只会换成 Bash 或别的。代价有四样：没有 diff 可看，人要么读脚本要么事后再 diff 一次；判据退化成脚本自己打印的那句话，而 `print('ok')` 和退出 0 都不证明改对了位置；一处简单编辑常要反复几轮才成；Windows 上还多一层引号与缩进的坑（openai/codex#3057 及其评论列的就是这四样）。脚本只留给真有算法内容的场景：按上游数据重新生成整份文件、几十个文件的同一变换、要先解析才知道改哪里；这类脚本要能重复执行，遍历和重试都写明终止条件。
- 多行内容一律用写入工具落盘再让命令读，不用 heredoc：反斜杠会被吃掉一层，加引号定界符也挡不住，而损坏是静默的——命令照样退出 0，写进去的内容已经变形。其余 shell、PowerShell 与 CI 路径别名的坑见 `peach-shell-commands`。
- HTTPS 结论必须使用项目 CA 做严格校验；Schannel、浏览器或取证入口失败时，立即报告原始错误和未取得的验收面，不能改用 HTTP 成功来声称 HTTPS 已通过。
- 本仓库最常见的缺陷是「只改了自己测试的那条路径」。收尾前按 `peach-surfaces` 逐项说明每个影响面适用还是不适用，不要跳过不适用的项。
