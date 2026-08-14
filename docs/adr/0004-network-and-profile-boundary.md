# ADR-0004：本地默认、正式联网能力与远程访问边界

- 状态：Accepted
- 日期：2026-08-14

## 决策

- Peach 默认仍是单用户、本地自托管、安装即用；不建设完整多账号系统。
- online 资产、追更和外部数据源是正式能力，不再受“绝不出网”旧约束；每个 connector 必须显式授权、控频、标注来源与保留策略。
- schema 预留 `app_user`/`profile`，当前只创建本地默认身份，不开放注册、密码找回、公共会话或复杂 RBAC。
- 远程访问以后可选择 VPN/Tunnel，或 DDNS + 反向代理 + HTTPS；应用本身不直接裸露公网端口。
- 局域网服务由 FastAPI 生命周期发布 DNS-SD；可用 `--no-mdns` 关闭，不再依赖旧 HTTP server。Windows 使用系统 `DnsServiceRegister`，以 `Peach` 为服务实例、实际计算机名（当前 `LMD-DST.local`）为 SRV 主机，并绑定首选 LAN 接口；该 API 不创建任意 `peach.local` A 记录。若必须使用品牌化主机别名，应由路由器本地 DNS/反代 DNS 或经验证的专用 responder 提供。其他平台保留 zeroconf，可直接发布自定义 `.local` 主机名。
- Uvicorn 支持显式证书/私钥的本机 TLS。`.local` 不能申请公开受信的 Let's Encrypt 证书；局域网需要 TLS 时使用受各客户端信任的本地 CA（如 mkcert），证书材料只放 `R:\peach-data\secrets`。
- 公网启用前必须完成强口令/身份、TLS、反代可信头、CSRF/速率限制、secret storage、审计与备份恢复验收。

## 后果

“本地默认”是部署基线，不再等同于“功能禁止联网”。mDNS 与可选 TLS 不开放公网；本轮不改防火墙、不配置 DDNS，也不自动生成或信任本地 CA。
