from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "fde" / "hooks"))

from unittest import mock  # noqa: E402

sys.path.insert(0, str(ROOT / "plugins" / "fde" / "scripts"))

import guard  # noqa: E402
import spec_store  # noqa: E402


class GuardTests(unittest.TestCase):
    def test_blocks_explicit_production_targets(self) -> None:
        cwd = ROOT
        blocked = (
            "databricks bundle deploy --target=prod",
            "databricks bundle run job -t production",
            "terraform -chdir=prod apply",
            "terraform destroy -var-file production.tfvars",
        )
        for command in blocked:
            with self.subTest(command=command):
                self.assertIsNotNone(guard.blocked_reason(command, cwd))

    def test_allows_dev_targets_and_force_with_lease(self) -> None:
        cwd = ROOT
        allowed = (
            "databricks bundle deploy --target dev",
            "terraform -chdir=dev apply",
            "git push --force-with-lease origin feature/example",
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command, cwd))

    def test_blocks_implicit_push_from_default_branch(self) -> None:
        for default_branch in ("main", "master"):
            with self.subTest(default_branch=default_branch):
                with tempfile.TemporaryDirectory() as raw:
                    repo = Path(raw)
                    self._git(repo, "init", "-b", default_branch)
                    self._git(repo, "config", "user.email", "test@example.com")
                    self._git(repo, "config", "user.name", "Test User")
                    (repo / "README.md").write_text("test\n", encoding="utf-8")
                    self._git(repo, "add", "README.md")
                    self._git(repo, "commit", "-m", "initial")

                    self.assertIsNotNone(
                        guard.blocked_reason("git push origin HEAD", repo)
                    )
                    self.assertIsNotNone(guard.blocked_reason("git push", repo))
                    self.assertIsNotNone(
                        guard.blocked_reason(
                            f"git push origin {default_branch}", repo
                        )
                    )
                    self.assertIsNotNone(
                        guard.blocked_reason(
                            f"git push origin HEAD:{default_branch}", repo
                        )
                    )
                    self.assertIsNone(
                        guard.blocked_reason("git push origin feature/example", repo)
                    )

    def test_branch_names_containing_default_branch_words_are_allowed(self) -> None:
        allowed = (
            "git push origin feat/master-data-load",
            "git push origin fix/main-ingest-bug",
            "git push origin feat/trunk-metrics",
        )
        for command in allowed:
            with self.subTest(command=command):
                self.assertIsNone(guard.blocked_reason(command, ROOT))

    def test_protects_main_and_master_when_remote_default_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            repo = Path(raw)
            self._git(repo, "init", "-b", "main")
            self._git(repo, "config", "user.email", "test@example.com")
            self._git(repo, "config", "user.name", "Test User")
            (repo / "README.md").write_text("test\n", encoding="utf-8")
            self._git(repo, "add", "README.md")
            self._git(repo, "commit", "-m", "initial")
            self._git(repo, "branch", "master")

            self.assertIsNotNone(guard.blocked_reason("git push origin main", repo))
            self.assertIsNotNone(guard.blocked_reason("git push origin master", repo))

            self._git(repo, "switch", "master")
            self.assertIsNotNone(guard.blocked_reason("git push", repo))

    def test_one_command_override_is_loud_and_allowed(self) -> None:
        payload = json.dumps(
            {
                "cwd": str(ROOT),
                "tool_input": {
                    "command": "FDE_GUARD_OVERRIDE=1 git push origin master"
                },
            }
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "plugins" / "fde" / "hooks" / "guard.py")],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0)
        self.assertIn("OVERRIDDEN", result.stderr)

    def test_override_applies_to_only_one_shell_segment(self) -> None:
        payload = json.dumps(
            {
                "cwd": str(ROOT),
                "tool_input": {
                    "command": (
                        "FDE_GUARD_OVERRIDE=1 git push origin master && "
                        "databricks bundle deploy --target=prod"
                    )
                },
            }
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "plugins" / "fde" / "hooks" / "guard.py")],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("OVERRIDDEN", result.stderr)
        self.assertIn("blocked", result.stderr)

    def test_blocks_force_but_allows_force_with_lease(self) -> None:
        self.assertIsNotNone(guard.blocked_reason("git push --force origin topic", ROOT))
        self.assertIsNotNone(guard.blocked_reason("git push -f origin topic", ROOT))
        self.assertIsNone(
            guard.blocked_reason("git push --force-with-lease origin topic", ROOT)
        )

    def test_cursor_before_shell_payload_uses_top_level_command(self) -> None:
        payload = json.dumps(
            {
                "cwd": str(ROOT),
                "command": "databricks bundle deploy --target=prod",
                "sandbox": False,
            }
        )
        result = subprocess.run(
            [sys.executable, str(ROOT / "plugins" / "fde" / "hooks" / "guard.py")],
            input=payload,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("blocked", result.stderr)

    def test_payload_helpers_accept_claude_and_cursor_shapes(self) -> None:
        claude = {
            "cwd": "/repo",
            "tool_input": {"command": "git push origin topic"},
        }
        cursor = {
            "cwd": "/repo",
            "command": "git push origin topic",
            "sandbox": False,
        }
        self.assertEqual(guard.payload_command(claude), "git push origin topic")
        self.assertEqual(guard.payload_command(cursor), "git push origin topic")
        self.assertEqual(guard.payload_cwd(claude), Path("/repo"))
        self.assertEqual(guard.payload_cwd(cursor), Path("/repo"))
        self.assertEqual(guard.payload_command({"tool_input": "not-a-dict"}), "")

    @staticmethod
    def _git(repo: Path, *args: str) -> None:
        subprocess.run(
            ["git", *args],
            cwd=repo,
            capture_output=True,
            text=True,
            check=True,
        )


class SingleWorkspaceTests(unittest.TestCase):
    """A prod-named target is ordinary work when the engagement has one workspace."""

    def _with_config(self, body: str | None):
        """Point the spec store at a temp dir optionally holding an fde.toml."""
        tmp = tempfile.TemporaryDirectory()
        store = Path(tmp.name)
        if body is not None:
            (store / "fde.toml").write_text(body, encoding="utf-8")
        patcher = mock.patch.object(guard, "_single_workspace", wraps=guard._single_workspace)
        return tmp, store, patcher

    def test_prod_target_blocked_by_default(self) -> None:
        with mock.patch.object(spec_store, "store_dir", return_value=Path(tempfile.mkdtemp())):
            self.assertIsNotNone(
                guard.blocked_reason("databricks bundle deploy --target prod", ROOT)
            )

    @unittest.skipIf(sys.version_info < (3, 11), "fde.toml needs tomllib (Python 3.11+)")
    def test_prod_target_allowed_when_single_workspace_declared(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw)
            (store / "fde.toml").write_text(
                "[safety]\nsingle_workspace = true\n", encoding="utf-8"
            )
            with mock.patch.object(spec_store, "store_dir", return_value=store):
                for command in (
                    "databricks bundle deploy --target prod",
                    "databricks bundle run etl --target production",
                ):
                    with self.subTest(command=command):
                        self.assertIsNone(guard.blocked_reason(command, ROOT))

    def test_destroy_still_blocked_when_single_workspace_declared(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw)
            (store / "fde.toml").write_text(
                "[safety]\nsingle_workspace = true\n", encoding="utf-8"
            )
            with mock.patch.object(spec_store, "store_dir", return_value=store):
                self.assertIsNotNone(guard.blocked_reason("databricks bundle destroy", ROOT))

    def test_unreadable_config_falls_back_to_strict(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            store = Path(raw)
            (store / "fde.toml").write_text("this is not = valid = toml [", encoding="utf-8")
            with mock.patch.object(spec_store, "store_dir", return_value=store):
                self.assertIsNotNone(
                    guard.blocked_reason("databricks bundle deploy --target prod", ROOT)
                )

    def test_safe_commands_never_consult_the_config(self) -> None:
        """The common path must not pay for a store lookup on every command."""
        with mock.patch.object(guard, "_single_workspace") as lookup:
            self.assertIsNone(guard.blocked_reason("pytest tests/", ROOT))
            self.assertIsNone(guard.blocked_reason("ls -la", ROOT))
            lookup.assert_not_called()


if __name__ == "__main__":
    unittest.main()
