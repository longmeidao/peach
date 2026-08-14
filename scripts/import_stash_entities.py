"""Import Stash performer identity metadata into Peach's canonical model.

This is a transitional adapter, not a second truth source. It imports stable IDs,
aliases, descriptions and declared URLs; placeholder images are deliberately ignored.
Dry-run is the default and applying requires a SQLite backup.
"""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
import struct
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit

from peach.config import DATABASE_PATH, GENERATED_DIR
from peach.migrations import sqlite_backup
from peach.stash import StashClient


QUERY = """query PeachPerformerIdentity {
  allPerformers { id name urls alias_list details birthdate country height_cm measurements image_path }
}"""


def normalized(value: str) -> str:
    return " ".join(value.casefold().split())


def link_kind(url: str) -> str:
    host = (urlsplit(url).hostname or "").casefold()
    if host.endswith(("x.com", "twitter.com", "instagram.com", "youtube.com", "tiktok.com")):
        return "social"
    return "catalog"


def collect(connection: sqlite3.Connection, performers: list[dict]) -> list[dict]:
    entities = {normalized(name): (entity_id, name) for entity_id, name in connection.execute(
        "SELECT id,canonical_name FROM entity WHERE kind='performer'"
    )}
    result = []
    for performer in performers:
        match = entities.get(normalized(performer.get("name") or ""))
        if not match:
            continue
        aliases = sorted({a.strip() for a in performer.get("alias_list") or [] if a.strip()},
                         key=str.casefold)
        urls = {u.strip() for u in performer.get("urls") or []
                if u.strip().startswith(("https://", "http://"))}
        for alias in aliases:
            social = re.fullmatch(r"(?:X|Twitter):\s*@?([A-Za-z0-9_]{1,15})", alias, re.I)
            if social:
                urls.add("https://x.com/" + social.group(1))
        urls = sorted(urls)
        result.append({
            "entity_id": match[0], "canonical_name": match[1], "stash_id": str(performer["id"]),
            "aliases": aliases, "urls": urls, "details": (performer.get("details") or "").strip(),
            "bio": {k: performer.get(k) for k in ("birthdate", "country", "height_cm", "measurements")
                    if performer.get(k) not in (None, "")},
            "has_real_image": bool(performer.get("image_path") and
                                   "default=true" not in performer["image_path"]),
            "image_url": performer.get("image_path") or "",
        })
    return result


def apply(connection: sqlite3.Connection, rows: list[dict]) -> dict:
    stamp = datetime.now(timezone.utc).isoformat()
    counts = {"external_refs": 0, "aliases": 0, "links": 0, "summaries": 0, "search_terms": 0}
    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("BEGIN IMMEDIATE")
    try:
        for row in rows:
            entity_id = row["entity_id"]
            existing = connection.execute(
                "SELECT external_id FROM entity_external_ref WHERE entity_id=? "
                "AND provider='stash' AND external_kind='performer'", (entity_id,),
            ).fetchone()
            if existing and existing[0] != row["stash_id"]:
                raise RuntimeError(f"Stash performer ID conflict for {row['canonical_name']}")
            connection.execute(
                "INSERT OR IGNORE INTO entity_external_ref(entity_id,provider,external_kind,external_id,"
                "metadata_json,last_synced_at) VALUES(?,'stash','performer',?,'{}',?)",
                (entity_id, row["stash_id"], stamp),
            )
            counts["external_refs"] += connection.execute("SELECT changes()").fetchone()[0]
            for alias in row["aliases"]:
                connection.execute(
                    "INSERT OR IGNORE INTO entity_alias(entity_id,alias,normalized_alias,source,confidence) "
                    "VALUES(?,?,?,'stash:performer',0.9)", (entity_id, alias, normalized(alias)),
                )
                counts["aliases"] += connection.execute("SELECT changes()").fetchone()[0]
                connection.execute(
                    "INSERT OR IGNORE INTO entity_search_term(entity_id,term,purpose,source,created_at) "
                    "VALUES(?,?,'discovery','stash:performer',?)", (entity_id, alias, stamp),
                )
                counts["search_terms"] += connection.execute("SELECT changes()").fetchone()[0]
            for url in row["urls"]:
                host = urlsplit(url).hostname or ""
                connection.execute(
                    "INSERT OR IGNORE INTO entity_link(entity_id,link_kind,label,url,hostname,is_sensitive,"
                    "metadata_json,created_at,updated_at) VALUES(?,?,?,?,?,0,'{}',?,?)",
                    (entity_id, link_kind(url), host or "Stash URL", url, host, stamp, stamp),
                )
                counts["links"] += connection.execute("SELECT changes()").fetchone()[0]
            current = connection.execute(
                "SELECT metadata_json FROM entity WHERE id=?", (entity_id,),
            ).fetchone()[0]
            try:
                metadata = json.loads(current or "{}")
            except ValueError:
                metadata = {}
            changed = False
            if row["details"] and not metadata.get("summary"):
                metadata["summary"] = row["details"]
                changed = True
            for key, value in row["bio"].items():
                if key not in metadata:
                    metadata[key] = value
                    changed = True
            if changed:
                connection.execute(
                    "UPDATE entity SET metadata_json=?,updated_at=? WHERE id=?",
                    (json.dumps(metadata, ensure_ascii=False, separators=(",", ":")), stamp, entity_id),
                )
                counts["summaries"] += 1
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    return counts


def image_size(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    if data.startswith(b"\xff\xd8"):
        offset = 2
        while offset + 9 < len(data):
            if data[offset] != 0xFF:
                offset += 1
                continue
            marker = data[offset + 1]
            offset += 2
            if marker in {0xD8, 0xD9}:
                continue
            if offset + 2 > len(data):
                break
            length = int.from_bytes(data[offset:offset + 2], "big")
            if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                          0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF} and offset + 7 <= len(data):
                return (int.from_bytes(data[offset + 5:offset + 7], "big"),
                        int.from_bytes(data[offset + 3:offset + 5], "big"))
            offset += max(length, 2)
    return None


def cache_images(rows: list[dict], destination: Path, minimum_short_side: int = 512) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    result = {"cached": 0, "too_small": 0, "placeholder_or_invalid": 0, "failed": 0}
    for row in rows:
        if not row["has_real_image"]:
            continue
        url = row["image_url"]
        parsed = urlsplit(url)
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            result["failed"] += 1
            continue
        try:
            with urllib.request.urlopen(url, timeout=20) as response:
                content_type = response.headers.get_content_type()
                data = response.read(10 * 1024 * 1024 + 1)
            size = image_size(data)
            if content_type not in {"image/jpeg", "image/png"} or not size or len(data) > 10 * 1024 * 1024:
                result["placeholder_or_invalid"] += 1
                continue
            if min(size) < minimum_short_side:
                result["too_small"] += 1
                continue
            target = destination / f"performer-{row['entity_id']}.img"
            temporary = target.with_suffix(".tmp")
            temporary.write_bytes(data)
            temporary.replace(target)
            Path(str(target) + ".ct").write_text(content_type + "\n", encoding="utf-8", newline="\n")
            Path(str(target) + ".provenance.json").write_text(json.dumps({
                "source": "Stash public performer adapter",
                "stash_performer_id": row["stash_id"],
                "cached_at": datetime.now(timezone.utc).isoformat(),
                "width": size[0], "height": size[1],
                "upstream_url": "local-stash-performer-endpoint",
            }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
            result["cached"] += 1
        except (OSError, ValueError):
            result["failed"] += 1
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", type=Path, default=DATABASE_PATH)
    parser.add_argument("--graphql", default="http://127.0.0.1:9999/graphql")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--backup", type=Path)
    parser.add_argument("--cache-images", action="store_true")
    args = parser.parse_args()
    performers = StashClient(args.graphql, timeout=60).graphql(QUERY).get("allPerformers") or []
    connection = sqlite3.connect(args.db)
    try:
        rows = collect(connection, performers)
        summary = {"stash_performers": len(performers), "exact_matches": len(rows),
                   "with_aliases": sum(bool(r["aliases"]) for r in rows),
                   "with_urls": sum(bool(r["urls"]) for r in rows),
                   "with_details": sum(bool(r["details"] or r["bio"]) for r in rows),
                   "with_real_image": sum(r["has_real_image"] for r in rows)}
        print({"mode": "apply" if args.apply else "dry-run", **summary})
        if not args.apply:
            return
        if not args.backup:
            raise SystemExit("--apply requires --backup")
        connection.close()
        sqlite_backup(args.db, args.backup)
        connection = sqlite3.connect(args.db)
        applied = apply(connection, rows)
        images = cache_images(rows, GENERATED_DIR / "avatars") if args.cache_images else None
        print({"applied": applied, "images": images, "backup": str(args.backup),
               "integrity": connection.execute("PRAGMA integrity_check").fetchone()[0],
               "foreign_key_errors": len(connection.execute("PRAGMA foreign_key_check").fetchall())})
    finally:
        connection.close()


if __name__ == "__main__":
    main()
