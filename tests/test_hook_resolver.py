from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from harnessmith import CompileOptions, compile_skill, write_package


ROOT = Path(__file__).resolve().parents[1]
ANALYZE = ROOT / "skills" / "speckit-analyze" / "SKILL.md"


class HookResolverTests(unittest.TestCase):
    def _package(self, target: str = "cursor"):
        return compile_skill(
            ANALYZE,
            CompileOptions(target=target, optimize_extension_hooks=True),
        )

    def _run(self, script: Path, event: str, project: Path):
        result = subprocess.run(
            [
                sys.executable,
                str(script),
                event,
                "--project-root",
                str(project),
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        return json.loads(result.stdout)

    def test_resolves_enabled_unconditional_hooks_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            output = temp / "compiled"
            project = temp / "project"
            config = project / ".specify" / "extensions.yml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "hooks:\n"
                "  before_analyze:\n"
                "    - extension: git\n"
                "      command: speckit.git.commit\n"
                "      enabled: true\n"
                "      optional: false\n"
                "      description: Commit outstanding changes\n"
                "    - extension: conditional\n"
                "      command: speckit.conditional.run\n"
                "      condition: env.RUN_HOOK is set\n"
                "    - extension: disabled\n"
                "      command: speckit.disabled.run\n"
                "      enabled: false\n",
                encoding="utf-8",
            )
            write_package(self._package(), output)
            before = config.read_bytes()

            payload = self._run(
                output / "scripts" / "resolve-extension-hooks.py",
                "before_analyze",
                project,
            )

            self.assertEqual("ok", payload["status"])
            self.assertEqual(1, payload["skipped_conditions"])
            self.assertEqual("/speckit-git-commit", payload["hooks"][0]["invocation"])
            self.assertFalse(payload["hooks"][0]["optional"])
            self.assertIn("**Automatic Pre-Hook**: git", payload["message"])
            self.assertEqual(before, config.read_bytes())

    def test_codex_resolver_uses_dollar_skill_invocation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            output = temp / "compiled"
            project = temp / "project"
            config = project / ".specify" / "extensions.yml"
            config.parent.mkdir(parents=True)
            config.write_text(
                "hooks:\n"
                "  after_analyze:\n"
                "    - extension: notes\n"
                "      command: speckit.notes.publish\n"
                "      optional: true\n"
                "      prompt: Publish notes?\n",
                encoding="utf-8",
            )
            write_package(self._package("codex"), output)

            payload = self._run(
                output / "scripts" / "resolve-extension-hooks.py",
                "after_analyze",
                project,
            )

            self.assertEqual("$speckit-notes-publish", payload["hooks"][0]["invocation"])
            self.assertIn("**Optional Hook**: notes", payload["message"])

    def test_missing_configuration_is_silent_status(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            output = temp / "compiled"
            project = temp / "project"
            project.mkdir()
            write_package(self._package(), output)

            payload = self._run(
                output / "scripts" / "resolve-extension-hooks.py",
                "before_analyze",
                project,
            )

            self.assertEqual("missing", payload["status"])


if __name__ == "__main__":
    unittest.main()
