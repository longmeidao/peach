"""外部来源 genre 到 Peach 内容标签的唯一映射位点。

不碰数据库、不碰 HTTP，和 `catalog_rules` 一样是纯策略层。

之前每个抓取脚本各带一份表：`scrape_codes.py` 只认 r18dev 的英文 genre，
`fetch_fc2_metadata.py` 只认 FC2 商品页的日文标签。结果是 dmm、mgstage、
dlgetchu 这些**日文官方来源**在 policy 里排在 tag 字段第一位，实际却一个标签
也产不出来——它们返回的全是日文，英文表一个都对不上，候选被静默丢掉。

三类结果必须分开，不能混成「没有」：

- 命中 `CONTENT_GENRES`：投影到 Peach 现有词表。
- 命中 `NON_CONTENT_GENRES`：来源确实给了值，但它描述的是画质、发行、促销或
  演员编成，不是内容。**明确排除**，不进候选也不算遗漏。
- 两边都不命中：`map_genres` 把原文回传给调用方登记。未收录不等于非内容，
  要么补进表里，要么补进排除表，不允许长期停在「不知道」。
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable


#: 来源原文 -> Peach 标签。只投影到 `catalog_rules` 已有的词表，不凭翻译造新标签。
#: 键混合英文（r18dev、aventertainment）与日文（dmm、mgstage、dlgetchu、libredmm），
#: 查表前统一走 `normalise_genre`，所以大小写与全半角写法不必在这里穷举。
CONTENT_GENRES: dict[str, str] = {
    # —— 行为 ——
    "Creampie": "中出内射", "中出し": "中出内射", "生中出し": "中出内射",
    "生ハメ": "中出内射",
    "Cream Pies": "中出内射", "No Condom": "中出内射",
    "Blowjob": "口交", "Oral": "口交", "フェラ": "口交", "フェラチオ": "口交",
    "口交": "口交",
    "Deep Throat": "深喉", "Iramatio": "深喉", "イラマチオ": "深喉",
    "ディープスロート": "深喉",
    "Cunnilingus": "舔阴", "クンニ": "舔阴", "指マン": "手交",
    "Facial": "颜射", "顔射": "颜射", "BUKKAKE": "颜射", "ぶっかけ": "颜射",
    "Bukkake/Facial": "颜射",
    "Oral Cum": "口爆", "口内発射": "口爆", "口内射精": "口爆",
    "Cum Swallowing": "吞精", "Swallowing": "吞精", "ごっくん": "吞精", "飲精": "吞精",
    "Handjob": "手交", "手コキ": "手交",
    "Titty Fuck": "乳交", "パイズリ": "乳交",
    "Footjob": "足交", "足コキ": "足交",
    "Squirting": "潮吹", "Squirts": "潮吹", "潮吹き": "潮吹",
    "Masturbation": "自慰", "オナニー": "自慰",
    "Anal Sex": "肛交", "Anal Play": "肛交", "Anal": "肛交",
    "アナル": "肛交", "アナルセックス": "肛交",
    "Cowgirl": "骑乘", "Girl on Top": "骑乘", "騎乗位": "骑乘",
    "Doggystyle": "后入", "Strong Doggy Style": "后入",
    "Standing Doggy Style": "后入", "バック": "后入",
    "POV": "主观视角", "Gonzo": "主观视角", "主観": "主观视角", "ハメ撮り": "主观视角",
    "Threesome / Foursome": "3P多人", "Threesome": "3P多人", "3P・4P": "3P多人",
    "3P": "3P多人",
    "Orgy": "多人", "乱交": "多人", "G*******g": "多人", "Harem": "多人", "ハーレム": "多人",
    "Lesbian": "百合", "レズ": "百合", "レズキス": "百合",
    "Double Penetrations": "双洞齐插",

    # —— 体貌 ——
    "Big Tits": "巨乳", "Big Tits Lover": "巨乳", "巨乳": "巨乳",
    "Fカップ": "巨乳",
    "Huge Tits": "爆乳", "爆乳": "爆乳", "Hカップ": "爆乳",
    "Beautiful Tits": "美乳", "Nice Tits": "美乳", "美乳": "美乳",
    "Small Tits": "贫乳", "貧乳": "贫乳", "貧乳・微乳": "贫乳",
    "おっぱい": "乳系",
    "Ass Lover": "美臀", "Big Asses": "美臀", "Butt": "美臀", "Nice Ass": "美臀",
    "美尻": "美臀", "尻": "美臀", "お尻": "美臀", "尻フェチ": "美臀",
    "巨尻": "美臀",
    "Foot Fetish": "美腿", "Legs": "美腿", "Beautiful Leg": "美腿",
    "美脚": "美腿",
    "Slender": "苗条", "スレンダー": "苗条",
    "Chubby": "丰满", "ぽっちゃり": "丰满",
    "Beautiful Girl": "高颜值", "Neat and Clean": "高颜值", "Beauty": "高颜值",
    "美少女": "高颜值", "美女": "高颜值", "可愛い": "高颜值", "かわいい": "高颜值",
    "美人": "高颜值", "清楚": "高颜值", "Pretty Face": "高颜值",
    "Shaved Pussy": "白虎", "パイパン": "白虎",
    "Glasses": "眼镜", "眼鏡": "眼镜", "メガネ": "眼镜",

    # —— 着装 ——
    "Pantyhose": "丝袜", "Stockings": "丝袜", "パンスト・タイツ": "丝袜",
    "ニーソックス": "丝袜", "黒パンスト": "丝袜", "Net tights": "丝袜",
    "Uniform": "制服", "Academy Uniform": "制服", "School Uniform": "制服",
    "Sailor Uniform": "制服", "制服": "制服", "セーラー服": "制服", "学生服": "制服",
    "Lingerie": "情趣内衣", "ランジェリー": "情趣内衣", "下着": "情趣内衣",
    "Swimsuit": "泳装", "Swimsuits": "泳装", "School Swimsuits": "泳装",
    "水着": "泳装", "スクール水着": "泳装",
    "Leotards": "体操服", "Gym Clothes": "体操服", "ブルマ": "体操服",
    "体操着・ブルマ": "体操服", "レオタード": "体操服",
    "Bunny Girl": "兔女郎", "バニーガール": "兔女郎",
    "Chinese Dress": "旗袍汉服", "チャイナドレス": "旗袍汉服",
    "Bride": "婚纱", "花嫁": "婚纱",
    "和服・浴衣": "和服浴衣", "着物・浴衣": "和服浴衣",
    "ツインテール": "双马尾",
    "High Heels": "高跟鞋", "ハイヒール": "高跟鞋",
    "Cosplay": "角色扮演", "コスプレ": "角色扮演", "コスプレ一般": "角色扮演",
    "Maid": "女仆", "メイド": "女仆",

    # —— 身份 ——
    "Amateur": "素人", "Amateur Girls": "素人", "素人": "素人",
    "配信専用素人": "素人",
    "Slut": "痴女", "Nymphomaniac": "痴女", "Bitch": "痴女", "痴女": "痴女",
    "ハード系": "痴女", "淫語": "淫语ASMR",
    "スケベな淫乱淑女": "痴女", "淫乱・ハード系": "痴女",
    "Extreme Ero Woman": "痴女",
    "Married Woman": "人妻", "Young Wife": "人妻", "人妻": "人妻",
    "人妻・主婦": "人妻", "若妻・幼妻": "人妻", "若妻": "人妻",
    "Mature Woman": "熟女", "MILF": "熟女", "Wives/Milf": "熟女",
    "熟女": "熟女",
    "Older Sister": "御姐", "お姉さん": "御姐",
    "Office Lady": "秘书OL", "Secretary": "秘书OL", "OL": "秘书OL", "秘書": "秘书OL",
    "School Girls": "学生", "College Girl": "学生", "女子校生": "学生",
    "ロリ": "萝莉",
    "女子大生": "学生", "大学生": "学生", "JD": "学生",
    "Nurse": "护士", "ナース・看護婦": "护士", "看護婦・ナース": "护士",
    "看護婦": "护士",
    "Female Teacher": "教师", "女教師": "教师", "教師": "教师",
    "Private Tutor": "老师", "家庭教師": "老师",
    "Stewardess": "空姐", "スチュワーデス": "空姐",
    "Picking Up Girls": "探花", "ナンパ": "探花",

    # —— 场景 ——
    "Outdoor": "户外露出", "露出": "户外露出", "野外・露出": "户外露出",
    "野外露出": "户外露出",
    "野外": "户外",
    "Car Sex": "车震", "カーセックス": "车震", "車内": "车内",
    "Massage": "按摩", "Massage Parlor": "按摩", "マッサージ": "按摩", "エステ": "按摩",
    "Bath": "浴室", "Shower, Bathroom": "浴室", "風呂": "浴室",
    "School": "教室学校", "学園もの": "教室学校",

    # —— 剧情 ——
    "Training": "调教", "BDSM": "调教", "Sadism": "调教", "Torture": "调教",
    "SM": "调教", "調教": "调教",
    "Bondage": "捆绑", "Ropes & Ties": "捆绑", "Restraint": "捆绑",
    "拘束": "捆绑", "縛り": "捆绑", "縛り・緊縛": "捆绑", "Bind": "捆绑",
    "Cheating Wife": "出轨", "Adultery": "出轨", "不倫": "出轨",
    "Cuckold": "绿帽NTR", "NTR": "绿帽NTR", "寝取り・寝取られ": "绿帽NTR",
    "寝取り・寝取られ・NTR": "绿帽NTR",
    "Incest": "近亲", "近親相姦": "近亲",
    "Voyeur": "偷拍偷窥", "Hidden Camera": "偷拍偷窥", "盗撮・のぞき": "偷拍偷窥",
    "Peeping": "偷窥", "のぞき": "偷窥",
    "Reluctant": "强制剧情", "無理矢理": "强制剧情",
    "Drama": "剧情", "ドラマ": "剧情",
    "顔出し": "露脸",
    "性教育": "性教育",
    "流出": "泄密流出",

    # —— 技术属性 ——
    "Digital Mosaic": "有码", "Minimal Mosaic": "有码", "デジモ": "有码",
    "無修正": "无码",
    "4K": "4K",
    "Virtual Reality": "VR", "VR Exclusive": "VR", "High-Quality VR": "VR",
    "8KVR": "VR", "VR専用": "VR",
    "Compilation": "混合集", "Actress Best Compilation": "混合集",
    "女優ベスト・総集編": "混合集", "総集編": "混合集",
}

#: 来源确实返回、但描述的不是内容的 genre。画质、载体、发行方式、促销企划和
#: 「单体作品／AV女優」这类演员编成都归这里：排除是判断，不是遗漏。
NON_CONTENT_GENRES: frozenset[str] = frozenset({
    # 画质与载体
    "Hi-Def", "HD High Definition", "FULL HD 1080P", "iPhone/iPad Movie",
    "Streaming Video", "ハイビジョン", "フルハイビジョン(FHD)", "高画質",
    "Blu-ray（ブルーレイ）", "DVD", "スマホ対応", "4K撮影",
    # 发行与促销
    "Exclusive Distribution", "独占配信", "Original Collaboration",
    "BIG Sale", "BIG Sale Part 2", "Sale (limited time)",
    "Prestige 40% Off Sale", "MOODYZ Campaign", "StaffPicks06",
    "Outlet (store That Sells Seconds, Discontinued Lines, Etc.)",
    "期間限定セール", "セール", "MGS限定特典映像", "特典映像あり",
    "配信専用", "MGSだけのおまけ映像付き", "Top Selling",
    "オリジナル動画", "超VIP", "1080p", "60fps",
    "Series", "Independent", "AV Open 2014 Heavyweight",
    # 样片与附属物料
    "Sample Video", "Sample Movie", "Photo Gallery", "サンプル動画",
    "写真集", "Editor's Choice", "Recommended", "本編なし",
    # 演员编成与片长
    "Featured Actress", "Female Porn Star", "AV女優", "単体作品",
    "企画", "Over 4 Hours", "4時間以上作品", "16時間以上作品",
    "Gril on top 2", "All Sex",
    # 同人载体
    "同人ソフト オリジナル",
})


#: 促销企划的名字是逐片起的——「プレステージ20周年特別企画」「春のBIGセール」
#: 「プレステージグループ秋の企画祭り」——穷举一轮就过期一轮。这几个词根本身
#: 就说明了它描述的是卖法而不是内容，按形状判非内容比逐条登记稳。
NON_CONTENT_PATTERNS = (
    re.compile(r"セール"),
    re.compile(r"キャンペーン"),
    re.compile(r"企画祭り"),
    re.compile(r"特別企画"),
    re.compile(r"(?i)big sale"),
)


def normalise_genre(raw: object) -> str:
    """统一全半角、空白与英文大小写，让一个来源写法只对应一个键。"""
    text = unicodedata.normalize("NFKC", str(raw or ""))
    return " ".join(text.split()).casefold()


_CONTENT_INDEX = {normalise_genre(key): value for key, value in CONTENT_GENRES.items()}
_NON_CONTENT_INDEX = frozenset(normalise_genre(value) for value in NON_CONTENT_GENRES)


def is_non_content_genre(raw: object) -> bool:
    key = normalise_genre(raw)
    if key in _NON_CONTENT_INDEX:
        return True
    return any(pattern.search(key) for pattern in NON_CONTENT_PATTERNS)


def map_genres(genres: Iterable[object]) -> tuple[list[str], list[str]]:
    """返回 (Peach 标签, 未收录原文)。已判定为非内容的原文两边都不出现。

    标签按首次出现去重保序；未收录原文原样回传，供调用方登记后补表。
    """
    tags: list[str] = []
    unmapped: list[str] = []
    seen_tags: set[str] = set()
    seen_unmapped: set[str] = set()
    for genre in genres or []:
        key = normalise_genre(genre)
        if not key or is_non_content_genre(key):
            continue
        tag = _CONTENT_INDEX.get(key)
        if tag is None:
            if key not in seen_unmapped:
                seen_unmapped.add(key)
                unmapped.append(" ".join(str(genre or "").split()))
            continue
        if tag not in seen_tags:
            seen_tags.add(tag)
            tags.append(tag)
    return tags, unmapped
