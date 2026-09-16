# feralui.dev/gradients 渐变生成器实测记录

- 取证日期：2026-09-16
- URL：<https://feralui.dev/gradients>
- 取证方式：打开生成器，读预览节点的实际渲染方式、bundle 体积与两种导出（CSS、JSON）的产物。

## 不登记进 `docs/reference-sources.json` 的理由

页面是闭源 React SPA，内容由 `assets/index-BalH5ccj.js`（约 1.06 MB，未见许可）在运行时
生成，取不到可哈希、可重抓的上游字节；渐变本体又是 Canvas 逐帧绘制的像素，没有可比对的
声明式源。按本目录的约定，这类实测留在快照正文说明，不进登记表。

## 实测

实时行为取证——渐变本体由 2D Canvas 逐帧绘制（Flow 预览画布 240×160 拉伸、Glow 型
1024×1280），上叠 PNG 噪点瓦片 `mix-blend-mode: overlay`；bundle `assets/index-BalH5ccj.js`
（约 1.06 MB，闭源，未见许可）；CSS 导出只有一条 `linear-gradient(135deg in oklab, …)`，
自带注释承认 CSS 画不出 mesh 场；JSON 导出的参数模型为 `type` / `stops[]`（hex+oklch+
position）/ `dividers` / `soften` / `noise` / `speed`。

## Peach 借了什么

只借三点，都不涉及它的代码或位图：

1. **参数模型**：一档配色 = 若干色标（hex 加位置）+ 柔化 + 噪点。Peach 的 `homeGlow` 落成
   三枚光斑（颜色、不透明度、圆心、椭圆半轴、收边位置），开关、强度、噪点单列，
   见 `web/app.js` 的 `HOME_GLOW_PRESETS`。
2. **`in oklab` 插值**：`web/css/01-base.css` 的 `.glowlayer::before` 三层渐变都走它，由
   `--glow-lerp` 一个变量给，`@supports` 判不出时退回 sRGB。
3. **噪点叠层**：`.glowlayer::after` 一层 `mix-blend-mode: overlay` 的瓦片，强度 0 即关。瓦片由
   SVG `feTurbulence` 的 data URI 当场生成，不引入它那张 PNG，也不往仓库里落位图。

渲染保持纯 CSS 径向光晕，不引入 Canvas：首页顶栏与筛选条都挂着 `backdrop-filter`，
一块逐帧重绘的画布压在它们下面会让这两处每一帧都重算。

## 与本快照的差异

Peach 最终只保留光斑层：它那种铺满画布的底色场和压在上面的遮罩，Peach 都不画，三枚光斑
各自向 `transparent` 收边，底下就是页面自己的 `--page`。
