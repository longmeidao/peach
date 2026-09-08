# BoardUI 适配

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

- `web/board.css` 是可独立关闭的视觉层。设置「使用旧版 UI」后应用并刷新，首屏加载前决定是否启用。
- 「增加对比度」关闭透明与折射；系统降低透明度偏好也使用实色。折射只作用于导航背景，不扭曲文字。
- 设置标题与控件在桌面同排，手机宽度不足时换行。单位与数值属于同一输入框；可关闭的功能显示开关，关闭时隐藏数值。
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

Input 的上游错误信息位于字段下方，并通过 `errorMessage` 关联；锚定的小提示是用户指定的 Peach 差异。设置布局来自公开 `settings-modal.json`：871×614、274px 导航、32px 内容边距、24px 外圆角。原始设置参考保存在同目录下 `boardui-full/settings-reference.json`。

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

Charts 已核对 Stat Cards、Bar List、Radar、Radial，以及 Orders、Revenue、Contributions、Heatmap、Funnel、Sankey 的数据需求。当前统计查询是快照，`last_played` 不是完整播放事件序列，因此不据此伪造时间热图或月度涨跌；非互斥口味标签不进入漏斗或流向图。

补充公开参考文件 SHA-256：

| 注册表 | SHA-256 |
| --- | --- |
| sidebar.json | b3fb5a01f2b334062a0645b71a6c55eec6874da90842270259ff0b1cdc67e42b |
| auth-card.json | cf4159a700769519867f150acbfafd6f3345b9990fd5b6b76c7609407f413cf2 |
| settings-modal.json | eb01742ca56daa473f042244176cd697fc20010ab18f680e3a3a8012d69f6c5b |
| typography.json | 5b7eca25350829755eb15cb474ab009fd1f8b929e62d54182f648b4f2e97bf8e |
| stat-cards.json | 3a140eeb9ab4ebc327e0e585f6cd6e4331be3e68694e72ec6aab80fd5adf705c |

## 验证记录

侧栏采用 AI chat 公开变体的分组标题、展开叶项与尾部计数；分组箭头位于右侧，标题高 36px，展开复用共享 Collapse。媒体库入口适配公开 `DashboardUserMenu`：265px 面板、16px 圆角、10px 内边距，桌面右侧 8px、手机下方展开，150ms ease-out 淡入、缩放 .95 与 2px 模糊。独立按钮控制侧栏展开；媒体库图标打开选择面板，展开面板时入口显示轮廓。首页使用 20px 槽位的 Peach logo，按透明边距校准可见轮廓及文字起点，收起态按钮为 36px 正方形。媒体库与导航图标统一 20px、1.7px 线宽，无图标底色。设置固定在底部，与明暗开关并排；收起时明暗开关只显示目标主题图标。主题动画参考公开 `https://www.boardui.com/r/theme-toggle.json`：200ms 滑块与 820ms 柔边扩散，缓动 `cubic-bezier(.16,1,.3,1)`，减少动态效果时直接切换。

媒体库使用 `[media.libraries]` 为声明路径命名，同名路径归为一库；`[media.library_icons]` 保存可选图标，自动模式按来源显示本地磁盘或本机提供的网盘图标。库选择限定作品列表与筛选项；来源 ID、挂载映射和 ledger 路径保留其业务含义。统计、口味和维护任务按整个部署汇总。预览只读，不保存真实配置。

颜色按 [Board Color](https://www.boardui.com/components/color) 的文字、背景、边框和交互角色映射；字阶按 [Typography](https://www.boardui.com/components/typography) 使用正文 14/20、紧凑 13/18、说明 12/16、标题 20/26 与页面标题 32/44。本机打包 Inter Variable。统计、口味、关注管理和配置使用对应结构的骨架；其它页面复用实体、海报与网格骨架的 Board 样式。关注的宽松与紧凑模式共享作者分组、排序和多选；行高分别为 64px 和 48px，宽松模式支持作者收起；批量删除使用数量明确的确认框，选择与启用状态独立；最近观看标题单行中间省略并链接视频详情。

详情使用并列观看进度卡与独立动作按钮；Esc 先退出详情、再收起侧栏。首页与实体页排序保持横向滚动，换批按钮沿用动画 SVG，采用中性 Board 按钮。

- 167 项前端测试通过，包含非法值不保存、关闭恢复、异步读取值恢复、图表数值、库名及图标提交、分组展开记忆、页面骨架与可访问语义；构建与类型检查通过。
- 18984 直接服务正式工作树。桌面已检查设置、首页、详情、统计、口味、数据管理、关注管理、配置与复核；390×844 已检查设置、详情、标签与事务所索引，没有页面横向溢出。
- 设置关闭图标中心偏差为 0；纯图标控件不覆盖工具栏业务显隐。旧版模式关闭 Board 样式，增加对比度时导航 `backdrop-filter` 为 `none`，退出两种状态均已核对。
- 预览只读，未写真实 ledger、配置或凭据；脱盘状态下真实播放未验证。生产入口与版本号未改。
- 390×844 实测索引页无横向溢出、输入 16px；设置数值控件 40px 高。侧栏收起后容器与内容均为 60px，横向滚动轨道隐藏。手机展开按钮位于抽屉内部，抽屉距顶部 12px。
