---
name: peach-jav-cover-workflow
description: 在用户说 JAV 封面、高清封面、缺封面、封面刮削、重探、来源比较或继续抓取时使用。
---

最后复核：2026-08-31
证据来源：`scripts/fetch_jav_covers.py`、`tests/test_jav_covers.py`、`docs/REUSE.md` 与 ABW-232 官方来源实测。

# JAV 封面获取流程

目标是取得可证明属于当前番号的最大官方封套。封面是可重建产物，不写 ledger；
`cover-fetch-log.csv` 是来源与尺寸证据，必须保留。

## 起跑前

1. 读 `docs/STATUS.md` 与 `docs/REUSE.md` 的 JAV 封面条目。
2. 检查是否已有 `fetch_jav_covers.py` 进程；不得重复起跑。
3. 运行只读盘点，记录番号、已解码、缺失、损坏和宽度分布：

   ```powershell
   & .\.venv\Scripts\python.exe .\scripts\fetch_jav_covers.py --audit
   ```

## 候选来源

所有候选都量尺寸，不设“某主机永远优先”的固定链：

1. 先离线复用 `sources/metadata/javinizer-go/<番号>/*.json` 的 `cover_url` 与
   `content_id`，不要为已有成功快照重复请求元数据站。
2. 从 DMM URL 生成并实测 modern `awsimgsrc.dmm.com/dig/...`、legacy
   `awsimgsrc.dmm.co.jp/pics_dig/...` 和原始 URL；覆盖 `digital/video`、
   `digital/amateur`、`mono/movie`。
3. 有 Prestige 厂牌证据时，再直连 MGS `EnlargeImage` 与 Prestige
   `api/search` → `api/product` → `packageImage`。
4. 把上轮成功日志的精确 URL 加回候选，保住已发现的 DUGA 等图片。
5. AVBase 被 Cloudflare 拦截时放弃，不绕过。DUGA 批量搜索没有代理店应用 ID 时不调用。
6. Amazon 日本只有完成真实 POC、匹配无歧义并登记来源后才能进入候选；不把 4K/8K 水印或放大图
   当作原始高清封面。

坏例：按主机名直接覆盖 1000×674 的 DUGA 图，换成 800×539 的 DMM 图。
好例：Range 读取图片头，校验可解码和宽度门槛，按像素面积选最大者。

## 下载与替换门槛

- 宽度低于 700、无法解码、缩略图、剧照、关联作品图都拒绝。
- Range 最多先取 64 KiB 量尺寸，胜出后才下载完整图片。
- 已有封面只有候选像素面积更大时才写同目录临时文件并原子替换。
- 单条网络异常写失败并换连接池，任务继续；确认无候选与瞬时失败分开记录。
- `DiskGuard` 运行期守住系统盘；每条完成后重写可续跑日志。

## 正式批次

先重探所有缺失，包括旧的确认落空：

```powershell
& .\.venv\Scripts\python.exe .\scripts\fetch_jav_covers.py --retry-misses
```

再重探宽度低于 1200 的已有封面；只会升级，不会降级：

```powershell
& .\.venv\Scripts\python.exe .\scripts\fetch_jav_covers.py --upgrade-existing --upgrade-max-width 1199
```

## 收尾

1. 再跑 `--audit`，报告前后缺失、损坏、尺寸分布、取得、保留与失败。
2. 抽查新增来源 URL 与本地图片尺寸，确认番号精确匹配。
3. 代码变更跑 `& .\scripts\test.ps1 -Scope metadata`；跨域时跑 full。
4. 分开报告代码/测试、真实封面产物、生产服务和 ledger；本流程正常不重启、不写 ledger。
