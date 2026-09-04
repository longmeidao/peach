# 安全说明

## 威胁模型

Peach 是单用户、本地优先的自托管应用：一个部署服务一个人，没有账号体系、没有权限分级，
也没有租户隔离。能访问服务的人就能读整个馆藏并调用写接口。设计上要防的只有一件事——
同一局域网里的其他设备被无意放进来。多用户与云托管不在范围内。

## 口令闸门

口令闸门在 `src/peach/routes_auth.py`，三个 `require_*` 依赖是唯一的判定入口。

- 口令由 `peach serve --token <口令>` 给出。**不给 `--token` 时闸门整体放行**，任何请求都不需要
  凭证。绑定到局域网地址就必须同时配口令。
- 比较用 `hmac.compare_digest`，不做长度或前缀短路。
- `POST /login` 提交表单后换到 HttpOnly cookie `tok`（`SameSite=Lax`，有效期一年，HTTPS 下带
  `Secure`）。脚本用 `X-Token` 请求头。`?t=` 查询参数也被接受，但它会把口令留在访问日志、
  代理日志和浏览历史里，只在一次性场合用。
- 未授权的 401 分三种形态：页面路由跳登录页，`app.css`／`app.js` 返回纯文本提示，API 与媒体路由
  返回 JSON。

## 网络暴露

- 默认监听 `127.0.0.1`，端口与地址在 `<数据根>/config.toml` 的 `[server]` 段。只有把 `host`
  改成 `0.0.0.0` 或某个局域网地址，同网段设备才能访问。
- HTTPS 用本机自签 CA，不用公开 CA。`peach init` 在 `<数据根>/secrets/tls/` 生成 CA 与服务器
  证书，`peach serve --ssl-certfile <证书> --ssl-keyfile <私钥>` 启用。叶子证书有效期 397 天
  （Apple 对 TLS 服务器证书的上限是 398 天）；本机地址变化时 `src/peach/certs.py` 用同一个 CA
  重签，CA 指纹保持不变，已信任过它的设备不必重新安装。
- 要访问的设备只安装并信任 `peach-local-ca.crt`，任何私钥都不分发。命令、信任步骤与指纹核对方式
  见 [`docs/OPERATIONS.md`](docs/OPERATIONS.md)。
- **不要把服务直接暴露到公网。** 没有速率限制、没有审计、没有第二道认证，一次端口转发或反向代理
  就等于把整个媒体库和写接口交出去。局域网之外的访问请走 VPN 一类的私有通道。

## 凭据与数据

- 站点凭据、令牌与 TLS 私钥都在 `peach-data/secrets/`，不进 Git、不进日志、不出现在任何 API
  返回里。备份数据根等于备份凭据，按凭据的标准存放那份备份。
- 账本 `peach-data/database/ledger.db` 记录路径、身份与观看行为。它和媒体一样不属于仓库，
  提交 issue、日志或截图前先去掉路径、局域网地址与账号名。

## 报告漏洞

请用本仓库 GitHub **Security** 标签页的 **Private vulnerability reporting** 提交，不要开公开 issue。
报告里写清受影响的版本或提交、复现步骤和实际影响。仓库由一个人维护，响应是尽力而为，
修复顺序按实际影响排。
