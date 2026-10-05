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

TEMPLATES = ROOT / "plugins" / "fde" / "templates"


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

    def test_check_rejects_unfilled_templates(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = Path(raw)
            for name in ("SPEC.md", "PLAN.md"):
                (spec / name).write_text(
                    (TEMPLATES / name).read_text(encoding="utf-8"), encoding="utf-8"
                )

            errors, _ = spec_store.check_spec(spec)

            self.assertTrue(any("unfilled template text" in error for error in errors))
            self.assertTrue(any("AC1 has no statement" in error for error in errors))

    def test_check_passes_a_traceable_spec(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = self._traceable_spec(Path(raw))

            self.assertEqual(spec_store.check_spec(spec), ([], []))

    def test_check_reports_uncovered_and_undefined_criteria(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = self._traceable_spec(Path(raw))
            (spec / "PLAN.md").write_text(
                "- [ ] **T1** Load orders\n  - covers: AC1, AC3\n  - verify: `pytest`\n",
                encoding="utf-8",
            )

            errors, _ = spec_store.check_spec(spec)

            self.assertEqual(
                errors,
                [
                    "PLAN.md: T1 covers AC3, which SPEC.md does not define",
                    "PLAN.md: no task covers AC2",
                ],
            )

    def test_check_warns_on_unbounded_spike_and_unverified_task(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = self._traceable_spec(Path(raw))
            (spec / "PLAN.md").write_text(
                "- [ ] **T1** Spike: can the API sustain 50 rps?\n"
                "- [ ] **T2** Load orders\n  - covers: AC1, AC2\n",
                encoding="utf-8",
            )

            errors, warnings = spec_store.check_spec(spec)

            self.assertEqual(errors, [])
            self.assertEqual(
                warnings,
                ["PLAN.md: spike T1 has no timebox", "PLAN.md: T2 has no verify step"],
            )

    def test_fields_after_unindented_prose_do_not_attach_to_a_task(self) -> None:
        plan = (
            "- [ ] **T1** Load orders\n  - covers: AC1\n"
            "When complete, add:\n  - done: 2026-01-01 · abc123\n"
        )

        tasks = spec_store.parse_tasks(plan)

        self.assertEqual(tasks, [{"id": "T1", "title": "Load orders", "fields": {"covers": "AC1"}}])

    @staticmethod
    def _traceable_spec(directory: Path) -> Path:
        (directory / "SPEC.md").write_text(
            "## Acceptance criteria\n\n"
            "- [ ] AC1 Orders land daily by 06:00\n"
            "- [ ] AC2 Totals match finance within 0.1%\n",
            encoding="utf-8",
        )
        (directory / "PLAN.md").write_text(
            "- [ ] **T1** Spike: confirm the source grain\n  - timebox: 1 hour\n"
            "- [ ] **T2** Load orders\n  - covers: AC1\n  - verify: `pytest tests/test_load.py`\n"
            "- [x] **T3** Reconcile totals\n  - covers: AC2\n  - verify: `pytest tests/test_totals.py`\n"
            "  - done: 2026-10-04 · uncommitted\n",
            encoding="utf-8",
        )
        return directory

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
