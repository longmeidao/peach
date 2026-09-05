"""采集设置与有界来源连接检查；凭据只写本机。"""
import io
import hashlib
import json
import time
import threading

from PIL import Image

from .http import HttpRequest
from .scraping_access import SOURCES, SourceTransport, describe, save

_COVER_LOCK = threading.Lock()


def w_scraping_cover(contract, body):
    """仅处理用户指定且馆藏命中的番号；完整解码后才允许升级封面。"""
    from .metadata import validate_provider_code
    code = validate_provider_code(str(body.get("code", "")))
    with contract.database.read_connection() as connection:
        if not connection.execute("SELECT 1 FROM asset WHERE code=? LIMIT 1", (code,)).fetchone():
            raise ValueError("馆藏未找到这个番号")
    return contract.scraping_cover_job.start_result(lambda: _fetch_cover(contract, code))


def _fetch_cover(contract, code):
    from .jav_cover_fetch import (best_cover, HostLimitedTransport, Unavailable,
                                 fc2_cover_candidates, logged_success_evidence)
    from .review_csv import read_rows
    target = contract.cover_root / (code + ".jpg")
    sidecar = target.with_suffix(".scraping.json")
    try:
        previous = json.loads(sidecar.read_text(encoding="utf-8"))
        if (time.time() - float(previous["checked_at"]) < 86400 and target.is_file()
                and hashlib.sha256(target.read_bytes()).hexdigest() == previous["raw_sha256"]):
            return {"ok": True, "code": code, "result": "已复用本机封面", **{
                key: previous[key] for key in ("width", "height", "raw_sha256")}}
    except (OSError, ValueError, KeyError, TypeError):
        pass
    raw = SourceTransport(contract.follow_secrets_root, max_requests=80,
                          max_bytes=32 * 1024 * 1024, max_seconds=180)
    transport = HostLimitedTransport(raw, 1.5)
    try:
        minimum = 0
        if target.is_file():
            with Image.open(target) as image:
                minimum = image.width * image.height
        fc2 = fc2_cover_candidates(contract.candidate_root / "fc2-candidate-log.csv").get(code)
        log = contract.candidate_root / "cover-fetch-log.csv"
        previous = logged_success_evidence(read_rows(log), code) if log.is_file() else None
        prior = tuple(item for item in (fc2, previous[0] if previous else None) if item)
        candidate, size, data = best_cover(transport, code, 0, minimum_pixels=minimum,
                                          prior_candidates=prior,
                                          metadata_root=contract.follow_sources_root / "metadata" / "javinizer-go")
        with _COVER_LOCK:
            if target.is_file():
                with Image.open(target) as image:
                    if image.width * image.height >= size[0] * size[1]:
                        return {"ok": True, "code": code, "result": "已保留更清晰的本机封面"}
            target.parent.mkdir(parents=True, exist_ok=True)
            temporary = target.with_suffix(".scraping.tmp")
            try:
                temporary.write_bytes(data)
                temporary.replace(target)
            finally:
                temporary.unlink(missing_ok=True)
            evidence = {"code": code, "width": size[0], "height": size[1],
                        "source": candidate.source, "source_url": candidate.url,
                        "raw_sha256": hashlib.sha256(data).hexdigest(),
                        "installed_sha256": hashlib.sha256(data).hexdigest(),
                        "checked_at": time.time(), "resolver": "peach-jav-cover-v1"}
            sidecar.write_text(json.dumps(evidence, ensure_ascii=False), encoding="utf-8")
        return {"ok": True, "code": code, "result": "高清封面已保存", "width": size[0],
                "height": size[1], "requests": raw.requests, "bytes": raw.bytes}
    except Unavailable:
        return {"ok": False, "code": code, "error": "未取得可升级封面，已有图片保留。高清来源可能需要代理。"}
    except Exception as exc:
        return {"ok": False, "code": code, "error": "采集未取得，已有图片保留。请检查来源连接与冷却状态。",
                "error_type": type(exc).__name__}
    finally:
        transport.close()


def q_scraping(contract, _args):
    return {"sources": [describe(contract.follow_secrets_root, source) for source in SOURCES
                        if source != "instagram"],
            "instagram_status": "Instagram 自动头像定位尚待独立登录会话验证"}


def w_scraping_settings(contract, body):
    return {"ok": True, "saved": save(contract.follow_secrets_root, str(body.get("source", "")), body)}


def w_scraping_check(contract, body):
    source = str(body.get("source", ""))
    if source not in SOURCES:
        raise ValueError("未知采集来源")
    targets = [("来源页面", SOURCES[source]["login"])]
    if source == "dmm":
        targets.append(("高清图片 CDN", "https://awsimgsrc.dmm.co.jp/pics_dig/digital/video/gyan00017/gyan00017pl.jpg"))
    results = []
    transport = SourceTransport(contract.follow_secrets_root)
    try:
        for label, url in targets:
            result = {"label": label, "ok": False}
            try:
                response = transport(HttpRequest("GET", url, {"Range": "bytes=0-65535"}), 10, 65536)
                result.update(status=response.status, bytes=len(response.body),
                              ok=response.status in {200, 206})
                if label == "高清图片 CDN" and result["ok"]:
                    with Image.open(io.BytesIO(response.body)) as image:
                        result["width"], result["height"] = image.size
                if not result["ok"]:
                    result["message"] = ("来源要求登录或验证，请在官网完成后重试。"
                                         if response.status in {401, 403} else "来源暂不可用，请稍后重试。")
            except Exception as exc:
                result.update(ok=False, message="连接未取得；此来源可能需要代理，请检查来源连接方式。",
                              error_type=type(exc).__name__)
            results.append(result)
    finally:
        transport.close()
    return {"ok": True, "results": results, "session_verified": False}
