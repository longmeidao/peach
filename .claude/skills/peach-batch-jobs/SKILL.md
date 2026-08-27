---
name: peach-batch-jobs
description: 在用户说抽帧、接触表、probe、sheets、creator_boards、刮削、批量、长任务、限流、续跑、流量预算或磁盘余量时使用。
---

# 长跑批处理与流量边界

最后复核：2026-08-27
证据来源：`scripts/probe.py`、`scripts/sheets.py`、`src/peach/jobs.py`、相关单元测试与 ADR-0015。

## 失败值

测量失败不能写成下游可误认的正常值。`probe.py` 曾把「ffprobe 无时长」写成 `duration=0`，
数据因此同时退出 `duration IS NULL` 队列又进不了 `duration>2` 队列。失败一律写 `-1`，
并提供 `--redo zero|failed|all`。

两组状态数字看似矛盾时，先查是否存在两边查询都遗漏的状态，不要直接判定其中一组错误。
待办数量统一报告「可执行 / 被阻塞 / 合计」。

## 磁盘闸门

起跑前一次 `require_free_space` 不是运行期闸门。`DiskGuard` 默认每 20 秒复查 `C:` 实际余量；
`probe.py`、`sheets.py`、`creator_boards.py` 触线后停止领新任务、保留已完成结果并返回退出码 3，
不得伪报正常完成。

2026-08-15 的 115 抽帧曾把系统盘写到零：真正膨胀的是 CloudDrive 位于系统盘的稀疏读取缓存，
不是产物所在磁盘。CloudDrive 退出可能重写配置，长跑前后都要复核缓存上限和淘汰策略，不能把
历史配置值当成当前事实。

## 限流

- 限流是各主机自己的事，不是任务属性。`HostLimiter` 按主机各记一个下次可发时刻；线程等 r18
  的空档去查 av-wiki 和 javdb，实测 12 位从约 8 秒/位降到 4.4 秒/位。
- 限流参数只能用与真实批次同量级的运行来标定。r18 在 12 个请求的短测里 1.0 秒间隔全过，
  据此降参后连跑约 18 分钟开始被拒，556 位里 203 位成了假阴性；改回 2.0 秒连跑 62 分钟稳定。
- 被 Cloudflare 拦的站一律放弃，不绕过机器人检测。

## 续跑

长任务必须能续跑。一次未捕获的 TLS EOF 曾让 62 分钟结果归零：网络异常降级为空值而不是抛出，
结果定期写入文件，`--resume` 只把成功判定当作已完成——`no_name` 这类多半是限流假阴性，冻结进
复核文件就再无重试机会。

## 流量与进程

- 200 GB 守卫默认只统计代理流量，覆盖 PikPak，看不到直连 115；需要覆盖直连时显式
  `--count-direct`，且不要在同一计量窗口混跑不同来源。
- 实测（2026-08-15，经 mihomo）：115 单文件 ffprobe 约 25 MB，九帧接触表约 285 MB；
  PikPak 单文件 probe 12–52 MB，九帧约 163 MB / 13.7 秒。PikPak 抽帧的主要约束是字节不是耗时。
  PikPak 策略组切 DIRECT 后九帧为 30.5 MB / 64.2 秒。
- `-probesize`/`-analyzeduration` 无法减少 CloudDrive 固定块预取；未知时长时创作者板可回退到
  60 秒 seek，不需要先做全量 PikPak probe。
- Windows 查询已消失 PID 可能抛 `OSError(winerror=87)` 而不是 `ProcessLookupError`，
  `PidFileLock` 必须识别为陈旧锁并安全清理。
- 长任务只停止自己拥有且命令行匹配的 Python/FFmpeg 进程树，禁止全机终止 FFmpeg。
- 导入运维脚本不得触发文件、网络或数据库副作用。

## 抽帧路径

`scripts/sheets.py`、`scripts/probe.py` 的 worker 直接用账本路径跑 FFmpeg，不走 MediaEngine。
修大小写敏感挂载层的失败必须先把 `peach.media.resolve_case_insensitive` 接入这两个 worker。
`sheets.py` 遇 `prim:reserved` 非法色彩元数据会带 bt709 声明重试，只在失败帧重试，不得无条件
给所有输入加色彩覆盖。
