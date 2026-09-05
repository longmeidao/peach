# PikPak 封面与缩略图夜跑

## 范围

先全量重跑 PikPak `probe`，再生成官方封套和九帧接触表；不运行创作者板、标签识别、人物归属或
其他元数据刮削。这里的「缩略图」是 `snapshot_path` 指向的九帧接触表，`/thumb` 直接返回它，
卡片海报再从中裁一格。

真实批次只在 Windows 写入端运行。macOS 当前是 reader，只用于代码验证和账本副本抽样，不能把
probe 结果写进真实 Mac ledger。开跑前必须确认 `/healthz.ledger_sync=writer`、`A:` 可列目录、
没有同类任务在跑、`C:` 至少剩 40 GiB，并用 SQLite backup API 备份本地真实 ledger。

队列数字不抄在这里。开跑前跑 `python scripts/job_status.py`，它按真实账本现算「可抽 / 缺时长
待 probe / 合计」；之前写在这里的那份 Mac 副本基线被当成过远端现值用，这类数字只在生成的那一刻
成立。口径上要分清 `duration=0`（还没探测）和 `duration<0`（探测失败，只有 `--redo all` 会重试），
正时长不超过 2 秒的资产不进接触表队列。

## 流量样本与停止条件

2026-08-22 Mac 隔离样本：506 MiB、1,769 秒视频生成九帧接触表耗时 11.69 秒，Stash 按
CloudDrive 进程连接增量计得下载 126,744,568 字节（120.9 MiB）、上传 107,604 字节；当前路线是
香港代理链，不是 DIRECT。官方封套样本 `KUZU-25010` 用 3.25 秒确认所有渠道无候选，下载
14,366 字节、上传 3,912 字节。旧 DIRECT 九帧样本为 30.5 MB / 64.2 秒；路线差异很大，夜跑报告
必须记录实际 chain，不能用单个样本外推总量。

全量缩略图不能承诺一夜完成。按当前代理样本线性外推会超过 1 TiB；旧 DIRECT 口径也约 300 GiB
且更慢。第一晚以 200 GB 守卫和磁盘闸门为硬上限，次日报告「完成 / 仍失败 / 待处理」与实际
字节，不能为了追求完成率调高预算。触发流量或磁盘闸门是安全中止，不算失败；下次用原命令续跑。

## Windows agent 执行步骤

先执行以下预检与备份；任何一项不满足就停止，不接管写入端：

```powershell
$peachRoot = Join-Path ([Environment]::GetFolderPath('Desktop')) 'peach'
$peachApp = Join-Path $peachRoot 'peach-app'
$peachData = Join-Path $peachRoot 'peach-data'
$peachPython = Join-Path $peachApp '.venv\Scripts\python.exe'
$peachDb = Join-Path $peachData 'database\ledger.db'
Set-Location $peachApp
$peachDirty = & git status --porcelain
if ($peachDirty) { throw 'Windows peach-app 工作区不干净，停止夜跑' }
& git pull --rebase
if ($LASTEXITCODE -ne 0) { throw 'git pull --rebase 失败' }
& $peachPython -m pip install -e .
if ($LASTEXITCODE -ne 0) { throw 'Peach 依赖安装失败' }
& .\scripts\test.ps1
if ($LASTEXITCODE -ne 0) { throw 'Windows 全量测试失败' }
& $peachPython -c "import importlib.metadata,socksio; print(importlib.metadata.version('socksio')); print(socksio.__file__)"
if ($LASTEXITCODE -ne 0) { throw 'socksio 验证失败' }
& $peachPython -m peach migrate status
if ($LASTEXITCODE -ne 0) { throw '迁移状态检查失败' }
$peachHealth = Invoke-RestMethod http://127.0.0.1/healthz
if ($peachHealth.ledger_sync -ne 'writer' -or $peachHealth.db -ne 'available') { throw 'Windows 不是可用的 Ledger writer' }
$peachMountItem = Get-ChildItem 'A:\' -Force -ErrorAction Stop | Select-Object -First 1
if (-not $peachMountItem) { throw 'PikPak A: 无法列出内容' }
$peachJobs = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'scripts\\(probe|sheets|traffic_watch)\.py' }
if ($peachJobs) { $peachJobs | Select-Object ProcessId,CommandLine; throw '已有同类批处理在运行' }
$peachFree = (Get-PSDrive 'C').Free
if ($peachFree -lt 40GB) { throw 'C: 可用空间不足 40 GiB' }
$peachStamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$peachBackup = Join-Path $peachData "database\ledger.pre-pikpak-visuals-$peachStamp.db"
& $peachPython -c "from pathlib import Path; from peach.migrations import sqlite_backup; import sys; sqlite_backup(Path(sys.argv[1]),Path(sys.argv[2]))" $peachDb $peachBackup
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $peachBackup)) { throw 'SQLite backup API 备份失败' }
Get-Item $peachBackup | Select-Object FullName,Length,LastWriteTime
```

先在独立窗口启动流量守卫；`--count-direct` 保证路线切到 DIRECT 后仍然计费：

```powershell
& $peachPython scripts\traffic_watch.py --limit 200 --warn 120 --count-direct
```

另一个窗口按顺序执行封套、probe 和接触表；probe 非零退出时不得继续接触表：

```powershell
& $peachPython scripts\fetch_jav_covers.py --location pikpak
& $peachPython scripts\probe.py --location pikpak --allow-metered --redo all --workers 6 --min-free 40
if ($LASTEXITCODE -ne 0) { throw "PikPak probe 未正常完成：$LASTEXITCODE" }
& $peachPython scripts\sheets.py --location pikpak --allow-metered --workers 4 --frames 9 --min-free 40
```

同一晚上只允许一个 PikPak 媒体批次，不混跑 115。夜跑期间不执行 Ledger 同步、接管、托盘重启
或其他真实库批处理。次日先核对日志、完整性、外键和前后计数；确认无误后，再由托盘的
「同步 Ledger」停服并推送共享副本。

## 次日验收

先打印实时队列并读取两类任务的最新日志：

```powershell
& $peachPython scripts\job_status.py
$peachProbeLog = Get-ChildItem (Join-Path $peachData 'logs') -Filter 'probe-*.log' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$peachSheetsLog = Get-ChildItem (Join-Path $peachData 'logs') -Filter 'sheets-*.log' | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($peachProbeLog) { Get-Content $peachProbeLog.FullName -Tail 60 }
if ($peachSheetsLog) { Get-Content $peachSheetsLog.FullName -Tail 60 }
```

再做数据库完整性与外键检查；任何一项不通过都不得同步：

```powershell
$peachDbCheck = & $peachPython -c "import sqlite3,sys; c=sqlite3.connect(sys.argv[1]); print(c.execute('PRAGMA integrity_check').fetchone()[0]); print(len(c.execute('PRAGMA foreign_key_check').fetchall()))" $peachDb
if ($LASTEXITCODE -ne 0 -or $peachDbCheck[0] -ne 'ok' -or $peachDbCheck[1] -ne '0') { throw 'PikPak 夜跑后的数据库检查失败' }
```

报告必须包含：probe 完成/失败/待处理、缩略图完成/失败/待处理、流量守卫累计下载、FlowLens 显示的
实际 PikPak chain、`C:` 剩余空间、备份路径、退出码，以及是否触发流量或磁盘闸门。不要只写
「跑完了」。
