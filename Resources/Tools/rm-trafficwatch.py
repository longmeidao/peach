#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流量哨兵 —— 代理下载增量超阈值就**停机报警**，不是提示后继续。

用户 2026-08-14 定的策略：构建期允许较大量用流量，短时大量消耗须停机报警；
阈值现场定（当晚 200 GB），50 GB 只是「值得警惕」的量级不是死上限。

背景：08-13 15:30 → 08-14 02:40 的 11 小时里代理下载 677 GB，
      89% 是 CloudDrive.exe 拉 PikPak。全是执行疏漏（脚本漏加 --location、
      测流量的脚本自己去拉、前端 bug 反复缓冲同一个 12.6 GB 文件），
      所以闸门必须自动执行，不能靠记性。

数据源：Clash Verge 的 external-controller 是空的、只开命名管道
        \\.\pipe\verge-mihomo，curl 打不到，直接对管道说 HTTP。
        ⚠️ downloadTotal **含 DIRECT**，不是代理用量（实测 60s 内 0.697 GB
        里有 0.531 GB 是 115 直连）。本脚本改为逐连接只累计非 DIRECT。

注意：115 走 GEOIP,CN,DIRECT 不计入代理量，所以这个哨兵只会因 PikPak 之类的出网触发。

用法:
  python rm-trafficwatch.py                       阈值 50 GB，每 30 秒查一次
  python rm-trafficwatch.py --limit 30 --interval 20
  python rm-trafficwatch.py --once                查一次当前用量就退出
"""
import os, re, sys, json, time, subprocess

PIPE = r"\\.\pipe\verge-mihomo"
SECRET = "set-your-secret"
LOG = r"R:\Resources\Migration_Logs\trafficwatch-{}.log".format(time.strftime("%Y%m%d-%H%M%S"))
ALERT = r"R:\Resources\Migration_Logs\流量警报.txt"

A = sys.argv[1:]
def _o(n, d, c=str): return c(A[A.index(n) + 1]) if n in A else d
LIMIT_GB = _o("--limit", 50.0, float)
WARN_GB = _o("--warn", LIMIT_GB * 0.6, float)
INTERVAL = _o("--interval", 2, int)
ONCE = "--once" in A
# 触发时要杀掉的任务（读网盘的那些）
KILL_PATTERNS = ["rm-probe.py", "rm-sheets.py", "rm-115sheets.py", "ppcost.py"]

logf = open(LOG, "a", encoding="utf-8", buffering=1)
def log(s):
    line = f"[{time.strftime('%H:%M:%S')}] {s}"
    print(line, flush=True); logf.write(line + "\n")

def clash(path="/connections"):
    req = (f"GET {path} HTTP/1.1\r\nHost: localhost\r\n"
           f"Authorization: Bearer {SECRET}\r\n"
           f"Accept: application/json\r\nConnection: close\r\n\r\n").encode()
    # 读到「响应真正结束」为止。
    # 上一版用 buf.endswith('}'/']'/'0') 判断结束 —— 在分块边界上会误判，
    # 连接数一多响应变大就必然在中途截断（Unterminated string）。
    with open(PIPE, "r+b", buffering=0) as f:
        f.write(req)
        buf = b""
        clen = None
        hdr_end = -1
        while True:
            try:
                chunk = f.read(65536)
            except Exception:
                break
            if not chunk:
                break
            buf += chunk
            if hdr_end < 0:
                hdr_end = buf.find(b"\r\n\r\n")
                if hdr_end >= 0:
                    head = buf[:hdr_end].lower()
                    m = re.search(rb"content-length:\s*(\d+)", head)
                    if m:
                        clen = int(m.group(1))
                    chunked = b"transfer-encoding: chunked" in head
            if hdr_end >= 0:
                body_len = len(buf) - hdr_end - 4
                if clen is not None and body_len >= clen:
                    break
                if clen is None and buf.endswith(b"\r\n0\r\n\r\n"):
                    break
    head, _, body = buf.partition(b"\r\n\r\n")
    if b"chunked" in head.lower():
        out, rest = b"", body
        while rest:
            ln, _, rest = rest.partition(b"\r\n")
            try: n = int(ln.strip().split(b";")[0], 16)
            except Exception: break
            if n == 0: break
            out += rest[:n]; rest = rest[n + 2:]
        body = out
    elif clen is not None:
        body = body[:clen]
    return json.loads(body)

def _is_direct(c):
    ch = c.get("chains") or []
    return len(ch) == 1 and ch[0] == "DIRECT"

def snapshot():
    """返回 {连接id: (已下载字节, 是否直连, 目标)} 以及 downloadTotal。

    ⚠️ 不能拿 downloadTotal 当代理用量 —— 实测它**把 DIRECT 也算进去**：
       60 秒内 downloadTotal +0.697 GB，其中 0.531 GB 来自 cdnfhnfile.115cdn.net
       （115 的 CDN，走 GEOIP,CN,DIRECT，免费），代理只占 0.010 GB。
       照这个比例，按 downloadTotal 设 200 GB 的闸门会在几小时内被免费流量撑爆，
       然后把不该停的 115 任务一起杀掉。
       所以改成：逐连接记账，只累计 chain 非纯 DIRECT 的增量。"""
    d = clash()
    per = {}
    for c in d.get("connections") or []:
        m = c.get("metadata") or {}
        per[c.get("id")] = (c.get("download", 0), _is_direct(c),
                            m.get("host") or m.get("destinationIP") or "?")
    return d.get("downloadTotal", 0), per

def kill_jobs():
    killed = []
    try:
        out = subprocess.run(["powershell", "-NoProfile", "-Command",
            "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
            "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }"],
            capture_output=True, text=True, timeout=60).stdout
        for ln in out.splitlines():
            pid, _, cmd = ln.partition("|")
            if any(p in cmd for p in KILL_PATTERNS):
                subprocess.run(["powershell", "-NoProfile", "-Command",
                                f"Stop-Process -Id {pid.strip()} -Force"],
                               capture_output=True, timeout=30)
                killed.append(f"{pid.strip()} {cmd.strip()[:80]}")
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        "Get-Process ffmpeg,ffprobe -ErrorAction SilentlyContinue | "
                        "Stop-Process -Force -ErrorAction SilentlyContinue"],
                       capture_output=True, timeout=30)
    except Exception as e:
        log(f"杀进程失败: {e}")
    return killed

try:
    total0, prev = snapshot()
except Exception as e:
    print("连不上 Clash 管道:", e); sys.exit(1)

proxy_bytes = 0.0        # 只累计走代理的
direct_bytes = 0.0       # 直连另记一笔，方便对照
hosts_proxy = {}

log(f"哨兵启动。mihomo 累计（含直连）{total0/1024**3:,.1f} GB，活跃连接 {len(prev)}")
log("计量口径：只累计非 DIRECT 连接的下载增量（115 直连不计入）")
log("⚠️ 这是**下界**：两次轮询之间开启又关闭的连接会整段漏掉。")
log("   CloudDrive 用大量短连接，30s 轮询曾比机场面板少算一半以上；已降到 2s，仍只是近似。")
log("   准确用量以机场面板为准。")
log(f"阈值：增量 {LIMIT_GB:.0f} GB 触发停机（{WARN_GB:.0f} GB 预警），每 {INTERVAL}s 查一次")

if ONCE:
    agg = {}
    for cid, (dl, dr, host) in prev.items():
        if not dr:
            agg[host] = agg.get(host, 0) + dl
    print("\n活跃**代理**连接按目标（下载字节，不含直连）:")
    for h, v in sorted(agg.items(), key=lambda x: -x[1])[:12]:
        print(f"  {v/1024**3:>8.3f} GB  {h}")
    print("\n注：mihomo 的 downloadTotal 含 DIRECT，不能当代理用量。")
    sys.exit(0)

warned = False
while True:
    time.sleep(INTERVAL)
    try:
        total, cur = snapshot()
    except Exception as e:
        log(f"读取失败（{e}），跳过本轮"); continue
    # 逐连接算增量：连接关闭后会从列表消失，最后一次增量在消失前那轮已计入
    for cid, (dl, dr, host) in cur.items():
        old = prev.get(cid, (0, dr, host))[0]
        delta = max(dl - old, 0)
        if dr:
            direct_bytes += delta
        else:
            proxy_bytes += delta
            hosts_proxy[host] = hosts_proxy.get(host, 0) + delta
    prev = cur
    nconn = len(cur)
    hosts = hosts_proxy
    used = proxy_bytes / 1024**3
    if used >= LIMIT_GB:
        top = sorted(hosts.items(), key=lambda x: -x[1])[:5]
        log(f"⛔ 增量 {used:.1f} GB 超过阈值 {LIMIT_GB:.0f} GB —— 停机")
        killed = kill_jobs()
        msg = [f"流量警报 {time.strftime('%Y-%m-%d %H:%M:%S')}",
               f"代理下载增量 {used:.1f} GB（阈值 {LIMIT_GB:.0f} GB）",
               f"（同期直连 {direct_bytes/1024**3:.1f} GB，不计入）",
               f"活跃连接 {nconn}", "", "活跃连接 Top:"]
        msg += [f"  {v/1024**3:>8.3f} GB  {h}" for h, v in top]
        msg += ["", "已杀掉的任务:"] + ([f"  {k}" for k in killed] or ["  （无匹配任务）"])
        open(ALERT, "w", encoding="utf-8").write("\n".join(msg))
        log("警报已写入 " + ALERT)
        for ln in msg: log("  " + ln)
        sys.exit(10)
    if used >= WARN_GB and not warned:
        warned = True
        log(f"⚠️ 增量已达 {used:.1f} GB（阈值 {LIMIT_GB:.0f} GB），接近停机线")
    log(f"代理 {used:>7.2f} GB / {LIMIT_GB:.0f} GB   "
        f"（直连 {direct_bytes/1024**3:>7.2f} GB 不计）   连接 {nconn}")
