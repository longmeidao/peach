#!/bin/sh
# 让 http://peach.local/ 不带端口也能打开。
#
# macOS 和其他 Unix 一样，1024 以下的端口只有 root 能监听。Peach 在 macOS 上跑在
# 非特权的 8900（见 peach.tray.MACOS_PORT），所以 `peach.local:8900` 通、
# `peach.local` 不通。
#
# 与其让整个服务以 root 跑，不如让内核把 80 转到 8900：pf 的 rdr 规则，服务本身
# 还是普通用户进程。这是 macOS 上的标准做法，也是唯一不需要提权跑 Python 的做法。
#
# 需要 sudo，且只需执行一次；重启后由 LaunchDaemon 重新加载。
#
#   sudo sh scripts/setup_macos_port80.sh install
#   sudo sh scripts/setup_macos_port80.sh uninstall
set -eu

ANCHOR_NAME="gg.lmd.peach"
ANCHOR_FILE="/etc/pf.anchors/${ANCHOR_NAME}"
DAEMON="/Library/LaunchDaemons/${ANCHOR_NAME}.pf.plist"
TARGET_PORT="${PEACH_PORT:-8900}"
ACTION="${1:-install}"

if [ "$(id -u)" -ne 0 ]; then
    echo "需要 root：sudo sh $0 $ACTION" >&2
    exit 1
fi

if [ "$ACTION" = "uninstall" ]; then
    launchctl bootout system "$DAEMON" 2>/dev/null || true
    rm -f "$DAEMON" "$ANCHOR_FILE"
    # /etc/pf.conf 里的 anchor 行留着无害（锚点为空即无规则），但也一并清掉。
    if [ -f /etc/pf.conf ]; then
        grep -v "$ANCHOR_NAME" /etc/pf.conf > /etc/pf.conf.peach.tmp
        mv /etc/pf.conf.peach.tmp /etc/pf.conf
    fi
    pfctl -f /etc/pf.conf 2>/dev/null || true
    echo "已移除 80 -> ${TARGET_PORT} 的重定向"
    exit 0
fi

cat > "$ANCHOR_FILE" <<RULES
# 由 scripts/setup_macos_port80.sh 生成，勿手改。
# 本机自己访问走 lo0，其他设备走真实网卡，两条都要。
rdr pass on lo0 inet proto tcp from any to any port 80 -> 127.0.0.1 port ${TARGET_PORT}
rdr pass inet proto tcp from any to any port 80 -> 127.0.0.1 port ${TARGET_PORT}
RULES

# rdr-anchor 必须排在 filter 规则之前，所以插在 pf.conf 的 scrub 段之后。
if ! grep -q "$ANCHOR_NAME" /etc/pf.conf; then
    cp /etc/pf.conf "/etc/pf.conf.peach.bak.$(date +%Y%m%d-%H%M%S)"
    printf '\nrdr-anchor "%s"\nload anchor "%s" from "%s"\n' \
        "$ANCHOR_NAME" "$ANCHOR_NAME" "$ANCHOR_FILE" >> /etc/pf.conf
fi

# 先做语法检查再真正加载：pf.conf 写坏会让整台机器的包过滤加载失败。
pfctl -n -f /etc/pf.conf

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

echo "已把 80 重定向到 ${TARGET_PORT}"
echo "  验证：curl -sI http://peach.local/healthz | head -1"
echo "  移除：sudo sh $0 uninstall"
