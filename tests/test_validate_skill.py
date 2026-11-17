#!/usr/bin/env python3
"""Regression tests: malformed or missing release files must be reported cleanly."""

from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ValidatorFailureTests(unittest.TestCase):
    def check_missing_file(self, relative_path: str) -> None:
        with tempfile.TemporaryDirectory(prefix="mydevfactory-validator-") as temp:
            copy = Path(temp) / "repo"
            shutil.copytree(
                ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__")
            )
            (copy / relative_path).unlink()
            result = subprocess.run(
                [sys.executable, str(copy / "scripts" / "validate_skill.py")],
                cwd=copy,
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ERROR:", result.stderr)
            self.assertIn(relative_path, result.stderr)
            self.assertNotIn("Traceback", result.stderr)

    def test_missing_skill(self) -> None:
        self.check_missing_file("skills/mydevfactory/SKILL.md")

    def test_missing_readme(self) -> None:
        self.check_missing_file("README.md")

    def test_missing_updater(self) -> None:
        self.check_missing_file("install/update.sh")


if __name__ == "__main__":
    unittest.main()
