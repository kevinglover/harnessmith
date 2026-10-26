"""Harmless shell/filesystem controls, not model instruction-compliance tests."""

import hashlib
import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


def inventory(workspace):
    return {
        p.relative_to(workspace).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in workspace.rglob("*") if p.is_file()
    }


class WorkflowDiscoveryV5Tests(unittest.TestCase):
    @unittest.skipUnless(shutil.which("rg"), "local discovery control requires rg")
    def test_scoped_hidden_discovery_finds_config_and_supplied_adapter_without_writes(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            expected = {
                ".specify/extensions.yml": "hooks: {}\n",
                ".specify/memory/constitution.md": "# Project principles\n",
                ".pilot/adapter.md": "# Local command integration\n",
            }
            for name, content in expected.items():
                path = workspace / name
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(content)
            (workspace / "specs").mkdir()
            (workspace / "specs/spec.md").write_text("# Feature\n")
            before = inventory(workspace)
            ordinary = subprocess.run(
                [shutil.which("rg"), "--files", "."], cwd=workspace,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, ordinary.returncode, ordinary.stderr)
            self.assertNotIn(".specify/extensions.yml", ordinary.stdout)
            self.assertNotIn(".pilot/adapter.md", ordinary.stdout)
            hidden = subprocess.run(
                [shutil.which("rg"), "--files", "--hidden", ".specify", ".pilot"],
                cwd=workspace, capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, hidden.returncode, hidden.stderr)
            self.assertEqual(set(expected), set(hidden.stdout.splitlines()))
            self.assertEqual(before, inventory(workspace))

    def test_direct_known_path_check_distinguishes_absent_empty_and_present_config(self):
        for state in ("absent", "empty", "present"):
            with self.subTest(state=state), tempfile.TemporaryDirectory() as temporary:
                workspace = Path(temporary)
                config = workspace / ".specify/extensions.yml"
                constitution = workspace / ".specify/memory/constitution.md"
                constitution.parent.mkdir(parents=True)
                constitution.write_text("Required governance\n")
                if state != "absent":
                    config.write_text("" if state == "empty" else "hooks: {}\n")
                before = inventory(workspace)
                returned_config = config.read_text() if config.is_file() else None
                self.assertEqual(
                    {"absent": None, "empty": "", "present": "hooks: {}\n"}[state],
                    returned_config,
                )
                self.assertEqual("Required governance\n", constitution.read_text())
                self.assertEqual(before, inventory(workspace))

    @unittest.skipUnless(shutil.which("bash"), "shell setup control requires bash")
    def test_setup_uses_shell_interpreter_and_preserves_exact_argument_tokens(self):
        with tempfile.TemporaryDirectory(prefix="router v5 ") as temporary:
            workspace = Path(temporary)
            script = workspace / ".specify/scripts/bash/check-prerequisites.sh"
            script.parent.mkdir(parents=True)
            script.write_text(
                "#!/bin/bash\n"
                "[[ $# == 3 && $1 == --json && $2 == --template "
                "&& $3 == checklist-template ]] || exit 9\n"
                "printf '%s\\n' "
                "'{\"FEATURE_DIR\":\"specs/example\",\"AVAILABLE_DOCS\":[],"
                "\"TEMPLATE_CONTENT\":\"# Checklist\"}'\n"
            )
            before = inventory(workspace)
            for arguments, expected_exit in (
                (["--json", "--template", "checklist-template"], 0),
                (["--json --template checklist-template"], 9),
                (["--json", "--template", "checklist-template", "extra"], 9),
            ):
                with self.subTest(arguments=arguments):
                    result = subprocess.run(
                        [shutil.which("bash"), str(script), *arguments], cwd=workspace,
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(expected_exit, result.returncode, result.stderr)
                    if expected_exit == 0:
                        self.assertEqual(
                            ["FEATURE_DIR", "AVAILABLE_DOCS", "TEMPLATE_CONTENT"],
                            list(json.loads(result.stdout)),
                        )
            self.assertEqual(before, inventory(workspace))

    @unittest.skipUnless(shutil.which("bash"), "shell failure control requires bash")
    def test_separate_context_read_retains_failure_and_cannot_be_skipped_by_mask(self):
        with tempfile.TemporaryDirectory(prefix="router v5 ") as temporary:
            workspace = Path(temporary)
            script = workspace / "setup.sh"
            script.write_text("#!/bin/bash\nprintf 'setup failed\\n' >&2\nexit 7\n")
            constitution = workspace / ".specify/memory/constitution.md"
            constitution.parent.mkdir(parents=True)
            constitution.write_text("governance-content-sentinel\n")
            before = inventory(workspace)
            masked = subprocess.run(
                [shutil.which("bash"), "-c",
                 f"bash {shlex.quote(str(script))} && "
                 f"cat {shlex.quote(str(constitution))} || true"],
                cwd=workspace, capture_output=True, text=True, check=False,
            )
            self.assertEqual(0, masked.returncode)
            self.assertEqual("", masked.stdout)
            self.assertIn("setup failed", masked.stderr)
            setup = subprocess.run(
                [shutil.which("bash"), str(script)], cwd=workspace,
                capture_output=True, text=True, check=False,
            )
            context = subprocess.run(
                ["cat", str(constitution)], cwd=workspace,
                capture_output=True, text=True, check=False,
            )
            self.assertEqual(7, setup.returncode)
            self.assertIn("setup failed", setup.stderr)
            self.assertEqual(0, context.returncode)
            self.assertEqual("governance-content-sentinel\n", context.stdout)
            self.assertEqual(before, inventory(workspace))


if __name__ == "__main__":
    unittest.main()
