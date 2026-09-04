#!/usr/bin/env python3
"""Select safe DRM render/encode nodes for the Selkies runtime."""

from __future__ import annotations

import argparse
import glob
import os
import re
import stat
import sys
from pathlib import Path
from typing import Callable, Iterable, NamedTuple, Optional, Tuple


DEFAULT_DEVICE_ROOT = Path("/dev/dri")
DEFAULT_ENVIRONMENT_DIR = Path("/run/s6/container_environment")


class GpuSelection(NamedTuple):
    render_node: str
    encode_node: str
    mode: str


class RenderNodeError(ValueError):
    def __init__(self, message: str, exit_code: int) -> None:
        super().__init__(message)
        self.exit_code = exit_code


def validate_render_node(
    node: str, *, device_root: Path = DEFAULT_DEVICE_ROOT
) -> None:
    """Require a numbered, existing, non-symlink DRM character device."""
    pattern = rf"^{re.escape(str(device_root))}/renderD[0-9]+$"
    if not re.fullmatch(pattern, node):
        raise RenderNodeError(
            f"GPU render node must match {device_root}/renderD<number>: {node}",
            64,
        )

    try:
        node_stat = os.lstat(node)
    except FileNotFoundError as error:
        raise RenderNodeError(
            "GPU render node must be an existing non-symlink character device: "
            f"{node}",
            78,
        ) from error

    if stat.S_ISLNK(node_stat.st_mode) or not stat.S_ISCHR(node_stat.st_mode):
        raise RenderNodeError(
            "GPU render node must be an existing non-symlink character device: "
            f"{node}",
            78,
        )


def discover_render_nodes(device_root: Path = DEFAULT_DEVICE_ROOT) -> list[str]:
    """Return mapped DRM render nodes in deterministic lexical order."""
    return sorted(glob.glob(str(device_root / "renderD*")))


def select_gpu_nodes(
    *,
    auto_gpu: str,
    render_node: str,
    encode_node: str,
    discovered_nodes: Iterable[str],
    validator: Callable[[str], None] = validate_render_node,
) -> GpuSelection:
    """Resolve explicit and automatic render/encode choices."""
    if auto_gpu not in {"true", "false"}:
        raise ValueError("AUTO_GPU must be true or false")

    render = render_node
    encode = encode_node
    if render and not encode:
        encode = render
    elif encode and not render:
        render = encode
    elif not render and not encode and auto_gpu == "true":
        discovered = sorted(discovered_nodes)
        if discovered:
            render = discovered[0]
            encode = render

    if not render and not encode:
        return GpuSelection("", "", "cpu-fallback")

    validator(render)
    validator(encode)
    mode = "zero-copy" if render == encode else "readback"
    return GpuSelection(render, encode, mode)


def _write_environment_file(
    directory_fd: int,
    name: str,
    value: str,
    owner: Optional[Tuple[int, int]],
) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_CLOEXEC
    file_fd = os.open(name, flags, 0o644, dir_fd=directory_fd)
    try:
        os.fchmod(file_fd, 0o644)
        if owner is not None:
            os.fchown(file_fd, owner[0], owner[1])
        os.write(file_fd, value.encode("utf-8"))
    finally:
        os.close(file_fd)


def write_container_environment(
    environment_dir: Path,
    render_node: str,
    encode_node: str,
    *,
    owner: Optional[Tuple[int, int]] = (0, 0),
) -> None:
    """Publish selected nodes for later s6 services without following links."""
    directory_fd = os.open(
        str(environment_dir),
        os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
    )
    try:
        _write_environment_file(directory_fd, "DRINODE", render_node, owner)
        _write_environment_file(directory_fd, "DRI_NODE", encode_node, owner)
    finally:
        os.close(directory_fd)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--environment-dir",
        type=Path,
        default=DEFAULT_ENVIRONMENT_DIR,
    )
    args = parser.parse_args()

    try:
        selection = select_gpu_nodes(
            auto_gpu=os.environ.get("AUTO_GPU", "false"),
            render_node=os.environ.get("DRINODE", ""),
            encode_node=os.environ.get("DRI_NODE", ""),
            discovered_nodes=discover_render_nodes(),
        )
    except RenderNodeError as error:
        print(error, file=sys.stderr)
        return error.exit_code
    except ValueError as error:
        print(error, file=sys.stderr)
        return 64

    if selection.render_node:
        write_container_environment(
            args.environment_dir,
            selection.render_node,
            selection.encode_node,
        )
        if selection.mode == "zero-copy":
            print(
                "GPU rendering and encoding node: "
                f"{selection.render_node}; same-device zero-copy expected"
            )
        else:
            print(
                f"GPU rendering node {selection.render_node} and encoding node "
                f"{selection.encode_node} use different devices; "
                "CPU readback expected",
                file=sys.stderr,
            )
    elif os.environ.get("AUTO_GPU", "false") == "true":
        print("AUTO_GPU found no mapped DRM render node; using CPU fallback")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
