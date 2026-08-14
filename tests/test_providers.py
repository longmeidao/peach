import unittest

from peach.providers import (
    ProviderCapabilities, ProviderKind, ProviderRegistry, ProviderStatus,
    default_registry,
)


class ProviderRegistryTests(unittest.TestCase):
    def test_default_health_is_passive_and_deterministic(self):
        registry = default_registry(lambda name: f"C:/tools/{name}.exe" if name == "codex" else None)
        health = registry.health()
        by_id = {item["id"]: item for item in health["providers"]}

        self.assertEqual(set(by_id), {
            "opencode-go", "codex-local", "claude-code-local-personal",
        })
        self.assertTrue(by_id["opencode-go"]["available"])
        self.assertTrue(by_id["codex-local"]["available"])
        self.assertFalse(by_id["claude-code-local-personal"]["available"])
        self.assertTrue(by_id["claude-code-local-personal"]["experimental"])
        for item in health["providers"]:
            self.assertEqual(set(item), {
                "id", "kind", "provider", "auth_mode", "available", "configured",
                "experimental", "capabilities", "note",
            })
            self.assertNotIn("secret_ref", item)
            self.assertNotIn("executable", item)

    def test_duplicate_provider_id_is_rejected(self):
        registry = ProviderRegistry()
        status = ProviderStatus(
            id="one", kind=ProviderKind.INFERENCE, provider="test",
            auth_mode="none", available=True, configured=True, experimental=False,
            capabilities=ProviderCapabilities(),
        )
        registry.register(status)
        with self.assertRaisesRegex(ValueError, "duplicate provider id"):
            registry.register(status)


if __name__ == "__main__":
    unittest.main()
