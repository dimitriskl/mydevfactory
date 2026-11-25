#!/usr/bin/env python3
"""Regression tests: malformed or missing release files must be reported cleanly."""

from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValidatorFailureTests(unittest.TestCase):
    def check_invalid_repo(self, change, message: str) -> None:
        with tempfile.TemporaryDirectory(prefix="mydevfactory-validator-") as temp:
            copy = Path(temp) / "repo"
            shutil.copytree(
                ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            env = os.environ.copy()
            change(copy, env)
            result = subprocess.run(
                [sys.executable, str(copy / "scripts" / "validate_skill.py")],
                cwd=copy,
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR:", result.stderr)
            self.assertIn(message, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def check_missing_file(self, relative_path: str) -> None:
        self.check_invalid_repo(lambda repo, _: (repo / relative_path).unlink(), relative_path)

    def test_missing_skill(self) -> None:
        self.check_missing_file("skills/mydevfactory/SKILL.md")

    def test_missing_readme(self) -> None:
        self.check_missing_file("README.md")

    def test_missing_updater(self) -> None:
        self.check_missing_file("install/update.sh")

    def test_stale_readme_version(self) -> None:
        def change(repo, _):
            readme = repo / "README.md"
            _, rest = readme.read_text(encoding="utf-8").split("\n", 1)
            readme.write_text(f"# MyDevFactory · Latest release v0.0.0\n{rest}", encoding="utf-8")

        self.check_invalid_repo(change, "README.md must show VERSION as the latest release")

    def test_pull_request_edits_outside_release_notes(self) -> None:
        def change(repo, env):
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "add", "--", "README.md"], cwd=repo, check=True)
            subprocess.run(
                ["git", "-c", "user.name=Test", "-c", "user.email=test@example.com",
                 "commit", "-qm", "README baseline"],
                cwd=repo, check=True,
            )
            env["MYDEVFACTORY_README_BASE"] = "HEAD"
            with (repo / "README.md").open("a", encoding="utf-8") as readme:
                readme.write("\nText outside the release notes.\n")

        self.check_invalid_repo(change, "Update the release notes at the top of README.md")


if __name__ == "__main__":
    unittest.main()
