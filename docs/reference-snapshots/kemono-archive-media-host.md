# 归档站静态资源主机实测

- 取证日期：2026-08-30
- 取证方式：`curl` 带常规浏览器 UA，无 Referer，记录状态码、`content-type` 与字节数；
  不跟随重定向以外的处理，不带任何凭据
- **不登记进 `docs/reference-sources.json`**：那张表要求每个来源有可哈希的上游快照，
  这里记的是「哪个主机能取到静态资源」，站点改版就会变。复核就按下面的方式重测。

## 起因

关注页上 pawchive 的卡片一律没有封面，详情里的媒体也是空白。前端对封面用
`onerror="this.remove()"`，所以取不到时表现为「没有预览图」，看不出是 404 还是防盗链。

## 实测

同一份路径分别请求主域与 `img.` 子域：

| URL | 状态 | content-type | 字节 |
| --- | --- | --- | --- |
| `kemono.cr/thumbnail/data/7e/6b/<hash>.jpg` | 302 | text/html | 138 |
| `img.kemono.cr/thumbnail/data/7e/6b/<hash>.jpg` | **200** | image/jpeg | 24,050 |
| `pawchive.pw/thumbnail/data/3f/9c/<hash>.gif` | 404 | text/html | 207 |
| `img.pawchive.pw/thumbnail/data/3f/9c/<hash>.gif` | **200** | image/gif | 12,796 |

结论：**两站的静态资源都应走 `img.` 子域。**kemono 主域只是重定向，浏览器跟随之后
仍能显示，所以这个问题在 kemono 上看不出来；pawchive 主域直接 404，卡片因此永远是空的。

`follow_sources.py` 里原来那条注释记的是 2026-08-27 主域回 200 `image/jpeg`——
站点行为在这三天里变了。**这类"当前哪个主机能取到"的结论必须带日期，并且会过期。**

## 未取得

pawchive 的**原始媒体**（`media_url`，非缩略图）正确形式未取得。已测且全部 404：

    pawchive.pw/<path>
    pawchive.pw/data/<path>
    img.pawchive.pw/<path>
    img.pawchive.pw/data/<path>

只有 `img.pawchive.pw/thumbnail/data/<path>` 可用，那是缩略图路径。原始文件可能需要
从帖子页另取链接，或者需要会话。**没有猜测代入**：详情里的媒体在拿到确证之前仍会失败，
不用缩略图冒充原图。

## 复核方式

```bash
curl -s -o /dev/null -w "%{http_code} %{content_type} %{size_download}\n" \
  -A "Mozilla/5.0" "https://img.pawchive.pw/thumbnail/data/<path>"
```

`<path>` 取自 `follow_item.thumb_url` 里 `/thumbnail/data` 之后的部分。
