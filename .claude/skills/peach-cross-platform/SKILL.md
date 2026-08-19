---
name: peach-cross-platform
description: 在 macOS 上开工、改动路径解析或挂载判定、遇到 git status 与 git diff 结果不一致，或要把改动交回 Windows 那台时使用。
---

# 跨 Windows / macOS 双机开发

最后复核：2026-08-19
证据来源：`src/peach/platform.py`、`README.md`「边界」、2026-08-19 的 macOS 迁移实测。

## 何时使用

- 当前工作目录在 macOS 上（`~/Desktop/lmd.gg/peach/peach-app`）。
- 改动涉及 `asset.path` 解析、`allowed_media_roots`、挂载可达性或磁盘闸门。
- `git status` 显示大量文件被修改，但 `git diff` 是空的。
- 改动要交回 Windows 那台继续。

## 路径口径

账本里的 `asset.path` **一律是 Windows 形态**：`R:\Media\...`（本地硬盘）、
`B:\...`（115）、`A:\...`（PikPak）。

不要为了 macOS 把账本改写成 POSIX 路径。翻译只发生在读取期，收敛在
`src/peach/platform.py` 一处；写回账本的索引脚本仍只在 Windows 上跑，路径口径
因此保持单一。**禁止从 macOS 写 `asset.path`**。

| 盘符 | Windows | macOS 默认 |
| --- | --- | --- |
| `R:` 本地硬盘 | `R:\` | `/Volumes/RESOURCES` |
| `B:` 115 | `B:\` | `~/Desktop/IMSL/115` |
| `A:` PikPak | `A:\` | `~/Desktop/IMSL/Pikpak` |

用 `PEACH_DRIVE_MAP=R=/mnt/res,B=/mnt/115` 覆盖；数据目录用 `PEACH_DATA_ROOT`。
CloudDrive 在 Windows 是盘符、在 macOS 是 macFUSE 挂载点，这层不是可选优化。

## 三条只在 Windows 成立的假设

- **授权根比较不能只看字面**。账本写 `R:\Media`，macOS 侧授权根是
  `/Volumes/RESOURCES/media`；pathlib 区分大小写而 exFAT/NTFS 不区分，字面比较会把
  全部本地资产判成越权。`within_root` 在字面不匹配时用 inode 比较兜底，交给文件系统
  判定。
- **挂载点「在不在」的判据是能否列出第一个条目**，不是 `is_dir()`。CloudDrive 掉线后
  挂载点目录仍然存在，读一个条目才会报 `Device not configured`。见 `root_online`。
- **磁盘闸门看系统盘**：Windows `C:`、macOS `/`，用 `system_volume()`。CloudDrive 的
  下载块缓存在两个平台都落在系统盘；写死 `C:/` 会让 macOS 侧直接抛 `FileNotFoundError`。

另外 `PidFileLock._running` 要吞掉 `OverflowError`：Windows 写下的 PID 可能超出 POSIX
的 `pid_t`，`os.kill` 会崩掉整轮任务，而超界的 PID 一定不是本机活进程。

## 脱盘模式

脱盘是**来源级**的，不是全局开关。外置盘拔掉只影响 `local` 的约 2.5k 条资产，
115/PikPak 的约 78k 条云端资产照常可播；CloudDrive 掉线时反过来也一样。

判据只有 `GET /api/sources` 一份。媒体层把整盘不可达从 `MediaUnavailable` 里分出
`MediaOffline`，HTTP 回 503 加 `X-Peach-Offline: 1`，和「单个文件缺失」的 404 分开。
前端据此置灰脱盘来源的筛选（数量仍然显示：脱的是盘不是账本），详情页换成脱盘面板
而不是挂一个必然失败的播放器。

## 运行环境

macOS 的 FFmpeg 走 PATH（`brew install ffmpeg`）。`peach-data/tools/ffmpeg` 里是
Windows 的 `.exe`/`.dll`，`FFmpegResolver` 按平台找不带后缀的 `ffmpeg`，会自动跳过它
——这套目录可以两台机器共用，不需要分叉。

macOS 的菜单栏项必须打成 `.app`（`scripts/build_macos_app.py`）：裸控制台进程启动时
AppKit 运行循环没有应用上下文会立刻返回，服务起来了但托盘父进程安静退出、零输出。
bundle 声明 `LSUIElement`，输出重定向到 `logs/macos-tray.log`。图标要 template image
才会跟着浅色/深色菜单栏反色；服务用非特权端口 8900。

测试入口：Windows `scripts/test.ps1`，macOS/Linux `scripts/test.sh`。两者契约相同。
**两边都必须绿**；只在一台上通过的改动不算完成。Windows 托盘专属的 DPI 声明和单实例
锁在非 Windows 上按 `skipUnless` 跳过，不要改成在 macOS 上伪造通过。

## 账本复制

三份副本：硬盘那份是权威，两台机器各持本地工作副本。**不是多主实时同步**——SQLite
没有安全的自动三方合并。见 `src/peach/sync.py` 与 README「账本复制」。

- 启动比对世代：硬盘新就拉、本地新就留、两边都动过就转只读报冲突，由人选一边。
- 运行中每 60 秒回写，回写前重新判定，别人抢先推过就转冲突，绝不覆盖。
- 硬盘不在时本地照常写，插回来再回写。
- 复制走 SQLite backup API，**不要复制 `.db` 文件**：WAL 里已提交未 checkpoint 的
  事务会丢，还可能和目标残留的 `-wal` 拼成损坏的库。
- 本地副本与共享副本是同一条路径时复制自动停用。Windows 目前仍直接用硬盘那份，
  所以它的行为不变；等它把 `PEACH_DATA_ROOT` 指到本机盘，三份副本才真正成立。
- 冲突不能靠合并解决，只能选一边：复制其一覆盖另一份，或删掉一侧 `.sync.json`
  重新播种。别写「已同步」这种含糊结论。

## 代码同步

代码在私有仓库 `longmeidao/peach`（`origin`），两台机器手动 push/pull，**不自动推送**。
开工前先 `sh scripts/sync_status.sh`：落后远端就先 `git pull --rebase`，别在旧代码上接着
写；账本是另一条链路（`peach.sync`），同一个脚本会一并报告。

## Git 陷阱

- **换行**由 `.gitattributes` 的 `* text=auto eol=lf` 固定，不要依赖各自的
  `core.autocrlf`。2026-08 之前 Windows 侧把 105 个已跟踪文件整体改写成 CRLF，
  `git status` 长期显示 117 个文件被修改、16213 行增删，而真正有实质改动的只有 1 个
  ——未提交的工作被假 diff 完全埋掉。
- **从 exFAT 复制过来的文件权限是 `rwx------`**（exFAT 没有 POSIX 权限位，macOS 挂载时
  统一合成）。这会让 git 的 stat 缓存长期对不上：`git status` 显示上百个文件被修改，
  `git diff` 却是空的，`git hash-object` 和 HEAD 逐字节相同。
  `git update-index --refresh` **只会报 `needs update`，修不好**；用 `git add` 重写
  stat 缓存才行。
- 判断真实差异一律看 `git diff HEAD --name-only`，**不要看 `git status`**。
