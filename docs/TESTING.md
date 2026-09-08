# 测试与依赖

## 环境与锁文件

源码安装使用 `uv sync --locked`。开发、测试和构建在隔离工作树创建 `.venv`，不对正在服务的环境执行精确同步。

安装全部测试依赖（先完成前端依赖安装和构建，再开始正式验证）：

```text
uv sync --locked --all-extras
```

添加直接依赖并同时更新清单和传递锁文件；版本必须精确固定：

```text
uv add "包名==版本"
```

构建环境只选择构建依赖：

```text
uv sync --locked --extra build
```

提交 `pyproject.toml` 与 `uv.lock`。CI 使用 `--locked` 拒绝过期锁文件；Dependabot 的 `uv` 生态负责更新。`uv pip install` 用于临时环境或安装产物，不用于维护项目依赖。普通 pip 安装 wheel 的冒烟仍独立验证打包声明。

npm 的两份清单还有一层派生产物：根 `package.json` 对应 `web/vendor/**` 与 `web/index.html` 的版本注释，`frontend/package.json` 对应 `web/dist/peach-ui.js`。Dependabot 只改 manifest 与 lock，算不出这些，它的 PR 上 `npm run check:vendor` 或 island 产物那一关会红——它的 workflow 拿到的 token 是只读的，推不回 `dependabot/**`。在隔离工作树里用 `scripts/adopt_dependency_bump.py --pr <编号> --co-author '<工具> (<模型>) <厂商 noreply>'` 接管：签出那份清单、重算派生产物、只暂存这些并提交，`--apply` 前先看它列出的文件清单。uv 与 github-actions 的升级没有派生产物，直接合并即可。

版本来自 `src/peach/__init__.py`，已纳入 uv 缓存键；源码版本更新后再次同步会刷新安装元数据。缓存规则采用 [uv 官方动态元数据机制](https://docs.astral.sh/uv/concepts/cache/#dynamic-metadata)。

## 验证频率

| 场景 | 验证 |
| --- | --- |
| 本机修改 | 正式入口默认 `auto`，按影响域取并集；同代码、环境与范围的有效记录可复用 |
| 普通 PR | macOS 影响域；Windows 关键系统与 Python 3.12 兼容性 |
| 普通主线提交 | macOS 全量；Windows 关键系统与 Python 3.12 兼容性 |
| 实际依赖、迁移、共享测试设施、未知影响面 | 两端 Python 3.14 全量，两端 Python 3.12 关键兼容性 |
| 手动 CI | 完整系统矩阵 |
| wheel | 每次独立最小安装，通常两组；完整矩阵四组 |
| Release | 复用同 SHA 主线成功 CI；构建后执行独立 EXE 冒烟 |

全量在两个独立 runner 按测试文件稳定分片；汇总任务要求所有分片和必需任务成功。分片不能签发本机全量记录。当前本机仍串行，避免共享资源竞争。

Windows 的路径、挂载、托盘、证书、进程编码、更新、认证及迁移属于 `core`。构建和工作流修改选择 `packaging` 与 `tooling`；测试调度自身仍全量。仅 uv 工具版本或项目展示字段变化不算依赖图变化；无法解析时全量。

人名对照等业务测试保留：修改相关域时执行，主线全量也执行。测试数据库从真实迁移生成模板，各用例复制独立临时库；迁移测试直接执行迁移。重试测试注入 sleeper 并断言退避序列。重复继承的测试只保留一份。

## 正式入口

Windows 按影响域验证：

```powershell
& .\scripts\test.ps1
```

macOS 按影响域验证：

```sh
./scripts/test.sh
```

显式全量用 Windows `-Scope full` 或 macOS 首参数 `full`。入口优先当前工作树环境、核对源码位置，并记录慢测试。依赖、代码在测试中变化会使证据失效；完成安装和编辑后再启动最终验证。

## 记录的环境身份

记录只在「代码、环境、范围」三项都匹配时可复用，环境那一项由 `scripts/test_evidence.py`
的 `environment()` 算成一个摘要：解释器与已安装包、平台、`PEACH_*` 等环境变量、前端
`node_modules` 锁，以及 node／npm／git／ffmpeg／ffprobe／openssl 六个外部工具。

工具身份取它**自报的版本**，不取 PATH 解析到的路径与文件字节。同一套 Git 安装在
PowerShell 里解析到 `Git\cmd\git.exe`、在 Git Bash 里解析到 `Git\mingw64\bin\git.exe`，
两个前端字节不同而版本和行为相同；按路径记身份会把记录绑在 shell 上——在一个 shell 里
跑出记录，换另一个 shell 跑 `integrate` 就报「缺少有效测试记录」，回到工作树跑 `auto`
又说「复用记录」，两句查的是两个键，代价是白跑一遍全量。

改 `environment()` 的算法本身时，主检出那份代码算不出新键，无法验证带着新算法的分支。
那一次的 `integrate` 用分支自己的脚本跑，并把仓库指到主检出。`--repo` 是顶层参数，
放在子命令前面，放后面会被 argparse 拒收：

```powershell
& .\.venv\Scripts\python.exe -X utf8 <工作树>\scripts\agent_worktree.py `
  --repo <主检出> integrate --branch <分支>
```
