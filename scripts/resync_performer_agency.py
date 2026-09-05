"""重新问一遍这几位女优现在签在谁名下，把答案写回 `entity.metadata_json.agency`。

事务所会拆、会改名、会被并购，而账本里那一行停在采集当天的答案。LIGHT 就是一例：
2026-09-05 实测，她的成员在 minnano-av 上的「所属事務所」已经分别写着
`ELTRA(エルトラ)旧・LIGHT` 和 `EST(エスト)旧・LIGHT`，一家变成了两家。

这个脚本只做证据那一半：按最新一次采集覆盖 `metadata.agency`，带来源和时间戳。把它
变成实体和归属是 `install_agencies.py` 的事——`entity_membership` 主键在成员一侧，
它用 REPLACE 写，所以移籍在那一步自然成立，这里不碰归属表。

**站上写什么就记什么，括号不拆。** `ELTRA(エルトラ)旧・LIGHT` 整串存下来，拆成现用名
和别名是 `install_agencies.py` 的判断。两边各拆一次的话，改了一边的规则就会得出两种
结论，而复核件上看不出是哪一边改的。

选人有两种，可以一起给：`--agency` 按现在的归属选整家，`--only` 直接点名。默认
dry-run，只出复核 CSV；`--apply` 必须同时给 `--backup`。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from peach.config import REVIEW_DIR, STATE_DIR   # noqa: E402
from peach.http import HttpRequest, HttpxTransport   # noqa: E402
from peach.jobs import job_main   # noqa: E402
from peach.minnano_av import actress_id, profile_text, search_url   # noqa: E402
from peach.review_csv import write_rows   # noqa: E402
from peach.scripting import (   # noqa: E402
    USER_AGENT, add_ledger_write_args, counts_of, open_for_write, verify_after_write,
)

FIELDS = ("entity_id", "performer", "current_agency", "site_agency", "verdict", "evidence")

MOVED, SAME, GONE, MISSING = "移籍", "未变", "站上没有事务所", "未取得"

#: 这一行是从哪儿来的。和 `repair_link_labels.py` 写的那一条同源，所以两条路径
#: 采到的同一件事在账本里长得一样。
AGENCY_SOURCE = "minnano-av 资料表「所属事務所」"

EXTRA_COUNTS = {
    "有事务所的女优": (
        "SELECT count(*) FROM entity WHERE kind='performer'"
        " AND json_extract(metadata_json,'$.agency.name') IS NOT NULL"),
}


def targets(connection, agencies: list[str], only: list[str]) -> list[dict[str, object]]:
    """要问的人：(entity_id, 规范名, 账本里现在写着的事务所)。

    两个条件是并集而不是交集：`--agency LIGHT --only 北野未奈` 要问的是这一家加上
    这个人，而不是「这一家里叫这个名字的」——移籍时人已经不在原来那一家名下了。
    """
    found: dict[int, dict[str, object]] = {}
    for name in agencies:
        for row in connection.execute(
                "SELECT e.id, e.canonical_name,"
                " json_extract(e.metadata_json,'$.agency.name') AS agency"
                " FROM entity e JOIN entity_membership m ON m.member_id=e.id"
                " JOIN entity a ON a.id=m.agency_id"
                " WHERE a.kind='agency' AND a.canonical_name=?", (name,)):
            found[row["id"]] = {"entity_id": row["id"], "performer": row["canonical_name"],
                                "current_agency": row["agency"] or ""}
    for name in only:
        for row in connection.execute(
                "SELECT id, canonical_name,"
                " json_extract(metadata_json,'$.agency.name') AS agency"
                " FROM entity WHERE kind='performer' AND canonical_name=?", (name,)):
            found[row["id"]] = {"entity_id": row["id"], "performer": row["canonical_name"],
                                "current_agency": row["agency"] or ""}
    return [found[key] for key in sorted(found)]


def ask(http, name: str, timeout: float) -> tuple[str, str, str]:
    """问站点：这个人现在的「所属事務所」写的是什么。返回（事务所, actress_id, 说明）。

    只采信重定向。检索页正文里那一堆 `actressNNN.html` 是「相关女优」，按正文解析
    会把别人的事务所安到这个人头上。
    """
    try:
        response = http(HttpRequest("GET", search_url(name), {"User-Agent": USER_AGENT}),
                        timeout, 4 << 20)
    except Exception as error:   # noqa: BLE001  取不到就是取不到，写进复核件等重跑
        return "", "", f"未取得：{type(error).__name__}"
    if response.status != 200:
        return "", "", f"未取得：HTTP {response.status}"
    found_id = actress_id(response.url or "")
    if not found_id:
        return "", "", "未取得：检索页未唯一命中，需人工消歧"
    html = response.body.decode("utf-8", "replace")
    return (profile_text(html, "所属事務所"), found_id,
            f"minnano-av actress{found_id} 资料表「所属事務所」")


def plan(connection, http, args) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    people = targets(connection, args.agency, args.only)
    print(f"待问 {len(people)} 位 performer")
    last = 0.0
    for person in people:
        wait = args.interval - (time.monotonic() - last)
        if wait > 0:
            time.sleep(wait)
        last = time.monotonic()
        shown, _, note = ask(http, str(person["performer"]), args.timeout)
        if not note.startswith("minnano-av"):
            verdict = MISSING
        elif not shown:
            verdict = GONE
        elif shown == person["current_agency"]:
            verdict = SAME
        else:
            verdict = MOVED
        rows.append({**person, "site_agency": shown, "verdict": verdict, "evidence": note})
        print(f"{str(person['performer'])[:12]:<12} {verdict} {shown}")
    return rows


def apply_rows(connection, rows: list[dict[str, object]], stamp: str) -> dict[str, int]:
    """只改 `metadata.agency`，只改判定为移籍的那几行。

    「站上没有事务所」不清空账本里那一行：站点某天不显示这一格，和这个人真的解约了，
    在页面上长得一模一样，而清空是不可逆的一半——归属表跟着 `install_agencies.py`
    走，这里一清那边就没有依据了。要清由人单独决定。
    """
    done = {"事务所": 0}
    for row in rows:
        if row["verdict"] != MOVED:
            continue
        current = connection.execute(
            "SELECT metadata_json FROM entity WHERE id=?", (int(row["entity_id"]),)
        ).fetchone()
        try:
            metadata = json.loads(current[0] or "{}")
        except (TypeError, ValueError):
            metadata = {}
        metadata["agency"] = {"name": str(row["site_agency"]),
                              "source": AGENCY_SOURCE, "checked_at": stamp}
        connection.execute(
            "UPDATE entity SET metadata_json=?,updated_at=? WHERE id=?",
            (json.dumps(metadata, ensure_ascii=False), stamp, int(row["entity_id"])))
        done["事务所"] += 1
    return done


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    add_ledger_write_args(parser)
    parser.add_argument("--output", type=Path,
                        default=REVIEW_DIR / "performer-agency-resync.csv")
    parser.add_argument("--agency", nargs="*", default=[],
                        help="把这几家现在的成员全部再问一遍，按 canonical_name 给")
    parser.add_argument("--only", nargs="*", default=[],
                        help="再问这几位，按 performer 的 canonical_name 给")
    parser.add_argument("--interval", type=float, default=1.5)
    parser.add_argument("--timeout", type=float, default=25.0)
    parser.add_argument("--lock", type=Path, default=STATE_DIR / ".performer-agency.lock")
    return parser


def run(args) -> int:
    if not args.agency and not args.only:
        raise SystemExit("要问谁：--agency 给事务所，--only 给人名，至少给一个")
    connection = open_for_write(args)
    http = HttpxTransport()
    try:
        before = counts_of(connection, EXTRA_COUNTS)
        rows = plan(connection, http, args)
        write_rows(args.output, FIELDS, rows, atomic=True, fill_missing=True)
        stats = {verdict: sum(1 for row in rows if row["verdict"] == verdict)
                 for verdict in (MOVED, SAME, GONE, MISSING)}
        print({"复核行": len(rows), **stats, "output": str(args.output)})
        if not args.apply:
            print("dry-run：没有写入。加 --apply --backup <路径> 才真的写。")
            return 0
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        done = apply_rows(connection, rows, stamp)
        connection.commit()
        after = counts_of(connection, EXTRA_COUNTS)
        integrity, violations = verify_after_write(connection)
        print("写入：" + "，".join(f"{key} {value}" for key, value in done.items()))
        for key in sorted(before):
            print(f"  {key}: {before[key]} -> {after[key]}")
        print(f"integrity_check={integrity} foreign_key_check={violations}")
        return 0
    finally:
        http.close()
        connection.close()


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    raise SystemExit(job_main(build_parser, run))
