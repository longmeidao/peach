# Swiper 14.1.0

- 来源：https://cdn.jsdelivr.net/npm/swiper@14.1.0/
- npm 包：`swiper@14.1.0`
- 许可证：MIT；原文见 `LICENSE`
- npm tarball SHA-1：`6ae183493719af555a0262b544d602340f0137c3`
- `swiper-bundle.min.js` SHA-256：`A853447E347A0A4A690A911F74135B1A1159A7E328456B24BB2480FA89032B53`
- `swiper-bundle.min.css` SHA-256：`9EE11E4189437A7F9F93445823ACE3227CAFAD913A18A872A4EB93AE2FED21B5`

Peach 自托管固定版本，不依赖 CDN。只有照片灯箱用它：大图轮播加底部缩略图条（`Thumbs`）、
键盘左右键（`Keyboard`）和双指/双击放大（`Zoom`）都在这个 bundle 里，不再自己写一套。
瀑布流本身是 CSS `column-count`，不经过 Swiper。脚本按需 `import()`，不进首屏。
