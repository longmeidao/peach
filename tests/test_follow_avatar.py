import json
import unittest

from peach.follow import FollowSourceError
from peach.follow_avatar import resolve_official_avatar
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
            "userId": user_id, "iconUrl": icon,
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

    def test_only_verified_fanbox_numeric_ids_are_accepted(self):
        for service, user in (("patreon", "30917150"), ("fanbox", "../secret")):
            with self.assertRaises(FollowSourceError):
                resolve_official_avatar(service, user, transport=_Transport([]))


if __name__ == "__main__":
    unittest.main()
