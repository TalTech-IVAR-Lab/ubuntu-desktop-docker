#!/usr/bin/env python3
"""Prepare and validate the desktop user's conventional persistent home."""

from __future__ import annotations

import argparse
import os
import re
import stat
import sys
from pathlib import Path, PurePosixPath
from typing import NoReturn


USERNAME = re.compile(r"^[a-z_][a-z0-9_-]{0,31}$")
PERSISTENT_HOME = "/config"
CONTRACT_ERROR = 78


def fail(message: str) -> NoReturn:
    print(message, file=sys.stderr)
    raise SystemExit(CONTRACT_ERROR)


def checked_paths(root: Path, username: str, expected_home: str) -> tuple[Path, Path]:
    if not USERNAME.fullmatch(username) or username == "root":
        fail("invalid desktop username")

    expected = PurePosixPath(expected_home)
    canonical = PurePosixPath("/home") / username
    if not expected.is_absolute() or expected != canonical:
        fail(f"desktop home must be {canonical}")

    root = root.resolve(strict=True)
    home_parent = root / "home"
    try:
        parent_mode = home_parent.lstat().st_mode
    except FileNotFoundError:
        fail(f"desktop home parent is missing: {home_parent}")
    if not stat.S_ISDIR(parent_mode) or stat.S_ISLNK(parent_mode):
        fail(f"desktop home parent must be a real directory: {home_parent}")

    return root, root / expected.relative_to("/")


def passwd_home(root: Path, username: str) -> str:
    passwd = root / "etc" / "passwd"
    try:
        mode = passwd.lstat().st_mode
    except FileNotFoundError:
        fail(f"passwd database is missing: {passwd}")
    if not stat.S_ISREG(mode) or stat.S_ISLNK(mode):
        fail(f"passwd database must be a regular file: {passwd}")

    matches = []
    try:
        for line in passwd.read_text(encoding="utf-8").splitlines():
            fields = line.split(":")
            if len(fields) >= 7 and fields[0] == username:
                matches.append(fields[5])
    except (OSError, UnicodeError) as error:
        fail(f"could not read passwd database: {error}")

    if len(matches) != 1:
        fail(f"desktop account must have exactly one passwd entry: {username}")
    return matches[0]


def require_account_home(root: Path, username: str, expected_home: str) -> None:
    actual_home = passwd_home(root, username)
    if actual_home != expected_home:
        fail(f"desktop account home must be {expected_home}, got {actual_home}")


def require_persistent_symlink(home: Path) -> None:
    try:
        mode = home.lstat().st_mode
    except FileNotFoundError:
        fail(f"desktop home symlink is missing: {home}")
    if not stat.S_ISLNK(mode) or os.readlink(home) != PERSISTENT_HOME:
        fail(f"desktop home must be a symlink to {PERSISTENT_HOME}: {home}")


def prepare_home(root: Path, username: str, expected_home: str) -> None:
    root, home = checked_paths(root, username, expected_home)
    require_account_home(root, username, expected_home)

    try:
        mode = home.lstat().st_mode
    except FileNotFoundError:
        mode = None

    if mode is None:
        home.symlink_to(PERSISTENT_HOME)
    elif stat.S_ISLNK(mode):
        require_persistent_symlink(home)
    elif stat.S_ISDIR(mode):
        try:
            home.rmdir()
        except OSError:
            fail(f"desktop home must be absent or an empty directory: {home}")
        home.symlink_to(PERSISTENT_HOME)
    else:
        fail(f"desktop home must be absent, empty, or a symlink: {home}")


def validate_home(
    root: Path, username: str, expected_home: str, environment_home: str
) -> None:
    root, home = checked_paths(root, username, expected_home)
    require_account_home(root, username, expected_home)
    require_persistent_symlink(home)
    if environment_home != expected_home:
        fail(f"HOME must be {expected_home}, got {environment_home or '<unset>'}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=("prepare", "validate"))
    parser.add_argument("--root", type=Path, default=Path("/"))
    parser.add_argument("--user", required=True)
    parser.add_argument("--expected-home", required=True)
    parser.add_argument("--home-env")
    args = parser.parse_args()

    if args.command == "prepare":
        if args.home_env is not None:
            parser.error("--home-env is valid only with validate")
        prepare_home(args.root, args.user, args.expected_home)
    else:
        if args.home_env is None:
            fail("HOME must be supplied for runtime validation")
        validate_home(args.root, args.user, args.expected_home, args.home_env)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
