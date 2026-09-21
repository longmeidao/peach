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

第三类的出口在复核页：用户当场给一个中文标签，或者判它不是内容，结论落进
`genre_decision`（迁移 0026）。这个模块仍然不碰数据库——决定由调用方读出来，
按 `decisions` 参数传进 `map_genres`，查表时排在两张静态表前面。
"""
from __future__ import annotations

import re
import unicodedata
from typing import Iterable, Mapping


#: 来源原文 -> Peach 标签。只投影到 `catalog_rules` 已有的词表，不凭翻译造新标签。
#: 键混合英文（r18dev、aventertainment）与日文（dmm、mgstage、dlgetchu、libredmm），
#: 查表前统一走 `normalise_genre`，所以大小写与全半角写法不必在这里穷举。
CONTENT_GENRES: dict[str, str] = {
    # —— 行为 ——
    "Creampie": "中出内射", "Creampies": "中出内射", "中出し": "中出内射",
    "中出": "中出内射", "生中出し": "中出内射", "生ハメ": "中出内射",
    "Cream Pies": "中出内射", "No Condom": "中出内射",
    "Blowjob": "口交", "Blow Job": "口交", "Oral": "口交", "Oral Sex": "口交",
    "フェラ": "口交", "フェラチオ": "口交", "口交": "口交",
    "Deep Throat": "深喉", "Deepthroat": "深喉", "Iramatio": "深喉",
    "Irrumatio": "深喉", "イラマチオ": "深喉", "ディープスロート": "深喉",
    "Cunnilingus": "舔阴", "Pussy Licking": "舔阴", "クンニ": "舔阴",
    "クンニリングス": "舔阴",
    "Facial": "颜射", "Facials": "颜射", "顔射": "颜射", "BUKKAKE": "颜射",
    "ぶっかけ": "颜射", "Bukkake/Facial": "颜射",
    "Oral Cum": "口爆", "Cum in Mouth": "口爆", "口内発射": "口爆", "口内射精": "口爆",
    "Cum Swallowing": "吞精", "Cum Swallow": "吞精", "Swallowing": "吞精",
    "Swallow": "吞精", "ごっくん": "吞精", "飲精": "吞精",
    # `指マン`／`手マン` 是同一个动作的两种写法，来源里两种都出现。
    "Handjob": "手交", "Hand Job": "手交", "Fingering": "手交", "手コキ": "手交",
    "指マン": "手交", "手マン": "手交",
    "Titty Fuck": "乳交", "Tit Fuck": "乳交", "Titjob": "乳交", "Paizuri": "乳交",
    "パイズリ": "乳交",
    "Footjob": "足交", "Foot Job": "足交", "足コキ": "足交",
    "Squirting": "潮吹", "Squirts": "潮吹", "Squirt": "潮吹", "潮吹き": "潮吹",
    "Masturbation": "自慰", "Masterbation": "自慰", "オナニー": "自慰",
    "Anal Sex": "肛交", "Anal Play": "肛交", "Anal": "肛交",
    "アナル": "肛交", "アナルセックス": "肛交",
    "Cowgirl": "骑乘", "Reverse Cowgirl": "骑乘", "Girl on Top": "骑乘",
    "Woman on Top": "骑乘", "騎乗位": "骑乘",
    "Doggystyle": "后入", "Doggy Style": "后入", "Doggy-Style": "后入", "Doggy": "后入",
    "Strong Doggy Style": "后入", "Standing Doggy Style": "后入",
    "バック": "后入", "後背位": "后入",
    "POV": "主观视角", "Gonzo": "主观视角", "主観": "主观视角", "ハメ撮り": "主观视角",
    "主觀視角": "主观视角",
    "Threesome / Foursome": "3P多人", "Threesome": "3P多人", "Foursome": "3P多人",
    "3P・4P": "3P多人", "3P/4P": "3P多人", "3P": "3P多人", "4P": "3P多人",
    "Orgy": "多人", "Gangbang": "多人", "Gang Bang": "多人", "Group Sex": "多人",
    "乱交": "多人", "G*******g": "多人", "Harem": "多人", "ハーレム": "多人",
    "Lesbian": "百合", "Lesbians": "百合", "レズ": "百合", "レズビアン": "百合",
    "レズキス": "百合",
    "Double Penetrations": "双洞齐插", "Double Penetration": "双洞齐插",
    "Kiss": "接吻", "Kissing": "接吻", "キス": "接吻", "キス・接吻": "接吻", "接吻": "接吻",
    "Sitting on Face": "颜面骑乘", "Facesitting": "颜面骑乘", "Face Sitting": "颜面骑乘",
    "顔面騎乗": "颜面骑乘",
    "69": "69", "シックスナイン": "69",
    "Peeing": "放尿", "Pissing": "放尿", "Golden Shower": "放尿", "放尿": "放尿",
    "おしっこ": "放尿", "お漏らし": "放尿", "小便": "放尿",
    # `局部アップ` 说的是镜头怎么给，和 `射精特写` 同一类；来源把它当 genre 写。
    "局部アップ": "局部特写", "Close Up": "局部特写", "Close-Up": "局部特写",
    "アップ": "局部特写",
    # 器具的名字分得很细——`バイブ` 是震动棒、`ローター` 是跳蛋、`電マ` 是电动按摩棒
    # ——但馆藏里每种各压一到五条，分成三个标签只会得到三个筛不动的稀标签。
    # 片假名 `オモチャ` 与平假名 `おもちゃ` 是同一个词，NFKC 不折叠假名，两种都登记。
    "Sex Toy": "性玩具", "Sex Toys": "性玩具", "Adult Toys": "性玩具", "Toys": "性玩具",
    "大人のおもちゃ": "性玩具", "おもちゃ": "性玩具", "オモチャ": "性玩具",
    "Vibrator": "性玩具", "Big Vibrator": "性玩具", "Egg Vibrator": "性玩具",
    "Dildo": "性玩具", "ディルド": "性玩具",
    "Pinkrotor": "性玩具", "Pink Rotor": "性玩具", "ピンクローター": "性玩具",
    "バイブ": "性玩具", "ローター": "性玩具", "電マ": "性玩具",

    # —— 体貌 ——
    "Big Tits": "巨乳", "Big Tits Lover": "巨乳", "Big Boobs": "巨乳", "Busty": "巨乳",
    "巨乳": "巨乳", "Fカップ": "巨乳",
    "Huge Tits": "爆乳", "Huge Boobs": "爆乳", "爆乳": "爆乳", "Hカップ": "爆乳",
    "Beautiful Tits": "美乳", "Beautiful Breasts": "美乳", "Nice Tits": "美乳", "美乳": "美乳",
    "Small Tits": "贫乳", "Tiny Tits": "贫乳", "Flat Chest": "贫乳",
    "貧乳": "贫乳", "貧乳・微乳": "贫乳", "微乳": "贫乳",
    "おっぱい": "乳系",
    "Ass Lover": "美臀", "Big Asses": "美臀", "Big Ass": "美臀", "Butt": "美臀", "Nice Ass": "美臀",
    "美尻": "美臀", "尻": "美臀", "お尻": "美臀", "尻フェチ": "美臀",
    "巨尻": "美臀",
    "Legs": "美腿", "Beautiful Leg": "美腿", "Beautiful Legs": "美腿", "Nice Legs": "美腿",
    "美脚": "美腿",
    # `Foot Fetish`／`足フェチ` 说的是恋足，不是腿好看。两者投影到同一个标签的话，
    # 「找恋足题材」和「找美腿出镜」在检索上就再也分不开。
    "Foot Fetish": "恋足", "足フェチ": "恋足", "Feet": "恋足", "足": "恋足",
    "足の裏": "恋足", "足裏": "恋足", "足指": "恋足",
    "Slender": "苗条", "Slim": "苗条", "Skinny": "苗条", "スレンダー": "苗条",
    "細身": "苗条", "苗條": "苗条",
    "Chubby": "丰满", "Plump": "丰满", "ぽっちゃり": "丰满", "むっちり": "丰满",
    "Glamorous Body": "丰满", "グラマー": "丰满", "グラマラス": "丰满",
    # `苗条` 说的是身材细，`娇小` 说的是个子小，两件事在检索上分得开。
    # `ミニマム` 是 MGS 给小个子开的格子。
    "Tiny Girl": "娇小", "Petite": "娇小", "小柄": "娇小", "低身長": "娇小",
    "ミニマム": "娇小",
    # `高身長グラマラス` 是 LUXU 系列的固定格子，说的是「个子高、身材丰腴」。
    # 一个原文只能投一个标签，取更能分开馆藏的那一半；丰腴那一半靠单独出现的
    # `Glamorous Body` 收。
    "Tall Girl": "高个", "Tall": "高个", "長身": "高个", "高身長": "高个",
    "高身長グラマラス": "高个",
    "Beautiful Skin": "美肌", "美肌": "美肌",
    "Ahegao": "阿黑颜", "アヘ顔": "阿黑颜",
    "Sweaty": "汗湿", "Sweat": "汗湿", "汗だく": "汗湿", "汗": "汗湿",
    "Nice Pussy": "美穴", "Beautiful Pussy": "美穴", "美マン": "美穴",
    "Big Cock": "巨根", "Big Dick": "巨根", "巨根": "巨根", "デカチン": "巨根",
    "Beautiful Girl": "高颜值", "Neat and Clean": "高颜值", "Beauty": "高颜值",
    "Cute": "高颜值",
    "美少女": "高颜值", "美女": "高颜值", "可愛い": "高颜值", "かわいい": "高颜值",
    "美人": "高颜值", "清楚": "高颜值", "Pretty Face": "高颜值", "Pretty Girl": "高颜值",
    "Shaved Pussy": "白虎", "Shaved": "白虎", "パイパン": "白虎",
    "Glasses": "眼镜", "眼鏡": "眼镜", "メガネ": "眼镜", "めがね": "眼镜",

    # —— 着装 ——
    "Pantyhose": "丝袜", "Stockings": "丝袜", "パンスト・タイツ": "丝袜",
    "パンスト": "丝袜", "タイツ": "丝袜", "ストッキング": "丝袜",
    "ニーソックス": "丝袜", "黒パンスト": "丝袜", "Net tights": "丝袜", "網タイツ": "丝袜",
    "Uniform": "制服", "Uniforms": "制服", "Academy Uniform": "制服", "School Uniform": "制服",
    "Sailor Uniform": "制服", "制服": "制服", "セーラー服": "制服", "学生服": "制服",
    "Lingerie": "情趣内衣", "Underwear": "情趣内衣", "ランジェリー": "情趣内衣",
    "下着": "情趣内衣",
    "Swimsuit": "泳装", "Swimsuits": "泳装", "School Swimsuits": "泳装",
    "Bikini": "泳装", "水着": "泳装", "スクール水着": "泳装", "ビキニ": "泳装",
    "Leotards": "体操服", "Gym Clothes": "体操服", "ブルマ": "体操服",
    "体操着・ブルマ": "体操服", "レオタード": "体操服",
    "Bunny Girl": "兔女郎", "バニーガール": "兔女郎",
    "Chinese Dress": "旗袍汉服", "チャイナドレス": "旗袍汉服",
    "Bride": "婚纱", "Wedding Dress": "婚纱", "花嫁": "婚纱", "ウェディングドレス": "婚纱",
    "Kimono": "和服浴衣", "Yukata": "和服浴衣", "着物": "和服浴衣", "浴衣": "和服浴衣",
    "和服・浴衣": "和服浴衣", "着物・浴衣": "和服浴衣",
    "Twintails": "双马尾", "Twin Tails": "双马尾", "Pigtails": "双马尾", "ツインテール": "双马尾",
    "Blonde": "金发", "Blond": "金发", "Blonde Hair": "金发", "金髪": "金发",
    "ブロンド": "金发", "金髪・ブロンド": "金发",
    "Short Hair": "短发", "ショートヘア": "短发", "ショートカット": "短发", "短髪": "短发",
    "High Heels": "高跟", "ハイヒール": "高跟",
    "Cosplay": "角色扮演", "コスプレ": "角色扮演", "コスプレ一般": "角色扮演",
    "Role Play": "角色扮演",
    "Maid": "女仆", "メイド": "女仆",

    # —— 身份 ——
    "Amateur": "素人", "Amateur Girls": "素人", "素人": "素人",
    "配信専用素人": "素人",
    "Slut": "痴女", "Nymphomaniac": "痴女", "Nympho": "痴女", "Bitch": "痴女",
    "痴女": "痴女", "淫乱": "痴女",
    "ハード系": "痴女", "淫語": "淫语", "Dirty Talk": "淫语",
    "スケベな淫乱淑女": "痴女", "淫乱・ハード系": "痴女",
    "Extreme Ero Woman": "痴女",
    "Married Woman": "人妻", "Young Wife": "人妻", "Housewife": "人妻", "Wife": "人妻",
    "人妻": "人妻", "主婦": "人妻",
    "人妻・主婦": "人妻", "若妻・幼妻": "人妻", "若妻": "人妻",
    "Mature Woman": "熟女", "Mature": "熟女", "MILF": "熟女", "Wives/Milf": "熟女",
    "熟女": "熟女", "熟女/人妻": "熟女",
    "Older Sister": "御姐", "お姉さん": "御姐",
    "Office Lady": "秘书OL", "Secretary": "秘书OL", "OL": "秘书OL", "秘書": "秘书OL",
    "School Girls": "学生", "Schoolgirl": "学生", "School Girl": "学生", "Student": "学生",
    "College Girl": "学生", "女子校生": "学生", "女学生": "学生",
    "ロリ": "萝莉",
    "女子大生": "学生", "大学生": "学生", "JD": "学生",
    "Nurse": "护士", "ナース・看護婦": "护士", "看護婦・ナース": "护士",
    "看護婦": "护士", "看護師": "护士", "ナース": "护士",
    "Female Teacher": "教师", "Teacher": "教师", "女教師": "教师", "教師": "教师",
    # 「老师」在中文里同时盖住校内教师和上门家教，和上一行的「教师」分不开。
    "Private Tutor": "家庭教师", "家庭教師": "家庭教师",
    "Stewardess": "空姐", "Flight Attendant": "空姐", "スチュワーデス": "空姐",
    "キャビンアテンダント": "空姐",
    "Picking Up Girls": "探花", "Pick up": "探花", "Pickup": "探花", "ナンパ": "探花",
    "Gal": "辣妹", "ギャル": "辣妹", "黒ギャル": "辣妹",
    "Princess & Mademoiselle": "千金小姐", "お嬢様・令嬢": "千金小姐", "お嬢様": "千金小姐",
    "Idol & Celebrity": "偶像艺人", "Idol": "偶像艺人", "アイドル・芸能人": "偶像艺人",
    "アイドル": "偶像艺人", "芸能人": "偶像艺人",
    "Instructor": "教练", "インストラクター": "教练",
    # `三十路` 是 DMM 按年龄段分的格子，三十岁往上就是这个馆藏里说的熟女。
    "三十路": "熟女", "四十路": "熟女", "五十路": "熟女",
    # `童貞` 说男方第一次、`処女` 说女方第一次，来源两个格子分开写。英文 `Virgin`
    # 单说时讲的是女方，男方那一边站上一律写成 `Virgin Boy`。
    "童貞": "处男", "Virgin Boy": "处男",
    "処女": "处女", "Virgin": "处女", "Virgin Girl": "处女",
    "Pregnant": "孕妇", "妊婦": "孕妇", "妊婦・出産": "孕妇",
    "Black Guy": "黑人", "Black Man": "黑人", "黒人": "黑人", "黒人男優": "黑人",

    # —— 场景 ——
    "Outdoor": "户外露出", "Outdoors": "户外露出", "Exhibitionism": "户外露出",
    "露出": "户外露出", "野外・露出": "户外露出", "野外露出": "户外露出",
    "野外": "户外", "屋外": "户外",
    "Car Sex": "车震", "カーセックス": "车震", "車内": "车内",
    "Massage": "按摩", "Massage Parlor": "按摩", "マッサージ": "按摩", "エステ": "按摩",
    # 涂油不一定在按摩店里：油光丝袜、涂油摔跤都是这个词，归进`按摩` 会把场景判错。
    "Oil": "油压", "Lotion": "油压", "オイル": "油压", "ローション・オイル": "油压",
    "ローション": "油压",
    "Bath": "浴室", "Shower": "浴室", "Bathroom": "浴室", "Shower, Bathroom": "浴室",
    "風呂": "浴室", "お風呂": "浴室", "シャワー": "浴室", "入浴": "浴室",
    "School": "教室学校", "Classroom": "教室学校", "学園もの": "教室学校",
    "学校": "教室学校", "教室": "教室学校",
    "Hotel": "酒店", "ホテル": "酒店",
    "Office": "办公室", "オフィス": "办公室",
    # 风俗店比按摩店宽：泡泡浴、外送和店内接客都归这一格，来源也用一个 `風俗` 盖住。
    "風俗": "风俗店", "風俗嬢": "风俗店", "ソープ": "风俗店", "Soapland": "风俗店",
    "デリヘル": "风俗店", "性風俗": "风俗店",
    # `温泉` 说的是旅程和露天池，`浴室` 说的是家里那一间，两件事在检索上分得开。
    "Hot Spring": "温泉", "温泉": "温泉", "温泉・旅行": "温泉",

    # —— 剧情 ——
    "Training": "调教", "BDSM": "调教", "Sadism": "调教", "Torture": "调教",
    "SM": "调教", "調教": "调教",
    "Slave": "调教", "Femsub": "调教", "Humiliation": "调教", "Spanking": "调教",
    "M女": "调教",
    "Bondage": "捆绑", "Ropes & Ties": "捆绑", "Restraint": "捆绑", "Shibari": "捆绑",
    "Tied Up": "捆绑",
    "拘束": "捆绑", "縛り": "捆绑", "緊縛": "捆绑", "縛り・緊縛": "捆绑", "Bind": "捆绑",
    "Cheating Wife": "出轨", "Cheating": "出轨", "Adultery": "出轨", "不倫": "出轨",
    "浮気": "出轨",
    "Cuckold": "绿帽NTR", "Netorare": "绿帽NTR", "NTR": "绿帽NTR",
    "寝取り": "绿帽NTR", "寝取られ": "绿帽NTR", "寝取り・寝取られ": "绿帽NTR",
    "寝取り・寝取られ・NTR": "绿帽NTR",
    "Incest": "近亲", "近親相姦": "近亲", "近親": "近亲",
    "Voyeur": "偷拍偷窥", "Hidden Camera": "偷拍偷窥", "盗撮・のぞき": "偷拍偷窥",
    "Peeping": "偷拍偷窥", "のぞき": "偷拍偷窥", "盗撮": "偷拍偷窥",
    "Reluctant": "强制剧情", "無理矢理": "强制剧情", "レイプ": "强制剧情",
    "Drama": "剧情", "ドラマ": "剧情",
    "顔出し": "露脸",
    "性教育": "性教育", "Sex Education": "性教育",
    "流出": "泄密流出",
    # `痴女` 说的是女方的角色性格，`女性主导` 说的是这一场里谁支配谁；同一部片
    # 两个都挂得上，合成一个就再也问不出「找女方掌控的题材」。
    "Femdom": "女性主导", "Female Domination": "女性主导", "女王様": "女性主导",
    "M男": "女性主导",
    "Panty Shot": "走光", "パンチラ": "走光",
    "初裏": "初次无码",
    # `初撮り` 是素人系列里「这个人第一次上镜」，`デビュー作品`／`Debut` 是厂牌从
    # 自己这边说的同一件事。它描述的是作品在演员生涯里的位置，但馆藏已经把「第一次」
    # 当题材收（`初拍`、`初次无码`），两种写法就落在同一格。
    "初撮り": "初拍", "初撮り娘": "初拍", "デビュー作品": "初拍", "Debut": "初拍",
    "逆ナン": "逆搭讪", "逆ナンパ": "逆搭讪",
    # `痴漢` 是电车与人群里下手的那一类，和 `盗撮`（只看不碰）、`無理矢理`（明着来）
    # 各是一格，来源三个词都在用。
    "痴漢": "痴汉", "Molester": "痴汉", "Groping": "痴汉", "チカン": "痴汉",
    "Sports": "运动", "スポーツ": "运动", "Athlete": "运动", "アスリート": "运动",
    "Drunk": "醉酒", "泥酔": "醉酒", "酔っ払い": "醉酒",
    # `媚薬` 与 `ドラッグ` 在来源那边是两个格子，说的都是「靠药物起作用」这件事。
    "Aphrodisiac": "药物", "Drug": "药物", "ドラッグ": "药物", "媚薬": "药物",
    "Documentary": "纪录片", "ドキュメンタリー": "纪录片",
    # `イメージビデオ`／`グラビア` 是不露骨的写真映像，和 `剧情` 不是一回事。
    "Image Video": "写真映像", "イメージビデオ": "写真映像", "グラビア": "写真映像",

    # —— 技术属性 ——
    "Digital Mosaic": "有码", "Minimal Mosaic": "有码", "Censored": "有码", "デジモ": "有码",
    "ギリモザ": "薄码",
    "無修正": "无码", "Uncensored": "无码",
    "ASMR": "ASMR", "音声": "ASMR", "音声作品": "ASMR",
    "4K": "4K",
    "Virtual Reality": "VR", "VR": "VR", "VR Exclusive": "VR", "High-Quality VR": "VR",
    "8KVR": "VR", "VR専用": "VR",
    "Compilation": "合集", "Omnibus": "合集", "Actress Best Compilation": "合集",
    "女優ベスト・総集編": "合集", "総集編": "合集", "ベスト・総集編": "合集",
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
    "オリジナル動画", "超VIP", "1080p", "720p", "480p", "60fps",
    "Series", "Independent", "AV Open 2014 Heavyweight",
    # 样片与附属物料
    "Sample Video", "Sample Movie", "Photo Gallery", "サンプル動画",
    "写真集", "Editor's Choice", "Recommended", "本編なし",
    # 演员编成与片长。`Famous Name` 是 aventertainments 给知名女优开的格子，
    # 说的是演员的名气，和 `Featured Actress` 同一条线。
    "Featured Actress", "Female Porn Star", "Famous Name", "AV女優", "単体作品", "單體作品",
    # `Variety` 是 `企画` 的英文：新抓的 genre 取日文原词，旧队列里冻着的那些还是英文。
    "企画", "Variety", "Over 4 Hours", "4時間以上作品", "16時間以上作品",
    "Gril on top 2", "All Sex",
    # 同人载体
    "同人ソフト オリジナル",
    # K-MIB 的氛围词与厂牌名：几乎每部都挂，区分不了内容
    "Sexy", "Glamour", "Model", "Couple", "Romantic", "Caress", "Orgasm",
    "JSmedia",
    # aventertainments 的氛围词：说的是激烈程度和叫声，不是某种行为或题材
    "Hardcore Fuck", "Scream for Joy",
    # 来源自己的兜底格：它说的是「归不进上面任何一格」，不是某种内容
    "Fetish", "フェチ", "その他フェチ", "Other Fetishes",
    "Various Professions", "職業色々", "その他", "Others",
    # 比现有词表细一档的服装、职业与日常场景：单独立一个标签只能压住一两部片，
    # 筛选面板上多一行、检索上什么也分不开
    "Jeans", "ジーンズ", "Shorts", "短パン", "Choker", "Kawaii Fashion",
    "Store Clerk", "店員", "Shopping", "買い物",
})


#: 促销企划的名字是逐片起的——「プレステージ20周年特別企画」「春のBIGセール」
#: 「プレステージグループ秋の企画祭り」——穷举一轮就过期一轮。这几个词根本身
#: 就说明了它描述的是卖法而不是内容，按形状判非内容比逐条登记稳。
NON_CONTENT_PATTERNS = (
    re.compile(r"セール"),
    re.compile(r"キャンペーン"),
    re.compile(r"企画祭り"),
    re.compile(r"特別企画"),
    re.compile(r"(?i)\bbig sale\b"),
    re.compile(r"(?i)campaign"),
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


#: `resolve_genre` 判「未收录」时的返回值。用空串而不是另起一个哨兵类型：调用方本来
#: 就要区分「有标签」和「没有标签」，多一种对象只会让每个调用点多写一次 import。
UNMAPPED = ""


def resolve_genre(raw: object,
                  decisions: Mapping[str, str | None] | None = None) -> str | None:
    """一个来源原文的去向：Peach 标签、`None`（非内容，明确排除）、或 `UNMAPPED`。

    查表顺序是用户决定、非内容、内容表。`decisions` 是用户在复核页当场定下的那批，
    键已规范化。它排在两张静态表前面：用户刚说过的话不该被发版时写下的默认盖掉，
    而把同一个词收录成别的标签正是他改主意的方式。

    抓取与复核折叠候选走同一个函数。各写一份的代价是「表里补了这个词，页面上它仍然
    停在未收录」：候选文件是抓取那一刻的产物，表却是后来才补齐的。实测本机 304 条带
    未收录 genre 的候选里，101 条的未收录项按当前的表全部认得出来。
    """
    key = normalise_genre(raw)
    if not key:
        return None
    if decisions and key in decisions:
        return decisions[key]
    if is_non_content_genre(key):
        return None
    return _CONTENT_INDEX.get(key, UNMAPPED)


def map_genres(genres: Iterable[object],
               decisions: Mapping[str, str | None] | None = None) -> tuple[list[str], list[str]]:
    """返回 (Peach 标签, 未收录原文)。已判定为非内容的原文两边都不出现。

    标签按首次出现去重保序；未收录原文原样回传，供调用方登记后补表。
    """
    tags: list[str] = []
    unmapped: list[str] = []
    seen_tags: set[str] = set()
    seen_unmapped: set[str] = set()
    for genre in genres or []:
        key = normalise_genre(genre)
        if not key:
            continue
        tag = resolve_genre(genre, decisions)
        if tag is None:
            continue
        if not tag:
            if key not in seen_unmapped:
                seen_unmapped.add(key)
                unmapped.append(" ".join(str(genre or "").split()))
            continue
        if tag not in seen_tags:
            seen_tags.add(tag)
            tags.append(tag)
    return tags, unmapped


#: 未收录原文在候选文件里的两种存法。`unmapped_genres` 是结构化的那份，`warnings`
#: 里那句话是给人读的。两样由同一个地方产出，反解也放在这里：2026-09-11 之前写下的
#: 候选文件只有那句话，而复核页要在它们上面就能把 genre 收录进来，不能等重抓一遍。
_UNMAPPED_GENRE_PREFIX = "来源还有 "
_UNMAPPED_GENRE_INFIX = " 个未收录 genre："


def unmapped_genre_warning(unmapped: list[str]) -> str:
    return f"{_UNMAPPED_GENRE_PREFIX}{len(unmapped)}{_UNMAPPED_GENRE_INFIX}" + "、".join(unmapped)


def genres_in_warning(text: object) -> list[str]:
    """从那句话里取回未收录原文；不是那句话就返回空。"""
    line = str(text or "")
    if not line.startswith(_UNMAPPED_GENRE_PREFIX) or _UNMAPPED_GENRE_INFIX not in line:
        return []
    return [part.strip() for part in line.split(_UNMAPPED_GENRE_INFIX, 1)[1].split("、") if part.strip()]
