#!/bin/sh
# 让 http(s)://peach.local/ 不带端口也能打开。
#
# macOS 和其他 Unix 一样，1024 以下的端口只有 root 能监听。Peach 在 macOS 上跑在
# 非特权的 8900（见 peach.tray.MACOS_PORT），所以 `peach.local:8900` 通、
# `peach.local` 不通。
#
# 与其让整个服务以 root 跑，不如让内核把 80 转到 8900：pf 的 rdr 规则，服务本身
# 还是普通用户进程。这是 macOS 上的标准做法，也是唯一不需要提权跑 Python 的做法。
#
# **`rdr-anchor` 必须落在 translation 段**。pf 要求规则严格按
# options → normalization → queueing → translation → filtering 排列，
# 把它追加到 /etc/pf.conf 末尾会落在 `anchor "com.apple/*"`（filtering）之后，
# 报 `Rules must be in order: ...`。所以插在最后一条 rdr-anchor/nat-anchor 之后。
#
# 改 /etc/pf.conf 之前先在临时文件上 `pfctl -n -f` 验证：这个系统文件写坏了，
# 开机时整个包过滤都加载不起来。install 同时也是修复——它会先剥掉本脚本此前写入的行
# 再重建。
#
#   sudo sh scripts/setup_macos_port80.sh install
#   sudo sh scripts/setup_macos_port80.sh uninstall
#   sh scripts/setup_macos_port80.sh check       # 只验证，不需要 root
set -eu

ANCHOR_NAME="gg.lmd.peach"
ANCHOR_FILE="/etc/pf.anchors/${ANCHOR_NAME}"
DAEMON="/Library/LaunchDaemons/${ANCHOR_NAME}.pf.plist"
TARGET_PORT="${PEACH_PORT:-8900}"
TLS_PORT="${PEACH_TLS_PORT:-8443}"
ACTION="${1:-install}"
WORK="$(mktemp -d)"
trap 'rm -rf "$WORK"' EXIT

# 去掉本脚本写过的行，并把 rdr-anchor 插回 translation 段。
rebuild_conf() {
    awk -v name="$ANCHOR_NAME" -v anchor_file="$ANCHOR_FILE" '
        index($0, name) { next }                       # 幂等：先剥掉旧的
        { line[++n] = $0; if ($0 ~ /^[[:space:]]*(rdr|nat)-anchor/) last = n }
        END {
            for (i = 1; i <= n; i++) {
                print line[i]
                if (i == last) printf "rdr-anchor \"%s\"\n", name
            }
            printf "load anchor \"%s\" from \"%s\"\n", name, anchor_file
        }
    ' "$1"
}

if [ "$ACTION" = "check" ]; then
    rebuild_conf /etc/pf.conf > "$WORK/pf.conf"
    if pfctl -n -f "$WORK/pf.conf" 2>"$WORK/err"; then
        echo "语法检查通过；install 会把它写入 /etc/pf.conf"
    else
        echo "语法检查失败：" >&2; cat "$WORK/err" >&2; exit 1
    fi
    exit 0
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "需要 root：sudo sh $0 $ACTION" >&2
    exit 1
fi

if [ "$ACTION" = "uninstall" ]; then
    launchctl bootout system "$DAEMON" 2>/dev/null || true
    rm -f "$DAEMON" "$ANCHOR_FILE"
    grep -v "$ANCHOR_NAME" /etc/pf.conf > "$WORK/pf.conf"
    cp "$WORK/pf.conf" /etc/pf.conf
    pfctl -f /etc/pf.conf 2>/dev/null || true
    echo "已移除 80/443 的重定向"
    exit 0
fi

cat > "$ANCHOR_FILE" <<RULES
# 由 scripts/setup_macos_port80.sh 生成，勿手改。
#
# translation 规则是**第一条命中就生效**（和 filter 的最后一条命中相反），所以
# 例外必须写在前面。没有这两条 \`no rdr\` 时，直连 127.0.0.1:${TARGET_PORT} 会 TCP
# 连得上、HTTP 却永远收不到响应——lo0 上的 rdr 状态把这条流也一起翻译了。托盘的
# 健康检查正好走这个地址，于是服务明明在跑却一直被判成「未运行」。
no rdr on lo0 proto tcp from any to any port ${TARGET_PORT}
no rdr on lo0 proto tcp from any to any port ${TLS_PORT}
# 本机自己访问走 lo0，其他设备走真实网卡，两条都要。
rdr pass on lo0 inet proto tcp from any to any port 80 -> 127.0.0.1 port ${TARGET_PORT}
rdr pass inet proto tcp from any to any port 80 -> 127.0.0.1 port ${TARGET_PORT}
rdr pass on lo0 inet proto tcp from any to any port 443 -> 127.0.0.1 port ${TLS_PORT}
rdr pass inet proto tcp from any to any port 443 -> 127.0.0.1 port ${TLS_PORT}
RULES

# 先在临时文件上验证，通过了才动系统文件。
rebuild_conf /etc/pf.conf > "$WORK/pf.conf"
if ! pfctl -n -f "$WORK/pf.conf" 2>"$WORK/err"; then
    echo "生成的 pf.conf 语法不合法，未改动系统文件：" >&2
    cat "$WORK/err" >&2
    exit 1
fi
cp /etc/pf.conf "/etc/pf.conf.peach.bak.$(date +%Y%m%d-%H%M%S)"
cp "$WORK/pf.conf" /etc/pf.conf

cat > "$DAEMON" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>${ANCHOR_NAME}.pf</string>
  <key>ProgramArguments</key>
  <array><string>/sbin/pfctl</string><string>-e</string><string>-f</string><string>/etc/pf.conf</string></array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><false/>
</dict></plist>
PLIST

pfctl -e 2>/dev/null || true
pfctl -f /etc/pf.conf
launchctl bootout system "$DAEMON" 2>/dev/null || true
launchctl bootstrap system "$DAEMON"

echo "已把 80 -> ${TARGET_PORT}、443 -> ${TLS_PORT}"
echo "  验证：curl -s --noproxy '*' -o /dev/null -w '%{http_code}\\n' http://peach.local/healthz"
echo "        curl -s --noproxy '*' -o /dev/null -w '%{http_code}\\n' https://peach.local/healthz"
echo "  移除：sudo sh $0 uninstall"
