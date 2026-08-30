# Vercel Geist Command Menu、Search Input、Spinner 与 Loading Dots

取证日期：2026-08-30。

## 锁定来源

- <https://vercel.com/geist/command-menu> HTML SHA-256：`0AC2CA5DBC1FC07E48700206C8E8EC21C447460C089D65CFC3324CAC9D0EC13E`
- <https://vercel.com/geist/search-input> HTML SHA-256：`55F62A034450EB68A4D2A46726A0A9A8CF806570C2E31162C6C869F4B38C21A2`
- <https://vercel.com/geist/spinner> HTML SHA-256：`DD1B8A0742A6504D0E8852FAA61269C8720CB7C360B1B9FED6C9BF4C64772C60`
- <https://vercel.com/geist/loading-dots> HTML SHA-256：`CB5548EF02D135DFA26DF1A9881F3E57E79F3F846C4DE3F3A94FB4AC4CEB8983`
- 官方 CSS `1zsi1fomvr48z.css`：`62B3416EB6D73D86FCF284B5A9FD05A69DCBB091E3D79B6725EC83F0990E6ECE`
- 官方 CSS `328y7_b581oob.css`：`3034E6739AE0E19814DF6E53BA7FEBEFE56CF986ED0F1C3534DF9AEE1F751B87`
- 官方 CSS `3ej-07gndl9ds.css`：`587B35B6741B202EE2A7ACAFB4D2A9C6EA2A2819DA55BCF218634FA91A5617EE`

通过项目既有 OpenSSL curl 路径取得。登录态浏览器已加载 Vercel 后台，但导航到 Command Menu 的自动化调用在 30 秒超时并重置运行时，因此实时动画帧与计算样式记为“未取得”；实现只采用锁定 CSS 中可重放的数值。

## 可迁移事实

- Command Menu 是全屏覆盖层。官方 Dialog 打开时使用 `350ms cubic-bezier(.4,0,.2,1)`，内容从 `translate3d(0,-40px,0); opacity:0` 到原位；关闭反向，背景同步淡入淡出。
- Search Input 前缀是搜索图标。Peach 在请求期间原位替换为 Spinner，输入框几何不变。
- Spinner 用于用户直接触发且等待结果的动作，例如按钮与分页；容器声明 `aria-busy=true`，Spinner 自身为 `role=status`。
- 官方 Spinner 由 10 根径向条组成，相隔 36°，持续 1000ms，延迟从 -900ms 到 0ms，透明度从 1 降至 .15。
- Loading Dots 用于仍在后台推进、总量未知的工作，不代替用户动作按钮的 Spinner。
- `prefers-reduced-motion: reduce` 下不得强行动画；状态文字与 ARIA 仍要保留。

## Peach 采用与差异

- 设置面板复用 Dialog 轨迹；普通来源菜单仍按既有证据无动画，不能把 Command Menu 动画套给所有展开控件。
- 添加关注使用 Search Input 前缀；搜索时只把前缀替换成 Spinner，来源筛选保留“全部来源”可见文字。
- 检查、加载、保存、应用等用户动作使用 Spinner；抓取更早内容和后台资源扫描说明使用 Loading Dots。
- Peach 是原生 ES module，不引入 Geist React 运行时；共享实现位于 `web/js/ui-components.js`。
- “没有更多历史内容”是成功的终止状态，使用中性可关闭 Note，不使用红色 error Note。
