#!/usr/bin/env python3
"""Rewrite LinuxServer's fixed ``abc`` desktop-user contract at image build time."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from typing import NoReturn


SOURCE_USER = "abc"
USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
SOURCE_TOKEN = re.compile(r"(?<![A-Za-z0-9])abc(?![A-Za-z0-9])")
TEXT_ROOTS = (
    "etc/s6-overlay/s6-rc.d",
    "etc/ssh",
    "defaults",
    "usr/local/bin",
)
ACCOUNT_NAMED_PATHS = (
    "defaults/crontabs/abc",
    "var/spool/cron/crontabs/abc",
)


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(64)


def validate_username(username: str) -> None:
    if not USERNAME.fullmatch(username) or username == "root":
        fail(
            "DESKTOP_USER must match ^[a-z_][a-z0-9_-]{0,31}$ "
            "and must not be root"
        )


def text_files(root: Path):
    for relative_root in TEXT_ROOTS:
        directory = root / relative_root
        if not directory.is_dir() or directory.is_symlink():
            continue
        for current, directories, filenames in os.walk(directory, followlinks=False):
            directories[:] = [
                name for name in directories if not (Path(current) / name).is_symlink()
            ]
            for filename in filenames:
                path = Path(current) / filename
                if path.is_symlink() or not path.is_file():
                    continue
                try:
                    payload = path.read_bytes()
                    if b"\0" in payload:
                        continue
                    text = payload.decode("utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
                yield path, text


def rewrite_contract(root: Path, username: str) -> int:
    validate_username(username)
    if username == SOURCE_USER:
        return 0

    replacements = 0
    for path, text in list(text_files(root)):
        rewritten, count = SOURCE_TOKEN.subn(username, text)
        if count:
            path.write_text(rewritten, encoding="utf-8")
            replacements += count

    for relative_path in ACCOUNT_NAMED_PATHS:
        source = root / relative_path
        if not source.exists() or source.is_symlink():
            continue
        target = source.with_name(username)
        if target.exists() or target.is_symlink():
            fail(f"desktop-user path already exists: {target}")
        source.rename(target)
        replacements += 1

    leftovers = [
        str(path.relative_to(root))
        for path, text in text_files(root)
        if SOURCE_TOKEN.search(text)
    ]
    if leftovers:
        fail("unrewritten desktop-user references: " + ", ".join(sorted(leftovers)))

    if replacements == 0:
        fail("no LinuxServer desktop-user references were found to rewrite")
    return replacements


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--user", required=True)
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.is_dir():
        fail(f"rewrite root is not a directory: {root}")
    replacements = rewrite_contract(root, args.user)
    print(f"desktop_user={args.user} rewritten_references={replacements}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
