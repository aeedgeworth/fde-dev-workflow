from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "fde" / "scripts"))

import spec_store  # noqa: E402


class SpecStoreTests(unittest.TestCase):
    def test_remote_forms_share_a_key_and_strip_credentials_and_ports(self) -> None:
        expected = "github.com/owner/repo"
        self.assertEqual(spec_store._normalize_remote("git@github.com:owner/repo.git"), expected)
        self.assertEqual(
            spec_store._normalize_remote("https://token@github.com:443/owner/repo.git"),
            expected,
        )

    def test_read_only_store_lookup_does_not_create_directories(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw) / "state"
            with (
                mock.patch.object(spec_store, "store_root", return_value=root),
                mock.patch.object(spec_store, "repo_key", return_value="example"),
            ):
                path = spec_store.store_dir()
                self.assertFalse(path.exists())
                self.assertEqual(
                    spec_store.store_dir(create=True), root / "specs" / "example"
                )
                self.assertTrue(path.is_dir())

    def test_active_specs_exclude_terminal_statuses(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            active = self._make_spec(directory, "001-active", "active")
            shipped = self._make_spec(directory, "002-shipped", "shipped")
            os.utime(active / "SPEC.md", (20, 20))
            os.utime(shipped / "SPEC.md", (30, 30))

            self.assertEqual(spec_store.active_spec_dirs(directory), [active])

    def test_resolve_prefers_exact_id_or_slug_and_rejects_ambiguity(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            first = self._make_spec(directory, "001-schema-guard", "draft")
            self._make_spec(directory, "002-schema-report", "draft")

            self.assertEqual(spec_store.resolve_spec(directory, "001"), first)
            self.assertEqual(spec_store.resolve_spec(directory, "schema-guard"), first)
            with self.assertRaisesRegex(SystemExit, "ambiguous"):
                spec_store.resolve_spec(directory, "schema")

    def test_create_spec_increments_ids_and_limits_slug_length(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            directory = Path(raw)
            first = spec_store.create_spec(directory, "One two three four five six seven")
            second = spec_store.create_spec(directory, "Another")

            self.assertEqual(first.name, "001-one-two-three-four-five-six")
            self.assertEqual(second.name, "002-another")

    @staticmethod
    def _make_spec(directory: Path, name: str, status: str) -> Path:
        spec = directory / name
        spec.mkdir()
        (spec / "SPEC.md").write_text(
            f"---\nstatus: {status}\n---\n", encoding="utf-8"
        )
        (spec / "PLAN.md").write_text("- [ ] **T1** work\n", encoding="utf-8")
        return spec


if __name__ == "__main__":
    unittest.main()
