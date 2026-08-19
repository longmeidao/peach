#!/bin/sh
# 用**现有的**本机 CA 重签服务器证书，把缺的名字补进 SAN。
#
# CA 不动，所以已经在 Mac 钥匙串和 iPhone 上信任过的那张根证书继续有效，不用重新装。
# 换掉的只有服务器证书（叶子证书）。
#
# 为什么要重签：原来的 SAN 是 `DNS:peach.local, IP:192.168.50.162`——那个 IP 是
# Windows 那台的。于是
#   * 本机用 `https://127.0.0.1:8443` 做健康检查会因为主机名不匹配失败；
#   * 手机只能用 `https://peach.local/`，用局域网 IP 直接开一定报错。
# 补上 localhost / 127.0.0.1 / 本机当前局域网地址之后两个问题一起消失。
#
#   sh scripts/setup_local_tls.sh
#   PEACH_EXTRA_IP=192.168.1.20 sh scripts/setup_local_tls.sh   # 再多加一个地址
set -eu

TLS_DIR="${PEACH_TLS_DIR:-$HOME/Desktop/lmd.gg/peach/peach-data/secrets/tls}"
CA_CRT="$TLS_DIR/peach-local-ca.crt"
CA_KEY="$TLS_DIR/peach-local-ca.key"
NAME="${PEACH_MDNS_NAME:-peach}.local"
LAN_IP="${PEACH_LAN_IP:-$(ipconfig getifaddr "$(route -n get default 2>/dev/null | awk '/interface:/{print $2}')" 2>/dev/null || true)}"
DAYS="${PEACH_CERT_DAYS:-825}"

[ -f "$CA_CRT" ] || { echo "找不到 CA 证书：$CA_CRT" >&2; exit 1; }
[ -f "$CA_KEY" ] || { echo "找不到 CA 私钥：$CA_KEY（只有它能重签）" >&2; exit 1; }

SAN="DNS:${NAME},DNS:localhost,IP:127.0.0.1"
[ -n "$LAN_IP" ] && SAN="${SAN},IP:${LAN_IP}"
[ -n "${PEACH_EXTRA_IP:-}" ] && SAN="${SAN},IP:${PEACH_EXTRA_IP}"

WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/san.cnf" <<CNF
[req]
distinguished_name = dn
prompt = no
[dn]
CN = ${NAME}
O = Peach
[ext]
subjectAltName = ${SAN}
keyUsage = critical, digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
basicConstraints = critical, CA:FALSE
CNF

openssl req -new -newkey rsa:2048 -nodes \
    -keyout "$WORK/peach.key" -out "$WORK/peach.csr" -config "$WORK/san.cnf" 2>/dev/null
openssl x509 -req -in "$WORK/peach.csr" \
    -CA "$CA_CRT" -CAkey "$CA_KEY" -CAcreateserial \
    -out "$WORK/peach.crt" -days "$DAYS" -sha256 \
    -extfile "$WORK/san.cnf" -extensions ext 2>/dev/null

# 先验证链再落盘，免得把能用的证书换成一张坏的。
openssl verify -CAfile "$CA_CRT" "$WORK/peach.crt" >/dev/null

STAMP="$(date +%Y%m%d-%H%M%S)"
[ -f "$TLS_DIR/peach.crt" ] && cp "$TLS_DIR/peach.crt" "$TLS_DIR/peach.crt.bak.$STAMP"
[ -f "$TLS_DIR/peach.key" ] && cp "$TLS_DIR/peach.key" "$TLS_DIR/peach.key.bak.$STAMP"
cp "$WORK/peach.crt" "$TLS_DIR/peach.crt"
cp "$WORK/peach.key" "$TLS_DIR/peach.key"
chmod 600 "$TLS_DIR/peach.key"

echo "已用现有 CA 重签服务器证书（CA 未改动，已装的信任继续有效）"
echo "  SAN: ${SAN}"
openssl x509 -in "$TLS_DIR/peach.crt" -noout -serial -dates | sed 's/^/  /'
echo "  重启服务后生效：python scripts/install_macos_agent.py install"
