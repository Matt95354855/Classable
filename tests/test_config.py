import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from classcale.social.config import CollectorConfig, Source, build_source_queries


class ConfigTests(unittest.TestCase):
    def test_source_query_batching(self) -> None:
        sources = tuple(Source(f"source{index}", "media", 3) for index in range(10))
        queries = build_source_queries(sources, batch_size=4)
        self.assertEqual(3, len(queries))
        self.assertIn("from:source0", queries[0])
        self.assertIn("-filter:replies", queries[0])

    def test_rejects_too_fast_polling(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "poll_interval_seconds": 10,
                        "sources": [{"username": "source", "tier": "media", "score": 3}],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                CollectorConfig.load(path)


if __name__ == "__main__":
    unittest.main()

