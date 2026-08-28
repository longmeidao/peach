# FANBOX 多媒体、Gofile API 与 Paheal 订阅证据

- 取证日期：2026-08-28
- 用途：FANBOX 多图切换、Gofile 文件页展开、Paheal 标签订阅与跨站去重。
- 凭据保护：只记录公开响应结构、状态、字节数和 SHA-256；API token 未取得、未记录。

## FANBOX 官方帖子详情

请求：`GET https://api.fanbox.cc/post.info?postId=12228983`，带 FANBOX 要求的公开
`Origin` 与 `Referer`。

- HTTP 200，6,961 字节，SHA-256
  `039DCE0418EBCA7703CC2277C8B9B803717D84C6DAF7989F6D55722DDA577653`。
- 顶层结构为 `body.post`；帖子免费且不受限。
- 正文 `body.blocks` 内含 `https://gofile.io/d/OS2Qz9`。
- `body.imageMap` 有 6 张图片，原图和缩略图均由官方响应直接给出。

Peach 因此在列表请求后有界回查公开详情：按正文块顺序保留全部图片，详情右侧使用
Mix 同款队列切换；正文中的文件站链接继续作为可点击资源页显示。

## Gofile 官方 API

官方文档：`https://gofile.io/api`。内容列表请求为
`GET https://api.gofile.io/contents/{contentId}`，账号 API token 仅放在
`Authorization: Bearer` 请求头。

- 未带 token 请求 `OS2Qz9` 返回 34 字节
  `{"status":"error-token","data":{}}`，SHA-256
  `C745FF20204557E4775521417A9351E949E9BBB0B3078582649BF961FC513C61`。
- 用户所说的 21 个视频在没有 token 时**未取得**，不能把分享页文字当成视频数。

Peach 新增独立的 Gofile API token 输入；配置后递归读取 API 返回的 `children`，只保留
MIME 为图片或视频的文件。文件直链留在服务端 metadata，浏览器只收到媒体序号、名称、
类型与缩略图；播放由 `/follow-stream` 代理，token 仍只进上游请求头。

## Rule34 Paheal

标签页：`https://rule34.paheal.net/post/list/InitialA/1`

- HTTP 200，92,657 字节，SHA-256
  `E2752C3C07258BF7A1C5DAD62369C6BC2306F438E6733F287341DB0CB932DC67`。
- `.shm-thumb[data-post-id]` 直接给帖子 ID、扩展名、标签、缩略图和文件地址。

详情：`https://rule34.paheal.net/post/view/7428820`

- HTTP 200，34,035 字节，SHA-256
  `5E59D3D1509FCE478633D2CEE6DFE22DD60C205A03BAAA7A7FCE297339779091`。
- `video#main_image source` 给 MP4，`poster` 给封面；信息表给精确 UTC 时间、28.4 秒、
  标签、上传者和原始出处 `https://subscribestar.adult/posts/2639932`。

Peach 以标签页为有界列表、逐条详情补全出处。该帖子归一为
`subscribestar:2639932`，与其他来源声明的同一 SubscribeStar 帖精确合并；标签拼出的
展示名不参与标题模糊去重。
