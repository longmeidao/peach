import json
import unittest

from peach.follow import FollowSourceError
from peach.follow_avatar import resolve_official_avatar, resolve_official_profile
from peach.http import HttpResponse


class _Transport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.requests = []

    def __call__(self, request, _timeout, _max_bytes):
        self.requests.append(request)
        return self.responses.pop(0)


class OfficialAvatarTests(unittest.TestCase):
    def _responses(self, *, user_id="30917150",
                   icon="https://pixiv.pximg.net/c/160x160/icon.jpeg"):
        metadata = {"urlContext": {"host": {"creatorId": "lazyprocrast"}}}
        page = (
            "<html><meta name='metadata' content='"
            + json.dumps(metadata).replace("'", "&#39;")
            + "'></html>"
        ).encode()
        api = json.dumps({"body": {"user": {
            "userId": user_id, "name": "LazyProcrastinator", "iconUrl": icon,
        }}}).encode()
        return [HttpResponse(200, {"content-type": "text/html"}, page),
                HttpResponse(200, {"content-type": "application/json"}, api)]

    def test_fanbox_avatar_comes_from_the_official_creator_profile(self):
        transport = _Transport(self._responses())
        avatar = resolve_official_avatar("fanbox", "30917150", transport=transport)
        self.assertEqual(avatar, "https://pixiv.pximg.net/c/160x160/icon.jpeg")
        self.assertEqual(transport.requests[0].url,
                         "https://www.pixiv.net/fanbox/creator/30917150")
        self.assertIn("creatorId=lazyprocrast", transport.requests[1].url)
        self.assertEqual(transport.requests[1].headers["Origin"],
                         "https://lazyprocrast.fanbox.cc")

    def test_the_same_verified_lookup_returns_the_official_profile(self):
        profile = resolve_official_profile(
            "fanbox", "30917150", transport=_Transport(self._responses()))
        self.assertEqual(profile.creator_id, "lazyprocrast")
        self.assertEqual(profile.name, "LazyProcrastinator")
        self.assertEqual(profile.url, "https://lazyprocrast.fanbox.cc/")

    def test_the_official_api_must_return_the_requested_user(self):
        with self.assertRaises(FollowSourceError):
            resolve_official_avatar(
                "fanbox", "30917150", transport=_Transport(
                    self._responses(user_id="999")))

    def test_the_avatar_cannot_redirect_to_an_untrusted_host(self):
        with self.assertRaises(FollowSourceError):
            resolve_official_avatar(
                "fanbox", "30917150", transport=_Transport(
                    self._responses(icon="https://example.test/avatar.jpg")))

    def test_only_verified_fanbox_identities_are_accepted(self):
        for service, user in (("patreon", "30917150"), ("fanbox", "../secret"),
                              ("fanbox", "")):
            with self.assertRaises(FollowSourceError):
                resolve_official_avatar(service, user, transport=_Transport([]))

    def test_a_creator_id_skips_the_lookup_page(self):
        """论坛名片上只有 `jul3dnsfw.fanbox.cc` 这一个身份，没有 pixiv 的数字 id。

        `creator.get` 本来就收创作者 id，那一步换算可以省掉。
        """
        transport = _Transport(self._responses()[1:])
        avatar = resolve_official_avatar("fanbox", "lazyprocrast",
                                         transport=transport)
        self.assertEqual(avatar, "https://pixiv.pximg.net/c/160x160/icon.jpeg")
        self.assertEqual(len(transport.requests), 1)
        self.assertIn("creatorId=lazyprocrast", transport.requests[0].url)

    def test_a_creator_id_still_needs_a_real_user_behind_it(self):
        # 没有可核对的数字 id 时，身份以官方资料回的为准；回不出就是没有头像。
        with self.assertRaises(FollowSourceError):
            resolve_official_avatar("fanbox", "lazyprocrast", transport=_Transport(
                self._responses(user_id="")[1:]))


if __name__ == "__main__":
    unittest.main()
