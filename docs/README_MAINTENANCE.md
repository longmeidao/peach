# README 维护


README 面向初次访问项目的人，依次解释定位、核心能力、开始使用、数据边界和文档入口。
中英文同批维护，平台支持、安装方式和能力限制保持一致。主线能力、已安装运行态和发行制品分别
以实现、STATUS 和 Releases 为准，README 不填写本机 IP、端口归属、真实馆藏数字或动态版本号。

| 内容 | 核验入口 |
| --- | --- |
| Python 与桌面命令 | `pyproject.toml`、`src/peach/cli.py`、`src/peach/tray.py` |
| 前端工具与产物 | `frontend/package.json`、`docs/FRONTEND.md` |
| 桌面包与平台范围 | `docs/TESTING_DESKTOP.md`、`.github/workflows/release.yml` |
| 当前行为与已部署范围 | 实现与测试、`docs/STATUS.md`、`docs/PRODUCT_BACKLOG.md` |
| 来源、配置与数据边界 | `docs/SOURCING.md`、`docs/OPERATIONS.md`、`docs/CLOUDDRIVE.md` |

README 迭代绑定 Codex 与 Claude 共用的工作树交付流程。每次提交前核对暂存差异，
涉及用户可见能力、安装、平台或构建要求时，同批更新中英文。只改变内部实现时保留 README，
在交付分支最后一个提交的 Git trailer 写明原因：

| 判断 | 提交消息末尾的独立字段 |
| --- | --- |
| 已更新两份 README | `README-Impact: updated; 同步了哪些用户说明` |
| 不影响 README | `README-Impact: none; 具体原因` |

声明与 `Co-Authored-By` 等其它 trailer 连续写在提交消息末尾的同一块里，彼此之间不留空行。
同一块里的署名形态见 `.claude/skills/peach-worktree/SKILL.md`「暂存与提交」。
`git interpret-trailers --parse` 只解析末尾那一块，被空行隔开的 `README-Impact` 属于正文段落，
`ready` 报「交付提交须有唯一 README-Impact」，而提交消息本身看不出哪一行不合格。

`scripts/check_readme_impact.py` 读取目标分支到交付 HEAD 的实际差异，并使用
`git interpret-trailers --parse` 读取最后提交的声明。涉及运行时代码、前端、迁移、资源、
依赖或安装说明时必须声明；纯测试和其他内部文档不触发。触发清单由脚本统一维护。
README 改动必须包含两种语言；`updated` 必须对应两份实际差异，`none` 不得伴随 README 改动。
提交后的暂存内容不能满足要求。原因的真实性仍由代码审阅负责，脚本不代替语义判断。

`agent_worktree.py ready/integrate` 在接受测试记录前执行这一门槛；漏项由当前智能体直接补齐，
再次验证后交付，不需要用户转述。检查覆盖本次分支交付，不追溯主线历史提交；
允许在最后交付提交统一核对整批差异。它不是 Git 全局 hook，直接 Git 提交不会触发，
但未通过的分支不能经项目入口集成。两个智能体都从 peach-worktree 技能读取流程。
无需定时任务、账号专属 hook 或额外模型调用。Python 下限、文案和快照校验继续复用现有测试。
结构或品牌调整时重读已登记的参考快照，上游变化只作为参考，计划功能不得写成已实现。

## 演示数据集

README、教程与网站的截图一律取自合成的 SFW 演示库，不取自真实馆藏，也不用分类模型从
真实馆藏里筛「看起来无害」的帧：筛出来的多是黑场与标题卡，卡片上的番号、姓名与厂牌
照样泄露来源，封面与抽帧也是他人作品。

生成器是 `scripts/demo_dataset.py`，只写目标目录，不碰任何账本：

```powershell
& .\.venv\Scripts\python.exe -X utf8 scripts\demo_dataset.py --output <目录> --count 24
```

画面是 FFmpeg lavfi 的渐变、测试图与分形，海报是 Pillow 画的几何图，作品、厂牌、系列、
出演者与标签全部虚构；`tests/test_demo_dataset.py` 把守词表与 `catalog_rules` 成人词表
不相交、目录布局符合 `library_nfo` 的边车规则、`process_library` 跑完没有发过外部请求。
`--seed` 固定内容，`--video stub` 用占位字节代替编码，给性能基准的规模档用。

三种形状对应三条产品路径：番号型（`<番号>/<番号>.mp4` 配 NFO 与 `-poster.jpg`，部分带
`P/` 图集）走本地资料入库；创作者型（`<创作者>/<标题>.mp4` 配 PNG 与无番号 NFO）走
`posters/<id>_4.jpg` 本地海报；裸文件演示「未识别到番号」。让 Peach 看见它：`peach init`
建演示数据根，在设置文件 `[media.locations]` 声明这个目录，`peach scan local`、
`peach process local`，候选在复核页全选通过或用 `scripts/apply_metadata_tags.py --source local_nfo`
按字段落地；要九宫格再跑 `scripts/probe.py` 与 `scripts/sheets.py`。生成器结束时会把这几步连同
当前平台的设置行一起打印出来。

新库的实体只来自复核落地，扫描本身不派生创作者，也不把图片挂到实体上，因此演示库的
创作者页与实体图集为空；这是产品现状，不是数据集缺项。

## 参考依据

- **README 结构（2026-09-06）**：依据聊天「寻找README范例」并取得 Immich、Bruno、Hoppscotch
  当前 README 原文，URL、日期与 SHA-256 见 `docs/reference-sources.json` 的 `readme-*` 条目。
  采用短定位、小尺寸具象 Logo、集中下载导航和精简能力分组；仅沿用 Peach 自有图标，
  不复制外部商标、截图、功能承诺或宣传内容。上游快照仅为取证，保留原文及上游许可入口。
  Peach 的 SFW 产品截图未取得，因此当前首页不展示产品截图；桌面、手机与深浅色渲染尚需实际浏览器验收。
