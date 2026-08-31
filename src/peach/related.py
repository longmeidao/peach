"""可解释、稳定且带多样性约束的相关推荐排序。"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping


KINDS = ("creator", "performer", "series", "studio", "tag")


def _stable_key(seed: str, asset_id: int) -> str:
    return hashlib.sha256(f"{seed}:{asset_id}".encode("utf-8")).hexdigest()


def _sets(item: Mapping) -> dict[str, set[int]]:
    raw = item.get("entities") or {}
    return {kind: set(raw.get(kind) or ()) for kind in KINDS}


def _idf(items: Iterable[Mapping]) -> dict[int, float]:
    rows = list(items)
    total = max(1, len(rows))
    counts: dict[int, int] = {}
    for row in rows:
        for entity_id in _sets(row)["tag"]:
            counts[entity_id] = counts.get(entity_id, 0) + 1
    return {entity_id: math.log((total + 1) / (count + 1)) + 1
            for entity_id, count in counts.items()}


def _weighted_jaccard(left: set[int], right: set[int], weights: Mapping[int, float]) -> float:
    union = left | right
    if not union:
        return 0.0
    shared = left & right
    return sum(weights.get(value, 1.0) for value in shared) / sum(
        weights.get(value, 1.0) for value in union
    )


def _closeness(left: Mapping, right: Mapping, weights: Mapping[int, float]) -> float:
    a, b = _sets(left), _sets(right)
    score = 0.55 * _weighted_jaccard(a["tag"], b["tag"], weights)
    score += 0.45 if a["creator"] & b["creator"] else 0.0
    score += 0.24 if a["series"] & b["series"] else 0.0
    score += 0.18 if a["performer"] & b["performer"] else 0.0
    score += 0.12 if a["studio"] & b["studio"] else 0.0
    left_year, right_year = left.get("year"), right.get("year")
    if left_year and right_year:
        score += max(0.0, 0.04 - 0.01 * abs(int(left_year) - int(right_year)))
    left_duration, right_duration = left.get("duration"), right.get("duration")
    if left_duration and right_duration:
        ratio = min(float(left_duration), float(right_duration)) / max(
            float(left_duration), float(right_duration)
        )
        score += 0.05 * ratio
    return score


def _reasons(source: Mapping, candidate: Mapping) -> list[str]:
    a, b = _sets(source), _sets(candidate)
    reasons = []
    for kind, label in (
        ("creator", "同创作者"), ("series", "同系列"),
        ("performer", "同出演者"), ("tag", "标签接近"), ("studio", "同厂牌"),
    ):
        if a[kind] & b[kind]:
            reasons.append(label)
    return reasons


def rank_related(source: Mapping, candidates: Iterable[Mapping], limit: int,
                 *, seed: str | None = None, diversity: float = 0.22) -> list[dict]:
    """以 IDF 加权相关度选片，再用 MMR 抑制连续出现的近重复作品。"""
    pool = [dict(candidate) for candidate in candidates
            if int(candidate["id"]) != int(source["id"])]
    weights = _idf([source, *pool])
    for candidate in pool:
        candidate["_relevance"] = _closeness(source, candidate, weights)
        candidate["_reasons"] = _reasons(source, candidate)
    pool = [candidate for candidate in pool
            if candidate["_relevance"] > 0 and candidate["_reasons"]]
    selected: list[dict] = []
    stable_seed = seed or str(source["id"])
    while pool and len(selected) < max(0, int(limit)):
        def key(candidate: Mapping):
            redundancy = max(
                (_closeness(candidate, prior, weights) for prior in selected),
                default=0.0,
            )
            mmr = float(candidate["_relevance"]) - diversity * redundancy
            return (-mmr, _stable_key(stable_seed, int(candidate["id"])))

        choice = min(pool, key=key)
        pool.remove(choice)
        reasons = choice.pop("_reasons")
        relevance = choice.pop("_relevance")
        choice["why"] = " · ".join(reasons[:2])
        choice["related_score"] = round(relevance, 4)
        selected.append(choice)
    return selected
