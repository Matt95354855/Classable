from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from classcale.social.models import CryptoEvent
from classcale.social.store import EventStore


def event() -> CryptoEvent:
    now = datetime.now(UTC).isoformat()
    return CryptoEvent(
        post_id="123",
        url="https://x.com/source/status/123",
        author="source",
        text="Bitcoin network upgrade",
        created_at=now,
        collected_at=now,
        language="en",
        verified=True,
        source_tier="protocol",
        source_score=4,
        event_types=("network_change",),
        assets=("BTC",),
        score=8,
        severity=3,
        content_hash="abc123",
    )


class StoreTests(unittest.TestCase):
    def test_deduplicates_events(self) -> None:
        with TemporaryDirectory() as directory:
            store = EventStore(Path(directory) / "events.db")
            self.assertTrue(store.insert(event()))
            self.assertFalse(store.insert(event()))
            self.assertEqual(1, store.count())
            self.assertEqual("123", store.latest(1)[0]["post_id"])


if __name__ == "__main__":
    unittest.main()
