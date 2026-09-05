# ADR-0024：发行版带清单，不带图片字节

- 状态：Proposed（方案，交由他人实施；每一步真实 ledger 写入仍按 `peach-ledger-write` 单独授权）
- 日期：2026-09-05
- 关系：属于 ADR-0023 第四阶段「让陌生人能装起来」的一部分；取图链路的判据见 `docs/SOURCING.md`，复用清单见 `docs/REUSE.md`。

## 背景

Peach 现在这台机器上已经攒了一批从公网取回来的图：厂牌与事务所的标识、女优头像、番号封面。
新用户装上一份空的 Peach，页面上全是空位，要自己把这批图重新抓一遍——而抓这一遍需要能连上
日文站点、需要登录态才能拿到某些头像、需要几个小时的限流等待。这三样不是每个用户都有。

所以问题是：这些图该不该直接打进发行版。

### 现状实测（2026-09-05，`peach-data/generated/`）

| 目录 | 图像文件 | 占用 | 来自公网 | 带 `source_url` 的边车 |
| --- | --- | --- | --- | --- |
| `logos/` | 224 | 4.7 MB | 是 | 181 |
| `avatars/` | 695 | 83.9 MB | 是 | 26 |
| `covers/` | 956 | 1393.5 MB | 是 | 0 |
| `posters/` | 8705 | 148.3 MB | 否，抽自本机媒体 | 0 |
| `photo-thumbs/` | 876 | 52.6 MB | 否，缩自本机媒体 | 0 |
| `link-marks/` | 38 | 0.4 MB | 是，按主机缓存 | 0 |

`posters/`、`photo-thumbs/` 是从用户自己的媒体文件派生的，本来就只对这台机器成立，不在讨论范围内。
`link-marks/` 是按主机缓存的站点图标，第一次访问就会自己长出来，也不需要随发行版走。
要讨论的是 `logos/`、`avatars/`、`covers/` 这 1875 个文件、约 1.45 GB。

边车已经有了形状（`<文件名>.provenance.json`）：

```json
{
  "source": "studio icon harvest",
  "source_url": "https://pbs.twimg.com/profile_images/2094369416905650176/GyqWkfql.jpg",
  "sha256": "23ec679e…5605",
  "installed_sha256": "23ec679e…5605",
  "variant": "icon",
  "verdict": "ok",
  "imported_at": "2026-09-05T09:32:29Z"
}
```

缺的不是格式，是覆盖率：三类合计 1875 个图像文件里只有 207 个记着来源地址。

## 决策

**发行版分发清单，不分发图片字节。云端只负责生成清单，同样不分发字节。**

1. `peach-app` 仓库里带一份 `data/marks/manifest.jsonl`（随代码走，纯文本，可 diff、可 review）。
   每行一条记录，说明「哪个实体的哪个位置，该去哪儿取哪一份图，取到之后 sha256 应该是多少」。
2. 新用户跑一条命令，本机按清单取图、校验 sha256、落盘到 `peach-data/generated/`。取不到的写
   `未取得`，页面照旧显示空位，不拿别的图顶替。
3. 云端主机（如果要有）只做一件事：定期重跑采集、生成新的清单、开 PR。它不托管图片，也不
   替用户取图。

### 为什么不打包字节

- **仓库是公开的。** 这批图里有第三方商标（厂牌标识）、真人肖像（女优头像）、成人作品封面。
  把它们提交进公开仓库，是由这个仓库对外再分发，和用户自己去原站取回来是两件事。
- **体积。** 1.45 GB 里 96% 是封面。Git 存二进制不 delta，每次更新一张就多一份全量。
- **图会变。** 事务所改版、艺人换头像、厂牌重做标识。打包进去的那一份从落盘那天起就开始过期，
  而清单里的 `sha256` 恰好能说出「它变了」。
- **平台政策。** 成人封面进公开仓库有被下架的实际风险，且下架会连带整个仓库。

### 为什么云端主机不替用户抓

替所有用户抓同一批图再发出去，就是上一节那件事换了个位置：字节仍然由这里对外再分发，只是从
Git 换成了 HTTP。云端能做而本地做不好的只有一件事——持续复查「这些地址还活着吗、图换了吗」，
那是清单的工作，不是字节的工作。

## 清单的形状

`data/marks/manifest.jsonl`，每行一个 JSON 对象，UTF-8、LF、按 `key` 排序（让 diff 稳定）：

```json
{"key":"agency/EST/icon","kind":"logo","target":"logos/EST.icon.img","url":"https://pbs.twimg.com/profile_images/2094369416905650176/GyqWkfql.jpg","sha256":"23ec679e…5605","bytes":74627,"size":"1134x1129","content_type":"image/png","verdict":"ok","checked_at":"2026-09-05T09:32:29Z"}
```

字段判据：

- `key`：稳定标识，`<实体类别>/<canonical_name>/<位置>`。实体改名时清单跟着改，这是一次可复核的 diff。
- `target`：相对 `peach-data/generated/` 的落盘路径。装图那一步只认这个字段，不再自己拼文件名。
- `url`：原站地址。**必须是不带签名的长期地址**。带签名的（Instagram CDN 的 `oh=`／`oe=`）不进清单——
  它们几小时就过期，写进去等于写了一条注定 404 的记录。`pbs.twimg.com/profile_images/…` 不带签名，可以进。
- `sha256`：取回来的原始字节的摘要，用来校验，也用来发现原站换了图。
- `verdict`：沿用采集器的判词（`ok`／`字标补白`／`未取得` 等），让装图那一步能跳过本来就没做成的行。
- `checked_at`：这条记录最后一次被验证的时刻。云端每次复查只改这个字段和变了的那几个。

封面另立一份 `data/marks/covers.jsonl`：它按番号而不按实体，且只对**拥有该番号资产**的用户有意义，
装图那一步要先和本机 ledger 对一次账，不能无条件取回 956 张。

## 要交付的东西

给实施者的四步，每步独立可验收：

1. **补齐来源记录。** 现在只有 207/1875 条记着地址。补的路子已经在库里：
   - `logos/`：缺的 43 条从 `generated/studio-logo-candidate-*.csv` 的 `resolved_url` 回填；
     实在找不到的重跑一遍 `scripts/harvest_studio_icons.py`，它现在每装一枚就写边车。
   - `avatars/`：`generated/performer-avatar-candidate-*.csv` 带 `source_url`、`width`、`height`；
     `scripts/harvest_social_avatars.py` 是它的采集入口。
   - `covers/`：`generated/cover-fetch-log.csv` 有 1401 行，带 `code`／`source`／`url`／`width`／`height`，
     和 `covers/<code>.jpg` 按番号对得上。`scripts/fetch_jav_covers.py` 是入口。
   这一步只写边车，不碰 ledger，也不重新下载。产出一份复核 CSV 说明每个文件的来源是从哪儿找回来的、
   哪些确实找不回（写 `未取得`，下一步重抓）。
2. **导出器。** `scripts/export_mark_manifest.py`：扫 `generated/` 的边车，出上面那两份 jsonl。
   默认 dry-run 只打印统计；带签名的地址、`未取得` 的行、以及边车里 `installed_sha256` 和实际文件
   对不上的行，都要单独列出来而不是静默丢掉。
3. **装图器。** `scripts/install_marks_from_manifest.py`：读清单、按 `target` 落盘、逐条校验 sha256。
   - 已经存在且 sha256 一致的跳过；不一致的按 `harvest_studio_icons._shorter_than_installed` 同一条
     规矩办——更小的那份不许覆盖已装的。
   - 限流、重试与超时沿用 `peach-batch-jobs` 的约定；传输层异常重试，状态码一次成局
     （`install_entity_links.resolves` 是现成的样子）。
   - 取不到的整条跳过并计入统计，绝不拿别的图顶替，绝不半截文件落盘。
   - 封面那一份先和 ledger 对账，只取本机确实拥有的番号。
4. **首次运行接进去。** `peach init` 之后提示「要不要现在按清单取图」，默认取标识（4.7 MB，224 个文件，
   最快见效），头像和封面另问。ADR-0023 第一阶段的问答逻辑在 `peach.onboarding`，复用它。

## 验收

- 一台干净的机器：`peach init` → 按清单装标识 → `/agencies` 页上有标识的家数和这台机器一致。
- 清单里每一条的 `url` 都能在无 Cookie、无登录态下取回，且 sha256 与记录一致；做不到的那几条
  必须在清单里就写着 `未取得`，而不是装的时候才发现。
- 导出器对同一份 `generated/` 跑两次，输出逐字节相同。
- 测试：导出器与装图器各自的单元测试进 `scripts/test_runner.py` 的 `tooling` 域；
  校验失败、地址过期、更小的图不覆盖，这三条各要一个用例。
- 仓库里不出现任何新的图片二进制（`tests/test_repo_hygiene.py` 加一条守卫）。

## 不在本 ADR 范围内

- 图床、CDN、以及任何由这个项目对外分发图片字节的形态。
- Instagram 头像。它的 HD 地址签名覆盖了 `stp`，无法构造，且只在登录态的资料页里偶尔出现
  （`docs/SOURCING.md` 有实测），不具备「任何用户都能按清单取回」的性质，不进清单。
- 云端主机本身的部署形态。清单只要能由 PR 进来，谁生成的不影响本 ADR 的判据。
