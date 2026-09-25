import unittest

from peach import catalog_rules
from peach.genre_taxonomy import (
    CONTENT_GENRES,
    NON_CONTENT_GENRES,
    NON_CONTENT_PATTERNS,
    PROFILE_GENRES,
    UNMAPPED,
    genres_in_warning,
    is_non_content_genre,
    map_genres,
    normalise_genre,
    resolve_genre,
    resolve_profile_tag,
    unmapped_genre_warning,
)
from peach.taste_history import TASTE_CATEGORY_TAGS


def _catalog_vocabulary() -> set[str]:
    names = (
        "LENGTH_TAGS", "TECH_TAGS", "ATTRIBUTE_TAGS", "RELATIONSHIP_TAGS",
        "ROLE_TAGS", "APPEARANCE_TAGS", "SCENE_TAGS", "STORY_TAGS", "POSITION_TAGS",
    )
    vocabulary: set[str] = set()
    for name in names:
        vocabulary |= set(getattr(catalog_rules, name))
    return vocabulary


class GenreTaxonomyTests(unittest.TestCase):
    def test_every_projection_lands_in_the_existing_catalog_vocabulary(self):
        """投影只能落在既有词表上。

        映射表凭翻译造一个新标签不会报错，只会让这个标签在筛选面板、同义词
        取代和统计里全部缺席——写进 ledger 后才发现，就已经是一次真实写入。
        """
        vocabulary = _catalog_vocabulary()
        unknown = sorted({tag for tag in CONTENT_GENRES.values() if tag not in vocabulary})
        self.assertEqual(unknown, [], "这些标签不在 catalog_rules 词表里，先决定收录还是改投影")

    def test_japanese_and_english_keys_share_one_table_and_one_value_space(self):
        """javbus/javdb 给日文类型词，r18dev 给英文；两套键共用一张表、一套值。

        身体尺寸与发行／营销／规格分类一概不进 `CONTENT_GENRES`，和既有的
        「`Featured Actress` 不入库」是同一条线。
        """
        self.assertEqual(CONTENT_GENRES["中出し"], "中出内射")
        self.assertEqual(CONTENT_GENRES["パイパン"], "白虎")
        self.assertEqual(CONTENT_GENRES["女子校生"], "学生")
        self.assertEqual(CONTENT_GENRES["寝取り・寝取られ"], "绿帽NTR")
        self.assertEqual(CONTENT_GENRES["巨乳"], "巨乳")
        self.assertEqual(CONTENT_GENRES["美乳"], "美乳")
        for measurement in ("Dカップ", "Gカップ", "Jカップ"):
            self.assertNotIn(measurement, CONTENT_GENRES,
                             f"{measurement} 是身体尺寸，词表里没有对应分类")
        for marketing in ("独占配信", "配信専用", "単体作品", "企画", "店長推薦作品",
                          "ハイビジョン", "フルハイビジョン(FHD)", "1080p", "60fps",
                          "4時間以上作品", "AV女優"):
            self.assertNotIn(marketing, CONTENT_GENRES,
                             f"{marketing} 是发行/营销/规格分类，不是内容标签")
        self.assertTrue({key for key in CONTENT_GENRES if not key.isascii()})

    def test_no_genre_maps_into_a_dropped_tag(self):
        """`乳系`、`足系` 这种粗桶已经撤掉，来源说到哪一级就取哪一级。

        映进撤掉的标签，等于写入一个账本清理时会整条删掉的值。`おっぱい` 只说到
        「胸」这一级，没有对应的具体标签，所以它不进表，作为未收录词回传。
        """
        offenders = sorted(
            f"{source} -> {mapped}"
            for table in (CONTENT_GENRES, PROFILE_GENRES)
            for source, mapped in table.items()
            if set(mapped if isinstance(mapped, tuple) else (mapped,)) & catalog_rules.DROPPED_TAGS)
        self.assertEqual(offenders, [], "这些映射落进了撤掉的粗桶")
        self.assertEqual(map_genres(["おっぱい"]), ([], ["おっぱい"]))

    def test_content_and_non_content_tables_do_not_overlap(self):
        both = {normalise_genre(key) for key in CONTENT_GENRES} & {
            normalise_genre(value) for value in NON_CONTENT_GENRES
        }
        self.assertEqual(both, set(), "同一个 genre 不能既是内容又被排除")

    def test_case_and_width_variants_hit_the_same_entry(self):
        self.assertEqual(map_genres(["Deep Throat"])[0], ["深喉"])
        self.assertEqual(map_genres(["deep throat"])[0], ["深喉"])
        self.assertEqual(map_genres(["ＤＥＥＰ　ＴＨＲＯＡＴ"])[0], ["深喉"])
        self.assertEqual(map_genres(["３Ｐ"])[0], ["3P多人"])

    def test_japanese_and_english_sources_project_to_one_tag(self):
        """dmm/mgstage 只给日文，r18dev 只给英文；两边必须落到同一个标签。

        这正是官方 tag 长期缺口的成因：抓取脚本各带一份英文表，日文官方来源
        排在 policy 第一位却一个标签也产不出来。
        """
        self.assertEqual(map_genres(["Creampie"])[0], map_genres(["中出し"])[0])
        self.assertEqual(map_genres(["Blowjob"])[0], map_genres(["フェラチオ"])[0])
        self.assertEqual(map_genres(["Big Tits"])[0], map_genres(["巨乳"])[0])

    def test_marketing_and_format_categories_are_excluded_not_missing(self):
        tags, unmapped = map_genres(["AV女優", "単体作品", "サンプル動画", "ハイビジョン"])
        self.assertEqual(tags, [])
        self.assertEqual(unmapped, [], "已判定的非内容分类不该再当成待补条目")
        self.assertTrue(is_non_content_genre("Featured Actress"))

    def test_unrecognised_genres_come_back_for_registration(self):
        tags, unmapped = map_genres(["Creampie", "まだ知らない分類", "Creampie"])
        self.assertEqual(tags, ["中出内射"])
        self.assertEqual(unmapped, ["まだ知らない分類"], "未收录不等于非内容，必须回传登记")

    def test_order_is_first_appearance_and_duplicates_collapse(self):
        tags, _ = map_genres(["巨乳", "Creampie", "Big Tits", "中出し"])
        self.assertEqual(tags, ["巨乳", "中出内射"])

    def test_campaign_names_are_excluded_by_shape_not_by_enumeration(self):
        """促销企划名逐片起，穷举一轮就过期一轮。

        实测样本：プレステージ20周年特別企画、春のBIGセール、
        プレステージグループ秋の企画祭り、プレステージ40％オフセール。
        """
        for value in ("プレステージ20周年特別企画", "春のBIGセール",
                      "プレステージグループ秋の企画祭り", "プレステージ40％オフセール",
                      "BIG Sale Part 2", "Summer BIG Sale",
                      "Adult Summer Campaign", "MOODYZ Fan Campaign"):
            self.assertTrue(is_non_content_genre(value), value)
        self.assertEqual(map_genres(["中出し", "春のBIGセール"]), (["中出内射"], []))
        # 形状判据不能误伤内容分类。
        for value in ("中出し", "巨乳", "コスプレ", "痴女"):
            self.assertFalse(is_non_content_genre(value), value)

    def test_abw_220_reproduces_the_mgs_product_page(self):
        """本轮的起点样本：r18dev 只给三个泛化类别，MGS 商品页给的是这些。"""
        tags, unmapped = map_genres([
            "MGS限定特典映像", "性教育", "中出し", "巨乳", "スレンダー",
            "単体作品", "フルハイビジョン(FHD)", "プレステージ20周年特別企画",
        ])
        # `性教育` 是题材类，用户复核后收进词表，不再算待决。
        self.assertEqual(tags, ["性教育", "中出内射", "巨乳", "苗条"])
        self.assertEqual(unmapped, [])

    def test_traditional_nfo_spellings_share_the_same_taxonomy(self):
        tags, unmapped = map_genres([
            "主觀視角", "苗條", "單體作品", "MGSだけのおまけ映像付き",
            "フルハイビジョン(FHD)",
        ])
        self.assertEqual(tags, ["主观视角", "苗条"])
        self.assertEqual(unmapped, [])

    def test_non_content_patterns_stay_narrow(self):
        # 每条形状判据都要说得出它为什么必然是卖法而不是内容。
        self.assertEqual(len(NON_CONTENT_PATTERNS), 6)

    def test_no_pattern_carries_a_control_character(self):
        """`\\b` 被 shell 吃掉一层就成了退格符，正则照样编译、照样静默不匹配。

        源码看上去完全正常，代价是「Summer BIG Sale」这类词一路走到复核页上等人判。
        """
        for pattern in NON_CONTENT_PATTERNS:
            with self.subTest(pattern=pattern.pattern):
                self.assertEqual(
                    [char for char in pattern.pattern if ord(char) < 32], [])

    def test_uncensored_source_vocabularies_project_too(self):
        """caribbeancom 与 javbus 的词表和 dmm/mgstage 不一样，同样要投影。"""
        carib, carib_left = map_genres([
            "オリジナル動画", "美乳", "中出し", "パイパン", "オナニー",
            "手コキ", "69", "クンニ", "初裏", "スレンダー"])
        self.assertEqual(carib, ["美乳", "中出内射", "白虎", "自慰", "手交", "69",
                                 "舔阴", "初次无码", "苗条"])
        self.assertEqual(carib_left, [])
        # 没把握的仍旧留给人决定：`Lunch Box Fuck` 是 aventertainments 自造的类目名，
        # 对应的日文原词未取得，不猜一个译法塞进表里。
        self.assertEqual(map_genres(["Lunch Box Fuck"])[1], ["Lunch Box Fuck"])
        heyzo, heyzo_left = map_genres([
            "中出し", "潮吹き", "淫語", "騎乗位", "口内発射", "看護婦", "指マン"])
        self.assertEqual(heyzo, ["中出内射", "潮吹", "淫语", "骑乘", "口爆", "护士", "手交"])
        self.assertEqual(heyzo_left, [])
        # javbus 会混进画质与演员编成，同样按非内容排除。
        self.assertTrue(all(is_non_content_genre(v)
                            for v in ("1080p", "60fps", "AV女優", "超VIP", "オリジナル動画")))


class VocabularyHygieneTests(unittest.TestCase):
    """一件事只留一个标签名，译名取通行写法。"""

    def test_no_retired_name_survives_anywhere(self):
        """退役名留在词表或投影表里，等于这次改名只改了一半。

        口味维度那张表也要查：它按标签名取资产，名字改过之后那一条只是不再命中，
        没有任何报错——`足系` 维度会安静地少掉一整类。
        """
        vocabulary = _catalog_vocabulary()
        self.assertEqual(sorted(set(catalog_rules.RETIRED_TAGS) & vocabulary), [])
        self.assertEqual(
            sorted({tag for tag in CONTENT_GENRES.values()
                    if tag in catalog_rules.RETIRED_TAGS}), [])
        taste = {tag for tags in TASTE_CATEGORY_TAGS.values() for tag in tags}
        self.assertEqual(sorted(taste & set(catalog_rules.RETIRED_TAGS)), [])
        self.assertEqual(sorted(taste - vocabulary), [], "口味维度只能按词表里真有的标签取资产")

    def test_every_retired_name_points_at_a_live_tag(self):
        """改名的目标必须是词表里真有的标签，否则改完那批资产就剩一个没人认得的名字。"""
        vocabulary = _catalog_vocabulary()
        self.assertEqual(
            sorted(set(catalog_rules.RETIRED_TAGS.values()) - vocabulary), [])
        self.assertEqual(
            sorted(set(catalog_rules.RETIRED_TAGS) & set(catalog_rules.RETIRED_TAGS.values())),
            [], "改名不能接力：一步到位，脚本才能重复执行")

    def test_an_english_word_is_judged_the_same_as_its_japanese_original(self):
        """同一个来源分类的两种写法必须同去向，否则英文那份就一路走到复核页上。

        候选文件停在抓取那一刻：日文原词是这之后才开始取的，旧队列里冻着的仍是英文。
        """
        for japanese, english in (("企画", "Variety"), ("盗撮・のぞき", "Peeping"),
                                  ("美脚", "Legs"), ("足フェチ", "Foot Fetish"),
                                  ("家庭教師", "Private Tutor")):
            with self.subTest(genre=english):
                self.assertEqual(map_genres([english]), map_genres([japanese]))

    def test_a_foot_fetish_genre_is_not_a_pair_of_nice_legs(self):
        """`Foot Fetish` 说的是恋足，不是腿好看。

        两者曾同投 `美腿`，于是「找恋足题材」和「找美腿出镜」在检索上分不开。
        """
        self.assertEqual(map_genres(["Foot Fetish"])[0], ["恋足"])
        self.assertEqual(map_genres(["足フェチ"])[0], ["恋足"])
        self.assertEqual(map_genres(["Legs"])[0], ["美腿"])
        self.assertEqual(map_genres(["美脚"])[0], ["美腿"])

    def test_the_name_the_library_actually_uses_wins(self):
        """规范名取馆藏里通行的写法，不取词表里先写下的那个。

        `合集` 3699 条、全部来自文件名；`混合集` 313 条、全部来自已关停的 Stash 导入。
        """
        self.assertEqual(map_genres(["総集編"])[0], ["合集"])
        self.assertEqual(map_genres(["ベスト・総集編"])[0], ["合集"])
        self.assertEqual(map_genres(["Compilation"])[0], ["合集"])
        self.assertEqual(map_genres(["淫語"])[0], ["淫语"])
        self.assertEqual(map_genres(["Dirty Talk"])[0], ["淫语"])

    def test_a_source_that_only_publishes_english_still_reaches_one_tag(self):
        """k-mib、aventertainments、javdb 的类目在来源页上就是英文，没有日文原词可换。

        重抓换不回日文，所以这几个词只能靠表里直接收录。同一件事的两种写法要落在
        一个标签上，否则筛选面板会摆出两行同义标签。
        """
        for english, japanese, tag in (
            ("Kiss", "キス", "接吻"),
            ("Ahegao", "アヘ顔", "阿黑颜"),
            ("Femdom", "女王様", "女性主导"),
            ("Tiny Girl", "小柄", "娇小"),
            ("Oil", "ローション・オイル", "油压"),
            ("Sitting on Face", "顔面騎乗", "颜面骑乘"),
            ("Beautiful Skin", "美肌", "美肌"),
        ):
            self.assertEqual(map_genres([english])[0], [tag])
            self.assertEqual(map_genres([japanese])[0], [tag])

    def test_every_toy_name_collapses_into_one_tag(self):
        """`バイブ` 是震动棒、`ローター` 是跳蛋、`電マ` 是电动按摩棒，各压一到五条。

        分成三个标签得到的是三个筛不动的稀标签，筛选面板上多三行、检索上分不开。
        """
        for word in ("Sex Toy", "Sex Toys", "大人のおもちゃ", "おもちゃ",
                     "Vibrator", "Big Vibrator", "Egg Vibrator",
                     "バイブ", "ローター", "電マ"):
            self.assertEqual(map_genres([word])[0], ["性玩具"], word)

    def test_a_catch_all_bucket_is_excluded_not_registered(self):
        """来源的兜底格说的是「归不进上面任何一格」，不是某种内容。"""
        for word in ("Fetish", "フェチ", "その他フェチ", "Other Fetishes",
                     "Various Professions", "職業色々"):
            self.assertTrue(is_non_content_genre(word), word)
        # 服装与职业细到这一档时，单独立标签只能压住一两部片。
        for word in ("ジーンズ", "短パン", "店員", "買い物"):
            self.assertTrue(is_non_content_genre(word), word)

    def test_two_source_words_for_one_thing_land_on_one_tag(self):
        """同义的来源词各投一个标签，就是页面上那两行重复的来处。"""
        self.assertEqual(map_genres(["Peeping"])[0], map_genres(["Voyeur"])[0])
        self.assertEqual(map_genres(["High Heels"])[0], ["高跟"])
        # 家教和校内老师是两件事，中文里「老师」把它们盖在一起。
        self.assertEqual(map_genres(["家庭教師"])[0], ["家庭教师"])
        self.assertEqual(map_genres(["女教師"])[0], ["教师"])

    def test_every_spelling_a_source_uses_reaches_the_same_tag(self):
        """同一个含义在各来源写法不同：英日、连写分写、片假名平假名。

        `normalise_genre` 只折叠大小写、全半角和空白，`Doggystyle` 与 `Doggy Style`、
        `おもちゃ` 与 `オモチャ` 在它眼里仍是两个键，词表里得各登记一次。
        """
        for spellings, tag in (
            (("Doggystyle", "Doggy Style", "Doggy", "バック", "後背位"), "后入"),
            (("Deep Throat", "Deepthroat", "Irrumatio", "イラマチオ"), "深喉"),
            (("Handjob", "Hand Job", "Fingering", "指マン", "手マン"), "手交"),
            (("Titty Fuck", "Tit Fuck", "Paizuri", "パイズリ"), "乳交"),
            (("Squirting", "Squirt", "潮吹き"), "潮吹"),
            (("Threesome", "Foursome", "3P・4P", "3P/4P", "4P"), "3P多人"),
            (("Orgy", "Gangbang", "Gang Bang", "Group Sex", "乱交"), "多人"),
            (("Sex Toy", "Toys", "Dildo", "おもちゃ", "オモチャ", "Pinkrotor", "ピンクローター"), "性玩具"),
            (("Facesitting", "Face Sitting", "顔面騎乗"), "颜面骑乘"),
            (("Big Tits", "Big Boobs", "Busty", "巨乳"), "巨乳"),
            (("Small Tits", "Tiny Tits", "Flat Chest", "貧乳"), "贫乳"),
            (("Slender", "Slim", "Skinny", "細身", "スレンダー"), "苗条"),
            (("Tiny Girl", "Petite", "小柄", "ミニマム"), "娇小"),
            (("Tall Girl", "Tall", "長身", "高身長", "高身長グラマラス"), "高个"),
            (("Pantyhose", "パンスト", "タイツ", "ストッキング", "網タイツ"), "丝袜"),
            (("Kimono", "Yukata", "着物", "浴衣", "和服・浴衣"), "和服浴衣"),
            (("Twintails", "Pigtails", "ツインテール"), "双马尾"),
            (("Married Woman", "Housewife", "Wife", "主婦", "人妻"), "人妻"),
            (("School Girls", "Schoolgirl", "Student", "女学生", "女子校生"), "学生"),
            (("Nurse", "看護婦", "看護師", "ナース"), "护士"),
            (("Stewardess", "Flight Attendant", "キャビンアテンダント"), "空姐"),
            (("Bath", "Shower", "Bathroom", "お風呂", "シャワー", "入浴"), "浴室"),
            (("School", "Classroom", "学校", "教室", "学園もの"), "教室学校"),
            (("Hotel", "ホテル"), "酒店"),
            (("Office", "オフィス"), "办公室"),
            (("Bondage", "Shibari", "Tied Up", "緊縛", "縛り"), "捆绑"),
            (("Cuckold", "Netorare", "寝取り", "寝取られ"), "绿帽NTR"),
            (("Cheating Wife", "Cheating", "不倫", "浮気"), "出轨"),
            (("Voyeur", "盗撮", "盗撮・のぞき"), "偷拍偷窥"),
            (("Uncensored", "無修正"), "无码"),
            (("Virtual Reality", "VR", "VR専用"), "VR"),
        ):
            for spelling in spellings:
                with self.subTest(spelling=spelling):
                    self.assertEqual(map_genres([spelling])[0], [tag])

    def test_a_debut_is_filed_with_the_first_shoot(self):
        """`デビュー作品`／`Debut` 是厂牌说的「第一次上镜」，和素人系列的 `初撮り` 同一格。"""
        for word in ("初撮り", "デビュー作品", "Debut"):
            self.assertEqual(map_genres([word])[0], ["初拍"], word)

    def test_fame_and_mood_words_are_excluded_not_registered(self):
        """`Famous Name` 说的是演员名气，`Hardcore Fuck`、`Scream for Joy` 是氛围词。

        `Choker`、`Kawaii Fashion` 和 `ジーンズ` 同档：比词表细一级的穿搭。
        """
        for word in ("Famous Name", "Hardcore Fuck", "Scream for Joy",
                     "Choker", "Kawaii Fashion"):
            self.assertTrue(is_non_content_genre(word), word)
        self.assertEqual(map_genres(["Famous Name", "中出し"]), (["中出内射"], []))

    def test_the_newly_localised_words_reach_their_tag(self):
        """本机候选里出现过、之前没有中文标签的那批，现在各有去处。

        这些原文此前逐轮回到复核页问同一个问题，而复核页给的答案只落在
        `genre_decision` 里——换一台机器、换一份候选又要再答一遍。
        """
        for spellings, tag in (
            (("風俗", "ソープ", "Soapland", "デリヘル"), "风俗店"),
            (("温泉", "Hot Spring"), "温泉"),
            (("金髪・ブロンド", "Blonde", "金髪", "ブロンド"), "金发"),
            (("Short Hair", "ショートヘア", "短髪"), "短发"),
            (("スポーツ", "Sports", "アスリート"), "运动"),
            (("童貞", "Virgin Boy"), "处男"),
            (("処女", "Virgin"), "处女设定"),
            (("汗だく", "Sweaty", "汗"), "汗湿"),
            (("泥酔", "Drunk", "酔っ払い"), "醉酒"),
            (("ドラッグ", "媚薬", "Aphrodisiac"), "药物"),
            (("局部アップ", "Close Up", "Close-Up"), "局部特写"),
            (("Nice Pussy", "Beautiful Pussy"), "美穴"),
            (("Glamorous Body", "グラマー"), "丰满"),
            (("ドキュメンタリー", "Documentary"), "纪录片"),
            (("イメージビデオ", "Image Video", "グラビア"), "写真映像"),
            (("痴漢", "Molester", "Groping"), "痴汉"),
            (("妊婦", "Pregnant"), "孕妇"),
            (("巨根", "Big Cock", "デカチン"), "巨根"),
            (("放尿", "Peeing", "おしっこ"), "放尿"),
            (("黒人", "Black Guy"), "黑人"),
        ):
            for spelling in spellings:
                with self.subTest(spelling=spelling):
                    self.assertEqual(map_genres([spelling])[0], [tag])

    def test_the_first_time_is_told_apart_by_whose_first_time_it_is(self):
        """`童貞` 说男方、`処女` 说女方；英文 `Virgin` 单说时讲的是女方。

        两边合成一个「第一次」标签，馆藏里就再也问不出想找的是哪一种。
        """
        self.assertEqual(map_genres(["童貞", "処女"])[0], ["处男", "处女设定"])
        self.assertEqual(map_genres(["Virgin"])[0], ["处女设定"])
        self.assertEqual(map_genres(["Virgin Boy"])[0], ["处男"])

    def test_words_whose_meaning_is_not_settled_stay_on_the_review_page(self):
        """含义还没查清的原文留给人判，不按字面猜一个标签。

        `Lunch Box Fuck` 是 aventertainments 机器翻译出来的格子，字面对不上任何
        行为；`Inter` 只在 SMBD-110 上出现，是站方截断的半个词，既可能是
        `Interracial` 也可能是 `Interview`。猜哪一个都会写出一条错标签。
        """
        for word in ("Lunch Box Fuck", "Inter"):
            with self.subTest(word=word):
                self.assertEqual(resolve_genre(word), UNMAPPED)


class ResolveGenreTests(unittest.TestCase):
    """抓取与复核折叠候选走同一个查表函数。"""

    def test_the_three_outcomes_are_told_apart(self):
        self.assertEqual(resolve_genre("中出し"), "中出内射")
        self.assertIsNone(resolve_genre("単体作品"), "非内容是结论，不是未收录")
        self.assertEqual(resolve_genre("まだ知らない分類"), UNMAPPED)
        self.assertIsNone(resolve_genre(""), "空值没有可判的东西")

    def test_a_decision_outranks_both_static_tables(self):
        decisions = {normalise_genre("中出し"): "内射体験", normalise_genre("巨乳"): None}
        self.assertEqual(resolve_genre("中出し", decisions), "内射体験")
        self.assertIsNone(resolve_genre("巨乳", decisions))


class UserDecisionTests(unittest.TestCase):
    """复核页收录下来的那批，和静态表一起参与查表。"""

    def test_a_recorded_genre_stops_coming_back_as_unmapped(self):
        decisions = {normalise_genre("Famous Name"): "有名女优"}
        tags, unmapped = map_genres(["中出し", "Famous Name", "Lunch Box Fuck"], decisions)
        self.assertEqual(tags, ["中出内射", "有名女优"])
        self.assertEqual(unmapped, ["Lunch Box Fuck"], "还没决定的那个仍要回来问")

    def test_a_genre_judged_non_content_is_excluded_not_asked_again(self):
        tags, unmapped = map_genres(["Lunch Box Fuck", "巨乳"],
                                    {normalise_genre("Lunch Box Fuck"): None})
        self.assertEqual(tags, ["巨乳"])
        self.assertEqual(unmapped, [], "排除也是结论；再问一遍等于没记下来")

    def test_the_written_form_does_not_split_one_decision_into_several(self):
        # 键已规范化，所以全角、半角和大小写写法命中同一条决定。
        decisions = {normalise_genre("Kiss"): "接吻"}
        self.assertEqual(map_genres(["ＫＩＳＳ"], decisions)[0], ["接吻"])
        self.assertEqual(map_genres([" kiss "], decisions)[0], ["接吻"])

    def test_a_decision_outranks_both_static_tables(self):
        """用户刚说过的话不该被发版时写下的默认盖掉。"""
        self.assertEqual(map_genres(["中出し"], {normalise_genre("中出し"): "内射"})[0], ["内射"])
        # `単体作品` 静态表判为非内容；用户改主意就该按他说的收录。
        self.assertEqual(map_genres(["単体作品"], {normalise_genre("単体作品"): "单体作品"})[0],
                         ["单体作品"])

    def test_the_warning_line_can_be_read_back_into_the_words(self):
        """2026-09-11 之前的候选文件只有那句话，复核页要能在它们身上继续收录。"""
        line = unmapped_genre_warning(["69", "初裏"])
        self.assertEqual(line, "来源还有 2 个未收录 genre：69、初裏")
        self.assertEqual(genres_in_warning(line), ["69", "初裏"])
        self.assertEqual(genres_in_warning("来源值含重复片段，已规范化：A → B"), [])
        self.assertEqual(genres_in_warning(""), [])


class LooksTests(unittest.TestCase):
    """颜值只在说的确实是两回事时才分开。"""

    def test_beauty_words_that_mean_the_same_share_one_tag(self):
        for word in ("美人", "美少女", "美女", "美顔", "Beautiful Girl", "Pretty Face"):
            with self.subTest(word=word):
                self.assertEqual(map_genres([word])[0], ["高颜值"])

    def test_seiso_and_cute_are_their_own_tags(self):
        """`清楚` 说的是气质干净、不张扬，不是长得好看；`可愛い` 是另一种好看。"""
        for word in ("清楚", "清楚系", "清純", "Neat and Clean"):
            with self.subTest(word=word):
                self.assertEqual(map_genres([word])[0], ["清纯"])
        for word in ("可愛い", "かわいい", "Cute"):
            with self.subTest(word=word):
                self.assertEqual(map_genres([word])[0], ["可爱"])


class ProfileTagTests(unittest.TestCase):
    """资料页的标签先查资料专用表，再落回作品的表。"""

    def test_each_trade_keeps_its_own_name(self):
        self.assertEqual(resolve_profile_tag("現役デリヘル嬢"), ("上门服务女郎",))
        self.assertEqual(resolve_profile_tag("ソープ嬢"), ("泡泡浴女郎",))
        self.assertEqual(resolve_profile_tag("セクシーパブ嬢"), ("性感酒吧女郎",))
        self.assertEqual(resolve_profile_tag("風俗嬢"), ("风俗从业",))
        # 作品上的 `看護師` 是角色扮演，资料上是她的本职。
        self.assertEqual(resolve_profile_tag("現役看護師"), ("现役护士",))

    def test_a_style_change_keeps_both_ends_of_the_arrow(self):
        self.assertEqual(resolve_profile_tag("ロリ→ギャル"), ("萝莉→辣妹",))
        self.assertEqual(resolve_profile_tag("微乳→巨乳"), ("贫乳→巨乳",))

    def test_a_cell_holding_several_tags_is_split(self):
        self.assertEqual(resolve_profile_tag("ショートカット、美乳、レズ"), ("短发", "美乳", "百合"))
        self.assertEqual(resolve_profile_tag("清楚お嬢様系"), ("清纯", "千金小姐"))

    def test_labels_and_career_notes_are_not_tags(self):
        for word in ("カリビアン", "改名・移籍", "引退", ""):
            with self.subTest(word=word):
                self.assertEqual(resolve_profile_tag(word), ())

    def test_everything_else_falls_back_to_the_work_table(self):
        self.assertEqual(resolve_profile_tag("巨尻"), ("巨臀",))
        self.assertEqual(resolve_profile_tag("単体作品"), ())
        self.assertIsNone(resolve_profile_tag("まだ知らない分類"), "未收录要让调用方照原文列")

    def test_a_decision_outranks_the_profile_table(self):
        decisions = {normalise_genre("風俗嬢"): "风俗", normalise_genre("カリビアン"): None}
        self.assertEqual(resolve_profile_tag("風俗嬢", decisions), ("风俗",))
        self.assertEqual(resolve_profile_tag("カリビアン", decisions), ())

    def test_the_profile_table_never_overlaps_the_exclusions(self):
        excluded = {normalise_genre(value) for value in NON_CONTENT_GENRES}
        self.assertEqual(sorted(key for key in PROFILE_GENRES
                                if normalise_genre(key) in excluded), [])


if __name__ == "__main__":
    unittest.main()
