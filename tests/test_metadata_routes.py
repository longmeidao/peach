"""按内容类型的来源链：判哪种内容、问哪几家、什么顺序、何时停。"""
import unittest

from peach.metadata_policy import SOURCE_SPECS
from peach.metadata_routes import (COMMUNITY_STAGE, CONTENT_TYPES, LIST_FIELD_DEPTH,
                                   OFFICIAL_STAGE, ROUTES, classify, community_route,
                                   official_route, parse_route_overrides, required_scalars,
                                   route, route_for_code, settles, stage_members,
                                   stages_for_code)


class ClassifyTests(unittest.TestCase):
    def test_the_shape_of_the_code_decides_the_type(self):
        """判定只看番号形状：等元数据到齐再判，该问的那家就永远轮不到。"""
        for code, expected in (
                ('ABW-220', 'censored'), ('DASS-468', 'censored'), ('IPX-060', 'censored'),
                ('300MIUM-1239', 'amateur'), ('259LUXU-1475', 'amateur'),
                ('SIRO-3508', 'amateur'), ('STP-26232', 'amateur'),
                ('092415_001', 'uncensored'), ('040221-001', 'uncensored'),
                ('HEYZO-1380', 'uncensored'), ('n0780', 'uncensored'),
                ('FC2-PPV-1812235', 'fc2'), ('fc2-ppv-1233719', 'fc2'),
                ('YUJ-103', 'kmib'), ('NOAH-101', 'kmib'),
                ('', 'unknown'), (None, 'unknown')):
            with self.subTest(code=code):
                self.assertEqual(classify(code), expected)

    def test_prestige_letter_prefixes_are_censored_not_amateur(self):
        """mgstage 首页同时挂有码号与素人号，按站点归类会把整个 Prestige 判成素人。"""
        for code in ('ABF-123', 'ABW-220', 'ABP-999'):
            with self.subTest(code=code):
                self.assertEqual(classify(code), 'censored')

    def test_every_type_has_a_chain(self):
        self.assertEqual(set(ROUTES), set(CONTENT_TYPES))


class RouteTableTests(unittest.TestCase):
    def test_members_are_sources_peach_has_a_parser_for(self):
        """链上只放已经接好的来源：写一个没有适配器的站进去，表现是每部片白跑一次。"""
        for content, chain in ROUTES.items():
            for source in chain:
                with self.subTest(content=content, source=source):
                    self.assertIn(source, SOURCE_SPECS)

    def test_censored_asks_the_official_mirror_first_and_javdb_last(self):
        """javdb 按出口 IP 计配额、主机间隔 5 秒，先问便宜的那两家。"""
        self.assertEqual(route_for_code('ABW-220'),
                         ('r18dev', 'avbase', 'javbus', 'javdb'))

    def test_amateur_keeps_the_same_chain_until_mgstage_is_wired_in(self):
        """MGS 素人第一源要等适配器；现在就往链首塞一个不存在的站只会是空洞。"""
        self.assertEqual(route_for_code('300MIUM-1239'), route_for_code('ABW-220'))

    def test_uncensored_never_asks_r18dev(self):
        """无码番号在 r18.dev 上没有，留着它等于每条白等一次主机间隔。"""
        for code in ('040221-001', 'HEYZO-1380', 'n0780'):
            with self.subTest(code=code):
                self.assertNotIn('r18dev', route_for_code(code))
                self.assertEqual(route_for_code(code), ('avbase', 'javbus', 'javdb'))

    def test_a_dated_code_only_asks_1pondo_when_this_file_says_so(self):
        """一本道与カリビアンコム 的番号同形，问错那家答回来的是另一部片。"""
        self.assertEqual(
            route_for_code('112312_478', 'R:/media/1pon/112312_478-1pon-whole1_hd.mp4'),
            ('1pondo', 'avbase', 'javbus', 'javdb'))
        self.assertEqual(
            route_for_code('040221-001', 'R:/media/Carib-040221-001-FHD/040221-001-carib.mp4'),
            ('avbase', 'javbus', 'javdb'))

    def test_fc2_asks_the_shop_then_the_archives_then_javdb_only(self):
        """AVBase 与 JavBus 对 FC2 番号一份证据都没给过，问了只是各撞一次空搜索。"""
        self.assertEqual(route_for_code('FC2-PPV-1812235'),
                         ('fc2', 'fc2cmadb', 'javarchive', 'javdb'))
        self.assertNotIn('r18dev', route_for_code('FC2-PPV-1812235'))

    def test_korean_mib_and_a_missing_code_ask_nobody(self):
        self.assertEqual(route_for_code('YUJ-103'), ())
        self.assertEqual(route_for_code(''), ())

    def test_official_and_community_stages_do_not_overlap(self):
        self.assertEqual(set(OFFICIAL_STAGE) & set(COMMUNITY_STAGE), set())

    def test_the_community_stage_is_capped_at_the_list_field_depth(self):
        """免复核要两家一致、封面互证要两个图源，3 家是下限不是上限。"""
        self.assertEqual(len(community_route('ABW-220')), LIST_FIELD_DEPTH)
        self.assertEqual(community_route('FC2-PPV-1812235'), ('javdb',))
        self.assertEqual(official_route('FC2-PPV-1812235'),
                         ('fc2', 'fc2cmadb', 'javarchive'))


class StageTests(unittest.TestCase):
    def test_stages_keep_the_official_sources_apart_and_fold_the_indexes(self):
        """官方那几家逐个成档才短路得了；综合索引那一档整档一起问。"""
        self.assertEqual(stages_for_code('ABW-220'), ('r18dev', 'community'))
        self.assertEqual(stages_for_code('040221-001'), ('community',))
        self.assertEqual(stages_for_code('FC2-PPV-1812235'), ('fc2', 'community'))
        self.assertEqual(stages_for_code('YUJ-103'), ())

    def test_stage_members_name_the_sources_the_evidence_files_use(self):
        chain = route_for_code('FC2-PPV-1812235')
        self.assertEqual(stage_members('fc2', chain), ('fc2', 'fc2cmadb', 'javarchive'))
        self.assertEqual(stage_members('community', chain), ('javdb',))
        self.assertEqual(stage_members('r18dev', chain), ())


class ShortCircuitTests(unittest.TestCase):
    def test_only_the_scalar_fields_this_row_still_misses_count(self):
        self.assertEqual(required_scalars(('title', 'tags', 'studio')), ('title', 'studio'))
        self.assertEqual(required_scalars(('tags',)), ())

    def test_a_stage_that_covers_the_missing_scalars_stops_the_chain(self):
        self.assertTrue(settles(('title', 'studio'), ('title', 'studio', 'tags')))
        self.assertFalse(settles(('title', 'performers'), ('title', 'studio')))

    def test_a_row_that_only_misses_list_fields_stops_at_the_first_answer(self):
        """要的本来就不是标量，再问下一档只会拿回一堆和现值相同的候选（ADR-0033）。"""
        self.assertTrue(settles((), ()))


class OverrideTests(unittest.TestCase):
    def test_an_override_replaces_the_whole_chain(self):
        overrides = parse_route_overrides('censored=r18dev,javdb')
        self.assertEqual(route('censored', overrides=overrides), ('r18dev', 'javdb'))
        self.assertEqual(route_for_code('ABW-220', overrides=overrides), ('r18dev', 'javdb'))
        self.assertEqual(community_route('ABW-220', overrides=overrides), ('javdb',))
        self.assertEqual(route('uncensored', overrides=overrides), ROUTES['uncensored'])

    def test_an_empty_chain_means_this_type_asks_nobody(self):
        overrides = parse_route_overrides({'fc2': ()})
        self.assertEqual(route_for_code('FC2-PPV-1812235', overrides=overrides), ())

    def test_a_mapping_and_a_text_line_mean_the_same_thing(self):
        self.assertEqual(parse_route_overrides('fc2=fc2;censored=r18dev'),
                         parse_route_overrides({'fc2': ['fc2'], 'censored': ['r18dev']}))

    def test_unknown_names_are_refused_instead_of_silently_dropped(self):
        """静默忽略的表现是「设置改了没生效」，比报错难查得多。"""
        with self.assertRaisesRegex(ValueError, '未知内容类型'):
            parse_route_overrides('hentai=javdb')
        with self.assertRaisesRegex(ValueError, '未知来源'):
            parse_route_overrides('censored=kin8')
        with self.assertRaisesRegex(ValueError, '类型=来源'):
            parse_route_overrides('censored')


if __name__ == '__main__':
    unittest.main()
