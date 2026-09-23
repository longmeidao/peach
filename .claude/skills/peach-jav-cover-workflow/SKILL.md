---
name: peach-jav-cover-workflow
description: 在用户说 JAV 封面、高清封面、缺封面、封面刮削、重探、来源比较或继续抓取时使用。
---

最后复核：2026-09-23
证据来源：`scripts/fetch_jav_covers.py`、`scripts/detect_cover_faces.py`、`tests/test_jav_covers.py`、`docs/REUSE.md` 与 ABW-232 官方来源实测。

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

所有候选都量尺寸，不设「某主机永远优先」的固定链：

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

## 取景 sidecar

新封面写入后补算人脸，否则页面只能用写死的锚点：

```powershell
& .\.venv\Scripts\python.exe .\scripts\detect_cover_faces.py
```

- 已算过的默认跳过，`--redo` 才重算；954 张实测检出 885 张，未检出的页面居中。
- sidecar 的 `cx` 和 `cy` 都要留着。用哪个轴由容器比例决定：`object-fit:cover`
  一次只裁一个轴，16:9 官方剧照在大图版式里裁的是横向，纵向锚点在那里不生效。
- 版式判据（1.2 / 1.65 两个分界）的真相在 `peach.jav_poster_crop`，`web/app.js`
  的 `coverAnchor` 里另有一份，改一处必须改两处：对不上就会出现「脚本按封套丢掉
  左半边的脸、页面按剧照用那张脸取景」。

大图卡片要的是另一样东西：书脊折痕在哪，同目录写 `<番号>.poster.json`：

```powershell
& .\.venv\Scripts\python.exe .\scripts\poster_crop_boxes.py
& .\.venv\Scripts\python.exe .\scripts\poster_crop_boxes.py --apply
```

- 判据在 `peach.jav_poster_crop`：Sobel 列梯度找书脊折痕，HEYZO／FC2／六位日期／韩国 MIB
  不裁；16:9 只认满高拼接缝（覆盖 ≥75% 行）夹出的居中正封（PASN 等），原图不动。
- **折痕按「切出来的正封形状对不对」认，不按它落在全宽的百分之几**。正封宽高比是印刷
  面的物理常数（DVD 135×190mm ＝ 0.711），本机 637 张实测中位 0.704、1% 分位 0.684、
  99% 分位 0.725；折痕在全宽里的位置则随背面留白与书脊厚度飘。所以只在 0.68～0.76
  （`PANEL_ASPECT_MIN`～`PANEL_ASPECT_MAX`）这个窗口里找峭壁，窗外再强的边是画面内容，
  按它切会削掉一截大标题：KBI-036 的背面分栏线与正封内一道边恰好关于中线对称。
- **窗里够强的边不止一条时按形状挑，不按谁更强**（`FOLD_RIVAL_RATIO`，到窗内最强边
  七成的都算候选，相邻列归并成一条边）。书脊有两条边，厚一点的两条都落在窗里，而左
  边那条常常更强，因为它挨着封底的留白，右边那条挨着正封的画面，按最强的切整条书脊都
  留在框里。ABP-968 的书脊 39 列，左缘切出 0.718、右缘 0.703，本机 67 张按这条定夺。
- **峰是斜坡最陡的那一列，不是斜坡尽头**。折痕在梯度上是一道有宽度的斜坡，书脊最后
  一两列还压在峰的右边，按峰切会在正封左缘留下一条竖线。选定之后再往右走到梯度落回
  窗内中位数为止（`FOLD_SETTLE_LIMIT`，最多走源图宽的 1%）：基线每张图各算各的，
  画面忙的封套门槛自然就高。本机实测位移中位 2 列、90% 分位 3 列。
- 框就是正封本身：`x0` 是折痕列，右下角就是源图右下角。框里不另取子区域，因为卡片的
  容器比例只有页面知道，在这一侧先按某个形状切一刀，只会把正封两侧各削掉一圈。
- 默认只算边车缺失、算法版本落后或源图尺寸对不上的封面，所以重探换上更大的图之后再
  跑一遍就会重算；`--redo` 才无条件全算。改了判据要进 `ALGORITHM_VERSION`，全库才会重算。
- 页面只用框里的 `x0`：`web/app.js` 的 `posterPanel` 把它换算成 `--panel-clip` 与
  `--panel-left`，图片按卡片高度铺满、`clip-path` 切掉折痕以左的封底，正封居中摆。
- **容器比例定在 0.75，别按单张封面调**：一行卡片必须等高，比例只能是全局一个数。
  切出来的正封宽高比落在 0.667～0.749 之间，全在 0.75 以下，所以一张都不用从左边切，
  两侧留白由 `--cover-blur` 那层模糊背景垫，每边中位 3.1%、最大 5.6%；取 0.72 会让 10
  张被切掉最多 3.8%，取 0.76 同样一张不切但留白到每边中位 3.7%。
- 找不到折痕的（本机 46 张）按 `PANEL_ASPECT` 从右缘量回去，方法记 `ratio`；形状仍是
  正封的物理比例，不会把书脊带进来。

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
