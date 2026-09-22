import unittest

from classcale.social.agent_config import LLMConfig
from classcale.social.llm_planner import OllamaPlanner


class PlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        config = LLMConfig(
            enabled=True,
            endpoint="http://127.0.0.1:11434",
            model="test",
            max_queries=2,
            timeout_seconds=10,
        )
        self.planner = OllamaPlanner(
            config,
            ("bitcoin hack", "ethereum outage"),
            ("secgov", "ethereum"),
        )

    def test_validates_and_bounds_llm_plan(self) -> None:
        plan = self.planner.validate(
            {
                "queries": [
                    "bitcoin ETF approval",
                    "https://evil.example/crypto",
                    "celebrity gossip",
                    "ethereum exploit",
                    "solana outage",
                ],
                "accounts": ["@SECGov", "unknown", "ethereum"],
                "reason": "Recherche des annonces factuelles",
            }
        )
        self.assertEqual(("bitcoin ETF approval", "ethereum exploit"), plan.queries)
        self.assertEqual(("secgov", "ethereum"), plan.accounts)
        self.assertTrue(plan.generated_by_llm)

    def test_falls_back_when_queries_are_invalid(self) -> None:
        plan = self.planner.validate(
            {"queries": ["javascript:alert(1)"], "accounts": ["unknown"], "reason": "x"}
        )
        self.assertEqual(("bitcoin hack", "ethereum outage"), plan.queries)
        self.assertEqual(("secgov", "ethereum"), plan.accounts)


if __name__ == "__main__":
    unittest.main()

