import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from classcale.social.agent_config import BrowserAgentConfig


class AgentConfigTests(unittest.TestCase):
    def test_rejects_unbounded_browser_cycle(self) -> None:
        with TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(
                json.dumps(
                    {
                        "poll_interval_seconds": 300,
                        "browser": {"max_pages_per_cycle": 99},
                        "seed_queries": ["bitcoin hack"],
                        "sources": [
                            {"username": "SECGov", "tier": "regulator", "score": 5}
                        ],
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaises(ValueError):
                BrowserAgentConfig.load(path)


if __name__ == "__main__":
    unittest.main()

