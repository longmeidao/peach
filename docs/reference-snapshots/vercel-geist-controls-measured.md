# Geist 控件实测记录

- 取证日期：2026-08-26
- URL：<https://vercel.com/geist/input>
- 取证方式：浏览器加载页面后读 `getComputedStyle`，不是读源码或截图量取
- **不在 `docs/reference-sources.json` 里登记**：那张表的契约是「每个来源都有可哈希的
  上游快照」，而这里记的是渲染结果，随上游发布变化且没有可锁定的文件哈希。把它塞进去
  会让 `sha256` 这个字段在别处的含义失真。要复核就按上面的方式重测一次。

## 实测值

| 项 | 值 |
| --- | --- |
| 输入框高 | 32 px |
| 按钮高 | 32 px |
| 字号（两者） | 14 px |
| 按钮圆角 | 4 px |
| 按钮边框 | `1px solid rgb(46, 46, 46)` |
| 按钮背景 | 透明（`rgba(0,0,0,0)`） |
| `--geist-radius` | 6 px |
| `--ds-gray-alpha-400` | `#ffffff24` |

## Peach 复用了什么

关注管理页（`web/app.css` 的「关注管理页」段）据此：控件统一 32 px 高、14 px 字；
圆角取根变量的 **6 px** 而不是按钮的 4 px；默认按钮描边透明，只有主操作填色。

配合 `design.md` 的「Reject generated-design reflexes」清单，被用作判据的四条是：
卡片套卡片或用边框补救层级、成排通栏条而彼此不共享量纲、细小灰字加随意字号、
把普通元信息做成胶囊徽章。面板因此去掉嵌套卡片盒子，分组改用标题加发丝分隔线，
字号收敛为 14 / 13 / 12 三档——`tests/test_follow_web.py` 直接断言这三档和「行不套框」，
多一档字号或给行加圆角都会红。

## 后来推广到全站（2026-08-26）

面板当初收敛出的那三档本来就该是全站的下三档，各写各的迟早会漂开。`web/app.css` 原先
散着 **21 种字号（9…48px）**，相邻两档常常只差半个像素——既排不出层级，也没法复核
「这里为什么是 12.5」。现在只有一套刻度：

| token | 值 | 用途 |
| --- | --- | --- |
| `--fs-xs` | 12px | 元信息、计数、标记。**这是下限** |
| `--fs-sm` | 13px | 次要文字 |
| `--fs-md` | 14px | 正文 |
| `--fs-lg` | 16px | 小标题、搜索框 |
| `--fs-xl` | 20px | 段标题、品牌 |
| `--fs-2xl` | 24px | 页标题 |
| `--fs-3xl` | 32px | 统计数字、实体名 |
| `--fs-4xl` | 48px | 占位字形 |

下限定在 12px 是因为 `design.md` 把「细小灰字加随意字号」列为要拒绝的生成式设计反射。
原来的 9px / 10px 灰字（侧栏分组标题、来源筛选按钮、计数徽章、沉浸模式的按钮说明）
全部提到 12px。提上来之后有两处露馅：`.toklabel` 的 `line-height:1` 会切掉中文字形
下缘 2px（9px 时切得少所以没人注意），`.tokcount` 的 16px 圆点装不下 12px 数字——
分别改成 1.25 行高和 18px。

**唯一保留字面像素的是移动端输入框那条 `16px!important`**：那是 iOS 的自动放大阈值，
不是刻度里的一档。让它跟着 `--fs-lg` 走的话，将来调整 lg 会悄悄破坏那个保护，
而症状（在 iPhone 上聚焦输入框页面猛地放大）跟字号改动看不出任何关系。

## 圆角也有词汇

同一份 `design.md` 点名的另一条反射是「把普通元信息做成胶囊徽章」。原先「整圆」有
`999px` / `99px` / `9999px` 三种写法并存，都是同一个意思却看不出是不是同一个决定。

- `--pill-radius:999px`：真正的胶囊——标签、筛选令牌、滚动条与进度条这类连续的条。
  `--tag-radius` 现在指向它。
- `--control-radius:6px`：按钮与分段器，取本页实测的 Geist 根变量。
  `.dupactions button`、`.indexmore`、`.photoback`、`.reviewtabs button`、`.javbar button` 归到这里——
  `.dupactions` 的注释本来就写着「必须看着像按钮」，整圆正好在跟它对着干。
- `--badge-radius:4px`：状态与元信息标记（`.fbadge`、`.fvkind`、`.dupmarks i`、`.dupflag`、
  `.deleteMark`）。它们做成整圆会跟真标签抢同一种视觉身份，用户以为可以点。

`tests/test_web_ui.py` 断言全站不再有字面整圆值，也断言上面几个选择器分别落在哪个
token 上；`app.css` 里除 iOS 那条之外出现任何字面字号都会红。

## Peach 主动保留的差异

继续使用自己的 `--tungsten` 主色和既有暗色表面变量，不引入 Geist 的调色板或字体。
这是有意的差异，不是没做完。

## 关注来源的头像与主题色取证（2026-08-27）

用户要「同一作者跨来源合并并显示头像」和「按站点主题色描边」，两件都要先取证。

### 头像：kemono 系拿得到，rule34 系未取得

`curl`（不带凭据，`--noproxy '*'`）：

| 端点 | 结果 |
| --- | --- |
| `https://kemono.cr/icons/fanbox/30917150` | 302 → `img.kemono.cr/icons/...`，200 `image/webp` 160×160 |
| `https://pawchive.pw/icons/fanbox/30917150` | 200，14,534 字节 |
| `https://coomer.st/icons/fanbox/30917150` | 404 |

浏览器里另测一次同一 URL（`new Image()` + `referrerPolicy='no-referrer'`）：`load 160x160`。
所以页面直接引用这个地址是可行的，不需要服务端代理。

coomer 那个 404 **只说明这个创作者不在 coomer 上**，不能据此断定 coomer 没有这个端点——
所以代码照样按同一规则给它 URL，取不到时由 `<img onerror>` 收场。

rule34video / rule34.xxx **未取得**：本机账本里没有这两个站的来源行，拿不到真实的作者页
样本可测（试过的一个 `/members/<id>/` 回 404，那只说明 id 是编的）。不猜路径。
取不到头像时界面显示一个明确的空位，**不用首字母冒充**——首字母会让「未取得」看着像取到了。

### 主题色：未取得，不要按印象填

想用 `<meta name="theme-color">` 当品牌色，实测这条路走不通：

| 站点 | `theme-color` |
| --- | --- |
| rule34video.com | `#ffffff` |
| f95zone.to | `#181a1d` |
| kemono.cr / coomer.st / pawchive.pw | 无（页面是 JS 渲染的，首屏 HTML 不到 2 KB） |
| rule34.xxx | 取不到（对 `curl` 回 403） |

`theme-color` 是浏览器 UI 底色，不是品牌色——rule34video 的白和 f95zone 的深灰都只是
各自页面底色。favicon 兜底也不成立：kemono 系 `/favicon.ico` 404，而 rule34video 和
f95zone 回的字节数完全相同（15,086），一看就不是各自的图标。

**结论是未取得**，边框颜色这一条没有可复现的依据可用，没有实现。要做得先定一个能复核的
口径（例如从各站主 CSS 里取按钮/链接的强调色，并记下文件哈希）。
