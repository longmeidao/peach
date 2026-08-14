#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
创作者级视觉标签 —— 把人工读风格板得出的结论写进 ledger。

标签来自 scripts/creator_boards.py 生成的 3x3 风格板，每张板横跨该创作者 9 个
不同视频，所以结论描述的是"这位创作者的稳定风格"，不是某一条视频的确证内容。
因此写入用 source='vision_creator'、confidence=0.6，与逐条确证的 vision(0.9)、
番号刮削的 r18(0.9) 区分开，下游可以按置信度取舍。

只给该创作者名下当前完全没有标签的视频补，不覆盖任何已有标注。
标签一律取自 ledger 现有词表，不新造词。

用法:
    python scripts/creator_tags.py [--apply]
"""
from __future__ import annotations

import os
import sqlite3
import sys

DB = r"R:\peach-data\database\ledger.db"
SOURCE = "vision_creator"
CONFIDENCE = 0.6

# 创作者 -> 标签。读风格板得出，只记反复出现的稳定特征。
BOARDS: dict[str, list[str]] = {
    "Retsu_dao":    ["素人", "乳系", "制服", "情趣内衣", "口交", "酒店", "多人"],
    "luckydog22":   ["美臀", "后入", "主观视角", "酒店", "素人", "骑乘"],
    "捅主任":        ["酒店", "素人", "制服", "丝袜", "探花", "角色扮演", "高跟"],
    "gattouz0":     ["素人", "无码", "口交", "骑乘", "主观视角", "美臀"],
    "SexySaffron":  ["眼镜", "自慰", "网红主播", "无码", "露脸", "丝袜", "手交"],
    "ruth_lee":     ["口交", "主观视角", "美臀", "骑乘", "自慰", "无码", "露脸"],
    "视频":          ["素人", "自慰", "丝袜", "情趣内衣", "网红主播"],
    "pandor_a":     ["自慰", "无码", "网红主播", "情趣内衣", "素人"],
    "luckydog11":   ["丝袜", "酒店", "后入", "美臀", "素人", "主观视角"],
    "oscarkim123":  ["足交", "足系", "美腿"],
    "Shinaryen":    ["素人", "无码", "主观视角", "骑乘", "美臀", "口交", "苗条"],
    "rina_vlog":    ["口交", "主观视角", "角色扮演", "情趣内衣", "丝袜", "乳交", "手交"],
    "chocoletmilkk": ["酒店", "美臀", "多人", "素人", "骑乘"],
    # asce 这一组混杂（含整条的游戏广告视频），只取反复确证的三个
    "asce":         ["制服", "骑乘", "手交"],
    "阿曼达":        ["素人", "酒店", "情趣内衣", "丝袜", "骑乘"],
    "LegsJapan":    ["足系", "足交", "美腿", "丝袜", "高跟", "无码"],
    "MattieDoll - pornhub.com": ["自慰", "无码", "网红主播", "素人", "苗条", "丝袜"],
    "roselip":      ["无码", "熟女", "女仆", "丝袜", "口交"],
    "emailprotected": ["丝袜", "美腿", "足系", "素人", "口交", "制服"],
    "OBOKOZU":      ["口交", "主观视角", "眼镜", "美臀", "无码", "素人"],
    "铃木美咲":      ["制服", "学生", "丝袜", "美腿", "自慰"],
    "kj":           ["口交", "车震", "主观视角", "素人"],
    "门槛":          ["素人", "情趣内衣", "丝袜", "骑乘", "后入"],
    "秀妍baby":      ["网红主播", "露脸", "素人", "丝袜", "自慰"],
    "임상병리학":     ["素人", "自慰", "露脸", "网红主播", "无码"],
    "Bewyx 2509":   ["角色扮演", "主观视角", "骑乘", "口交"],
    "羊羊子":        ["口交", "酒店", "露脸", "高颜值", "素人"],
}

# 读了板但故意不打标的，理由记在这里，免得下次重读一遍得出同样结论。
SKIPPED = {
    "BNST033":    "全部 34 条是 H 游戏推广广告（hgame1/2/3.xyz + 二维码），不是内容",
    "G3104":      "是某人的私人相机胶卷（宠物、写作业、自拍、夜景），基本不含成人内容",
    "tuki_1154":  "可用样张仅 5 张且过暗过糊，无法确证任何标签",
}

APPLY = "--apply" in sys.argv[1:]


def main() -> int:
    conn = sqlite3.connect(DB, timeout=60)
    conn.execute("PRAGMA busy_timeout=60000")

    known = {r[0] for r in conn.execute(
        "SELECT DISTINCT tag FROM asset_tag WHERE source IN ('name','r18','vision')")}
    unknown = {t for tags in BOARDS.values() for t in tags} - known
    if unknown:
        print("以下标签不在现有词表，先确认再写:", sorted(unknown))
        return 1

    total_assets = total_rows = 0
    for creator, tags in BOARDS.items():
        ids = [r[0] for r in conn.execute(
            "SELECT id FROM asset WHERE medium='video' AND creator=? "
            "AND id NOT IN (SELECT asset_id FROM asset_tag)", (creator,))]
        if not ids:
            print(f"  {creator[:24]:<24} 无待打标视频，跳过")
            continue
        print(f"  {creator[:24]:<24} {len(ids):>4} 条 x {len(tags)} 标签  {' '.join(tags)}")
        total_assets += len(ids)
        total_rows += len(ids) * len(tags)
        if APPLY:
            conn.executemany(
                "INSERT OR IGNORE INTO asset_tag(asset_id,tag,confidence,source) VALUES(?,?,?,?)",
                [(aid, tag, CONFIDENCE, SOURCE) for aid in ids for tag in tags])

    if APPLY:
        conn.commit()
        print(f"\n已写入：{total_assets} 条视频，约 {total_rows} 条标签")
    else:
        print(f"\n预演：将覆盖 {total_assets} 条视频，约 {total_rows} 条标签。加 --apply 落库。")
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
