"""Capture a private baseline and report edits made during one agent dispatch."""

import argparse
import filecmp
import hashlib
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys
import tempfile


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", *args])


def dirty_paths():
    # Expand renames into two paths and enumerate individual untracked files.
    staged = git("diff", "--cached", "--name-only", "--no-renames", "-z", "HEAD", "--")
    unstaged = git("diff", "--name-only", "--no-renames", "-z", "--")
    untracked = git("ls-files", "--others", "--exclude-standard", "-z")
    return {os.fsdecode(name) for name in (staged + unstaged + untracked).split(b"\0") if name}


def state(path):
    # A tracked directory replaced by a symlink must never lead us outside the tree.
    try:
        for parent in reversed(path.parents):
            info = parent.lstat()
            if not stat.S_ISDIR(info.st_mode):
                return {"kind": "missing"}
            if os.name == "nt" and info.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
                return {"kind": "missing"}
        mode = path.lstat().st_mode
    except (FileNotFoundError, NotADirectoryError):
        return {"kind": "missing"}
    if stat.S_ISLNK(mode):
        return {"kind": "link", "target": os.readlink(path)}
    if not stat.S_ISREG(mode):
        raise ValueError(f"inspect this directory, submodule or special file separately: {path}")
    return {"kind": "file", "mode": stat.S_IMODE(mode)}


def capture(root):
    temp_root = Path(tempfile.gettempdir()).resolve()
    if root == temp_root or root in temp_root.parents:
        raise ValueError("choose a temporary directory outside the worktree for the snapshot")
    folder = Path(tempfile.mkdtemp(prefix="mydevfactory-dispatch-", dir=temp_root))
    try:
        files = {}
        for number, name in enumerate(sorted(dirty_paths())):
            path = Path(name)
            record = state(path)
            if record["kind"] == "file":
                record["backup"] = str(number)
                shutil.copyfile(path, folder / str(number))
            files[name] = record
        manifest = {
            "root": str(root),
            "head": git("rev-parse", "HEAD").decode().strip(),
            "index": hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest(),
            "files": files,
        }
        (folder / "snapshot.json").write_text(json.dumps(manifest), encoding="utf-8")
    except BaseException:
        shutil.rmtree(folder)
        raise
    print(folder)


def compare(root, folder):
    snapshot = json.loads((folder / "snapshot.json").read_text(encoding="utf-8"))
    if str(root) != snapshot["root"] or git("rev-parse", "HEAD").decode().strip() != snapshot["head"]:
        raise ValueError("worktree or HEAD changed during dispatch")
    if hashlib.sha256(git("ls-files", "--stage", "-z")).hexdigest() != snapshot["index"]:
        raise ValueError("staged contents changed during dispatch")

    before = snapshot["files"]
    changed = dirty_paths() - before.keys()
    for name, saved in before.items():
        path = Path(name)
        current = state(path)
        metadata = {key: value for key, value in saved.items() if key != "backup"}
        if current != metadata:
            changed.add(name)
        elif saved["kind"] == "file" and not filecmp.cmp(folder / saved["backup"], path, shallow=False):
            changed.add(name)
    print(json.dumps(sorted(changed)))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("capture")
    commands.add_parser("compare").add_argument("folder", type=Path)
    args = parser.parse_args()
    try:
        root = Path(os.fsdecode(git("rev-parse", "--show-toplevel")).rstrip("\r\n")).resolve()
        os.chdir(root)
        if args.command == "capture":
            capture(root)
        else:
            compare(root, args.folder)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
