# ADR-0017：双机本机运行与分通道同步

- 状态：已接受
- 日期：2026-08-21

## 背景

Peach 的目标是 Windows 与 macOS 各自拥有内置盘上的代码、运行数据、虚拟环境和 worktree，
两台机器可以同时开发并启动 Peach；外置 `RESOURCES` 盘以后只承担媒体资源盘角色。2026-08-21
核对发现，macOS 已完成本机化，但 Windows 仍从外置盘的 `R:\peach-app`、`R:\peach-data`
运行，没有独立代码与运行数据。旧文档把目标状态写成了已完成事实。

外置盘现有 `peach-data` 也不能整体搬进 GitHub或普通双向同步：`database/` 含活跃 WAL 账本和
大量历史备份，`generated/` 同时混有可重建缓存、图片资产和人工复核产物，另外还有凭据、日志、
机器锁、工具与临时文件。同步整个目录会扩大冲突面，并可能传播凭据或损坏 SQLite。

## 决策

### 每台机器独立持有运行环境

- Windows 目标根目录为 `C:\Users\longm\Desktop\peach`：`peach-app`、`peach-data`、
  `peach-worktrees` 均位于内置盘。迁移完成前，`R:\peach-app`、`R:\peach-data` 只是旧运行态
  和迁移来源，不是目标路径。
- macOS 保持 `~/Desktop/lmd.gg/peach/{peach-app,peach-data,peach-worktrees}`。
- 外置盘的正式职责收窄为媒体资源：Windows `R:\media`，macOS
  `/Volumes/RESOURCES/media`。拔盘只让 `local` 来源进入脱盘模式，不影响代码、账本、115/PikPak
  或应用启动。
- `.venv`、打包产物、凭据、日志、机器锁、临时文件和可重建缓存均为本机状态，不跨机器复制。

### 不同步 worktree 目录

- 私有 GitHub 仓库只同步被跟踪的代码、文档、迁移、资源和 Git 分支。
- 主分支和仍需跨机器继续的任务分支必须先 commit/push；另一台 fetch 后按分支重建 worktree。
- `peach-worktrees` 目录及其 `.git` 指针带绝对本机路径，不进入 GitHub，也不通过文件同步工具复制。

### `peach-data` 按性质分通道

- `database/ledger.db`：两台机器各持本地 SQLite 工作副本，通过 Peach 自己的单写者复制同步，
  不进入 GitHub，也不交给通用文件同步。复制继续使用 SQLite backup API。
- 第一阶段的共享账本副本放在 Windows 内置盘的专用同步目录，由 SMB 暴露给 macOS；它是同步
  传输点，不是任一 Peach 实例直接运行的数据库。Windows 关机时 macOS 仍用本地副本运行，恢复
  后再同步。
- 两台服务可以同时在线，但账本仍是单写者：完成显式写入者/只读者模式和运行中安全拉取前，
  只能指定一台接受写入，另一台只读。不得把“同时运行”写成“SQLite 多主写入”。
- 需要跨机器保存的图片资产、原始证据和复核产物从 `generated/`、`sources/`、`review/` 中拆成
  独立、稳定命名的 artifact 集；拆分后可用 Syncthing 一类文件同步工具复制。活账本、`-wal`、
  `-shm`、同步标记、凭据、日志、锁、临时文件、转码与流分片必须排除。

### 两个局域网入口

- macOS 固定使用 `peach.local`，Windows 固定使用 `peach-win.local`，两台可以同时广播，避免
  同名 mDNS 记录互相覆盖。

## 放弃方案

- 把 `peach-data`、worktree 或整个 Peach 父目录提交到 GitHub：会传播真实数据库、凭据和大量
  派生文件；worktree 的本机路径在另一台也无效。
- 用 Syncthing、Dropbox 等直接双向同步整个 `peach-data`：文件冲突副本不能合并 SQLite 事务，
  也不能保证 WAL 与主库是一致快照。
- 继续让外置盘保存代码、运行数据和共享账本：任一机器没插盘就无法独立运行，违背本次目标。
- 改成 PostgreSQL 或新增远程数据库服务：当前单用户规模不需要，且会把本地优先应用变成网络
  服务依赖；除非以后明确需要双主写入，否则不引入。

## 后果

- GitHub 同步范围保持小而可审查；worktree、venv 和运行态问题不再跨机器污染。
- Windows 首次迁移需要内置盘克隆、venv、运行数据播种、路径配置、托盘重建和独立验收。
- 现有 `src/peach/config.py` 仍把外置盘设为 Windows 数据根与共享根，`peach.sync` 也缺少显式
  只读角色和运行中安全拉取；在这些改完并于 Windows 验收前，目标架构尚未部署。
- artifact 拆分前不启用 `peach-data` 整体同步；外置盘上的旧目录保留为只读迁移来源和备份，
  直到两端独立运行验收完成后再单独决定清退。

## 实施清单

1. 将当前 `master` 推到私有 GitHub；在 Windows 内置盘克隆到
   `C:\Users\longm\Desktop\peach\peach-app`，建立本机 `.venv` 并跑 `scripts\test.ps1`。
2. 在 Windows 建立 `C:\Users\longm\Desktop\peach\peach-data` 与 `peach-worktrees`，把
   `PEACH_DATA_ROOT`、构建产物、桌面/Startup 快捷方式和日志路径切到内置盘。
3. 停止两端 Peach，确认当前账本世代一致并备份；用 SQLite backup API 把权威账本播种到
   Windows 本机副本，核对迁移版本、计数、完整性和外键。
4. 把共享账本副本迁到 Windows 内置盘的专用 SMB 同步目录；修改默认配置，外置盘不再作为
   `PEACH_SHARED_DATA_ROOT`。
5. 为 `peach.sync` 增加显式 writer/reader 角色、运行中安全拉取和可见状态；完成前禁止两端同时
   接受写入。
6. 拆分 durable artifacts 与本机缓存，再配置选择性文件同步；不对整个 `peach-data` 开同步。
7. Windows 重新构建 `dist/Peach/Peach.exe`，安装指向内置盘的新 Startup，固定发布
   `peach-win.local`。
8. 拔掉外置盘复验两台 Peach 均可启动、账本可用、115/PikPak 可用且 `local` 正确显示脱盘；
   插盘后再复验两端本地媒体与账本单写者同步。
