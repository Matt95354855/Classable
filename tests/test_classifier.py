from datetime import UTC, datetime
import unittest

from classcale.social.classifier import EventClassifier
from classcale.social.config import Source
from classcale.social.models import RawPost


def post(text: str, author: str = "ethereum", verified: bool = True) -> RawPost:
    now = datetime.now(UTC).isoformat()
    return RawPost(
        post_id="1",
        url="https://x.com/ethereum/status/1",
        author=author,
        text=text,
        created_at=now,
        collected_at=now,
        verified=verified,
    )


class ClassifierTests(unittest.TestCase):
    def setUp(self) -> None:
        sources = {"ethereum": Source("ethereum", "protocol", 4)}
        self.classifier = EventClassifier(sources, min_score=7)

    def test_keeps_official_security_event(self) -> None:
        event = self.classifier.classify(post("Ethereum client vulnerability and upgrade announced"))
        self.assertIsNotNone(event)
        assert event is not None
        self.assertIn("ETH", event.assets)
        self.assertIn("security_incident", event.event_types)
        self.assertGreaterEqual(event.score, 7)

    def test_rejects_non_event_commentary(self) -> None:
        self.assertIsNone(self.classifier.classify(post("Ethereum is interesting today")))

    def test_rejects_unverified_promotion(self) -> None:
        value = post("Guaranteed 100x bitcoin giveaway", author="random", verified=False)
        self.assertIsNone(self.classifier.classify(value))

    def test_rejects_unrelated_event(self) -> None:
        self.assertIsNone(self.classifier.classify(post("A network outage affected city trains")))

    def test_does_not_confuse_french_sol_with_solana(self) -> None:
        self.assertIsNone(self.classifier.classify(post("Incident au sol pendant une panne")))


if __name__ == "__main__":
    unittest.main()
