"""可解释、稳定且带多样性约束的相关推荐排序。"""
from __future__ import annotations

import hashlib
import math
from collections.abc import Iterable, Mapping
from dataclasses import dataclass


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


def _feature(item: Mapping):
    """打分只用得到这三样。抽出来是因为 MMR 会对同一条候选反复算 closeness，
    每次都从 `entities` 重建五个集合的话，集合构造本身就成了主要开销。"""
    return _sets(item), item.get("year"), item.get("duration")


def _closeness_features(left, right, weights: Mapping[int, float]) -> float:
    a, left_year, left_duration = left
    b, right_year, right_duration = right
    score = 0.55 * _weighted_jaccard(a["tag"], b["tag"], weights)
    score += 0.45 if a["creator"] & b["creator"] else 0.0
    score += 0.24 if a["series"] & b["series"] else 0.0
    score += 0.18 if a["performer"] & b["performer"] else 0.0
    score += 0.12 if a["studio"] & b["studio"] else 0.0
    if left_year and right_year:
        score += max(0.0, 0.04 - 0.01 * abs(int(left_year) - int(right_year)))
    if left_duration and right_duration:
        ratio = min(float(left_duration), float(right_duration)) / max(
            float(left_duration), float(right_duration)
        )
        score += 0.05 * ratio
    return score


def _closeness(left: Mapping, right: Mapping, weights: Mapping[int, float]) -> float:
    return _closeness_features(_feature(left), _feature(right), weights)


def _reasons_features(a: Mapping[str, set[int]], b: Mapping[str, set[int]]) -> list[str]:
    return [label for kind, label in (
        ("creator", "同创作者"), ("series", "同系列"),
        ("performer", "同出演者"), ("tag", "标签接近"), ("studio", "同厂牌"),
    ) if a[kind] & b[kind]]


def _reasons(source: Mapping, candidate: Mapping) -> list[str]:
    return _reasons_features(_sets(source), _sets(candidate))


@dataclass(slots=True)
class _Entry:
    row: dict
    feature: tuple
    relevance: float
    key: str
    redundancy: float = 0.0


def rank_related(source: Mapping, candidates: Iterable[Mapping], limit: int,
                 *, seed: str | None = None, diversity: float = 0.22) -> list[dict]:
    """以 IDF 加权相关度选片，再用 MMR 抑制连续出现的近重复作品。

    朴素 MMR 的代价是 O(limit² × 候选池)：每选中一条，都要把整池和**全部**已选重算一遍
    closeness。候选池上限 4000，生产实测 limit=20 要 3.2 秒、limit=28 要 6.2 秒、
    limit=60 要 28 秒——`/api/related` 的耗时几乎全在这里，不在 SQL。
    「候选对已选集的最大 closeness」可以增量维护：新选中一条时只和这一条比一次，取较大值。
    这是等价变换，选出来的结果逐条不变，代价降到 O(limit × 候选池)。
    """
    want = max(0, int(limit))
    source_id = int(source["id"])
    pool = [dict(candidate) for candidate in candidates
            if int(candidate["id"]) != source_id]
    weights = _idf([source, *pool])
    source_feature = _feature(source)
    stable_seed = seed or str(source_id)

    entries: list[_Entry] = []
    for candidate in pool:
        feature = _feature(candidate)
        relevance = _closeness_features(source_feature, feature, weights)
        if relevance <= 0:
            continue
        reasons = _reasons_features(source_feature[0], feature[0])
        if not reasons:
            continue
        candidate["why"] = " · ".join(reasons[:2])
        candidate["related_score"] = round(relevance, 4)
        entries.append(_Entry(candidate, feature, relevance,
                              _stable_key(stable_seed, int(candidate["id"]))))

    selected: list[dict] = []
    while entries and len(selected) < want:
        best = min(range(len(entries)), key=lambda index: (
            -(entries[index].relevance - diversity * entries[index].redundancy),
            entries[index].key,
        ))
        chosen = entries.pop(best)
        selected.append(chosen.row)
        if len(selected) >= want:
            break
        for entry in entries:
            closeness = _closeness_features(entry.feature, chosen.feature, weights)
            if closeness > entry.redundancy:
                entry.redundancy = closeness
    return selected
