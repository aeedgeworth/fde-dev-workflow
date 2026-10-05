from __future__ import annotations

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugins" / "fde"


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


class ManifestTests(unittest.TestCase):
    def test_host_manifests_have_the_same_identity_and_version(self) -> None:
        manifests = (
            load_json(PLUGIN / ".claude-plugin" / "plugin.json"),
            load_json(PLUGIN / ".codex-plugin" / "plugin.json"),
            load_json(PLUGIN / ".cursor-plugin" / "plugin.json"),
        )

        self.assertEqual({manifest["name"] for manifest in manifests}, {"fde"})
        versions = {str(manifest["version"]).split("+", 1)[0] for manifest in manifests}
        self.assertEqual(versions, {"0.3.0"})
        self.assertRegex(
            str(manifests[1]["version"]), r"^0\.3\.0\+codex\.\d{14}$"
        )

    def test_cursor_manifest_resolves_every_declared_component(self) -> None:
        manifest = load_json(PLUGIN / ".cursor-plugin" / "plugin.json")

        for field in ("skills", "commands", "hooks"):
            relative = manifest[field]
            self.assertIsInstance(relative, str)
            resolved = PLUGIN / relative
            self.assertTrue(resolved.exists(), f"missing Cursor {field}: {resolved}")

        hooks = load_json(PLUGIN / str(manifest["hooks"]))
        self.assertEqual(hooks["version"], 1)
        self.assertEqual(
            set(hooks["hooks"]), {"sessionStart", "beforeShellExecution"}
        )

    def test_marketplaces_resolve_the_plugin_directory(self) -> None:
        claude = load_json(ROOT / ".claude-plugin" / "marketplace.json")
        cursor = load_json(ROOT / ".cursor-plugin" / "marketplace.json")

        self.assertEqual(claude["name"], "adam-fde")
        self.assertEqual(cursor["name"], "adam-fde")
        self.assertEqual(claude["plugins"][0]["source"], "./plugins/fde")
        self.assertEqual(cursor["metadata"]["pluginRoot"], "plugins")
        self.assertEqual(cursor["plugins"][0]["source"], "fde")


if __name__ == "__main__":
    unittest.main()
