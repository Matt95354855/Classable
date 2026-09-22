import unittest

from classcale.social.x_browser import XBrowser, parse_status_url


class BrowserParsingTests(unittest.TestCase):
    def test_parses_status_url(self) -> None:
        self.assertEqual(
            ("ethereum", "123456"),
            parse_status_url("https://x.com/ethereum/status/123456"),
        )

    def test_rejects_non_status_url(self) -> None:
        self.assertIsNone(parse_status_url("https://x.com/explore"))

    def test_normalizes_visible_tweet(self) -> None:
        post = XBrowser._normalize(
            {
                "statusUrl": "https://x.com/ethereum/status/123456",
                "text": " Ethereum   network upgrade ",
                "lang": "en",
                "createdAt": "2026-09-22T10:00:00Z",
                "verified": True,
            },
            "ethereum upgrade",
        )
        self.assertIsNotNone(post)
        assert post is not None
        self.assertEqual("ethereum", post.author)
        self.assertEqual("Ethereum network upgrade", post.text)
        self.assertTrue(post.verified)


if __name__ == "__main__":
    unittest.main()

