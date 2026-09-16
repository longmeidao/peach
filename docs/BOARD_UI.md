# BoardUI 适配

## 空状态操作入口

空状态复用 `emptyStateHtml`，操作位于说明下方、居中排列，窄屏可换行。关注列表与关注更新的空状态提供「添加关注」主按钮；馆藏、标签和实体索引中的关注入口也直达 `/follow-manage?tab=add`。关注管理区域写入地址栏，刷新与返回可恢复对应区域。馆藏有「添加内容」主按钮时，关注入口为次按钮。

统计空状态提供对应入口：内容标签和标签来源前往数据管理补全资料，观看记录前往馆藏，存储来源前往配置添加媒体文件夹。统计分区操作使用次按钮。

关注来源行保持勾选、名称、来源状态、检查时间和操作同一行；卡片宽度不超过 600px 时省略年份，不超过 460px 时省略时分，完整时间保留在可聚焦时间字段的说明中。创作者标题中的全选与收起保持同一行；全选使用 Lucide 1.40.0 的 `check-check` 双勾图标，卡片不超过 460px 时只显示图标，操作名称随全选状态同步。列表骨架复用正式的区域属性、工具栏、批量操作与创作者卡片，每条来源使用相同五列布局。

空状态巡检覆盖馆藏与实体索引、关注更新与管理、统计、口味、播放列表、任务中心、高清目标、重复文件、复核、垃圾文件和回收站。筛选无结果保留现有筛选恢复入口；播放列表、手动别名、口味采集与复核抽帧的动作已在相邻表单或工具栏提供。任务记录、高清目标、无重复文件、无复核候选、垃圾文件与回收站为空属于正常状态，不要求用户启动任务或制造内容。来源搜索、详情推荐和图表中的局部空结果保留说明。

## 创作者别名与扫描操作

创作者别名区域依次提供「手动添加别名」、待合并与已保存列表。查找关注来源先问 F95zone，登录后读命中线程首楼名片上的其他平台手柄，再拿手柄去其余来源查；勾选登记带手柄的结果时，手柄直接存为检索词的别名，不进待合并。关注设置中的「首次采集历史范围」默认最近 30 天，可选 7 天、90 天或不限时间；按发布时间排除较早内容，无日期条目仍保留；范围内不足 30 条时补入范围外最近的条目，首页不够就往前翻页（最多 5 页），边界随之挪到收下的最早一条。每个新来源首次采集时固定边界，重试和自动更新沿用；已有来源不追溯处理，手动历史分页先补回首页被跳过的内容，再向前翻页。列表统计包含全部已导入的未看条目。

2026-09-13 核对 [Table](https://www.boardui.com/components/table) 和 [Data Table](https://www.boardui.com/components/data-table)。实时表格使用 `role="grid"`，单元格为 14px、内边距 10px 12px；页面 CSS 部署标识为 `dpl_QqDLotDUMyvoaXmnBoPEK5tSk8mc`。官方 `https://www.boardui.com/r/table.json` 的 SHA-256 为 `fc12a8f2f4012d9e983e0b9bbb10f9fe3288d74046566d2623d60e7056c50d88`。

创作者别名复用现有 Table 样式，待合并按选择、规范创作者、平台别名、依据和操作分列，已保存别名独立成表。两个名字列各占 18%，依据使用剩余宽度；每行可勾选，表头支持全选与半选，右上角提供带数量的「合并所选」和「全部合并」。支持逐条合并、手动添加和移除。批量合并先列出归属关系，失败时保留未完成项供重试。Peach 这两张表用逐字复制进 `frontend/src/react/boardui/` 的 `table` 条目（建在 React Aria 上）配既有别名 API；待合并与已保存都只有几行，排序与分页用不上，不接 `@tanstack/react-table`。

2026-09-13 实测 [Table 分页](https://www.boardui.com/components/table)：上一页／下一页位于两端，页码居中，按钮高 32px、圆角 8px、14px 字号，前后按钮内边距 6px 8px，分页区域间距 8px。点击下一页后当前页变为 2；官方 `/r/pagination.json` 的 SHA-256 为 `cbbb09ecb86b3f93d4c923f02d272a7086db624ab69eaf5768f036b7458435f8`。Peach 复用既有 `pagination.ts` 与 Board 样式，保留 Lucide 箭头和中文标签，手机页码独占第二排。

关注列表默认视图按完整创作者组分页，表格按排序后的来源分页；每页 10、20、50、100，默认 20，数量偏好保存在本机。排序、版式与数量切换回到第一页，页码写入地址，越界页落到末页。默认视图支持全部展开／收起；选择跨页、跨视图保留，全选本页只影响本页来源。底部批量操作复用人工复核的 `selectiondock`、计数和取消选择模式，提供检查、启用、暂停、删除；批量请求使用全部已选来源。滚动表格建立局部定位边界，避免隐藏表头文本撑出手机页面。加载骨架按已选版式预留卡片或表格结构。

扫描与采集复用口味页的 Split Button 外观和共享菜单定位：默认扫描并补全资料，菜单提供同名主动作、只扫描、只采集。图标使用固定版 Lucide 的 `database`、`hard-drive`、`globe`，分别指资料、本地磁盘和外部来源，无新增依赖。

隔离内存样例已验证全部合并、来源筛选、手动添加与菜单键盘焦点。1280px 桌面和 390×844 手机页面无横向溢出；待合并表格在自身区域横向滚动，已保存表格与添加表单在手机换行。

## 窄屏筛选框滚动

760px 及以下，首页与实体资料页的共享筛选框向下滚时随页面离开顶部，向上滚时恢复吸顶。方向累计 8px 才切换，使用现有 `--board-motion` 过渡顶部约束，文档占位保持不变；减少动态效果时即时切换。页面顶端、键盘焦点、输入与展开菜单保持筛选可见，桌面维持吸顶。原生 sticky 与滚动事件足够覆盖此交互，不新增依赖；浏览器视觉验收未取得。

## 窄屏搜索玻璃动效

2026-09-11 核对 [liquid-gooey spring.ts](https://github.com/Jakubantalik/Libraries/blob/422180dd7a5ac646c85deedc65500c4a74339127/packages/liquid-gooey/src/spring.ts)，MIT，源码 SHA-256 `9dc0d5e9dd269000d95743572320039404982803d1b2da9977e717b5956d5481`。

形变证据来自同一 revision 的 `LiquidItem.tsx`：`morph.shape` 将尺寸变化描述为弹性形变、过冲和软胶回落；`observer.ts`（SHA-256 `5e44c076e50ceb707572cd7b4e083f835a5d454cc21fb405f5c7dd3ff3ef4865`）分别驱动位置、尺寸和圆角。此前记录的裁切与透明度方案未满足用户要求的图标形变，不能作为形变验收证据。 <!-- copy-lint-disable-line -->

Peach 使用现有 313ms 玻璃弹簧（stiffness 1700、damping 46、mass 1），从图标真实矩形变为搜索框，轮廓中途鼓起、回落，反向操作从当前可见矩形接续。关键帧限制在视口内，玻璃全程可见，文字不横向缩放。尺寸动画只作用于绝对定位的搜索层，建议面板在动画结束后显示；起止同高 36px、共用顶栏中心线。右侧按钮依次为搜索、沉浸、多选。

未新增依赖；上游未作为完整搜索组件复刻。上游搜索交互与本轮浏览器实测未取得，本轮按用户要求不调用浏览器工具。

## 数据整理子页

2026-09-09 使用内置浏览器读取组件目录及 Dashboard 侧栏的八个模板。线上 CSS 资源版本为
`dpl_3cjHNDgN6SsY8bTxSfXGACCCc8Zp`，样式资源为 `0pj0_xn8e6w4j.css`、
`0i-yg_o67~u3a.css`、`0z54_bq~~57b~.css`。

| 当前参考 | 实际观察与采用范围 |
| --- | --- |
| `/components` | 检查 Foundations、Base、Blocks、Charts、Templates 完整目录；目录覆盖不等于逐组件全部状态验收 |
| `/components/segmented-control` | 单选滑块、方向键移动、Space 选择；适合短的局部视图选择 |
| `/components/tabs` | 下划线面板切换与 PillTab 局部筛选区分；Peach 复核十类采用纵向分类，保留面板关联和键盘操作 |
| `/components/data-table` | 结果数、筛选、逐行操作、部分选择状态、分页分层；复用 Peach 已有选择与分页逻辑 |
| `/components/stat-cards` | 紧凑统计与底部比较栏两种结构；子页只有当前任务读数，不引入无实际数据的趋势 |
| `/templates/dashboard` | 面包屑、标题动作、统计与结果工具行；radio 轨道 padding 4px、radius 10px |
| `/templates/marketing` | 分类筛选与结果表独立；采用局部筛选结构 |
| `/templates/calendar` | 月份导航与日期网格；五个子页不采用日历 |
| `/templates/finance` | 汇总指标与交易结果表分层；采用结果标题与操作区归属 |
| `/templates/medical-profile` | 主体信息、指标与提醒分区；复核保留主体、证据、动作分区 |
| `/templates/ai-chat` | 项目侧栏与 Code、Changes、Browser 局部切换；不把局部切换当第二层页面导航 |
| `/templates/ai-image-generation` | Gallery、Styles 与图像网格；采用预览优先的卡片结构 |
| `/templates/ai-profile` | 身份概要与指标卡；不引入与文件整理无关的数据面板 |

模板已逐页读取实时 DOM；没有宣称八个模板的所有交互、动画和响应式状态均已验证。
Pro 模板只作为公开外观和信息层级参考。实现使用现有 Preact、共享 HTML 控件及 Board token，无新增依赖。

作用范围是 `/review`、`/quality-goals`、`/duplicates`、`/junk-files`、`/trash`。
数据管理入口保持卡片导航。复核分类在桌面纵向排列，窄屏自动换行；分组、候选、批量动作和分页沿用既有实现。
重复组提供文件预览及尺寸、时长、位置比较；高清版、垃圾文件和回收站共用预览卡片的版式。

预览来源核对：8095 的 `app.js` 和 `board.css` 匹配 `claude-entity-float-and-settings`，
其提交已包含于当前 master；8097 的 `app.js` 匹配本次工作树基线 `f09fc8b6`，
`board.css` 匹配 master。18984 使用当前 `codex-data-pages-board` 的源码和构建，写入请求由只读预览拒绝。
生产入口、真实 ledger 和凭据未修改。

Peach 使用 Board 的视觉与组件语义，保留 Vite、Preact、FastAPI 和现有媒体行为。Board 的公开实现依赖 React Aria，不能把组件名称相同当作 Preact 可直接替换的证明。本次由共享 HTML 控件、原生键盘行为与 Preact 数值控件适配；没有新增 React 运行时。

## 控件对应

| Peach / Geist 语义 | Board 对应 | 实施方式 |
| --- | --- | --- |
| Toggle，布尔开关 | Switch | 42×24 轨道、18px 滑块、内嵌标记；保留 checkbox 与 switch 语义 |
| Switch，互斥分段 | Segmented Control | 单选 radio，轨道内选中背景；方向键沿用原生行为 |
| Button / Icon Button | Button / Icon Button | 主动作蓝色，危险操作沿用危险色；纯图标按钮清除默认内边距 |
| Input / Input 前后缀 | Input adornment | 单位在框内尾部，分隔背景；独立数字输入保持可访问名称 |
| 数值范围说明 | Invalid + HintText | 合法范围验证；错误时显示锚定字段的小提示，修正后消失 |
| Select | Select | 保留已实现的列表键盘、焦点与菜单定位，使用 Board 尺寸与表面 |
| Checkbox / Radio | Checkbox / Radio | 保留原生状态与选择范围；共享颜色与焦点 |
| Tabs / 页面导航 | Tabs | 管理导航下划线，配置与设置按内容分区 |
| Fieldset | 卡片正文与操作区组合 | 标题在框内，操作区用相邻色阶，不增加框中框 |
| Modal | Settings Modal / Dialog | 设置左侧分区、右侧标题及独立滚动；业务确认保留后果和错误恢复 |
| Toast | Notification | 短暂操作回执沿用现有通知通道 |
| Note / Banner | 字段反馈 / Announcement | 数据错误与恢复动作留在发生位置 |
| Tooltip | Tooltip | 保留含义与键盘焦点可见性 |
| Table | Table / Data Table | 保留选择、排序、批处理和实际数据 |
| Tag / Badge | Chip / Badge | 标签与状态语义分开，保留可操作范围 |
| Sidebar / Drawer | Sidebar 的收起与展开 | 一个按钮控制同一导航，移动端使用遮罩 |
| 指标带 | Stat Cards | 图标、主读数、色阶底栏；保留统计视图切换，无历史对比时不显示涨跌 |
| 口味排名 / 维度 | Bar List / Radar Chart | 独立 SVG 与排名条，至少三个有效维度才绘制雷达 |
| 来源数量分布 | Radial Chart | 独立分布环，与来源明细共用当前查询结果 |
| Spinner / Skeleton / Progress | 原有等价反馈 | 不虚构进度，保持业务请求时机 |
| Scroller / Collapse | 溢出滚动 / 展开分组 | 保留键盘、溢出和展开行为 |
| 视频播放器、照片灯箱、沉浸队列 | 无直接替代 | 保留专用交互，仅统一外围卡片与控件 |

## 设计边界

- `web/board.css` 是盖在 `web/css/` 上的视觉层，随页面一起加载，没有开关。两份要一起读：
  尺寸、颜色和布局的底稿在 `web/css/`，board.css 只做覆盖，选择器权重必须压得过底稿。
- 「增加对比度」关闭透明与折射；系统降低透明度偏好也使用实色。折射只作用于导航背景，不扭曲文字。
- 设置标题与控件在桌面同排，手机宽度不足时换行。单位与数值属于同一输入框；可关闭的功能显示开关，关闭时隐藏数值。
- 设置页的保存键统一叫「保存配置」，回执「已保存配置」；保存、检查、添加、刷新这类操作键用 BoardUI `Button` 的 `primary`（缺省值，蓝底白字）。`secondary` 只给面板触发键与「取消」，不可逆操作用 `danger`（`frontend/test/settings-buttons.test.ts`）。
- 数值非法时不保存；关闭搜索记录后不读取或记入搜索记录，关闭相关推荐后不请求该模块。
- Board 免费源码以官网声明的 MIT 条款使用；Pro 图表与模板不取用收费源码。项目自有图表不宣称来自 Pro，也不承诺 Pro 更新权益。
- Remix Icon 固定为 4.9.1，按包内 Remix Icon License v1.0 登记；官网所写的 Apache 2.0 不代替实际包许可证。保留已确认图标，候选由 `attic/evidence/20260908-boardui-preview/boardui-full/icon-review.html` 审查。

## 参考证据

2026-09-08 读取官方公开注册表，原始文件在 `attic/evidence/20260908-boardui-preview/board-reference/`。

| 来源 | SHA-256 |
| --- | --- |
| https://www.boardui.com/r/input.json | ac1e66c9ed15f9db2750dd528bc894c856ac84e79f72ff4acb96f14b1ab9c249 |
| https://www.boardui.com/r/switch.json | 3412c1910b2fa7f5d17404bf50bd2503e9ca097cf9d741366379cf18e09ebeb6 |
| https://www.boardui.com/r/segmented-control.json | 62300be25310fef31962ddc237818739a2efd0d0143dd0832f3d1a2166c28e38 |
| https://www.boardui.com/r/button.json | 89cc2c176d1d94d481bbfc6e34f233ccf109c10d319533cc7c1e98923b6e7d69 |

Input 的上游错误信息位于字段下方，并通过 `errorMessage` 关联；锚定的小提示是用户指定的 Peach 差异。设置布局来自公开 `settings-modal.json`：871×614、274px 导航、32px 内容边距、24px 外圆角。每组设置坐在一张灰卡上（16px 圆角、左内边距 12px），上半列的开关行与「这台电脑」下的配置页同一种卡；卡里再分块（媒体文件夹、CloudDrive 分档）用白底加分隔线色描边，不和外面的卡同色。原始设置参考保存在同目录下 `boardui-full/settings-reference.json`。

## 排版、动画与进度

正文 14/20、次要文字 13/18、说明 12/16，标题按 24/34、20/26、18/26 分层；手机可编辑输入 16px、40px 控件，避免输入缩放。输入焦点环占用的外侧空间计入索引标题行留白。

桌面侧栏宽 60/260px，按钮与导航共用同一容器；宽度与标签透明/模糊使用 300ms `cubic-bezier(.4,0,.2,1)`。设置面板使用 300ms `cubic-bezier(.32,.72,0,1)`，缩放 .85→1、模糊 4→0；手机抽屉沿水平方向滑入。设置标题下方为 40px 渐隐，滚动后以 200ms 显示。保留分组内行分隔，不给每张统计卡套线。播放器拖拽、时间进度、沉浸切片等没有 Board 等价物，维持媒体语义；系统减少动态效果时关闭装饰动画。

Agent Progress 的公开演示使用定时步骤。Peach 的作业由服务端状态推进，采用自有圆形数量进度，不把计时当作完成，也不把逐作品循环的阶段假装成整批已完成步骤。共核对 9 类入口：

| 入口 | 本次处理 |
| --- | --- |
| 扫描与采集 | 当前阶段文字 + 已处理视频数 |
| 链接检测 | 已检查 / 总数 |
| 失效链接清理 | 共享后台作业数量进度 |
| 资源扫描 | 已完成来源 / 总来源 |
| 资源清理 | 共享后台作业数量进度 |
| 关注更新 | 已完成来源 / 总来源 |
| 口味采集 | 共享后台作业数量进度 |
| 添加关注 | 共享后台作业数量进度 |
| 版本更新 | 已有下载、校验与安装阶段；由版本分支负责 |

Charts 已核对 Stat Cards、Bar List、Radar、Radial、Contributions、Heatmap 和 Sankey 的公开行为。馆藏统计使用当前快照；浏览历史按去重后的真实访问时间生成星期／小时热图与每日活跃格，支持 7、30、90、365 天和全部时间。`last_played` 不充当完整播放事件序列。创作者流向使用来源网站与创作者线索的实际关联计数；非互斥口味标签不进入漏斗或流向图。

Slider、Notification、Tooltip、Carousel、Checkbox、Chip、Dropdown、Link Button、Button Group 已取得官方公开注册表，文件位于验收目录的 `board-reference`。范围控件保留原生键盘操作，Checkbox 支持部分选中，通知悬停与聚焦暂停计时，图片查看复用 Swiper 的缩放及键盘导航。排名默认展示五项，通过底部渐隐和按钮展开当前排名数据。

Radial Chart Card、Bar List Card、Heatmap 与 Sankey 的 Pro 源码**未取得**；当前为依据公开文档实现的 Peach 适配，不是安装 Pro 组件。环形图连接媒体库及网盘计数，支持加载、聚焦与选中反馈；Sankey 使用 d3-sankey 的成熟布局计算，保留来源颜色、流线聚焦与数值联动。

补充公开参考文件 SHA-256：

| 注册表 | SHA-256 |
| --- | --- |
| sidebar.json | b3fb5a01f2b334062a0645b71a6c55eec6874da90842270259ff0b1cdc67e42b |
| auth-card.json | cf4159a700769519867f150acbfafd6f3345b9990fd5b6b76c7609407f413cf2 |
| settings-modal.json | eb01742ca56daa473f042244176cd697fc20010ab18f680e3a3a8012d69f6c5b |
| typography.json | 5b7eca25350829755eb15cb474ab009fd1f8b929e62d54182f648b4f2e97bf8e |
| stat-cards.json | 3a140eeb9ab4ebc327e0e585f6cd6e4331be3e68694e72ec6aab80fd5adf705c |

### 关注列表的表格视图（2026-09-08）

取证来源是 https://www.boardui.com/components/data-table 的实时 DOM 与样式表：`_next/static/chunks/0n0ugaibgw__p.css`（SHA-256 `a856db5e9e1a58b2e32b7bfa6d7f1cab69dd09e4bd7ac22fc455dd10b525cf27`）里的 `.bui-table` 规则，以及公开注册表 `r/table.json`（`fc12a8f2f4012d9e983e0b9bbb10f9fe3288d74046566d2623d60e7056c50d88`）和 `r/data-table.json`（`613299eca0f448460a546f7959feab8dab19fbfd6e18670f7216ff304a1e3574`）。

2026-09-16 迁页时重取这三份：`r/table.json` 与 `r/pagination.json` 逐字节未变，`r/data-table.json` 已是 `7bb73a6cd099b9b16390e5fe00f8ba2d55b5ef96c1e8f90a056168cd2e3235e6`（24531 字节），上游自己改过。Peach 复制进树的是 `table` 条目，`data-table` 只读不抄（原因见 `frontend/src/react/boardui/ORIGIN.md`），所以这次漂移不影响已复制文件的哈希。

| 上游实测 | Peach 表格视图 |
| --- | --- |
| `th`／`td` 内边距 `--spacing`×3 / ×2.5，实测 10px 12px；`vertical-align:middle` | 同值 |
| 字阶 `text-body-medium`，实测 14/20、500；表头 `--color-text-tertiary`，正文 `--color-text-primary` | 同值；Board 层用同名 token，旧版层用 `--muted`／`--ink` |
| 表格摆在 `--color-background-primary-default` 面上；表头 `--color-background-secondary-default` 底，上下各一条 `--color-separator-border` | 同值。外框不用作者卡那块 `--ground`：Board 层把它定成 secondary，与表头同色 |
| `tbody tr` 只有一条下边线，悬停不换底（实测 `rgba(0,0,0,0)`） | 同值 |
| 行焦点 `data-focus-visible` 内嵌 2px 焦点环 | 未采用：Peach 的行不可聚焦，焦点落在格子里的控件上 |
| `bui-table-sm` 紧凑档（10px 6px、`text-body-2-medium`）与表尾 Normal／Compact 分段器 | 不采用：视图开关本身就是密度选择 |
| 表头首格全选复选框，带 indeterminate | 不采用：全选连着批量动作留在列表上方的选择栏，避免两个全选框 |
| 分页底部 Previous／Next | 不采用：关注列表一次全量 |
| 可排序表头带 `ChevronSortDown` 字形 | 表头两列接入工具栏已有的两种排序；方向字形沿用工具栏的 `arrow-up`／`arrow-down` |
| 表格 `min-w-[1000px]`，外层 `overflow-x-auto` | `min-width:760px`，外层横向滚动，窄屏不折叠列 |

选中行的样式上游页面没有暴露出来（复选框选中后 `tr` 无 `data-selected`）：Peach 给选中行铺一层蓝色 8% 的底，不描蓝线。表格外面多一层 `.ftableframe` 管边线与圆角，`.ftablewrap` 只管横向滚动：两端按滚动位置渐隐说明「那边还有」，鼠标停在表格上时竖向滚轮转成横向，与复核页标签条同一份接线；边线留在外层，才不会跟内容一起淡掉。表头五列都能点，维度与工具栏下拉是同一份并集：作者、上次检查按作者分组比，来源、站点、状态按单条来源比。

### 关注列表的框、来源行与勾选框（2026-09-08）

取证来源是公开注册表 `r/checkbox.json` 与 `r/checkbox-card.json`（`checkbox-glyph.tsx`、`checkbox-card.tsx`），以及站点样式表 `0n0ugaibgw__p.css`（SHA-256 `a856db5e9e1a58b2e32b7bfa6d7f1cab69dd09e4bd7ac22fc455dd10b525cf27`）里的 `check-draw`、`--shadow-checkbox-selected`、`--shadow-xs` 与 token 定义。

| 上游 | Peach |
| --- | --- |
| CheckboxCard：10px 圆角、1px `border-button-default`、pl 16 / pr 20 / py 12，悬停 `background-primary-hover` 150ms，整卡可点 | 关注列表的每条来源行；勾选框在左（Peach 的行右边是检查、移除两枚动作键）；选中行沿用焦点环色的边，上游只亮勾选框 |
| Checkbox 16px、4px 圆角；未选 `border-checkbox-default`（亮 neutral-300、暗 neutral-700）+ `shadow-xs`；悬停边线到 neutral-400／500，底不变 | `.pcheck` 同值；旧版层的悬停换底被 Board 层压掉 |
| 选中 blue-500→600 渐变 + `inset 0 2px 0 0 #ffffff40, inset 0 0 0 1px accent-500`；悬停渐变提到 400→500 | 同值，渐变取 `--board-blue` |
| 勾 2px 圆头，`pathLength=1`，`check-draw` 200ms cubic-bezier(.65,0,.35,1) 从零画出；减少动态效果时直接显示 | 勾是雪碧图的 `check`，无法写 pathLength，按路径实长 23 写 dasharray；其余同值 |
| 页面上卡片摆在 primary 面上 | 关注列表整段是一只 `--ground` 卡（与「添加关注」同一只），作者卡是 primary 面，来源行才是 CheckboxCard；这样悬停的 primary-hover 才不与底同色 |
| Segmented Control 暗色：轨道 neutral-925、滑块 neutral-800 | Peach 暗色页面本身更深，轨道留 tertiary（#262626），滑块提主文字色 14%；上一节写的「未取得」以此为准 |
| Avatar `avatar-neutral-background`：亮 neutral-300、暗 `background-primary-default` | 首页两排与身份头像继续用主文字色 10% 混底：暗色里上游值与卡片底同色，正是用户回执的问题 |

媒体库图标选择器同批：格子与触发钮同一枚 20px、2 描边的字形，装在同一个 20px 盒子里居中；候选 42 枚一行七枚，题材、身份、场景、媒介各一组；网盘库不另选时显示来源站标（服务端 `media_libraries.libraries` 本就把单一来源的库落到该来源），本地路径没有可识别的来源，写作「默认」并显示磁盘。

### 下拉菜单的开合动效（2026-09-08）

取证来源是公开注册表 `r/dropdown.json`（SHA-256 `e91198d2f1eb131570a0aab53685a4c2c724365d17aecbc5d2113e561152b0b6`）里的 `components/base/dropdown/menu-styles.ts`：`MENU_POPOVER_SURFACE` 写着 `transition duration-150 ease-out`，`data-[entering]` 与 `data-[exiting]` 都是 `opacity-0 scale-95 blur-[2px]`，缩放原点按 `data-[placement]`：bottom 用 `origin-top-left`、top 用 `origin-bottom-left`、left／right 用 `origin-right`／`origin-left`。同一份配方由 Select 与 Dropdown 共用。

| 上游 | Peach |
| --- | --- |
| 150ms ease-out，透明度、scale .95、2px 模糊一起进出 | 同值，`board-menu-in`／`board-menu-out` 两组关键帧 |
| React Aria 在 entering／exiting 期间挂 data 属性 | 进场由 CSS 按 `:not([hidden])` 起；退场加 `leaving`，`dismissMenu` 等 `animationend` 再 hidden |
| 原点按 placement | `wireAnchoredMenu` 写 `data-placement`（bottom／top／right）；侧栏添加页面的 listbox 向上开，原点固定在下沿 |
| 只有 Dropdown 与 Select 两种面板 | 全站的下拉都走同一份：锚定菜单、Select、上下文卡、媒体库菜单、搜索建议、播放器右键菜单、侧栏添加页面、标签选择器 |
| 未取得：`shadow-dropdown` 与 `--color-border-button-default` 的具体值 | 面板的边框、投影沿用 Board 层已有的写法 |

旧版 Geist 层不加动画；系统减少动态效果时由全局规则关掉，`dismissMenu` 读到 `animation-name:none` 就直接藏。

### Toast、Note 与 Notification 的对照（2026-09-08）

取证来源是公开注册表 `r/notification.json`（SHA-256 `92d9e93d7c89f5cdfd79b5f05c14f3663f5aa9fd7bb6bf68729aa0b6e6bb714e`）里的 `components/base/notification/notification.tsx`：卡片 `p-4 pr-11`、`rounded-2xl`、`border-border-button-default`、`bg-background-primary-default`、`shadow-dropdown`；40px 圆形状态图标；标题 `text-body-medium`、说明 `text-body-regular text-text-secondary`；关闭键 `top-3 right-3`；3px 蓝色倒计时条；退场 `opacity 0 / y 8 / scale .96 / blur 3px`，180ms ease-out；进场只在传了 `introDelay` 时才有；视口栈 `min(400px,100vw-24px)`、间距 12px，位置变化走 spring。

| Peach 现有 | 处理 | 依据 |
| --- | --- | --- |
| Toast（操作回执、撤销） | 切成 Notification：卡片、状态圆、倒计时条已由 Board 层承接，本次补上 180ms 退场 | 短暂、可自动消失的回执正是 Notification 的用途 |
| Toast 的进场 | 保留 Peach 的 180ms 淡入 | 上游无 `introDelay` 时不做进场；一条突然出现的卡片在 Peach 里没有别的东西衬托 |
| Toast 的正文与动作 | 保留单段正文和行内文字动作，未拆标题／说明、未换成下方小按钮 | Peach 的回执只有一句话、最多一个「撤销」 |
| 成功态的颜色 | 保留信息蓝 | `notification-success-*` token 的值未取得 |
| Note（字段、任务面板旁的持久反馈：读取失败、任务状态、完成汇总、权限过宽） | 保留，不切 | Notification 是浮在视口角上、会自动消失的栈；这些要留在发生位置，失败还得带重试入口 |
| Banner（页面级问题与恢复动作） | 保留，不切 | 上游注册表里没有 Announcement 的对应源码，未取得 |
| Tooltip | 保留 | 已有 Board Tooltip 的对应 |

### 口味、复核、首页与详情控件的对齐（2026-09-08）

新增取证：公开注册表 `r/tabs.json`（SHA-256 `feab9789b17008436597b51e52b90de5cff6180924f2a7c8bef14a2136d3a240`，含 `tabs.tsx` 与 `pill-tab.tsx`）、`r/avatar.json`（`614f2a384e2d44c0a15df8e3fc42c1648ccd7101f1c8be98911087641ab28aec`）、`r/chip.json`（`d2b0dd38146325acada58fbc241d13fcd633bb5407ce1ef457e752023fe282de`），与已登记的 `segmented-control.json`、`sidebar.json` 一起保存在 `attic/evidence/20260908-boardui-preview/board-reference/`。`avatar-group`、`bar-list-card`、`radar-chart-card` 在注册表返回 404，未取得。

| 位置 | 上游 | Peach |
| --- | --- | --- |
| 口味维度、复核分类的标签条 | Tabs：1px 基线、2px 蓝线随选中项 `transform`／`width` 各 200ms 滑动；选项 px 10 / py 8、Body 1，选中蓝字 Medium；计数徽标 Caption Medium、px 4 / py 1、4px 圆角 | 复核页的 `.reviewtabs` 接进同一份 `wireBoardTabs`；两处按上游字号与间距重排，计数徽标沿用上游两态 |
| 口味页「浏览器记录／Peach 内部」 | Segmented Control：tertiary 轨道 p 4 / r 10、选项 px 10 / py 4 / r 6、滑块 200ms | `.insightswitch` 接进 `wireBoardSegments`，原生 radio 不变 |
| 排序行的版式切换 | 同上，高度 36px | 压到 30px 与同一行的排序键、换批键齐平：主动保留的差异 |
| 分段滑块的暗色 | `segmented-control-selected` 暗色值未取得 | 主文字色 14% 混进轨道色；暗色里轨道与 primary 同值，滑块必须比轨道亮一档 |
| 排名条、雷达图 | 上游 Pro 图表源码未取得 | 进入视口后从零长出 1.2s，与统计圆环同一条曲线；减少动态效果时直接显示 |
| 排名行悬停与展开键 | PillTab 悬停 `background-primary-hover` 200ms | 悬停改为主文字色 6% 薄底 + 200ms：暗色 primary-hover 太跳、亮色看不见；展开键同一层 |
| 三个面板标题（口味总结、浏览器画像、数据源） | Heading 20/26 | 同一档、同一内边距（24 / 24 / 12） |
| 复核「跳过」 | Chip blue：亮 200/800、暗 950@60%/300 | 采用；`error`／`primary` 不变 |
| 交集条上已生效的筛选 | Chip subtle + neutral：`px-1.5 py-1`、Body 1 Medium、tertiary 底配次文字色，不描边 | 主动偏离：用户点名以详情面板那颗标签为基底统一全站标签，所以这一颗也走 `--tag-radius`（这套里是 8px）+ 一圈 `--line` + 28px 移除键，只有填充取 `--picked` 说明它已生效。上游 Chip 只标状态，Peach 的每一颗都要能就地撤掉，同一个词还要在卡片、详情面板、筛选条上认得出是同一样东西 |
| 侧栏名单的展开键 | 无对应（上游侧栏不截断名单） | 取排名卡那枚展开药丸的身量；再按一下收的是整组，不是把名单退回另一个断点 |
| 侧栏收起键 | 36px、`rounded-2lg`、`foreground-icon-secondary`，收起时与品牌相隔 10px | 采用，图标沿用 Peach 的 `panel-left` |
| 详情页门挡 | 无对应 | 铺满播放器格不留黑；播放器格只圆左上角（右贴侧栏、下接「接着看」），窄屏与影院模式圆上面两角 |
| 没有图的身份头像 | Avatar initials 盘 `avatar-neutral-background` 值未取得 | 主文字色 10% 混底、次文字色首字 |
| 首页女优与厂牌两排 | 无 Avatar Group；PillTab gray + Avatar sm（24px） | 见 2026-09-09 那一节：女优竖排人像格、厂牌 40px 灰 Pill |
| 管理页标题 | 无对应 | 只在 812px 窄列页面居中，别处与面包屑同一左边线 |
| 沉浸模式 | 无对应 | 随机流在入口筛掉脱盘来源的片子 |

### 排名列表、复核悬浮框、批量条与侧栏切换器（2026-09-08）

取证来源是 boardui.com 的实时 DOM：`/components/bar-list-card` 与首页侧栏（`aside` 260px / 收起 60px）。`r/bar-list-card.json` 与 `r/sidebar.json` 之外的注册表条目未取得。

| 位置 | 上游 | Peach |
| --- | --- | --- |
| 排名行 | 行 36px、圆角 8、无悬停类；填充条 `absolute inset-y-0 left-0` 圆角 8，`chart-6` 14% 透明，只对宽度和颜色做 500ms 过渡 | 行与填充条圆角 8，填充 14%，去掉行悬停底（两层叠一起就是回执里的「违和」）；行高保留 44 容两行字 |
| 「Show N more」 | 40×20 药丸，居中贴底 4px，`border-button-default` 描边、primary 底、xs 阴影，14px 箭头，悬停 primary-hover 150ms；被折起的行直接不渲染，没有渐隐 | 同尺寸同色；保留 48px 渐隐是主动差异；点按展开键时列表高度走共用 Collapse 的 `.2s ease-in-out`（用户要求，上游没有高度动画；先快后慢的曲线在头一帧就把视口里那截长完，展开看不出动画），过渡只在点按那一下挂上，切维度标签引起的高度变化直接到位，不跟着抖；收起时展开键逐帧钉在指针下（用户选定），卡片多在页底，变短引起的视口回退朝一个方向完成，不先上移再回滚 |
| 数据源卡的删除键 | 站上图标键 `size-9 rounded-2lg text-foreground-icon-secondary`，只过渡颜色 | 36px、圆角 10、透明底，悬停主文字色 6% 薄底加 `--drop` 文字，`transform:none` |
| 指标卡悬停 | 无对应 | `--surface` 与 `--ground` 在亮色里同为白，改主文字色 6% 混底 |
| 管理页标题 | 无对应 | `body body.cleanup-layout` 写错让标题一直留在 812px 窄列；标题、面包屑、导语不看布局类一律对齐 1120（复核、高清版、重复文件这些子页没有布局类），复核页容器同宽 |
| 主按钮 | Button 36px、Body Medium | `.primary` 也进 36px / 圆角 10 / Body Medium 的盒子；复核底部工具条整条压 `--control-h`，主按钮跟着 |
| 灰卡上的控件 | secondary 底上放 primary 白底控件 | 配置页下拉、输入、图标触发键与关注页添加框都白底 |
| 通知状态圆 | Notification 用 lucide 图标 | 警告态换 `circle-alert`（自绘 `i-alert` 在 20px 下只剩一个点）；Note 与上下留 12px |
| 复核页悬浮 | 无对应 | 标签条留在原地，工具条自己悬浮；分组条贴在它下面时两条合成一个平底玻璃框（上 20 0 0 / 下 0 0 20 20，同一块 `--glass-fill`，中间只靠 20px 间隔分开）；两条都向外扩 16px 再垫回，控件与卡片同一左边 |
| 详情页关闭键 | 用户以 YouTube 为参照：播放器上的键亮色下也是黑底 | 60% 黑底白字，悬停 20% 白晕；此前亮色下白底白晕看不出悬停 |
| 数据管理骨架 | 无对应 | 扫描卡的「采集来源」「扫描并补全资料」从骨架起就都在位，内容换入只是变成可点 |
| 批量条 | 无对应 | Board 的 `inline-flex` 曾压过 `[hidden]`，从垃圾页回首页会多出三个键；「移入回收站」用 error 按钮同一条红色渐变，首页与垃圾页文案统一 |
| 媒体库菜单 | 侧向弹出的菜单贴在侧栏右缘外 8px | 收起时触发钮只有 32px，菜单从侧栏右缘起算，不再压到侧栏上 |
| 视频网格 | bar-list-card 之外无对应 | 去掉网格外面那一圈框，卡片直接摆在页面上 |
| 社媒标记 | 无对应 | Instagram 与 X 同一只墨色圆盘，字形取 Phosphor instagram-logo |
| 侧栏切换器 | 32px 圆头像 + 名字 + 双向箭头，`gap-2`，悬停在按钮外 6/5px 处描 2px 圆环；收起键只有 20px 高的图标、无底 | 数据库标识放进 32px `tertiary` 圆盘，悬停与展开态同一圈线；收起键展开时 20×20 靠右，收起时 36×20 在标识上方，相隔 10px，头部 62px 与上游同高 |

### 首页两排、关注批量条、复核分页与数据管理页（2026-09-09）

取证来源：公开注册表 `r/pagination.json`（`pagination.tsx`）、`r/stat-cards.json`（`stat-cards.tsx` 的 PlainStatCard）、`r/avatar.json`（`avatar.tsx`），以及 `/templates/dashboard` 与 `/templates/finance` 的实时 DOM。这三份 JSON 本轮只读了正文，SHA-256 未取得。模板左侧可切换的其它视图（calendar、medical-profile、ai-chat、ai-image-generation、ai-profile）是日历、档案、对话与生图页，与 Peach 现有页面无对应，未采用。

| 位置 | 上游 | Peach |
| --- | --- | --- |
| 首页女优一排 | Avatar 只到 lg 36px，没有竖排人像格 | 竖排格：48px 圆头像在上（取上游 `size-12` 那一级）、名字 Caption 在下，格宽 76、圆角 12、不描边；悬停 primary-hover，选中 tertiary 底 |
| 首页厂牌一排 | PillTab gray | 40px 灰 Pill 放大一档：28px 圆标识在左、名字在右、圆角 12。标签那一排是 30px 描边药丸，厂牌靠身量、圆标识和无边框跟它分开 |
| 关注页批量条 | 无对应 | 批量条只有保存、跳过这类按行动作；勾选靠每行行首的「全选／全不选」 |
| 复核队列分页 | Pagination：nav 两端对齐 `gap-2`；Previous／Next 是 32px 次级小键（圆角 8、内边距 6/8、带箭头）；页码 `size-8 rounded-lg` Body Medium，当前页 border-button 描边 + primary 底 + xs 阴影并标 `aria-current="page"`，其余次文字色、悬停 secondary-hover；两侧折成「…」各留一个邻页；一页时不渲染；没有过渡 | 尺寸与颜色照抄；分页做在前端，一页 20 张（接口 4.6 MB 本机读 0.1 秒，卡的是一次画 1300 张卡）；箭头用雪碧图的 `chevron-left/right`，文案「上一页／下一页」；分组与筛选按整条队列算、卡片只画本页；换分类／分组／筛选回第 1 页 |
| 数据管理页 | dashboard／finance 模板：顶上一排 plain stat card（132px、圆角 16、secondary 底、p 16；32px 图标格 + 20px 字形；标签 Body Medium 次文字色；读数 title-1-medium 24/34；`grid-cols-2 lg:grid-cols-4 gap-4`），下面是图表卡与数据表 | 五张读数卡一行（1120 内），窄了折两列、再折一列；整张卡是入口按钮，悬停抬主文字色 6% 底（上游卡不可点）；读数下一行 Caption 是同一份 payload 的分项；扫描与采集、空文件夹各占一整行，左说明右按钮；链接管理与资源同步不动 |

### 复核卡的候选、未收录 genre 与骨架（2026-09-11）

Radio card 沿用 2026-09-08 取得的 `r/checkbox-card.json`（`checkbox-card.tsx`），本轮未新取证据：
上游只有 CheckboxCard 一件，Radio 版是同一只卡换控件类型。

| 位置 | 上游 | Peach |
| --- | --- | --- |
| 元数据候选 | CheckboxCard：整卡可点、10px 圆角、1px `border-button-default`、悬停 primary-hover，选中沿用焦点环色的边 | 一组候选是 `role="radiogroup"`，每张卡整块可点、圆点在右；卡内上半是这条来源给的值、下半是证据行，证据沉一档底色并加一道 `border-top`——两段一个颜色时看不出哪句是值、哪句是佐证 |
| 候选卡标题 | 无对应 | 卡上先写它在问哪个字段（`梓怡 · 女优`），来源与取证说明留在下面；此前标题只有主语，末尾省略号一截，看不出这条候选要替换什么 |
| 未收录 genre | 无对应 | 候选卡下挂一块 `--surface` 的收录区：原文在左、中文标签输入在中、「收录」与「不是内容」在右。它定的是「这个词以后算什么」，和候选卡的「这条记录写什么」不是一件事，所以不混进候选列 |
| 玻璃框的边 | 无对应 | 工具条与分组条各描一圈 `inset` 的 `--glass-rim`／`--glass-low`，接缝那条边不描（上面不画底边、下面不画顶边），两条合起来仍是一圈。暗色下这块玻璃的底和页面一样黑，没有这一圈就只剩一块黑方块 |
| 复核骨架 | Skeleton 只是占位形状 | 骨架直接用最终容器的类名（`.review-workspace`、`.reviewcontrols`、`.reviewbulktoolbar`、`.reviewlist`），分栏、列宽、卡高全由复核页自己那套规则给；`renderInitialSurfaceLoading()` 先写 `data-surface` 才画，否则深链冷启动会先按默认版式铺一遍再跳。分类名是静态文案直接显示，只有计数和三件工具条控件是占位 |
| 骨架里的悬浮框 | 无对应 | 骨架没有分组条可接，工具条自己封口：四角都圆、四边都描，也不吸顶——`updateReviewSticky` 要等数据到货才有东西可量 |

### 艺人／厂牌资料页与关注页（2026-09-12）

证据在 `attic/evidence/20260912-boardui-profile-tabs/`：`tabs.json`（SHA-256
`feab9789b17008436597b51e52b90de5cff6180924f2a7c8bef14a2136d3a240`，13612 B）、`avatar.json`
（`614f2a38…b28aec`）、`chip.json`（`d2b0dd38…e282de`）、`badge.json`（`264755bb…9aec6`）。
`card`、`page-header`、`profile-card` 三个注册表条目 404，未取得：资料卡的形沿用 2026-09-08
取得的关注管理页那只 `.fsec`，不另补猜测。

| 位置 | 上游 | Peach |
| --- | --- | --- |
| 资料卡 | 未取得（card／profile-card 404）；卡形沿用 `.fsec`：secondary 底、18px 圆角、不描边、卡脚 `--board-card-foot` | `<section class="entityhero">`：`.entityprofile` 里 120px 头像加身份三行——名字 Title 3（24/32、500）、别名·视频数·事务所、外链排成 36px／10px 圆角的 secondary Button；同台艺人收进卡脚 `.entityfoot` 那条带，它是这个人的附注，不是正文；事务所的名册是正文，走 Tabs 里那一档。窄屏卡不变，只有卡里正文那一格改成单列居中、头像 96px |
| 视频／照片／艺人切换 | `tabs.tsx` 是页面级导航的形；这一组按用户口味留在筛选浮层上，不取 Tabs | 浮层最左端的一组媒体圆键（`mediaViewButtonsHtml`，`aria-pressed`），选中那枚由圆玻璃 `viewglide-round` 滑过去标出，跟四枚观看状态各一块玻璃；隔一道竖杠再是观看状态、再一道才是标签。`boardTabsHtml()` 的下划线 Tabs 只给索引页切地址用 |
| 资料页筛选条 | 无对应 | 媒体圆键、四枚观看状态、标签三段由粗到细，`aria-label`「媒体与标签」；照片、名册视图下标签收起、竖杠隐去，圆键留着 |
| 关注页 | 无对应（上游没有更新流页） | 对齐首页而不是另起一套：顶上两排对着首页那两排——作者行 `.followauthors` 对女优，是 48px 头像加名字的 `.av`；题材行 `.followworks` 对厂牌，是 28px 圆标加名字的 `.brandpill`，两排都跟首页共用 board.css 里同一份规则，骨架也各铺各的档（`data-skeleton-tier` 取 `av` 与 `brandpill`）。题材收的是来源记成 copyright 的作品和记成 character 的人物，同一系列的各代归成一枚（`_WORK_SERIES` 前缀加 `_WORK_ALIASES` 别名），人物末尾的消歧括号只影响显示；发行商、平台、节庆和占位词按 `_NON_WORK_TAGS` 加公司后缀形态 `_COMPANY_TAG_RE` 剔掉，被记成 character 的种族与占位词按 `_NON_CHARACTER_TAGS` 剔掉；显示名按词提首字母（`_work_label`），来源自己写了大小写的词原样留；三排（作者、题材、标签）的取样一律走 `followRandomOrder`，按本次访问的种子随机取、进一次换一批，和首页那两排同一个道理——按条数取前 24 的话，八十来个题材里永远只露出同样那二十几个；圆标走 `/work-icon?work=`，服务端拿这个身份在账本里按「带 `3d`、评分高」排出五个候选，顺着取第一张脸够大的封面（取的是站点高清那层，250px 缩略图里一张脸只剩十几像素、检不出来）：「YuNet 检出了脸」这一关太松，实测它在远景图上会给出占长边百分之五、分数 0.69 的框、罩在肩背的纹身上，而圆标正是按这个框放大的，圆里于是是一小块皮肤；判据因此是 `_usable_face` 两条线：占比 `_WORK_ICON_FACE_SHARE`（`FACE_PX_IN_STORE ÷ ICON_SIDE`，脸框宽占画面长边 6.6%——正好是「按默认那一档存下来脸还有 34 个像素」那条线）问圆里落下的是不是脸，像素 `FACE_PX_IN_STORE`（34px）问这张脸放得大放不大——页面按脸放大时不许上采样，源图里那张脸有多少像素就是天花板。缺哪条都漏一类：实测本库 74 枚圆标里有五枚占比全过却仍旧看不清，它们那一条没有封面、候选只能退回站点那层 250px 的缩略图，脸在里面只剩 18～24 个像素，放到头也只占圆的三成。两条都过才停，否则看下一张。本库这几张全都不够时接着去站点问一趟（`work_icon_search_urls`）：库里存的是用户关注的那几位作者发的东西，一个题材常常只有一两条、未必有正脸，而站上同一个标签下有成千上万帖，`sort:score` 要最热的 8 张接在本库那几张后面继续找——先只要带 `3d` 的，那个标签下一张都没有再问一次不限形式的。标签写法取本库 rule34xxx 条目里用得最多的那个（`the_witcher_(series)`、`dbd`、`clair_obscur:_expedition_33`），照归一化后的题材身份拼出来的在站上是零命中。这一趟是惰性的：本库挑得出脸就一个字节都不出网；取不到凭据、站点报错或网络不通一律当作没有候选，圆标退回首字母而不是 500。都走完还是一张都不够格的题材按「没有头」处理：退回第一张取得到的图、不写人脸记录，页面于是按样式表里的默认取景摆整张封面。这类题材多半真的给不出正脸——顶着头发的背影、非人形的主角，或者站上那个标签下本来就只有远景；与其把画面里最大的那块皮肤放大成一枚认不出的圆，不如老实摆一张全身，它至少还认得出是哪部作品。本库 74 个题材按占比那条线分开的两边正是「一眼认得出」和「认不出」。核对图床主机、按 `trim_letterbox` 裁掉源图自己留的黑边（判据是这一行的平均亮度和最亮那个像素都低：只看平均会把夜景整片暗部当黑边裁掉，只看最大值又会被一颗噪点挡住；裁完剩不到四成就当判据认错了东西，不裁），再按 `icon_side` 算出的边长存本机，页面递不进地址，挑不出时退回首字母。落盘这一档按「页面放大到头要多少像素」定，不按圆标那 28px 定——放大的上限之一是源图里那张脸有多少像素，缩到 256px 时脸框只剩 19～30px，正好卡住。每一枚各算各的：脸在画面里占得越小，落盘边长越大（`FACE_PX_IN_STORE`＝28px 的圆 × 双倍屏 × 脸最多占六成），下限是 `ICON_SIDE`（512px）；远景全身图按这条要两千像素，`MAX_ICON_SIDE`（1024px）在那里刹住——再小的脸就认了放不大，一枚圆标不值两百 KB。取景由服务端写在图旁的 `.face.json`，facet 行第五位带回页面、走头像那套 `facePos` 落成 `object-position`，再由 `face-frame.js` 按脸框放大；28px 的圆上比例那一档（32%）只给得出 9px 的脸，改由 `MIN_FACE_PX` 这条像素下限接管，48px 的作者头像上它算出来低于 32%、仍走比例。脸够大不等于摆得正：脸心离画面边缘近时，把它拉到框心的位移会让图露白、于是被夹回边上，所以「摆正」本身也算放大的理由（`centred`），再由 `FACE_CEILING`（脸框占框 60%，整颗头刚好填满）刹住。检不出脸的退到样式表里的 `50% 25%`。筛选条 `.tagbar` 与读数 `.count` 收进同一块 `mountFilterFrame` 浮层。上排最左是视频／图片两枚媒体圆键，跟资料页同一个控件、同一块圆玻璃（`GLIDE_ROWS.media` 多认 `.followmediaview`），隔一道竖杠才是四枚状态（全部、未看、已保存、已忽略，不挂计数）——它们是首页四枚视图的同一个控件，共用那块滑动玻璃（`GLIDE_ROWS.views` 多认 `.followviews`）；来源图标与标签在右半截横滚，来源类型的着色只在选中时上色。下排读数照首页写「N 项更新 · 显示 M」，右端是 `sortControlsHtml` 那一组：换一批（切到 `sort=rand&seed=`，整批按种子打散、种子写进地址），然后是更新时间／热度／时长三档排序；图片墙上多一枚 30px 见方的「仅显示图片」图标开关（字形是 Lucide `captions-off`，不跟媒体那一档的图片字形撞），开着时垫的是筛选条那块滑动玻璃（`GLIDE_ROWS.imagesonly`），跟旁边的版式分段器同一块料、同一副尺寸——浮层上的分段器轨道不留内边距，选项 30px 见方、8px 圆角。换一批等数据时也画首页那段描边忙态（读数行挂 `aria-busy`）。排序归服务端（`/api/follow?sort=&dir=&seed=`）：分页在它那一侧，浏览器只拿到当前这几页，而 `FollowStore.group()` 结尾无条件按 `newest_at` 倒序，所以条目层和发布组层都要按同一把尺再排一次（`_sorted_items` 与 `_sorted_groups`）。生效的筛选摊在浮层正下方，用的就是首页那条交集筛选条（`.combo` 容器加 `.cb` 芯片加「全部清除」）——放上方会把吸顶玻璃和两排头像一起推下去，放下方只推列表，而列表本来就要重画。换排序、点作者头像这类只换内容的操作也只重画列表：`.followlist` 换成 `pageSkeletonHtml` 的卡片骨架，浮层、两排头像和交集条留在原地。页头右端「管理关注」是次级按钮，「检查更新」在它右边当这一屏唯一的主按钮（没有来源时不出，蓝色归空态里的「添加关注」）；底部「加载更多」旁不再重复读数。图片墙的每张 `<img>` 带 `width`/`height`，浏览器在图落地前就按固有比例占位，列不会随加载重排；尺寸是条目上的一个字段（清单内的图各带一对），来源接口给的（fanbox imageMap、rule34.xxx dapi）、回填脚本问文件头得到的、界面加载完回写的（`data-learn-dims` → `POST /api/follow/image-dims`）三条路同权、只补空缺；两层都没有的卡片按 1:1 占位，不硬猜 |
| 两页骨架 | Skeleton 只是占位形状 | 都把 `.board-filter-frame` 外框和上下两排的 `data-filter-row` 写全，否则等的那几秒钟是两块各带圆角的浮层；资料页骨架用 `.entityprofile`／`.entityidentity` 的真实类名，筛选条那排用 `data-skeleton-tier="pill"` 铺药丸 |
| 外链图标 | `avatar.tsx` 只有圆形；站标那一档无对应 | 资料卡外链按钮里的 favicon 与社媒标记 `.entitylinkicon` 收成 `--badge-radius` 的圆角方框，跟 20px 的图标位同形；外链一律 `target="_blank" rel="noreferrer"` |
| 艺人／厂牌／事务所索引（`/performers`、`/studios`、`/agencies`、`/creators`） | 索引网格无对应；卡形取 `stat-card`（secondary 底、16px 圆角、p16 收成 p12）、名字 Body Medium 14/20 500、计数 Caption | `.icell` 是一张卡，悬停抬 6% 主文字色；大图版式头像 10px 圆角、文字左对齐；「载入更多」是 36px／10px 圆角的 secondary Button。厂牌与事务所是两条地址，页头下那排 `boardTabsHtml()` 的下划线 Tabs（`data-index-kind`，带对象图标）切页，不是筛选。`/performers` 另有本地／在线一档（`data-performer-scope`，跟标签页共用 `INDEX_SCOPES` 与 `scopeTabsHtml()`）：在线那档读 `/api/follow/authors`，一个人的几个来源按别名归成一行、计数与关注页的读数同一个口径（按条目数，不是发布组），点开去 `/follow?author=`；地址带 `?scope=online`，深链进来直接落在那一档 |
| 标签页（`/tags`） | 字母表无对应；分组卡取 `stat-card` 形，行取 bar-list 的 36px／8px | 本地／在线是页面级的 Tabs（`data-tag-scope`）；换档只重画 `#indexBody`，页头、搜索框和那块浮层是同步就有的东西，跟着一起铺骨架等于把已经在屏幕上的控件抹掉再画一遍。类型药丸、读数、按首字跳转、标签云／字母表切换收进首页那块玻璃浮层 `tagFilterFrameHtml()`：上排 `.tagcategories` 药丸带类型色点，下排读数＋`.alphajump`＋`iconSwitchHtml`；浮层住在 `#indexFilters` 里，那个父级只有浮层那么高，sticky 会被卡死，`display:contents` 让它退出盒树。字母表 `.alphagroup` 每个首字一张卡，字头旁挂 `.board-tab-count` 徽标，`scroll-margin-top` 给吸顶浮层让位 |

## 首次设置 Auth Card

Button 取证（2026-09-10）：对照官网 `/components/button` 与保存的
`board-reference/button.json`。选择文件夹为 medium 纯图标 secondary，添加媒体库为
带前置图标的 secondary，完成设置为 primary；高度 36px、图标 20px、圆角 10px。
主按钮渐变使用官网实测色值；按下缩放至 0.98，
按下 220ms、释放 420ms，曲线为 `cubic-bezier(.4,0,.2,1)`，减少动态效果时关闭。
按钮保留原动作、键盘焦点、忙态防重复与禁用语义，不写入预览配置。

纠正（2026-09-12）：这一段此处一度记过「上游 primary 没有悬停态」，同日取到规则原文后作废。
当时那三条证据全落在同一个盲点上——悬停那一层挂在伪元素上。① 读 `className` 看不到：悬停
不是 Tailwind 的 `hover:` 类，写在样式表里；② 真鼠标悬停读 computed 也看不到：读的是元素
自己的 `background-image`，变的是 `::before` 的 `opacity`，`getComputedStyle(el)` 不传第二个
参数就取不到那一层；③ 注册表 `/r/button.json` 的 primary 那一行确实只有
`bg-button-primary text-text-white shadow-xs`，因为三档全长在 `.bg-button-primary` 这个类里。
取证结论涉及「某个状态没有样式」时，伪元素两个都要显式读一遍再下判断。

`.bg-button-primary` 的规则原文（2026-09-12 实测）：类自身 `isolation:isolate` 加
`background-image:var(--gradient-button-primary-default)`；`::before` 是 `inset:0`、
`z-index:-1`、`pointer-events:none`、`border-radius:inherit`，铺
`var(--gradient-button-primary-hover)`、`opacity:0`、`transition:opacity var(--button-transition-ms) ease`
（该 token 为 .15s），`:hover:not(:disabled):not([aria-disabled=true])::before` 把它抬到 1；
`:active` 换成 `var(--gradient-button-primary-active)` 并把那层压回 0；`:disabled` 换
`--gradient-button-primary-disabled` 且 `::before{display:none}`。三档渐变都是 180deg 两停点，
按色阶排 default `accent-500→600`、hover `400→500`、active `600→700`，实测像素
400=`#3392ff`、500=`#2b7fff`、600=`#155dfc`、700=`#1447e6`。其余 computed：`height:36px`、
`padding:8px`、`border:0px`、`border-radius:10px`、`box-shadow:rgba(0,0,0,.05) 0 1px 2px`、
`color:#fff`、`font:500 14px/20px Inter`。

Peach 照抄这一副面，包括 `::before` 的交叉淡入和 `border:0`——补一圈透明边会在
`box-sizing:border-box` 下把内容盒压掉 2px，而 `background-origin` 是 padding-box，渐变被压到
34px 再延展回 36px，色标就跟上游错开一像素。三档 token 是 `--board-blue`、`--board-blue-hover`、
`--board-blue-active`，连同规则只在 `web/board.css` 一处，错误页、登录页和首启页由
`routes_pages._board_button_rules()` 取同一份过去；判据写在
`test_the_primary_tier_has_one_face_and_crossfades_into_its_hover`。

Peach 在这一档上的主动差异有两项：`padding` 取 `8px 12px` 而不是上游的四边 `8px`，中文字比
拉丁字宽，四边等距时两侧字贴着边；上游 `active` 那一下的 0.98 缩放（`transform .42s`）没有跟，
按下换渐变已经读得出来。

Checkbox 动效取证（2026-09-10）：项目保存的 `board-reference/checkbox.json` 中
`checkbox-glyph.tsx` 使用 16px SVG、`pathLength=1` 与 `animate-check-draw`。
实时 `/components/checkbox` CSS 确认为 200ms `cubic-bezier(.65,0,.35,1)`，
`stroke-dashoffset` 从 `1px` 到 `0`；减少动态效果时立即显示完整勾线。
150ms 只负责背景、边框和阴影过渡，不能用它代替描线动画。
setup 使用同一勾线形状、蓝色渐变及这两组状态规则。

2026-09-10 使用内置浏览器核对 `/components/auth-card`，复用已登记的
`boardui-auth-card.json`：集中式标题、Logo、表单与底部主按钮，24px 圆角、
24/32px 内边距和轻阴影。Peach 的媒体来源表单采用 560px 上限；保留目录增删、
来源选择、可选密码、高级设置、扫描及历史导入。390px 下单列，无横向溢出。
独立只读预览为 18985；不提交真实配置、不启动扫描，生产未切换。

## 验证记录

侧栏采用 AI chat 公开变体的分组标题、展开叶项与尾部计数；分组箭头位于右侧，标题高 36px，展开复用共享 Collapse。媒体库入口适配公开 `DashboardUserMenu`：265px 面板、16px 圆角、10px 内边距，桌面右侧 8px、手机下方展开，150ms ease-out 淡入、缩放 .95 与 2px 模糊。独立按钮控制侧栏展开；媒体库图标打开选择面板，展开面板时入口显示轮廓。首页使用 20px 槽位的 Peach logo，按透明边距校准可见轮廓及文字起点，收起态按钮为 36px 正方形。媒体库与导航图标统一 20px、1.7px 线宽，无图标底色。设置固定在底部，与明暗开关并排；收起时明暗开关只显示目标主题图标。主题动画参考公开 `https://www.boardui.com/r/theme-toggle.json`：200ms 滑块与 820ms 柔边扩散，缓动 `cubic-bezier(.16,1,.3,1)`，减少动态效果时直接切换。

媒体库使用 `[media.libraries]` 为声明路径命名，同名路径归为一库；`[media.library_icons]` 保存可选图标，自动模式按来源显示本地磁盘或本机提供的网盘图标。库选择限定作品列表与筛选项；来源 ID、挂载映射和 ledger 路径保留其业务含义。统计、口味和维护任务按整个部署汇总。预览只读，不保存真实配置。

颜色按 [Board Color](https://www.boardui.com/components/color) 的文字、背景、边框和交互角色映射；字阶按 [Typography](https://www.boardui.com/components/typography) 使用正文 14/20、紧凑 13/18、说明 12/16、标题 20/26 与页面标题 32/44。本机打包 Inter Variable。统计、口味、关注管理和配置使用对应结构的骨架；其它页面复用实体、海报与网格骨架的 Board 样式。关注的默认视图与表格视图共享作者分组、排序和多选；默认视图作者卡内行高 64px 并支持作者收起，表格视图一行一条来源、表头可排序；批量删除使用数量明确的确认框，选择与启用状态独立；最近观看标题单行中间省略并链接视频详情。

详情使用并列观看进度卡与独立动作按钮；Esc 先退出详情、再收起侧栏。首页与实体页排序保持横向滚动，换批按钮沿用动画 SVG，采用中性 Board 按钮。

- 178 项前端测试通过，包含非法值不保存、关闭恢复、异步读取值恢复、图表数值、库名及图标提交、分组展开记忆、页面骨架、排名展开与流向聚焦、图标草稿取消、分段切换及演示状态不请求任务接口；构建与类型检查通过。
- 18984 服务工作树的完整构建快照，避免编辑期间混用源码和产物。桌面已检查设置、首页、详情、统计、口味、数据管理、关注管理、配置与复核；390×844 已检查统计、口味、首页、设置、详情、标签与事务所索引，没有页面横向溢出。
- 设置关闭图标中心偏差为 0；纯图标控件不覆盖工具栏业务显隐。旧版模式关闭 Board 样式，增加对比度时导航 `backdrop-filter` 为 `none`，退出两种状态均已核对。
- 预览只读，未写真实 ledger、配置或凭据；脱盘状态下真实播放未验证。生产入口与版本号未改。
- 390×844 实测索引页无横向溢出、输入 16px；设置数值控件 40px 高。侧栏收起后容器与内容均为 60px，横向滚动轨道隐藏。手机展开按钮位于抽屉内部，抽屉距顶部 12px。

## 控件与状态预览

2026-09-08 通过严格证书校验取得公开 `checkbox-card.json`、`date-picker.json` 与
`segmented-control.json`，保存于本机 `attic/evidence/20260908-boardui-preview/board-reference/`。
分段切换复用原生 radio，选中底板按实际位置与尺寸作 200ms 位移，设置主题保留系统选项。
Checkbox Card 的整卡选择与独立操作按钮分离；暂停使用黄色 Chip。媒体库图标弹层采用
DatePicker 的内面板、候选草稿及取消／应用结构，候选不包含网盘品牌图标。
统计圆环进入可见区域后从零增长，持续 1.2 秒；减少动态效果时直接显示读数。
圆弧关键帧统一使用长度单位，浏览器逐帧采样确认圆弧与数字连续增长。
空文件夹先只读扫描，发现候选后显示删除入口，删除仍通过共享确认框。

筛选栏通过「换一批」切到随机并更新种子；默认随机仍在浏览设置中选择。亮色玻璃用淡蓝灰与暖色光斑形成色差，光斑半径为画布的 32%／38%。媒体库选择弹层复用玻璃材质与现有菜单开合。窄屏设置导航与正文之间保留 16px 间距；这些样式的浏览器视觉验收未取得。

内部正文导航复用 `LinkButton`，右箭头沿用本地共享图标；无底色、无描边、4px 图文间距、20px 图标、hover 下划线。来源为 https://www.boardui.com/components/link-button 的公开注册表 https://www.boardui.com/r/link-button.json ，2026-09-11 取得，SHA-256 `05eb37b3cf1334c153e0702de05fe4989e4359c9c74d5ba55cc552a58e4629bd`。保留 Peach 的 Preact 与蓝色令牌，不新增依赖。外链保持外链图标和蓝色文字；Note 统一带淡背景、图文垂直居中。封面采集反馈列出本机与候选尺寸或实际失败原因，不以网络推测代替来源结果。

搜索玻璃使用原生 `blur(22px)`，保留底色、光晕与描边。主题扩散快照期间，各玻璃表面以当前主题实底承接光晕，结束或跳过动画后恢复实时背景采样；媒体库顶层弹窗使用同一规则。离开页面后清理已移除面板的 SVG 滤镜和尺寸监听。浏览器视觉验收未取得。

已知总量的任务只显示一套进度与处理数量，未知总量才显示加载圆点。扫描、关注检查、链接检查和资源扫描共用这一规则。
复核卡片在接近视口时初始化滚动条，屏幕外卡片暂缓布局；819 条记录的页面滚动至 2400px 时只初始化 6 张卡片。

关注列表右侧工具栏按检查全部、视图、排序、展开状态排列，展开状态仅在默认视图显示。表格的全选本页 checkbox 位于创作者列左侧，默认视图的入口位于列表上方，跨页选择保留。全选使用叠勾，取消使用空心叠勾；复核分组与本页选择沿用这套状态图标。复核分组按钮在吸顶时靠右，类型与标题保留间距。
采集来源明确未收录资料或封面时保留中性记录，不计失败或自动重试集合；超时、网络和读取错误保留错误反馈。采集明细使用共享 Collapse，资源链接使用正常文字色。
