"""换头像：候选从哪来、地址边界在哪、装上去之后盘上是什么。"""
from __future__ import annotations

import importlib.util
import io
import json
import shutil
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw

from peach import avatar_picker, gfriends, http as peach_http
from peach.avatar_face import sidecar_path
from peach.avatar_provider import AvatarCandidateCache, inspect_avatar, provenance_now
from peach.http import HttpResponse

from support.ledger import fresh_ledger

HAS_DEPS = all(importlib.util.find_spec(name) for name in ("fastapi", "httpx"))

FILETREE = {
    "Content": {
        "0-Hand-Storage": {"葵つかさ.jpg": "葵つかさ.jpg?t=1"},
        "7-S1": {"葵つかさ.jpg": "葵つかさ.jpg?t=2"},
        "y-Minnano": {"葵つかさ.jpg": "AI-Fix-葵つかさ.jpg?t=3"},
        "8-GRAPHIS": {"別人.jpg": "別人.jpg?t=4"},
        # 同一个人按另一种写法另存的一批。图库里这是常态，而它跟上面三张一个键也不共用。
        "3-Prestige": {"葵ツカサ.jpg": "葵ツカサ.jpg?t=5"},
    }
}
LIBRARY_REF = "gfriends:7-S1/葵つかさ.jpg"


def picture(width: int = 40, height: int = 60, colour: str = "red") -> bytes:
    """一张有内容的图：底色之上压一块对比色。

    `images.is_flat` 把整张一个颜色的当成「来源取不到图时给的一块底色」挡在候选之外，
    所以拿来当人像用的固定件必须有起伏。压一块矩形就够——这些用例问的是「哪些候选
    列出来、排第几」，不是像素长什么样；`colour` 仍然决定内容哈希，各用例互不串图。
    """
    buffer = io.BytesIO()
    image = Image.new("RGB", (width, height), colour)
    ImageDraw.Draw(image).rectangle(
        (0, 0, width, height // 2), fill="black" if colour != "black" else "white")
    image.save(buffer, format="JPEG")
    return buffer.getvalue()


def flat_picture(width: int = 40, height: int = 60, colour: str = "white") -> bytes:
    """整张一个颜色——`is_flat` 要挡住的正是这种。"""
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), colour).save(buffer, format="JPEG")
    return buffer.getvalue()


def transport_of(body: bytes, status: int = 200, calls: list[str] | None = None):
    """一个只会吐出这张图的 transport。真实取图由 HTTP 域的用例覆盖。"""
    def send(request, timeout=None, max_bytes=None):
        if calls is not None:
            calls.append(request.url)
        return HttpResponse(status, {}, body, request.url)
    return send


def seed_library(providers_root: Path) -> Path:
    """把图库索引放进候选缓存，测试全程不出网。"""
    index_dir = providers_root / avatar_picker.GFRIENDS_CACHE
    index_dir.mkdir(parents=True, exist_ok=True)
    (index_dir / gfriends.INDEX_NAME).write_text(json.dumps(FILETREE),
                                                 encoding="utf-8")
    return index_dir


def seed_person(database: Path) -> None:
    """规范名是简体、图库里只有日文写法的那一类人，别名链的必要性全在这里。"""
    connection = sqlite3.connect(database)
    with connection:
        connection.execute(
            "INSERT INTO entity(id,kind,canonical_name,normalized_name,"
            "created_at,updated_at) VALUES(7792,'performer','葵司','葵司','t','t')")
        connection.execute(
            "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
            "confidence) VALUES(7792,'葵つかさ','葵つかさ','r18:performer',1.0)")
    connection.close()


class IndexTests(unittest.TestCase):
    """索引的解析与排序。目录前缀是来源优先级，`0-` 排在最前。"""

    def test_the_index_maps_one_name_to_every_source_best_first(self):
        index = gfriends.parse_filetree(json.dumps(FILETREE).encode("utf-8"))
        self.assertEqual(index["葵つかさ"], [
            ("0-Hand-Storage", "葵つかさ.jpg"),
            ("7-S1", "葵つかさ.jpg"),
            ("y-Minnano", "AI-Fix-葵つかさ.jpg"),
        ])

    def test_unknown_prefixes_sort_last_instead_of_first(self):
        """`find` 认不出的前缀返回 -1，直接拿去排序会让它抢到最前面。"""
        self.assertGreater(gfriends.quality_key("《怪目录", "a.jpg"),
                           gfriends.quality_key("z-DMM", "a.jpg"))

    def test_a_missing_index_is_empty_rather_than_an_error(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(gfriends.load_index(Path(folder)), {})
            self.assertIsNone(gfriends.index_age(Path(folder)))

    def test_every_name_on_the_chain_brings_its_own_pictures(self):
        """并起来，不是停在第一个命中的名字上。

        同一个人在图库里常按好几种写法各存一批，停下来就只剩其中一批——实测「新有菜」
        那条链，先命中的那个名下 1 张、后面那个名下 11 张。
        """
        index = gfriends.parse_filetree(json.dumps(FILETREE).encode("utf-8"))
        match = gfriends.candidates(index, ["葵司", "葵つかさ", "葵ツカサ"])
        self.assertEqual(match.names, ("葵つかさ", "葵ツカサ"))
        # 并完之后整体重排：挑图看的是哪张该先试，不是它由链上第几个名字找到的。
        self.assertEqual([category for category, _ in match.items],
                         ["0-Hand-Storage", "3-Prestige", "7-S1", "y-Minnano"])
        # 一张图的来路记的是找到它的那个名字，不能记成整条链。
        self.assertEqual(match.finder[("3-Prestige", "葵ツカサ.jpg")], "葵ツカサ")

    def test_a_picture_two_names_both_point_at_is_listed_once(self):
        index = {"甲": [("7-S1", "a.jpg")], "乙": [("7-S1", "a.jpg")]}
        match = gfriends.candidates(index, ["甲", "乙"])
        self.assertEqual(match.items, (("7-S1", "a.jpg"),))
        # 先指到它的那个名字算它的来路。
        self.assertEqual(match.finder[("7-S1", "a.jpg")], "甲")

    def test_a_chain_that_hits_nothing_is_falsy(self):
        index = gfriends.parse_filetree(json.dumps(FILETREE).encode("utf-8"))
        self.assertFalse(gfriends.candidates(index, ["谁都不是"]))


class SourceBoundaryTests(unittest.TestCase):
    """手填地址的边界。Peach 跑在用户机器上，这道判据挡的是「替人去探内网」。"""

    def test_only_public_https_names_are_accepted(self):
        with mock.patch.object(peach_http, "host_addresses",
                               return_value=("93.184.216.34",)):
            self.assertTrue(avatar_picker.allowed_source("https://example.com/a.jpg"))
            for rejected in ("http://example.com/a.jpg", "https://127.0.0.1/a.jpg",
                             "https://169.254.169.254/a.jpg", "https://peach.local/a.jpg",
                             "https://[::1]/a.jpg", "https://user:pw@example.com/a.jpg",
                             "ftp://example.com/a.jpg", "https://localhost/a.jpg",
                             "https://box.internal/a.jpg", ""):
                self.assertFalse(avatar_picker.allowed_source(rejected), rejected)

    def test_a_public_name_that_resolves_inward_is_still_refused(self):
        """名字像公网、解析出来的地址却不可全球路由——这正是绕开字面判据的走法。

        第三组是「一个公网地址加一个链路本地地址」：`169.254.169.254` 是云上取实例
        凭据的那个端点，只要有一个地址不合格就得整条拒掉，不能因为第一个合格就放行。
        """
        for addresses in ((), ("127.0.0.1",), ("93.184.216.34", "169.254.169.254")):
            with mock.patch.object(peach_http, "host_addresses",
                                   return_value=addresses):
                self.assertFalse(
                    avatar_picker.allowed_source("https://example.com/a.jpg"),
                    str(addresses))

    def test_bytes_have_to_decode_as_a_picture(self):
        """格式由解码结果定：响应头和扩展名都是别人说了算的。"""
        with self.assertRaises(avatar_picker.PickerError):
            avatar_picker.accept_image(b"<svg width='9'><rect/></svg>")
        with self.assertRaises(avatar_picker.PickerError):
            avatar_picker.accept_image(b"x" * (avatar_picker.MAX_IMAGE_BYTES + 1))
        self.assertEqual(avatar_picker.accept_image(picture()).width, 40)


class PickerFixture(unittest.TestCase):
    def setUp(self):
        self.folder = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.providers = self.folder / "provider-cache" / "performer-avatars"
        self.avatars = self.folder / "avatars"
        self.avatars.mkdir(parents=True)
        seed_library(self.providers)
        self.database = fresh_ledger(self.folder)
        seed_person(self.database)
        self.connection = sqlite3.connect(self.database)
        self.addCleanup(self.connection.close)
        # 人脸模型要下 232 KB ONNX，测试不出网；取景本身由头像域的用例覆盖。
        self.face = mock.patch("peach.avatar_provider.FaceProbe").start()
        self.face.return_value.return_value = None
        self.addCleanup(mock.patch.stopall)

    def remember(self, body: bytes, provider: str = "social-web",
                 external_id: str = "old", url: str = "") -> str:
        """把一张图放进候选缓存并留下证据，等同「这个人取过这张」。

        `url` 给显式值是为了造「同一张图既在图库里、也在取过的图里」那一幕：跨来源
        认同一张图靠的是缓存记录里的地址，不是证据文件自己说了算。
        """
        cache = AvatarCandidateCache(self.providers / provider)
        inspected = inspect_avatar(body)
        url = url or f"https://{provider}.example/{external_id}.jpg"
        cache.store(url, body, inspected)
        cache.store_provenance(provenance_now(
            entity_id=7792, provider=provider, source_kind="official_profile",
            matched_name="葵司", name_source="canonical", external_id=external_id,
            upstream_url=url, width=inspected.width, height=inspected.height,
            mime_type=inspected.mime_type, sha256=inspected.sha256,
            cache_path=f"objects/{inspected.sha256}{inspected.extension}"))
        return inspected.sha256

    def listed(self) -> dict:
        return avatar_picker.choices(self.connection, self.providers,
                                     self.avatars, "performer", 7792)


class ChoiceTests(PickerFixture):
    def test_the_alias_is_what_finds_her_in_the_library(self):
        """规范名是简体，图库里只有日文写法；不查别名一张也列不出来。"""
        out = self.listed()
        self.assertEqual(out["names"], ["葵司", "葵つかさ"])
        self.assertEqual(out["matched_names"], ["葵つかさ"])
        self.assertEqual([one["ref"] for one in out["choices"]], [
            "gfriends:0-Hand-Storage/葵つかさ.jpg",
            LIBRARY_REF,
            "gfriends:y-Minnano/AI-Fix-葵つかさ.jpg",
        ])
        # 只有一个名字找得到时不必说是哪一个：那一屏上写着的就是她。
        self.assertEqual({one["found_by"] for one in out["choices"]}, {""})

    def test_a_second_writing_of_her_name_brings_its_own_pictures(self):
        """两种写法在图库里是两批图，而屏幕上要说清哪一张是按哪个名字找到的。

        找错人是这里唯一会出的大错，名字是唯一的线索：只报「图库里找到的」，一张
        同名不同人的图就没有任何能让人起疑的地方。
        """
        with self.connection:
            self.connection.execute(
                "INSERT INTO entity_alias(entity_id,alias,normalized_alias,source,"
                "confidence) VALUES(7792,'葵ツカサ','葵ツカサ','user:alias',1.0)")
        out = self.listed()
        self.assertEqual(out["matched_names"], ["葵つかさ", "葵ツカサ"])
        found = {one["ref"]: one["found_by"] for one in out["choices"]}
        self.assertEqual(found["gfriends:3-Prestige/葵ツカサ.jpg"], "葵ツカサ")
        self.assertEqual(found[LIBRARY_REF], "葵つかさ")

    def test_pictures_taken_before_show_up_as_their_own_group(self):
        """换回去不该再下一次：取过的图按内容哈希躺在候选缓存里。"""
        digest = self.remember(picture(colour="blue"))
        history = [one for one in self.listed()["choices"]
                   if one["source"] == "history"]
        self.assertEqual([one["ref"] for one in history], [f"sha256:{digest}"])

    def test_every_label_reads_as_where_the_picture_came_from(self):
        """格子底下写来源，不写取图时用的那串代号。

        `x:aoi_tsukasa8`、`jae:actress.html#joyu117` 回答的是「批处理怎么再找到它」，
        对着屏幕选图的人读不出意思。图库那一侧同理：目录名首字母是图库自己的优先级
        记号（`quality_key` 读的就是它），`S1`、`Minnano` 才说得出这张图出自谁家。
        """
        self.remember(picture(colour="blue"), external_id="x:aoi_tsukasa8")
        out = self.listed()["choices"]
        self.assertEqual([one["label"] for one in out if one["source"] == "gfriends"],
                         ["Hand-Storage", "S1", "Minnano"])
        self.assertEqual([one["label"] for one in out if one["source"] == "history"],
                         ["社交主页"])

    def test_a_picture_with_one_colour_never_reaches_the_grid(self):
        """整张一个颜色的不是人像，是来源取不到图时给的一块底色。

        X 取不到头像时回的那张是 143×143 纯白：尺寸过得了短边下限、格式是正经图片，
        只有看像素才分得出来。摆出来就是一块白格子，而点下去真的会把它装成头像。
        """
        self.remember(flat_picture(), external_id="blank")
        self.assertEqual([one for one in self.listed()["choices"]
                          if one["source"] == "history"], [])

    def test_the_one_on_disk_right_now_is_marked_and_comes_first(self):
        """在用的那张是这一屏唯一的参照物——别的候选好不好，是跟它比出来的。"""
        body = picture(colour="green")
        digest = self.remember(body, external_id="now")
        (self.avatars / "performer-7792.img").write_bytes(body)
        out = self.listed()["choices"]
        self.assertEqual([one["ref"] for one in out if one["current"]],
                         [f"sha256:{digest}"])
        self.assertEqual(out[0]["ref"], f"sha256:{digest}")

    def test_one_picture_is_one_choice_even_when_two_routes_found_it(self):
        """图库里的图取过之后，它同时也是「这个人取过的图」。

        两个格子长得一模一样、点哪个结果也一样，只有标签不同。留图库那一边：`S1`
        说得出这张图是谁家的，「图库」只说得出它是从哪条路子来的。尺寸也一并从缓存
        记录里补上——判一张图多大用不着把它读出来。
        """
        digest = self.remember(picture(colour="blue"), provider="gfriends",
                               external_id="7-S1/葵つかさ.jpg",
                               url=gfriends.image_url("7-S1", "葵つかさ.jpg"))
        out = self.listed()["choices"]
        self.assertEqual([one["ref"] for one in out].count(LIBRARY_REF), 1)
        self.assertNotIn(f"sha256:{digest}", [one["ref"] for one in out])
        listed = next(one for one in out if one["ref"] == LIBRARY_REF)
        self.assertEqual((listed["width"], listed["height"]), (40, 60))

    def test_a_stale_index_is_reported_rather_than_refreshed(self):
        """页面不为一次点击同步拉 6 MB；过期就说出来，补索引是批处理的事。"""
        self.assertFalse(self.listed()["index_stale"])
        old = gfriends.INDEX_MAX_AGE_SECONDS + 3600
        with mock.patch.object(gfriends, "index_age", return_value=old):
            stale = self.listed()
        self.assertTrue(stale["index_stale"])
        self.assertEqual(stale["index_age_hours"], round(old / 3600, 1))


class ResolveTests(PickerFixture):
    def test_a_library_candidate_is_downloaded_once(self):
        body = picture()
        calls: list[str] = []
        transport = transport_of(body, calls=calls)
        got, origin = avatar_picker.resolve(LIBRARY_REF, self.connection,
                                            self.providers, 7792, transport)
        self.assertEqual(got, body)
        self.assertEqual(origin["gfriends_category"], "7-S1")
        self.assertTrue(origin["upstream_url"].startswith(gfriends.GFRIENDS_RAW))
        AvatarCandidateCache(self.providers / avatar_picker.GFRIENDS_CACHE).store(
            origin["upstream_url"], body, inspect_avatar(body))
        avatar_picker.resolve(LIBRARY_REF, self.connection, self.providers, 7792,
                              transport)
        self.assertEqual(len(calls), 1)

    def test_a_reference_outside_what_was_listed_is_refused(self):
        """`ref` 要在服务端刚枚举出来的那一批里，否则就是一个任意地址抓取的口子。"""
        for bad in ("gfriends:8-GRAPHIS/別人.jpg", "gfriends:../../etc/passwd",
                    "https://evil.example/a.jpg", "sha256:" + "0" * 64, ""):
            with self.assertRaises(avatar_picker.PickerError, msg=bad):
                avatar_picker.resolve(bad, self.connection, self.providers, 7792,
                                      transport_of(picture()))

    def test_an_upstream_error_reads_as_a_failure_not_a_picture(self):
        with self.assertRaises(avatar_picker.PickerError):
            avatar_picker.resolve(LIBRARY_REF, self.connection, self.providers,
                                  7792, transport_of(b"", status=404))

    def test_without_a_transport_an_uncached_candidate_says_so(self):
        with self.assertRaises(avatar_picker.PickerError):
            avatar_picker.resolve(LIBRARY_REF, self.connection, self.providers,
                                  7792, None)

    def test_a_remembered_picture_comes_back_without_the_network(self):
        body = picture(colour="blue")
        digest = self.remember(body)
        got, origin = avatar_picker.resolve(f"sha256:{digest}", self.connection,
                                            self.providers, 7792, None)
        self.assertEqual(got, body)
        self.assertEqual(origin["provider"], "history")


class InstallTests(PickerFixture):
    def test_installing_writes_the_four_files_and_keeps_the_evidence(self):
        body = picture(colour="purple")
        result = avatar_picker.install(
            self.providers, self.avatars, "performer", 7792, body,
            {"source": "avatar picker", "provider": "upload", "external_id": "a.jpg"})
        target = self.avatars / "performer-7792.img"
        self.assertEqual(target.read_bytes(), body)
        self.assertEqual(Path(f"{target}.ct").read_text(encoding="utf-8"),
                         "image/jpeg")
        record = json.loads(Path(f"{target}.provenance.json").read_text("utf-8"))
        self.assertEqual(record["provider"], "upload")
        self.assertEqual(record["sha256"], result["sha256"])
        self.assertTrue(record["imported_at"])
        evidence = list(self.providers.glob("upload/evidence/performer-7792-*.json"))
        self.assertEqual(len(evidence), 1)
        self.assertEqual(json.loads(evidence[0].read_text("utf-8"))["source_kind"],
                         "user_selected")

    def test_the_replaced_picture_stays_reachable_as_history(self):
        """被顶下来的那张不删不搬：换回去只是再装一次，不重新取。"""
        first = picture(colour="orange")
        digest = inspect_avatar(first).sha256
        avatar_picker.install(self.providers, self.avatars, "performer", 7792,
                              first, {"provider": "upload"})
        avatar_picker.install(self.providers, self.avatars, "performer", 7792,
                              picture(colour="teal"), {"provider": "upload"})
        refs = {one["ref"] for one in self.listed()["choices"]
                if one["source"] == "history"}
        self.assertIn(f"sha256:{digest}", refs)
        back, _ = avatar_picker.resolve(f"sha256:{digest}", self.connection,
                                        self.providers, 7792, None)
        self.assertEqual(back, first)

    def test_a_stale_face_box_never_survives_a_swap(self):
        """留着上一张图的脸框，页面会按它给新图取景，放大到一个空位置上。"""
        target = self.avatars / "performer-7792.img"
        sidecar = sidecar_path(target)
        sidecar.write_text('{"focus": {}}', encoding="utf-8")
        avatar_picker.install(self.providers, self.avatars, "performer", 7792,
                              picture(), {"provider": "upload"})
        self.assertFalse(sidecar.exists())

    def test_a_face_that_is_found_lands_beside_the_new_picture(self):
        self.face.return_value.return_value = {"focus": {"x": 0.5, "y": 0.4}}
        avatar_picker.install(self.providers, self.avatars, "performer", 7792,
                              picture(), {"provider": "upload"})
        sidecar = sidecar_path(self.avatars / "performer-7792.img")
        self.assertEqual(json.loads(sidecar.read_text("utf-8"))["focus"]["y"], 0.4)

    def test_what_is_not_a_picture_never_reaches_the_avatar_tree(self):
        with self.assertRaises(avatar_picker.PickerError):
            avatar_picker.install(self.providers, self.avatars, "performer", 7792,
                                  b"not an image", {"provider": "upload"})
        self.assertFalse((self.avatars / "performer-7792.img").exists())


@unittest.skipUnless(HAS_DEPS, "FastAPI/httpx 尚未安装")
class AvatarPickerRouteTests(unittest.TestCase):
    """三个端点：列出候选、取候选的预览图、换上去。"""

    def setUp(self):
        from fastapi.testclient import TestClient
        from peach.api import create_app
        from peach.config import PeachSettings

        self.folder = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.folder, True)
        self.candidates = self.folder / "generated"
        self.avatars = self.folder / "avatars"
        self.avatars.mkdir(parents=True)
        self.providers = self.candidates / "provider-cache" / "performer-avatars"
        seed_library(self.providers)
        database = fresh_ledger(self.folder)
        seed_person(database)
        self.face = mock.patch("peach.avatar_provider.FaceProbe").start()
        self.face.return_value.return_value = None
        self.addCleanup(mock.patch.stopall)
        self.app = create_app(PeachSettings(
            db_path=database, configured=True, token="secret",
            avatar_root=self.avatars, candidate_root=self.candidates))
        self.picture = picture(colour="navy")
        self.app.state.http_transport = transport_of(self.picture)
        self.client = TestClient(self.app)
        self.addCleanup(self.client.close)

    def test_the_choices_endpoint_needs_the_token(self):
        self.assertEqual(
            self.client.get("/api/avatar-choices?kind=performer&id=7792").status_code,
            401)

    def test_the_choices_endpoint_lists_the_library_candidates(self):
        out = self.client.get(
            "/api/avatar-choices?kind=performer&id=7792&t=secret").json()
        self.assertEqual(out["matched_names"], ["葵つかさ"])
        self.assertIn(LIBRARY_REF, [one["ref"] for one in out["choices"]])

    def test_a_preview_serves_the_picture_and_a_bad_reference_404s(self):
        response = self.client.get(
            "/avatar-choice", params={"kind": "performer", "id": 7792,
                                      "ref": LIBRARY_REF, "t": "secret"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "image/jpeg")
        self.assertEqual(response.content, self.picture)
        missing = self.client.get(
            "/avatar-choice", params={"id": 7792, "ref": "gfriends:8-GRAPHIS/別人.jpg",
                                      "t": "secret"})
        self.assertEqual(missing.status_code, 404)

    def test_picking_a_library_candidate_installs_it(self):
        response = self.client.post("/api/avatar-pick?t=secret",
                                    json={"kind": "performer", "id": 7792,
                                          "ref": LIBRARY_REF})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["sha256"],
                         inspect_avatar(self.picture).sha256)
        self.assertEqual((self.avatars / "performer-7792.img").read_bytes(),
                         self.picture)

    def test_a_file_from_this_machine_arrives_as_the_request_body(self):
        body = picture(colour="olive")
        response = self.client.post(
            "/api/avatar-pick?id=7792&kind=performer&name=me.jpg&t=secret",
            content=body, headers={"content-type": "image/jpeg"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual((self.avatars / "performer-7792.img").read_bytes(), body)

    def test_a_typed_address_is_checked_before_peach_goes_and_fetches_it(self):
        refused = self.client.post("/api/avatar-pick?t=secret",
                                   json={"id": 7792, "url": "http://169.254.169.254/a.jpg"})
        self.assertEqual(refused.status_code, 400)
        self.assertFalse((self.avatars / "performer-7792.img").exists())
        with mock.patch.object(peach_http, "host_addresses",
                               return_value=("93.184.216.34",)):
            accepted = self.client.post(
                "/api/avatar-pick?t=secret",
                json={"id": 7792, "url": "https://example.com/a.jpg"})
        self.assertEqual(accepted.status_code, 200)
        self.assertEqual((self.avatars / "performer-7792.img").read_bytes(),
                         self.picture)

    def test_a_request_without_a_picture_or_an_id_is_refused(self):
        for payload in ({"id": 7792}, {"ref": LIBRARY_REF}, {"id": 0}):
            response = self.client.post("/api/avatar-pick?t=secret", json=payload)
            self.assertEqual(response.status_code, 400, str(payload))
        self.assertFalse((self.avatars / "performer-7792.img").exists())


if __name__ == "__main__":
    unittest.main()
