# ox · Windows JAV 与 PikPak 夜跑交接单

## 目标与边界

ox 负责耗时、机械、可续跑的发现与候选生产：

1. 补全全库 JAV 官方封套，并生成封套人脸取景旁车。
2. 按 `docs/PIKPAK.md` 全量重跑 PikPak probe 与九帧接触表，单独计量速度和流量。
3. 补跑番号元数据候选，审计缺女优、厂牌、系列的作品。
4. 审计女优高清头像缺口，以及实体合并后遗留在旧 ID 下的孤立头像。
5. 只生成文件名、目录整理的 dry-run 计划，不直接移动目录。

ox 不做：`--apply` 写真实 ledger、实体合并、覆盖现有头像、跨 `A:`/`B:`/`R:` 移动、清空或删除、
服务重启、Ledger 同步或接管。代码改动只在独立 worktree/分支提交，不自行合并主线。

## 已知样本诊断

- `MIDV-751CH.mp4` 已识别为番号 `MIDV-751`，并已有 `中文字幕` 标签；官方封套
  `MIDV-751.jpg` 也已存在。它不是番号后缀漏识别样本。
- `CWPBD-126`、`SMBD-145` 都已有女优 `立花美凉` 和厂牌关系，但当前没有官方封套。
  `SMBD-145` 上一轮三源均无候选，已记为 settled miss；普通续跑会跳过，只有
  `--retry-misses` 才会重试。
- `立花美凉` 当前实体是 `performer 8022`，界面会请求 `performer-8022.img`，该文件缺失后回落到
  视频抽帧头像。旧实体 `8168` 下仍有经过来源记录的 Gfriends `500×600` 头像。这是实体合并后的
  头像文件 ID 没迁移，不是身份刮削失败。
- 2026-08-22 Mac reader 快照仅供定位：全库封套 483 张、缺 482 个番号，其中 149 个是 settled
  miss，默认可续抓 333；缺口几乎都来自 115，PikPak 只剩 1 个。Windows 开跑前必须重算。

## 0. 预检

以 `C:\Users\longm\Desktop\peach\peach-app` 的最新 `master` 为代码基线，先完整执行
`docs/PIKPAK.md` 的预检、依赖安装、`socksio` 验证、测试、writer/mount/disk/job 检查和 SQLite
backup。任何一项失败都停止，不换路径猜测，也不使用迁移前的 `R:\peach-app`。

每个阶段单独记录开始/结束时间、退出码、日志路径、命中/未取得/待处理、FlowLens chain 与流量。
封面 HTTP 请求和 PikPak 媒体读取不能放在同一个流量计量窗口，否则无法回答 PikPak probe/缩略图
实际消耗。

## 1. 全库 JAV 封套

先跑默认续抓；它跳过已有图片和上一轮确定无候选的番号：

```powershell
& $peachPython scripts\fetch_jav_covers.py
```

默认批次正常结束且时间有余，再单独重试 settled misses：

```powershell
& $peachPython scripts\fetch_jav_covers.py --retry-misses
```

最后为新封套生成取景旁车；不加 `--redo`，已有结果跳过：

```powershell
& $peachPython scripts\detect_cover_faces.py
```

这一步只写 `peach-data\generated\covers` 和 `cover-fetch-log.csv`，不写 ledger。报告必须单列
`CWPBD-126`、`SMBD-145` 的结果；未取得就是来源缺口，不能拿搜索结果缩略图冒充官方封套。

## 2. PikPak 全量 probe 与九帧接触表

严格照 `docs/PIKPAK.md` 执行：先开 200 GB 流量守卫，再依次运行：

```powershell
& $peachPython scripts\fetch_jav_covers.py --location pikpak
& $peachPython scripts\probe.py --location pikpak --allow-metered --redo all --workers 6 --min-free 40
if ($LASTEXITCODE -ne 0) { throw "PikPak probe 未正常完成：$LASTEXITCODE" }
& $peachPython scripts\sheets.py --location pikpak --allow-metered --workers 4 --frames 9 --min-free 40
```

probe 非零退出时不继续 sheets。触发 200 GB 或 40 GiB 磁盘闸门属于安全停止，下次原命令续跑。
同一窗口不混跑 115、不跑番号元数据、不同步 ledger。

## 3. 番号元数据：候选模式

`scrape_codes.py` 的默认 Windows 路径仍是迁移前的 `R:`，必须显式传新路径；不加 `--apply`：

```powershell
$peachCodeCsv = Join-Path $peachData 'generated\code-scrape.csv'
$peachLogDir = Join-Path $peachData 'logs'
& $peachPython scripts\scrape_codes.py --db $peachDb --out $peachCodeCsv --log-dir $peachLogDir
```

它按 CSV 续跑，只产候选。交付新增番号行、各来源命中率、`not_found`、冲突和缺出演关系清单。
不得直接 `--apply`；旧 CSV 里已经出现过重复女优串，写库前需要主 agent 复核规范实体与兼容投影。

## 4. 高清女优头像：ox 的独立代码任务

成熟实现仍在 `agent/claude/performer-portraits` 的 `scripts/import_performer_portraits.py` 与测试中；
不要直接在旧分支对当前 ledger 运行 `--apply`。从最新 master 新建独立 worktree，只把其中的
Gfriends 索引、图像完整校验、长边 ≥500/短边 ≥300、provenance 和按主机限速逻辑迁入当前脚本。

当前 ledger 已完成中文规范名本地化，所以新审计器必须：

1. 只选缺 `generated\avatars\performer-<entity_id>.img` 的 performer。
2. 依次用 canonical name、alias、`metadata_json.name_localization.jp`、已核实旧名匹配 Gfriends。
3. 默认只写 CSV，列出 entity ID、匹配名、来源档位、尺寸、URL、判定；网络失败可续跑。
4. 审计所有 `performer-<已删除 ID>.img`：只有旧 ID 的 provenance 名能唯一命中当前实体、当前目标
   不存在时，才列为 `orphan_relink` 候选；不覆盖、不删除旧文件。
5. 为 `8022 <- 8168` 写回归测试，证明能找到 500×600 Gfriends 图并保留 provenance。

ox 交付分支和 dry-run CSV，由主 agent 代码审阅后再决定是否复制头像文件或写 ledger。

## 5. 文件名与网盘目录

ox 可以先生成保守文件名净化清单：

```powershell
$peachNameCsv = Join-Path $peachData 'generated\name-clean.csv'
& $peachPython scripts\clean_names.py --db $peachDb --out $peachNameCsv --log-dir $peachLogDir --location 115
```

此阶段不加 `--apply`。目录整理另出 CSV，至少包含源路径、目标路径、依据、同名碰撞、大小写-only
改名、非法 Windows 字符、来源盘和关联 asset ID。不得跨盘移动，也不得按文件夹名猜创作者。

实际文件/目录改名必须放到独立维护窗口：停止同类任务，确认 Windows 是 writer，SQLite backup，
逐条同目录 rename 与 ledger path/name 同步，失败时文件名回滚；最后跑完整性、外键和路径存在性检查。

## 交付

ox 最终只交：

- 分阶段日志、退出码、起止时间和 FlowLens 流量/chain。
- 封套、probe、接触表的完成/失败/待处理计数。
- 番号元数据、头像缺口、孤立头像、文件名/目录计划 CSV。
- 独立代码分支及测试结果；不合并、不部署、不重启、不同步。
- 明确列出需要主 agent 决策的冲突，不能用“基本完成”代替数字。
