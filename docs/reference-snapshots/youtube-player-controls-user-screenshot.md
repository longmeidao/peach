# YouTube 播放器控制栏截图测量

- 取证日期：2026-08-30
- 来源：用户提供的 YouTube 播放器截图，以及本轮实时访问
  <https://www.youtube.com/watch?v=jNQXAC9IVRw>（`Me at the zoo`）取得的 DOM、计算样式和播放器资源
- 实测视口：1280×720 CSS px，DPR 2；播放器版本：`e937390a`
- 播放器 CSS：<https://www.youtube.com/s/player/e937390a/www-player.css>，SHA-256
  `24cb353f7db6c8025eaf8648aa1f941cddfac84342d06ed4fb9def4523328bb3`
- 播放器 JS：<https://www.youtube.com/s/player/e937390a/player_es6.vflset/zh_CN/base.js>，SHA-256
  `81279f22cbecf0e8ef33abad68b31947b7d22855f73c3d556396e7e410c78ef5`
- 原图：2733×195 px
- SHA-256：`781c6e032251f5d0a3f3c1a16095afa7b6385be86983b8443d2ca70933508f1a`
- 对照图：用户同轮提供的 Peach 生产截图，2819×101 px，SHA-256
  `af03bedef18c752c03dec65f7f83f1b6eca7ce87861f2d0b8dbdab82fd3fc632`
- 第二轮对照图：用户指出整块毛玻璃背景不需要，1429×155 px，SHA-256
  `e6587d90e0d163844561e36cc6246288b2c7bfa1ab13df61582fd8f9758707cc`
- 第三轮对照图：用户指定中央播放键和左上角工具键也统一为圆形，637×445 px，SHA-256
  `66096283446a85e8070fa0f6b9f338a7f133d5c9185f30ce00365a0c1865ef5b`
- 第四轮参考图：精确拖动时刻、缩略图和波形层级，625×631 px，SHA-256
  `4890e1c267a7ae3f06fb924bfe40e67ceec83cb524b48694e3a917644b6aa3ef`
- 第四轮 Peach 对照图：2829×131 px，SHA-256
  `65e7a4fe5f6d335642a8a78a154375593a32979c1f67c4c65dddaa043439cd07`
- 第四轮 YouTube 控件分组图：2709×113 px，SHA-256
  `ca84427227cf75ffab5ecad77a8c3dcc69c25e68f2f4dfec7adf47be957f2d42`
- 第五轮进度条参考图：2811×77 px，SHA-256
  `faa0f88a1895bc718758596e9d8d769ada818c994c9713846bb80ac794b6e8ab`
- 第五轮卡片观看进度参考图：1129×889 px，SHA-256
  `41246447eef380c9f6435f7bb699694fea38ae2ce25edc13d86be9710678017f`
- 第六轮 Peach 高度对照图：459×103 px，SHA-256
  `2cd687877698b0be198c031e7786255322dfaa7bc0fc509d91f32bb3c06a1828`
- 第六轮 YouTube 设置面板参考图：749×681 px，SHA-256
  `046d6bb9b8414f1ad2f2347eb2330e44941ff1096f7b34f3293060fa2f19111b`
- 第六轮 YouTube 影院模式参考图：629×275 px，SHA-256
  `a0d51dc86414efffba746faaaa8ab7a12b49bfde5c2b1ba09fa9d53b0a67fec1`
- 第七轮 Peach 控制栏／音量／设置偏差图共 3 张，SHA-256
  `89003281cd0f6736da8217b19c6409955a98284680f675b21d6f281cfa072493`、
  `f0fe864e03ceb005d9d6b30ddd865e72e5ee719122eac6199cbc19f700a42cd3`、
  `b8b4a65ccce1b80067ae2ac81540b357589ea5ef882e42f66be844eaf84d4dfa`
- 第七轮 YouTube 控制栏／音量／设置参考图共 3 张，SHA-256
  `5518710e5755794cb9043d5ce4d7ebbb453f7383e8b5249f666a5beffb64911a`、
  `f49aae4bce641ba3c5b206768860c5f82f788d5319ee60a24ec60583443f9f28`、
  `a594b7296659e9c995a2edf968ac35cd46ebe5229b1b462733beb82a257be44b`
- 第八轮用户标注的音量裁切、底部播放、控件底色、中央按钮和影院两态偏差图共 8 张，SHA-256
  `dc94e534b1092671f6f46d501169f9a75c52e4462c7782dc2ddfaa97c9db0d3b`、
  `fef85b91cebbba9ae0a72d05e56c694e298281c0201e5a27662f82a546fd6b80`、
  `f93473a5e802bd64a6141305c847dbc3e700af2053689437d5737dd2bc618417`、
  `1d332f48a2a1a70ebfae043623f86d5192b297095bbe40e10a1b477d53703ba0`、
  `1adff33f7da0ef88d02923cb302e212a620ef83fc7701d42e83873bc3709d53e`、
  `093e41fbbeef96d7bfcf9bef1b2ef2e1ebea66c35fb2338c5fe6abcedb216049`、
  `9f14dbd6a4b4d62d45766b245e45bf9bcf764b83451b8461557097886f99e891`、
  `27381b857bd80eb76c15314ca47b12144e451c8520ffdeb4cd2911e50c5c71bd`
- 第九轮用户标注的时间背景、影院音量、设置主层／子层和整栏图标偏差图共 5 张，SHA-256
  `3199eda86cf160b92fd0f9a27ce27857ab42db6c91438716f1ee9dc96742e97e`、
  `78bec4f733ab87cbf8eadb1ce10e322a8af30c29b5605b2a109eec32fff0aa27`、
  `24c91a1804bca776e3244ebd0be6d582cd8bcd425d0a6681005efe6dcd06ebd2`、
  `732f1d356299e9c2ec0523d55399cb2154eb50c259b87eac2c11c31b5cf6cf44`、
  `bfaeaef7e620367c4421a00528d83c27fbd052ae7a95bd5ae65cffe1ef421950`
- 第十轮用户标注的音量重叠、设置对齐、实际 YouTube 设置面板和全屏未铺满偏差图共 4 张，SHA-256
  `c72284752f1bb819da90530b180e5119d619fd22e1220eb887b6d645a86860b3`、
  `06c71239b969d3e15cb2fd36ca453dfc52d4f4518869b5459eb4b2018a03fcab`、
  `41c8b2dda5d79044361960f249fa4dd702784da690cc1ca113e299464502c49e`、
  `d2fe79b33c72950951310a7224262c9b0d4a5ede5779cfe890cdc2ffcdba8914`
- 第十一轮用户标注的 loading／中央反馈重合、音量重叠、三枚设置图标、行尾箭头、清晰度子层和
  YouTube 子层缩进参考共 7 张，SHA-256
  `e38d78d48e90f23cc772c5a5bbf3612626f8d5e115f1fcbee493613e2e344d8e`、
  `be33b4623f3f22a19bce255e4ebb8d2674be672605041c19f4259bc7d3a2aead`、
  `00904ac28cff16350135143d3ec4b7c913fbb7ac21efd33a32617bb62af83260`、
  `00ed60c1bfed5fc84c363e6f0e3743280bcdaa88804f7ddad6c263a1b064552d`、
  `55ff69e21df05c36b6c09647170d5039a9e9cc71b0d13c21102d5136aa82e776`、
  `12bd9bbb9775b027c44302adb1872c33f0c8f6e5d3365125df10fdb56b18dc4e`、
  `e9b009dc847f90e917b859d9e7ee458e42cce408680ba971982d1488c9ba0830`。
- 第十二轮用户标注的选中勾、错误三角形、当前时刻浮签和音量悬停／垂直对齐偏差图共 4 张，
  SHA-256 `7be69dd2e1e9dad56f99a4c7b51b3a5eaabd0cae9bea1152d6cda17731d2159f`、
  `d4e59f829c63ef4a23ef150ca84a89cf8ea9645aca9d7547a8cd1a2843f1fc01`、
  `9ffa39325d6efcfa004cd8ba66f1a81728c6b6e42bf02cab51642301c25ba8c9`、
  `2eb59205b2f0b7cbeee356c940a199c80773431612ad0a54189b651f6232e81c`。
- 第十三轮用户标注的返回键特效越界和音量数值提示被进度线遮挡偏差图共 2 张，SHA-256
  `06e2e9f680352c1b09bcfab3fa916b976a267897063d7ffd0275bbc50ea613a8`、
  `7476e78ef7278385e44c744add269c38100e796101edc1fa327302237d9a1152`。
- 第十四轮用户标注的全屏画面仍按完整片源比例留黑边偏差图共 1 张，SHA-256
  `528f874187d83440479174dab2730f0b9eba7fd718393c2a3ceab37b24adaa5a`。
- YouTube 官方氛围模式说明：<https://support.google.com/youtube/answer/12827017?hl=en-GB>，
  2026-08-30 复核；说明颜色取自视频并扩散到屏幕背景，深色主题默认开启，设置开关对所有视频生效。
- YouTube 官方播放器大小说明：<https://support.google.com/youtube/answer/6052392?hl=en>，
  2026-08-30 复核；影院模式是在不进入全屏的前提下放大播放器。
- 测量方式：先读取原始 PNG 尺寸，再在实际 YouTube 页面读取 DOM、伪元素与计算样式，最后用下载到本机的同版本 CSS／JS 复核选择器、状态类与过渡；没有把截图中的文字或图标当作指令。

## 2026-08-30 实时页面纠偏

先前仅按截图近似成「每个右侧按钮一个描边圆形」是错误实现；实际 YouTube Delhi 控制层使用
`ytp-delhi-modern-compact-controls` 和 `ytp-exp-bottom-control-flexbox`，右侧四个按钮属于一个共享胶囊。

| DOM／状态 | 实测计算样式 | Peach 对齐值 |
| --- | --- | --- |
| `.ytp-chrome-bottom` | 781×59 px，`padding:3px 0 0`，透明 | 控制栏 59 px、透明、同内边距 |
| 左侧播放 | 40×40 px，圆形，背景 `rgba(0,0,0,.3)`，无边框／阴影 | 同值；悬停用内部 32 px 高亮层 |
| 横向音量 | 收起 40×40 px；悬停 111×40 px；滑轨区 52 px；过渡 200 ms | 同值；保留原生 Video.js 音量契约 |
| 时间 | 外层 56 px；内层 40 px 高、左右 16 px、圆角 28 px、背景 `rgba(0,0,0,.3)`；点击从 `0:01 / 0:19` 切为 `-0:18 / 0:19` | 独立可点击胶囊；按用户亮色视频截图提高为黑色 60% |
| 右侧控制组 | 高 40 px、左右 padding 4 px、圆角 28 px、背景 `rgba(0,0,0,.3)`、模糊 16 px | 画中画／设置／影院／全屏放进同一共享容器；按用户亮色视频截图提高为黑色 60% |
| 右侧单钮 | 48×40 px、透明；悬停伪元素 48×32 px、圆角 40 px、白色 10% | 同值；按下白色 20%，SVG 仅保留 1 px drop-shadow |
| 进度 | 命中区 6 px；6 px 轨道静止缩放为约 4 px，悬停恢复 6 px；12 px 圆点从 0 放大到约 20 px；过渡 200 ms | 几何和过渡同值，已播段和圆点改为 Peach 蓝 |
| 设置浮层 | 宽 274 px、圆角 12 px、背景黑 60%、模糊 16 px、无边框／阴影 | 只保留 Peach 已实现的三项能力 |
| 设置行 | 约 48 px；图标 24 px；图标列 56 px；正文 14/18.2 px；悬停白色 10% | 同值，不再使用旧 58 px 行高和大字号 |
| 设置开关 | 40×24 px、圆角 12 px；圆点 20 px、边距 2 px、开启位移 16 px | 同值，状态仍由 Peach 全局设置持久化 |
| 设置子层 | 标题栏 57 px；返回钮 32×32 px、白色箭头；标题距返回钮 8 px | 速度与清晰度共用同一标题栏，不再把返回钮画成整行 |
| 控制图标 | 音量与全屏使用 24×24 viewBox 的实心轮廓；按钮仍分别为 40×40 与 48×40 px | 音量、画中画、全屏改用统一 24 px 本地 SVG，静音／全屏退出各有反向状态 |

### 第八轮 DevTools 状态取证

- 实际底部播放键为 40×40 px、圆形、黑色 30% 底；播放与暂停使用不同的居中 SVG，不是
  Video.js 字体图标。Peach 保留尺寸，把用户要求的可读性底色提高为黑色 60%。
- 实际横向音量容器 `overflow:visible`；收起 40×40 px、悬停展开 111×40 px。Peach 改为只隐藏
  滑轨本身，提示层不再被胶囊裁切。
- 实际影院按钮为 48×40 px；普通态图标表示横向展开，影院态图标改为横向收回，提示分别为
  「影院模式」和「默认视图」。Peach 使用两枚本地图标表达同一状态语义。
- 用户截图指定的中央交互是单个深色圆形播放／暂停键；左右 10 秒键删除，键盘跳转能力保留。

### 第九轮 DevTools 状态取证

- 实际 `.ytp-time-wrapper` 为 40 px 高、左右 16 px、28 px 圆角、黑色 30% 胶囊；点击
  `.ytp-time-contents` 会在已播时间与负号开头的剩余时间间切换，总时长保持不变。
- 影院模式下实际 `.ytp-volume-area` 收起仍为 40×40 px、28 px 圆角和黑色 30% 背景；模式切换
  不移除音量胶囊底色。Peach 为亮色视频保留用户指定的黑色 60%，并显式覆盖影院与全屏状态。
- 实际设置主层宽 274 px、黑色 60%、12 px 圆角；每行约 48 px，24 px 图标位于 56 px 图标列
  左侧 8 px，正文与状态都是 14/18.2 px。子层标题栏 57 px，返回钮 32 px，白色图标，标题紧随其后。
- 实际底栏音量图标使用 24×24 实心轮廓，全屏按钮 48×40 px 且展开／退出使用反向图形；Peach
  用同尺寸本地 SVG 取代 Video.js 字体图标，避免与设置、影院图标产生光学大小漂移。

### 第十轮 DevTools／官方 CSS 纠偏

- `.ytp-volume-area` 与 `.ytp-time-wrapper` 都使用 `inset:4px` 的内部伪元素；悬停为白色 10%，
  按下为白色 20%，过渡 200 ms。音量从 40 px 展开时，40 px 静音按钮仍固定在容器内，不能沿用
  Video.js 的偏移量。
- `.ytp-progress-list` 本体高 6 px，静止 `scaleY(.667)`、悬停恢复 1；12 px scrubber 静止缩为 0，
  悬停放大到 1.67。两者使用 200 ms `cubic-bezier(.05,0,0,1)`。
- 设置菜单内边距 8 px、行高 48 px；每一整行（包括末端值和展开箭头）统一覆盖白色 10% 悬停层。
  开关为 40×24 px，圆点 20 px、四周 2 px；关闭态轨道黑色 30%、圆点白色 70%，开启态轨道
  白色 30%、圆点纯白并平移 16 px。
- 现代中央反馈层为 78×78 px、黑色 60%、16 px 模糊；播放／暂停触发 1 秒反馈动画：0% 透明，
  25%–75% 不透明且放大到 1.33，100% 恢复尺寸并淡出。
- 全屏不是继承父容器的 `100%`；播放器要固定到视口四边并使用 `100vw × 100vh`，视频 tech 同样
  覆盖视口后以 `contain` 保留完整画面。
- 用户随后明确要求切到 Chrome DevTools。首次扩展发现返回不可用；用户要求复核后，同一 Chrome
  扩展成功连接并同时加载实际 YouTube 与 Peach 页面，证明“未安装”判断错误。随后 Playwright
  evaluate、`DOM.getDocument` 和全新标签三条读取路径均在 20–60 秒超时并重置控制会话，故本轮新增
  Chrome computed style 仍标为「未取得」。精确值来自已锁定同版本官方 `www-player.css` 和此前实际
  YouTube 页面 DOM／计算样式，不把仅加载成功写成 DevTools 样式验收成功。

### 第十一轮当前源码纠偏

- 2026-08-31 重新访问实际视频 <https://www.youtube.com/watch?v=mPV-oMZwSW4>；页面当前仍引用
  `e937390a` 的 `www-player.css`，SHA-256 仍为
  `24cb353f7db6c8025eaf8648aa1f941cddfac84342d06ed4fb9def4523328bb3`，同时引用
  <https://www.youtube.com/s/player/e937390a/player_ias.vflset/zh_HK/base.js>，SHA-256
  `88d946f3db89b2d71e52554318b6520c2c518e07cc9827c7c942b042ac65cdc1`。
- `base.js` 的 `FsY` 直接给出 loading 的左右半圆 DOM；CSS 锁定 64 px、6 px 圆环，线性旋转
  `1.5682352941176s`、缓动旋转 `5332ms`、左右半圆各 `1333ms`。Peach 复用 Video.js 的
  `vjs-waiting`／`vjs-seeking` 状态，仅把内部结构和动画换成该来源值；中央播放／暂停改为用户手势后的
  1 秒 bezel 反馈，初始不渲染可见按钮，waiting／seeking 时强制隐藏，所以两层不能重叠。
- 同一 `base.js` 的 modern 分支直接给出环境模式、播放速度、画质三枚 24×24 SVG path，以及
  36×36 播放／暂停 bezel path；Peach 本轮原样登记为本地 symbol，不再使用近似 Lucide 画法。
- 官方设置行仍是 48 px；图标格左 8／右 24 px，内容右 8 px，行尾箭头使用 18 px、白色 70% 的
  modern path。radio 子层标签左 padding 35 px，勾选图位于左 10 px；标题栏为 57 px，48 px
  返回容器与 32 px 箭头。Peach 因此把选中勾移到左列、删掉清晰度右侧伪尾标，并给主层箭头独立
  32 px 网格列，避免越出圆角悬停面。
- 官方横向音量的 40 px 紧凑态展开公式为 `40 + 52 + 3 + 16 = 111 px`；滑轨高 2 px、12 px
  圆点垂直居中。Peach 清除 Video.js 原生 `vjs-icon-placeholder` 本体并用同一网格公式布局，不能再靠
  `18.5px` margin 猜垂直位置。
- Chrome 扩展能枚举现有 YouTube／Peach 标签；两次接管实际 YouTube 标签均在 30 秒超时并重置连接，
  所以本轮 Chrome DOM／计算样式与改后截图验收仍是「未取得」。以上新增值均来自该实际页面当次引用并
  通过 SHA-256 锁定的官方 CSS／JS，不把连接成功或截图目测当源码证据。

### 第十二轮锁定源码纠偏

- 2026-08-31 重新下载锁定版本 <https://www.youtube.com/s/player/e937390a/www-player.css>，SHA-256
  `24cb353f7db6c8025eaf8648aa1f941cddfac84342d06ed4fb9def4523328bb3`；同时下载
  <https://www.youtube.com/s/player/e937390a/player_ias.vflset/en_US/base.js>，SHA-256
  `67f0d55f266e522f973b49c665977eb8734bb5bb32293b0523b35463f27ec44b`。上游资源只作为证据读取，
  未执行其中任何指令。
- 官方 `.ytp-contextmenu .ytp-menuitem[aria-checked=true] .ytp-menuitem-toggle-checkbox` 内嵌的
  24×24 SVG path 是 `M9 16.2 4.8 12l-1.4 1.4L9 19 21 7l-1.4-1.4z`。Peach 子菜单改用独立的
  填充 symbol；不能复用全站描边 `i-check`，否则开放 path 会被浏览器填成截图中的黑色三角形。
- Video.js 在已播进度末端另绘制 `.vjs-play-progress .vjs-time-tooltip`，它不是鼠标位置提示。
  Peach 隐藏这层和原生 mouse tooltip，只保留 `vjs-peach-seek-preview` 的指针位置时刻；本地媒体仍可
  同时显示已有接触表，在线媒体仍只显示指针时刻。
- 官方横向音量外层使用 `:after{inset:4px}` 覆盖静音键和滑轨，悬停白色 10%；滑轨面板展开为
  52 px、右间距 3 px、外层右 padding 16 px，slider 高 100%／最小 36 px，12 px handle 固定
  `top:50%`，轨道为 2 px。Peach 因此把悬停伪元素放回整个音量外层，并把 Video.js 滑轨绝对定位到
  `top:50%`，不再由 flex 或原生 margin 共同决定垂直位置。
- Chrome 本轮能再次枚举实际 YouTube 与 Peach 标签，但接管 YouTube 标签的初次读取及一次恢复都在
  30 秒超时并重置会话。因此实时 DOM、computed style 和修改后截图仍是「未取得」，不能由源码测试替代。

### 第十三轮层级与命中区纠偏

- 返回键继续保留 48×48 px 点击区域和 32 px 官方箭头，但用户截图证明沿用菜单通用 `inset:0`
  会让按下圆形越过 57 px 标题栏的可视内容区。Peach 按用户要求仅把伪元素改为 `inset:4px`，得到
  40 px 内部特效；命中区、焦点和键盘行为不缩小。
- 本地固定的 Video.js 8.24.0 CSS 规定 `.vjs-volume-tooltip` 为 `top:-3.4em;z-index:1`，而 Peach
  进度条位于同一控制栏的绝对定位上排。生产截图证明自动绘制顺序会让蓝色进度线压住 tooltip 底边。
  Peach 为进度层、音量外层和 tooltip 分别锁定 `z-index:2/3/4`，并让 2 px volume bar
  `overflow:visible`；只改变绘制和裁切，不改变百分比、拖动或音量状态。
- 本轮没有再次取得可控浏览器 DOM／修改后截图；视觉验收仍待现有生产标签刷新后由用户复核，页面源测试
  和生产静态资源哈希不能替代该结论。

### 第十四轮全屏画面填充纠偏

- 当时把问题归因成全屏继续使用 `object-fit:contain`；CSS 已部署且静态资源哈希一致，但修改后画面
  没有取得，用户随后实测确认没有生效。这条根因判断因此撤回，不能再把 CSS 命中当作事实。
- 普通详情页继续使用 `contain`，确保浏览时不裁内容；只有 Video.js 的全屏状态改用 `cover`，让画面覆盖
  `100vw × 100vh`。这是用户明确要求的 Peach 差异：非等比例片源会裁掉少量上下或左右边缘，以换取
  全屏无外部黑边，不把它写成 YouTube 默认行为。
- 修改后浏览器画面仍需在真实非 16:9 片源上复核；页面源测试不能替代视觉验收。

### 第十五轮全屏运行态兜底

- 用户当前复测的本地片源 `1275` 经只读 `ffprobe` 确认为 1920×1080、SAR 1:1；连续 8 秒
  `cropdetect` 都返回完整 1920×1080，排除了画面黑边已经编码进这个片源。
- Chrome 能打开并截图真实 `/item/1275`，但自动化点击、DOM 和 CDP 读取连续超时；直接调用按钮的
  Playwright 点击没有 Fullscreen API 所需的真实用户激活，因此不能把页面滚动后的截图冒充全屏验收。
- 全屏填充改为双重状态源：继续接受 Video.js 的 `.vjs-fullscreen`／原生 `:fullscreen`，同时监听播放器
  `fullscreenchange`、`enterFullWindow`、`exitFullWindow`，把 `isFullscreen()` 同步到
  `data-peach-fullscreen`；CSS 还覆盖 `body.vjs-full-window` 回退。这样不再把类名同步时序当成唯一入口。

## 可复用证据

| 项 | 截图证据 | Peach 实现 |
| --- | --- | --- |
| 控制层 | 控件悬浮在画面上；用户明确不要整块背景 | 控制栏透明，不再绘制圆角渐变或毛玻璃面板 |
| 进度 | 独占上排，横跨面板可用宽度 | `vjs-progress-control` 脱离底排 flex，绝对定位到上排 |
| 左下 | 播放、音量、当前时间／总时长共用一条基线 | 播放为 40 px 圆钮；音量胶囊从 40 px 展开；时间胶囊点击切换已播／剩余；前后 10 秒移出控制栏，键盘快进仍保留 |
| 右下 | 实时 DOM 证实四个操作共用一个 40 px 高胶囊，单钮 48×40 px | 使用 Video.js spacer，把四个真实操作推到右侧共享胶囊；按钮只在悬停／按下时显示内部高亮 |
| 进度状态 | 细轨道、品牌色已播段和圆点；卡片缩略图底边显示已观看段 | Peach 把红色替换为 `--tungsten` 蓝，卡片按 `play_seconds / duration` 绘制同色进度 |
| 拖动提示 | 指针时刻上方显示时间；精确拖动时可带缩略图 | 本地媒体复用九宫格接触表近似对应时刻，在线媒体只显示时间，不伪造逐帧预览 |
| 清晰度 | 齿轮图标带 `HD` 状态标记，实际选项在菜单内 | 齿轮显示 `HD`／`4K`，菜单继续只列媒体真实分辨率 |
| 中央播放 | 首次 loading 不与播放键重合；点击后才出现播放／暂停反馈 | 初始只由 Video.js waiting 状态显示 64 px 官方结构 spinner；用户手势触发状态变化后才显示 78 px bezel |
| 中央反馈 | 用户补充中央不只播放，还要暂停；第八轮明确删除左右快退／快进 | 按状态切换官方 36×36 SVG path 并播放 1 秒反馈动画；键盘跳转保留 |
| 左上工具 | 用户要求与播放器按钮统一 | 播放统计键使用相同的 40 px 无描边圆钮、底色和悬停反馈 |
| 左上状态 | Peach 对照图中统计圆钮约 80px 高，加载速度约 75px 高 | CSS 固定两者为相同 40px 逻辑高度、相同 `top:11px` 和 `box-sizing:border-box` |
| 设置面板 | 圆角半透明浮层，主层展示氛围模式、播放速度、清晰度；子层选择实际值 | Peach 复用现有清晰度等级和 Video.js `playbackRate`，加入同层氛围开关与返回式子菜单；不画没有实现的睡眠定时 |
| 影院模式 | 独立图标按钮，展开／收回使用不同图标，悬停提示包含 `T` 快捷键 | 两态图标和「影院模式／默认视图」文案随状态同步；按钮、`T` 键和持久设置共用同一状态 |
| 氛围模式 | 官方说明为视频颜色扩散到背景，深色主题默认开，可在设置中为所有视频关闭 | Peach 原有 32×18 当前帧取色、模糊画布方向一致；补全全局持久开关，并让本地和在线视频共用 |
| 窄屏 | 截图未提供 | Peach 保留两排结构，隐藏 10 秒按钮以避免横向溢出 |

## Peach 主动保留的差异

- 不复制 YouTube 品牌、字幕、睡眠定时和自动播放开关；没有真实能力就不画假按钮。
- 保留 Video.js、键盘前后跳转、画中画、影院模式、全屏和真实清晰度菜单；控制栏与中央覆盖层都不重复画前后 10 秒按钮。
- 单一路源只显示实测分辨率或原画；`HD`／`4K` 只是当前媒体等级标记，不伪造可切换线路。
