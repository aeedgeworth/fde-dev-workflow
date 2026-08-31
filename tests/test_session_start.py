from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "plugins" / "fde" / "hooks"))

import session_start  # noqa: E402


class SessionStartTests(unittest.TestCase):
    def test_cursor_adapter_emits_additional_context_json(self) -> None:
        for host_environment in (
            {"FDE_HOOK_HOST": "cursor"},
            {"CURSOR_VERSION": "3.17.21"},
        ):
            with self.subTest(host_environment=host_environment):
                with tempfile.TemporaryDirectory() as raw:
                    spec = Path(raw) / "001-example"
                    spec.mkdir()
                    (spec / "PLAN.md").write_text(
                        "- [x] **T1** First outcome\n- [ ] **T2** Next outcome\n",
                        encoding="utf-8",
                    )
                    output = io.StringIO()

                    with (
                        patch.object(
                            session_start, "store_dir", return_value=Path(raw)
                        ),
                        patch.object(
                            session_start, "active_spec_dirs", return_value=[spec]
                        ),
                        patch.dict(os.environ, host_environment, clear=True),
                        redirect_stdout(output),
                    ):
                        self.assertEqual(session_start.main(), 0)

                    payload = json.loads(output.getvalue())
                    self.assertIn(
                        "Active spec: 001-example", payload["additional_context"]
                    )
                    self.assertIn(
                        "Next task: **T2** Next outcome",
                        payload["additional_context"],
                    )

    def test_claude_adapter_emits_plain_text(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            spec = Path(raw) / "001-example"
            spec.mkdir()
            (spec / "PLAN.md").write_text(
                "- [ ] **T1** Next outcome\n", encoding="utf-8"
            )
            output = io.StringIO()

            with (
                patch.object(session_start, "store_dir", return_value=Path(raw)),
                patch.object(session_start, "active_spec_dirs", return_value=[spec]),
                patch.dict(os.environ, {}, clear=True),
                redirect_stdout(output),
            ):
                self.assertEqual(session_start.main(), 0)

            self.assertTrue(output.getvalue().startswith("Active spec: 001-example"))


if __name__ == "__main__":
    unittest.main()
