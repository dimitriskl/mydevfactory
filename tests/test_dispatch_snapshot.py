"""Verify per-dispatch attribution in disposable Git worktrees."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skills/mydevfactory/scripts/dispatch_snapshot.py"


class DispatchSnapshotTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name) / "repo"
        self.root.mkdir()
        self.env = dict(os.environ, TMPDIR=temp.name, TEMP=temp.name, TMP=temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Workflow Test")
        self.git("config", "user.email", "workflow@example.invalid")
        self.git("config", "core.autocrlf", "false")
        self.card = self.root / "card.md"
        self.card.write_bytes(b"original\n")
        self.git("add", "card.md")
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "baseline")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.root, env=self.env, check=True, capture_output=True)

    def snapshot(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.root,
                              env=self.env, capture_output=True, text=True)

    def capture(self):
        result = self.snapshot("capture")
        self.assertEqual(result.returncode, 0, result.stderr)
        return Path(result.stdout.strip())

    def changes(self, folder):
        result = self.snapshot("compare", str(folder))
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def test_agent_edit_to_already_dirty_card_preserves_baseline(self):
        self.card.write_bytes(b"orchestrator history\r\n")
        notes = self.root / "untracked notes.bin"
        notes.write_bytes(b"\x00user bytes")
        folder = self.capture()
        self.assertEqual(self.changes(folder), [])
        self.card.write_bytes(b"reviewer rewrote history\n")
        notes.write_bytes(b"\x00new bytes")
        self.assertEqual(self.changes(folder), ["card.md", notes.name])
        files = json.loads((folder / "snapshot.json").read_text())["files"]
        self.assertEqual((folder / files["card.md"]["backup"]).read_bytes(), b"orchestrator history\r\n")
        self.assertEqual((folder / files[notes.name]["backup"]).read_bytes(), b"\x00user bytes")
        self.assertEqual(self.card.read_bytes(), b"reviewer rewrote history\n")

    def test_removed_restored_and_new_paths(self):
        self.card.unlink()
        notes = self.root / "previous notes"
        notes.write_text("before")
        folder = self.capture()
        self.card.write_bytes(b"original\n")
        notes.unlink()
        (self.root / "new file").write_text("after")
        self.assertEqual(self.changes(folder), ["card.md", "new file", "previous notes"])

    def test_staged_and_unstaged_edits_that_cancel_still_have_a_backup(self):
        self.card.write_bytes(b"staged version\n")
        self.git("add", "card.md")
        self.card.write_bytes(b"original\n")
        folder = self.capture()
        self.assertEqual(self.changes(folder), [])
        files = json.loads((folder / "snapshot.json").read_text())["files"]
        self.assertEqual((folder / files["card.md"]["backup"]).read_bytes(), b"original\n")
        self.card.write_bytes(b"agent edit\n")
        self.assertEqual(self.changes(folder), ["card.md"])

    def test_index_and_head_changes_block_comparison(self):
        folder = self.capture()
        self.card.write_text("staged")
        self.git("add", "card.md")
        result = self.snapshot("compare", str(folder))
        self.assertEqual(result.returncode, 1)
        self.assertIn("staged contents changed", result.stderr)
        self.git("-c", "commit.gpgsign=false", "commit", "-qm", "agent commit")
        result = self.snapshot("compare", str(folder))
        self.assertEqual(result.returncode, 1)
        self.assertIn("HEAD changed", result.stderr)
