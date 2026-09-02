#!/usr/bin/env python3
"""Static contract tests for the maintained Ubuntu desktop images."""

from __future__ import annotations

import hashlib
import importlib.util
import os
import re
import stat
import struct
import subprocess
import tempfile
import unittest
from pathlib import Path
from types import ModuleType


ROOT = Path(__file__).resolve().parents[1]
SELKIES_DOCKERFILE = ROOT / "Dockerfile"
SELKIES_COMPAT_DOCKERFILE = ROOT / "Dockerfile.compat"
WORKFLOW = ROOT / ".github" / "workflows" / "docker_build.yml"
DEPENDABOT = ROOT / ".github" / "dependabot.yml"
README = ROOT / "README.md"
ADVANCED_USAGE = ROOT / "docs" / "ADVANCED_USAGE.md"
GPU_VALIDATION = ROOT / "docs" / "GPU_VALIDATION.md"
GPU_VERIFY = ROOT / "files" / "usr" / "local" / "bin" / "taltech-verify-gpu"
SELKIES_FILES = ROOT / "selkies-files"
SELKIES_S6_ROOT = SELKIES_FILES / "etc" / "s6-overlay" / "s6-rc.d"
SELKIES_INIT = SELKIES_S6_ROOT / "init-taltech-selkies" / "run"
GPU_SELECTOR = (
    SELKIES_FILES / "usr" / "local" / "libexec" / "taltech-select-gpu-nodes.py"
)
SELKIES_PYPROJECT = ROOT / "pyproject.toml"
SELKIES_UV_LOCK = ROOT / "uv.lock"
SELKIES_REQUIREMENTS = ROOT / "selkies-requirements.txt"
XVFB_DRI3_PATCH = ROOT / "patches" / "xorg-server-21.1.24-xvfb-dri3.patch"
DESKTOP_USER_REWRITER = ROOT / "build-scripts" / "configure-desktop-user.py"
IVAR_WALLPAPER = (
    ROOT / "files" / "usr" / "share" / "backgrounds" / "taltech" / "ivar-lab.png"
)
IVAR_WALLPAPER_SHA256 = (
    "1686ae406c39d8da711c8b057b48c27f56de7b8ae9b3ba291a5f095ef4827cfc"
)


class ImageContractTests(unittest.TestCase):
    @staticmethod
    def _load_gpu_selector(name: str) -> ModuleType:
        spec = importlib.util.spec_from_file_location(name, GPU_SELECTOR)
        if spec is None or spec.loader is None:
            raise AssertionError(f"Could not load {GPU_SELECTOR}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_only_current_production_dockerfiles_remain(self) -> None:
        self.assertTrue((ROOT / "Dockerfile").is_file())
        self.assertTrue((ROOT / "Dockerfile.compat").is_file())

        for obsolete in (
            "Dockerfile_Selkies",
            "Dockerfile_Selkies_Compat",
            "Dockerfile_Focal",
            "Dockerfile_Jammy",
        ):
            self.assertFalse((ROOT / obsolete).exists(), obsolete)

        workflow = WORKFLOW.read_text()
        self.assertIn("dockerfile: Dockerfile.compat", workflow)
        self.assertIn("dockerfile: Dockerfile", workflow)
        self.assertNotIn("Dockerfile_Selkies", workflow)
        self.assertNotIn("XRDP", GPU_VERIFY.read_text())

    def test_ci_runs_contract_tests(self) -> None:
        content = WORKFLOW.read_text()

        self.assertIn("python3 -B -m unittest -v tests.test_image_contract", content)

    def test_ci_actions_are_immutable_and_automatically_maintained(self) -> None:
        workflow = WORKFLOW.read_text()
        action_refs = re.findall(r"^\s*uses:\s*([^#\s]+)", workflow, re.MULTILINE)
        versioned_action_refs = re.findall(
            r"^\s*uses:\s*[^#\s]+\s+#\s+v\d+\s*$", workflow, re.MULTILINE
        )

        self.assertTrue(action_refs)
        for action_ref in action_refs:
            self.assertRegex(action_ref, r"^[^@\s]+@[0-9a-f]{40}$")
        self.assertEqual(len(action_refs), len(versioned_action_refs))
        self.assertIn("permissions:\n  contents: read", workflow)
        self.assertIn("persist-credentials: false", workflow)
        self.assertIn("timeout-minutes: 180", workflow)

        def step(name: str) -> str:
            start = workflow.index(f"      - name: {name}\n")
            end = workflow.find("\n      - name:", start + 1)
            return workflow[start:] if end < 0 else workflow[start:end]

        publish_guard = (
            "github.event_name == 'push' && github.ref == 'refs/heads/main'"
        )
        self.assertIn(f"if: {publish_guard}", step("Login to Docker Hub"))
        self.assertIn(
            f"push: ${{{{ {publish_guard} }}}}", step("Build and push to Dockerhub")
        )
        self.assertIn(
            f"if: {publish_guard} && matrix.tag == '24.04'",
            step("Update description on Docker Hub"),
        )

        dependabot = DEPENDABOT.read_text()
        self.assertIn('package-ecosystem: "github-actions"', dependabot)
        self.assertIn('interval: "monthly"', dependabot)

    def test_ci_builds_all_ubuntu_lts_from_focal_for_both_architectures(self) -> None:
        content = WORKFLOW.read_text()

        for value in (
            "focal",
            "jammy",
            "noble",
            "resolute",
            "20.04",
            "22.04",
            "24.04",
            "26.04",
        ):
            self.assertIn(value, content)
        self.assertIn("linux/amd64,linux/arm64", content)
        self.assertIn("UBUNTU_CODENAME", content)
        self.assertRegex(
            content,
            r"- codename: noble\s+tag: 24\.04\s+dockerfile: Dockerfile",
        )
        self.assertIn("file: ${{ matrix.dockerfile }}", content)

    def test_documentation_lists_all_ubuntu_lts_from_focal(self) -> None:
        content = README.read_text()

        self.assertIn("Ubuntu 20.04", content)
        self.assertIn("Ubuntu 22.04", content)
        self.assertIn("Ubuntu 24.04", content)
        self.assertIn("Ubuntu 26.04", content)
        self.assertNotIn("Legacy; no new builds", content)
        self.assertIn("docker build -f Dockerfile.compat", content)
        self.assertIn("--build-arg EXPECTED_UBUNTU_CODENAME=jammy", content)

    def test_documentation_presents_all_supported_lts_lanes_as_selkies(self) -> None:
        readme = README.read_text()
        advanced = ADVANCED_USAGE.read_text()
        gpu_validation = GPU_VALIDATION.read_text()

        self.assertNotIn("Selkies prototype", readme)
        for release in (
            "Ubuntu 20.04 Focal",
            "Ubuntu 22.04 Jammy",
            "Ubuntu 24.04 Noble",
            "Ubuntu 26.04 Resolute",
        ):
            self.assertIn(release, readme)
        self.assertIn("https://HOST:3001/", readme)
        self.assertIn("CUSTOM_USER", readme)
        self.assertIn("PASSWORD_FILE", readme)
        self.assertIn("docker build -f Dockerfile", readme)
        self.assertIn("docker build -f Dockerfile.compat", readme)
        self.assertNotIn("XRDP quick start", readme)
        self.assertNotIn("XRDP lanes", readme)

        self.assertIn("All published image lanes use Selkies", advanced)
        self.assertNotIn("XRDP lanes", advanced)
        self.assertIn("actual remote session", advanced)

        for image_id in (
            "sha256:aa05c948e046615825d90b384f139428f86c0293ad3e12c6050e720abfaa88d2",
            "sha256:454766567db6e78ba479bbdb7b5177829998650986fb746bee57c796c845a4b3",
            "sha256:8e76a77b1d8b5a6472665ab353479dade28507db92a8e832d8c0289d6bd2f780",
            "sha256:032719e41ef74d002259c84f03ffcb5c596ca870e0bb28d307302a33dd8d72a5",
        ):
            self.assertIn(image_id, gpu_validation)
        self.assertIn("H.264/NVENC proof: `PASS`", gpu_validation)
        self.assertIn("1,495 decoded frames", gpu_validation)
        self.assertIn("1,467 decoded frames", gpu_validation)
        self.assertNotIn("NVENC and zero-copy encoding remain unverified", gpu_validation)
        self.assertIn(
            "sha256:3f3090928451bcc9bf85686d82bb3b5bf1f9a0b2af251b1c438330db319163a7",
            gpu_validation,
        )
        self.assertIn("Jazzy on Selkies partial", gpu_validation)
        self.assertIn("robot-model interaction remains untested", gpu_validation)
        self.assertIn(
            "After recreation, the harness repeated web authentication and ROS/DDS checks",
            gpu_validation,
        )

    def test_gpu_verification_harness_checks_real_rendering(self) -> None:
        self.assertTrue(GPU_VERIFY.is_file(), GPU_VERIFY)
        self.assertTrue(GPU_VERIFY.stat().st_mode & stat.S_IXUSR, GPU_VERIFY)
        content = GPU_VERIFY.read_text()

        self.assertIn("/dev/dri/renderD", content)
        self.assertIn("glxinfo -B", content)
        self.assertIn("nvidia-smi", content)
        for software_renderer in (
            "llvmpipe",
            "softpipe",
            "swrast",
            "lavapipe",
            "swiftshader",
            "openswr",
        ):
            self.assertIn(software_renderer, content)

    def test_selkies_configures_same_gpu_for_zero_copy(self) -> None:
        for dockerfile in (SELKIES_DOCKERFILE, SELKIES_COMPAT_DOCKERFILE):
            with self.subTest(dockerfile=dockerfile.name):
                self.assertIn("AUTO_GPU=true", dockerfile.read_text())

        init = SELKIES_INIT.read_text()
        selector = GPU_SELECTOR.read_text()
        self.assertIn("renderD[0-9]+", selector)
        self.assertIn("os.lstat(node)", selector)
        self.assertIn("stat.S_ISLNK", selector)
        self.assertIn("stat.S_ISCHR", selector)
        self.assertIn('os.environ.get("DRINODE", "")', selector)
        self.assertIn('os.environ.get("DRI_NODE", "")', selector)
        self.assertIn("discover_render_nodes()", selector)
        self.assertIn('"DRINODE"', selector)
        self.assertIn('"DRI_NODE"', selector)
        self.assertIn("same-device zero-copy expected", selector)
        self.assertIn("use different devices", selector)
        self.assertIn("CPU readback expected", selector)
        self.assertIn(
            "/usr/bin/python3 /usr/local/libexec/taltech-select-gpu-nodes.py",
            init,
        )

    def test_gpu_selector_exercises_the_complete_decision_tree(self) -> None:
        self.assertTrue(GPU_SELECTOR.is_file(), GPU_SELECTOR)
        module = self._load_gpu_selector("taltech_gpu_selector")

        first = "/dev/dri/renderD128"
        second = "/dev/dri/renderD129"
        cases = (
            ("false", "", "", [], ("", "", "cpu-fallback")),
            ("true", "", "", [], ("", "", "cpu-fallback")),
            ("true", "", "", [second, first], (first, first, "zero-copy")),
            ("false", first, "", [], (first, first, "zero-copy")),
            ("false", "", second, [], (second, second, "zero-copy")),
            ("false", first, first, [], (first, first, "zero-copy")),
            ("true", first, second, [], (first, second, "readback")),
        )
        for auto_gpu, render, encode, discovered, expected in cases:
            with self.subTest(
                auto_gpu=auto_gpu,
                render=render,
                encode=encode,
                discovered=discovered,
            ):
                selection = module.select_gpu_nodes(
                    auto_gpu=auto_gpu,
                    render_node=render,
                    encode_node=encode,
                    discovered_nodes=discovered,
                    validator=lambda _node: None,
                )
                self.assertEqual(expected, tuple(selection))

        with self.assertRaisesRegex(ValueError, "AUTO_GPU must be true or false"):
            module.select_gpu_nodes(
                auto_gpu="yes",
                render_node="",
                encode_node="",
                discovered_nodes=[],
                validator=lambda _node: None,
            )

    def test_gpu_selector_rejects_unsafe_render_nodes_behaviorally(self) -> None:
        self.assertTrue(GPU_SELECTOR.is_file(), GPU_SELECTOR)
        module = self._load_gpu_selector("taltech_gpu_validator")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            regular = root / "renderD128"
            symlink = root / "renderD129"
            regular.write_text("not a device")
            symlink.symlink_to("/dev/null")

            for node, message in (
                (regular, "non-symlink character device"),
                (symlink, "non-symlink character device"),
                (root / "renderD130", "existing non-symlink character device"),
                (root / "card0", "renderD<number>"),
            ):
                with self.subTest(node=node):
                    with self.assertRaisesRegex(ValueError, message):
                        module.validate_render_node(str(node), device_root=root)

    def test_gpu_selector_writes_environment_for_dependent_services(self) -> None:
        self.assertTrue(GPU_SELECTOR.is_file(), GPU_SELECTOR)
        module = self._load_gpu_selector("taltech_gpu_environment")

        with tempfile.TemporaryDirectory() as directory:
            environment_dir = Path(directory)
            module.write_container_environment(
                environment_dir,
                "/dev/dri/renderD128",
                "/dev/dri/renderD128",
                owner=None,
            )
            for name in ("DRINODE", "DRI_NODE"):
                target = environment_dir / name
                self.assertEqual("/dev/dri/renderD128", target.read_text())
                self.assertEqual(0o644, stat.S_IMODE(target.stat().st_mode))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            real_environment = root / "environment"
            real_environment.mkdir()
            environment_link = root / "environment-link"
            environment_link.symlink_to(real_environment, target_is_directory=True)

            with self.assertRaises(OSError):
                module.write_container_environment(
                    environment_link,
                    "/dev/dri/renderD128",
                    "/dev/dri/renderD128",
                    owner=None,
                )
            self.assertEqual([], list(real_environment.iterdir()))

        for protected_name in ("DRINODE", "DRI_NODE"):
            with self.subTest(protected_name=protected_name):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    environment_dir = root / "environment"
                    environment_dir.mkdir()
                    protected_target = root / f"{protected_name}.target"
                    protected_target.write_text("protected")
                    (environment_dir / protected_name).symlink_to(protected_target)

                    with self.assertRaises(OSError):
                        module.write_container_environment(
                            environment_dir,
                            "/dev/dri/renderD128",
                            "/dev/dri/renderD128",
                            owner=None,
                        )
                    self.assertEqual("protected", protected_target.read_text())

        init = SELKIES_INIT.read_text()
        invocation = "/usr/bin/python3 /usr/local/libexec/taltech-select-gpu-nodes.py"
        self.assertIn(invocation, init)
        self.assertLess(init.index(invocation), init.index("CUSTOM_USER must be set"))

    def test_zero_copy_validation_records_runtime_proof(self) -> None:
        gpu_validation = GPU_VALIDATION.read_text()
        advanced = ADVANCED_USAGE.read_text()

        self.assertIn("Four-lane zero-copy proof: `PASS`", gpu_validation)
        for image_id in (
            "sha256:e21da502b66c823d3cdebef718d16e207bcb2982beb20db6bc9491d6a5cbeac2",
            "sha256:1ed71b974ac149767b18a075538c5890099d366eedfc7becacbad09da3f07c70",
            "sha256:e955ebbe8b9945f4e39de233ee8b77f0c93cd53ef92852f40ea617a4cc9726e3",
            "sha256:8cb96d6676e18193bc081b21eccd2b422e0732bba0b9f753d271b1194db25642",
        ):
            self.assertIn(image_id, gpu_validation)
        for evidence_hash in (
            "68742dc669bb1daa4cd3f80bfc32cd5e0f029175d15c2d52496bb475e95ef182",
            "178705774bf5a96b0a0cda6a817e68439907cdf817417b39fe270e4681801640",
            "6c90066b681b705d5a965bd17c65c171aa615aec192351f6904f2cf0a33ff11a",
            "760c313ff5f5545c901edce6864e84bd4642ebf6a8d55f02e7c5960a38966639",
            "f46ff38ca6febb651a9b0193c32c3f5b4e1d0a03aebeebd1dde331c2093a7296",
            "addcbf3eb14dcf54df3234343bbfaab7894a164ea662e2cde32394c51d54fe88",
            "1ecee1c7a2df7c502db7b00dcb2db5dbd966cb094150ab9cba6769b5f3153d69",
            "c0c2bb7d21a84bc90774c5a45ab717dcad1495beb7ef0123434f48e86bd4c447",
        ):
            self.assertIn(evidence_hash, gpu_validation)
        self.assertIn(
            "`DRINODE=/dev/dri/renderD128` and `DRI_NODE=/dev/dri/renderD128`",
            gpu_validation,
        )
        self.assertIn(
            "`[Wayland] NVENC Encoder initialized successfully.`",
            gpu_validation,
        )
        self.assertIn(
            "`[Wayland] Decision: Zero-Copy path active.`",
            gpu_validation,
        )
        self.assertIn(
            "No PixelFlux readback, split-GPU, or CPU-encoding fallback decision",
            gpu_validation,
        )
        self.assertNotIn("These results do not establish zero-copy operation", advanced)
        self.assertIn("zero-copy capture feeding NVENC", advanced)

    def test_gpu_verification_harness_is_not_ignored_by_git(self) -> None:
        result = subprocess.run(
            ["git", "check-ignore", "-q", str(GPU_VERIFY.relative_to(ROOT))],
            cwd=ROOT,
            check=False,
        )

        self.assertNotEqual(0, result.returncode)

    def test_gpu_verification_harness_rejects_software_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            glxinfo = bin_dir / "glxinfo"
            nvidia_smi = bin_dir / "nvidia-smi"
            glxinfo.write_text(
                "#!/bin/sh\n"
                "printf 'OpenGL vendor string: Test Vendor\\n'\n"
                "printf 'OpenGL renderer string: %s\\n' \"$FAKE_RENDERER\"\n"
                "printf 'OpenGL version string: 4.6 Test\\n'\n"
                "exit \"${FAKE_GLXINFO_EXIT:-0}\"\n"
            )
            nvidia_smi.write_text("#!/bin/sh\necho 'Test GPU, 999.0'\n")
            glxinfo.chmod(0o755)
            nvidia_smi.chmod(0o755)
            environment = {
                **os.environ,
                "DISPLAY": ":99",
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
            }

            for renderer in (
                "NVIDIA GeForce GTX 1070",
                "Mesa Intel(R) UHD Graphics 770",
            ):
                with self.subTest(renderer=renderer):
                    hardware = subprocess.run(
                        [GPU_VERIFY],
                        env={**environment, "FAKE_RENDERER": renderer},
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(0, hardware.returncode, hardware.stderr)
                    self.assertIn("GPU_ACCELERATION=PASS", hardware.stdout)

            for renderer in (
                "llvmpipe (LLVM 20.0)",
                "softpipe",
                "Mesa X11 swrast",
                "zink Vulkan 1.3 (llvmpipe via lavapipe)",
                "ANGLE (Google, Vulkan 1.3 SwiftShader Device)",
                "OpenSWR renderer",
                "Mesa Software Rasterizer",
            ):
                with self.subTest(renderer=renderer):
                    software = subprocess.run(
                        [GPU_VERIFY],
                        env={**environment, "FAKE_RENDERER": renderer},
                        check=False,
                        capture_output=True,
                        text=True,
                    )
                    self.assertEqual(1, software.returncode)
                    self.assertIn("GPU_ACCELERATION=FAIL", software.stderr)

            failed_probe = subprocess.run(
                [GPU_VERIFY],
                env={
                    **environment,
                    "FAKE_RENDERER": "NVIDIA GeForce GTX 1070",
                    "FAKE_GLXINFO_EXIT": "42",
                },
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, failed_probe.returncode)
            self.assertIn("GPU_ACCELERATION=FAIL", failed_probe.stderr)

    def test_gpu_verification_harness_enforces_expected_renderer_regex(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            bin_dir = Path(directory)
            glxinfo = bin_dir / "glxinfo"
            nvidia_smi = bin_dir / "nvidia-smi"
            glxinfo.write_text(
                "#!/bin/sh\n"
                "printf 'OpenGL vendor string: Mesa\\n'\n"
                "printf 'OpenGL renderer string: zink Vulkan 1.4 (NVIDIA GeForce RTX 4090 D)\\n'\n"
                "printf 'OpenGL version string: 4.6 Test\\n'\n"
            )
            nvidia_smi.write_text("#!/bin/sh\necho 'NVIDIA GeForce RTX 4090 D, 580.126.09'\n")
            glxinfo.chmod(0o755)
            nvidia_smi.chmod(0o755)
            environment = {
                **os.environ,
                "DISPLAY": ":10.0",
                "PATH": f"{bin_dir}:{os.environ['PATH']}",
            }

            matching = subprocess.run(
                [GPU_VERIFY],
                env={**environment, "EXPECTED_RENDERER_REGEX": "NVIDIA"},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(0, matching.returncode, matching.stderr)
            self.assertIn("GPU_ACCELERATION=PASS", matching.stdout)

            mismatching = subprocess.run(
                [GPU_VERIFY],
                env={**environment, "EXPECTED_RENDERER_REGEX": "AMD|Intel"},
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(1, mismatching.returncode)
            self.assertIn("does not match EXPECTED_RENDERER_REGEX", mismatching.stderr)

    def test_selkies_native_images_are_pinned_and_selected_by_ci(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()
        workflow = WORKFLOW.read_text()

        self.assertIn(
            "ARG SELKIES_RUNTIME_BASE=ghcr.io/linuxserver/baseimage-selkies@sha256:"
            "bdbdb9fa0b7505e6d8b4ed2a357e711b7bd53ab96e7f9f11a3d3bbfecafb3663",
            content,
        )
        self.assertIn("ARG SELKIES_RUNTIME_BASE", content)
        self.assertIn("FROM ${SELKIES_RUNTIME_BASE}", content)
        self.assertIn("ARG EXPECTED_UBUNTU_CODENAME=noble", content)
        self.assertIn('if [ "${VERSION_CODENAME}" != "${EXPECTED_UBUNTU_CODENAME}" ]', content)
        self.assertNotIn("linuxserver/rdesktop", content)
        self.assertNotIn("xrdp", content.lower())
        self.assertIn("EXPOSE 22 3001", content)
        self.assertIn("VOLUME /config /var/lib/taltech-desktop", content)
        self.assertIn("sha256:bdbdb9fa0b7505e6d8b4ed2a357e711b7bd53ab96e7f9f11a3d3bbfecafb3663", workflow)
        self.assertIn("sha256:8bb0d9343b764034c048c2c3895127bfe885a824fcc93ad472281fdd6d4a582f", workflow)
        self.assertNotIn("Selkies prototype", content)

    def test_selkies_compat_images_cover_focal_and_jammy(self) -> None:
        content = SELKIES_COMPAT_DOCKERFILE.read_text()
        workflow = WORKFLOW.read_text()

        self.assertIn("ARG UBUNTU_BASE_IMAGE", content)
        self.assertIn("FROM ${UBUNTU_BASE_IMAGE}", content)
        self.assertIn("ARG EXPECTED_UBUNTU_CODENAME", content)
        self.assertIn('case "${VERSION_CODENAME}" in', content)
        self.assertIn("focal|jammy", content)
        self.assertIn('if [ "${VERSION_CODENAME}" != "${EXPECTED_UBUNTU_CODENAME}" ]', content)
        self.assertIn("PIXELFLUX_WAYLAND=true", content)
        self.assertIn("XKB_CONFIG_ROOT=/usr/share/X11/xkb", content)
        self.assertIn("      xwayland \\\n", content)
        self.assertNotIn("linuxserver/rdesktop", content)
        self.assertNotIn("xrdp", content.lower())
        self.assertIn("Dockerfile.compat", workflow)
        self.assertIn("sha256:a784bc01de33e51655d8e179fac80077a055aee79d9b01c4c7839c6aebbc01ae", workflow)
        self.assertIn("sha256:0d16f40efc3663125f1004b70feff091f2d13771f1cc005ea30c28bd777e05e2", workflow)

    def test_focal_selkies_python_is_isolated_from_system_python(self) -> None:
        content = SELKIES_COMPAT_DOCKERFILE.read_text()

        self.assertIn("ARG SELKIES_PYTHON_VERSION=3.12.11", content)
        self.assertIn(
            "ARG SELKIES_PYTHON_SHA256=7b8d59af8216044d2313de8120bfc2cc00a9bd2e542f15795e1d616c51faf3d6",
            content,
        )
        self.assertIn("/opt/selkies-python", content)
        self.assertIn("/opt/selkies-venv", content)
        self.assertNotIn("/usr/bin/python3 ->", content)
        self.assertNotIn("update-alternatives", content)
        self.assertNotIn("rm -f /usr/bin/python3", content)

    def test_compat_selkies_uses_private_modern_libxkbcommon(self) -> None:
        content = SELKIES_COMPAT_DOCKERFILE.read_text()

        self.assertIn("ARG LIBXKBCOMMON_VERSION=1.5.0", content)
        self.assertIn(
            "ARG LIBXKBCOMMON_SHA256="
            "560f11c4bbbca10f495f3ef7d3a6aa4ca62b4f8fb0b52e7d459d18a26e46e017",
            content,
        )
        self.assertIn("/opt/selkies-xkbcommon", content)
        self.assertIn("PKG_CONFIG_PATH=/opt/selkies-xkbcommon/lib/pkgconfig", content)
        self.assertIn("CFLAGS=-I/opt/selkies-xkbcommon/include", content)
        self.assertIn("LDFLAGS=-L/opt/selkies-xkbcommon/lib", content)
        self.assertIn("/etc/ld.so.conf.d/selkies-xkbcommon.conf", content)
        self.assertIn("ninja -C /tmp/xkbcommon-src/build install", content)
        self.assertNotIn("meson compile", content)
        self.assertIn(
            "from pixelflux import CaptureSettings, ScreenCapture; "
            "from selkies import media_pipeline; "
            "assert media_pipeline.CaptureSettings is CaptureSettings; "
            "assert media_pipeline.ScreenCapture is ScreenCapture",
            content,
        )

    def test_compat_selkies_uses_private_modern_libva(self) -> None:
        content = SELKIES_COMPAT_DOCKERFILE.read_text()

        self.assertIn("ARG LIBVA_VERSION=2.22.0", content)
        self.assertIn(
            "ARG LIBVA_SHA256="
            "467c418c2640a178c6baad5be2e00d569842123763b80507721ab87eb7af8735",
            content,
        )
        self.assertIn("/opt/selkies-libva", content)
        self.assertIn("COPY --from=selkies_python_builder /opt/selkies-libva/", content)
        self.assertIn(
            "LD_LIBRARY_PATH=/opt/selkies-libva/lib:/opt/selkies-xkbcommon/lib",
            content,
        )
        self.assertIn("-Dwith_x11=yes", content)
        self.assertIn("-Dwith_wayland=no", content)
        builder_dependencies = content.split(
            "FROM ${UBUNTU_BASE_IMAGE} AS selkies_python_builder", 1
        )[1].split("ADD --checksum", 1)[0]
        self.assertIn("libgbm1", builder_dependencies)
        self.assertIn("libpixman-1-0", builder_dependencies)
        self.assertIn("from pixelflux import CaptureSettings, ScreenCapture", content)

    def test_compat_runtime_uses_pinned_selkies_and_patched_target_xvfb(self) -> None:
        content = SELKIES_COMPAT_DOCKERFILE.read_text()

        self.assertIn(
            "ghcr.io/linuxserver/baseimage-selkies@sha256:"
            "7f4f69e5184e3e1876e96ca0c5d66bc3ef5ffe3d47a910cbf6366fe59db3e972",
            content,
        )
        self.assertIn("xvfb", content)
        self.assertIn("ARG MESON_VERSION=1.5.2", content)
        self.assertIn(
            "ARG MESON_SHA256="
            "f955e09ab0d71ef180ae85df65991d58ed8430323de7d77a37e11c9ea630910b",
            content,
        )
        self.assertIn(
            "github.com/mesonbuild/meson/releases/download/"
            "${MESON_VERSION}/meson-${MESON_VERSION}.tar.gz",
            content,
        )
        self.assertIn("python3 /opt/meson/meson.py setup", content)
        self.assertIn("python3-distutils", content)
        self.assertIn("ARG XORGPROTO_VERSION=2024.1", content)
        self.assertIn(
            "ARG XORGPROTO_SHA256="
            "372225fd40815b8423547f5d890c5debc72e88b91088fbfb13158c20495ccb59",
            content,
        )
        self.assertIn(
            "xorg.freedesktop.org/archive/individual/proto/"
            "xorgproto-${XORGPROTO_VERSION}.tar.xz",
            content,
        )
        self.assertIn("--prefix=/opt/xorgproto", content)
        self.assertIn("ninja -C /tmp/xorgproto-build install", content)
        self.assertIn(
            "PKG_CONFIG_PATH=/opt/xwayland/lib/pkgconfig:"
            "/opt/xorgproto/share/pkgconfig",
            content,
        )
        self.assertIn("xfonts-utils", content)
        self.assertIn("ARG XORG_SERVER_VERSION=21.1.24", content)
        self.assertIn(
            "ARG XORG_SERVER_SHA256="
            "1a4eb36ca65cc3b1b936566d677a9786e13c11cd5806e951ac55f3f5ce3984af",
            content,
        )
        self.assertIn(
            "xorg.freedesktop.org/archive/individual/xserver/"
            "xorg-server-${XORG_SERVER_VERSION}.tar.xz",
            content,
        )
        self.assertIn(
            "COPY patches/xorg-server-21.1.24-xvfb-dri3.patch "
            "/tmp/xorg-server-21.1.24-xvfb-dri3.patch",
            content,
        )
        self.assertIn(
            "patch --fuzz=0 --batch --forward -p1 < "
            "/tmp/xorg-server-21.1.24-xvfb-dri3.patch",
            content,
        )

        self.assertIn("meson setup", content)
        self.assertIn("ninja -C", content)
        self.assertNotIn("apt-get source xorg-server", content)
        self.assertNotIn("dpkg-buildpackage", content)
        self.assertIn("COPY --from=xvfb_builder /usr/local/bin/Xvfb /usr/local/bin/Xvfb", content)
        self.assertIn("Xvfb -help 2>&1 | grep -F -- '-vfbdevice device-path'", content)
        self.assertIn("ARG WAYLAND_VERSION=1.23.1", content)
        self.assertIn(
            "ARG WAYLAND_SHA256="
            "864fb2a8399e2d0ec39d56e9d9b753c093775beadc6022ce81f441929a81e5ed",
            content,
        )
        self.assertIn("ARG WAYLAND_PROTOCOLS_VERSION=1.34", content)
        self.assertIn(
            "ARG WAYLAND_PROTOCOLS_SHA256="
            "c59b27cacd85f60baf4ee5f80df5c0d15760ead6a2432b00ab7e2e0574dcafeb",
            content,
        )
        self.assertIn("ARG LIBDRM_VERSION=2.4.124", content)
        self.assertIn(
            "ARG LIBDRM_SHA256="
            "ac36293f61ca4aafaf4b16a2a7afff312aa4f5c37c9fbd797de9e3c0863ca379",
            content,
        )
        self.assertIn("-Dtests=false", content)
        self.assertIn("ARG LIBXCVT_VERSION=0.1.3", content)
        self.assertIn(
            "ARG LIBXCVT_SHA256="
            "a929998a8767de7dfa36d6da4751cdbeef34ed630714f2f4a767b351f2442e01",
            content,
        )
        self.assertNotIn("/opt/libxcvt", content)
        self.assertIn("ARG XWAYLAND_VERSION=24.1.13", content)
        self.assertIn(
            "ARG XWAYLAND_SHA256="
            "173aea3d6f79609164c04528e1c8e4c9b60fcd59391c3c9dad4667297d727fb6",
            content,
        )
        self.assertIn(
            "xorg.freedesktop.org/archive/individual/xserver/"
            "xwayland-${XWAYLAND_VERSION}.tar.xz",
            content,
        )
        self.assertIn("-Dxkb_dir=/usr/share/X11/xkb", content)
        self.assertIn("-Dxkb_bin_dir=/usr/bin", content)
        self.assertNotIn("-Dxwayland=true", content)
        self.assertIn(
            "COPY --from=xvfb_builder /opt/xwayland/ /opt/xwayland/",
            content,
        )
        self.assertIn("/opt/xwayland/bin/Xwayland -version", content)
        self.assertIn("xwayland_version=\"$(", content)
        self.assertIn("-version 2>&1 || :", content)
        self.assertIn(
            "grep -F 'The X.Org Foundation Xwayland Version 24.1.13'",
            content,
        )
        self.assertIn("LD_LIBRARY_PATH=/opt/xwayland/lib", content)
        self.assertIn("DISABLE_DRI3=false", content)
        self.assertNotIn("lscr.io/linuxserver/xvfb", content)
        self.assertNotIn("COPY --from=current_selkies /usr/bin/Xvfb", content)
        self.assertIn("COPY pyproject.toml uv.lock /tmp/selkies-lock/", content)
        self.assertIn("SELKIES_REVISION=348bc4f61da66198573e7e57db9a266aca1991d5", content)

    def test_patched_xvfb_destroys_gbm_buffers_before_their_device(self) -> None:
        patch_content = XVFB_DRI3_PATCH.read_text()
        buffer_destroy = "gbm_bo_destroy(pvfb->front_bo);"
        device_destroy = "gbm_device_destroy(pvfb->gbm);"

        self.assertIn(buffer_destroy, patch_content)
        self.assertIn(device_destroy, patch_content)
        self.assertLess(
            patch_content.index(buffer_destroy), patch_content.index(device_destroy)
        )
        self.assertNotIn("gbm_device_destroy(glamor_egl->gbm);", patch_content)

    def test_selkies_defaults_to_full_hd_wayland_gpu_streaming(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()

        for setting in (
            "PIXELFLUX_WAYLAND=true",
            "SELKIES_IS_MANUAL_RESOLUTION_MODE=true",
            "SELKIES_MANUAL_WIDTH=1920",
            "SELKIES_MANUAL_HEIGHT=1080",
            "SELKIES_SCALING_DPI=96",
            "SELKIES_FRAMERATE=60",
            "NVIDIA_DRIVER_CAPABILITIES=all",
        ):
            self.assertIn(setting, content)

    def test_selkies_does_not_upgrade_pixelflux_without_matching_selkies(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()

        for line in content.splitlines():
            if "pip install" in line and "--no-deps" in line:
                self.assertNotIn("pixelflux", line.lower())

    def test_selkies_uses_one_pinned_matched_application_stack(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()
        pyproject = SELKIES_PYPROJECT.read_text()
        uv_lock = SELKIES_UV_LOCK.read_text()

        self.assertIn(
            "FROM ghcr.io/linuxserver/baseimage-selkies@sha256:"
            "7f4f69e5184e3e1876e96ca0c5d66bc3ef5ffe3d47a910cbf6366fe59db3e972 "
            "AS current_selkies",
            content,
        )
        self.assertIn(
            "ARG SELKIES_REVISION=348bc4f61da66198573e7e57db9a266aca1991d5",
            content,
        )
        self.assertIn(
            "ADD --checksum=sha256:"
            "c18f7292cf895f44769e19347d9acb9296a907aa0067fe813d1dd2e7d0413f5d",
            content,
        )
        self.assertIn("COPY --from=current_selkies /usr/share/selkies/ /usr/share/selkies/", content)
        self.assertIn("COPY pyproject.toml uv.lock /tmp/selkies-lock/", content)
        self.assertIn('"pixelflux==2.0.0"', pyproject)
        self.assertIn('"pcmflux==2.0.0"', pyproject)
        self.assertIn('"setuptools==84.0.0"', pyproject)
        self.assertIn('revision = 3', uv_lock)
        self.assertIn('name = "pixelflux"', uv_lock)
        self.assertIn('name = "pcmflux"', uv_lock)
        self.assertIn("uv export --locked", content)
        self.assertNotIn("uv export --frozen", content)
        self.assertIn("uv pip sync", content)
        self.assertNotIn("StripeCallback", content)

    def test_selkies_python_dependencies_are_artifact_hash_locked(self) -> None:
        self.assertTrue(SELKIES_PYPROJECT.is_file())
        self.assertTrue(SELKIES_UV_LOCK.is_file())
        self.assertFalse(SELKIES_REQUIREMENTS.exists())

        lock = SELKIES_UV_LOCK.read_text()
        self.assertRegex(lock, r'sdist = \{ url = ".+", hash = "sha256:[0-9a-f]{64}"')
        self.assertRegex(lock, r'\{ url = ".+", hash = "sha256:[0-9a-f]{64}"')
        self.assertNotIn("/archive/master.zip", lock)

        for dockerfile in (SELKIES_DOCKERFILE, SELKIES_COMPAT_DOCKERFILE):
            content = dockerfile.read_text()
            self.assertIn("COPY pyproject.toml uv.lock /tmp/selkies-lock/", content)
            self.assertIn("uv export --locked", content)
            self.assertNotIn("uv export --frozen", content)
            self.assertIn("uv pip sync", content)
            self.assertIn("--require-hashes", content)
            self.assertNotIn("selkies-requirements.txt", content)

    def test_selkies_internal_user_is_build_time_configurable(self) -> None:
        for dockerfile in (SELKIES_DOCKERFILE, SELKIES_COMPAT_DOCKERFILE):
            content = dockerfile.read_text()
            self.assertIn("ARG DESKTOP_USER=ivar", content)
            self.assertIn("DESKTOP_USER=${DESKTOP_USER}", content)
            self.assertIn(
                "COPY build-scripts/configure-desktop-user.py ", content
            )
            self.assertIn(
                '/usr/bin/python3 /tmp/configure-desktop-user.py --user "${DESKTOP_USER}"',
                content,
            )
            self.assertIn('groupmod --new-name "${DESKTOP_USER}" abc', content)
            self.assertIn('usermod --login "${DESKTOP_USER}" abc', content)
            self.assertIn('getent passwd "${DESKTOP_USER}"', content)
            self.assertIn('getent group "${DESKTOP_USER}"', content)

        readme = README.read_text()
        self.assertIn("DESKTOP_USER", readme)
        self.assertIn("defaults to `ivar`", readme)
        self.assertIn("independent of `CUSTOM_USER`", readme)

    def test_desktop_user_rewriter_is_strict_and_rewrites_runtime_contract(self) -> None:
        self.assertTrue(DESKTOP_USER_REWRITER.is_file(), DESKTOP_USER_REWRITER)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            service = root / "etc" / "s6-overlay" / "s6-rc.d" / "svc-test" / "run"
            ssh_config = (
                root
                / "etc"
                / "ssh"
                / "sshd_config.d"
                / "10-container-desktop.conf"
            )
            crontab = root / "defaults" / "crontabs" / "abc"
            for path in (service, ssh_config, crontab):
                path.parent.mkdir(parents=True, exist_ok=True)
            service.write_text(
                "as_abc() { s6-setuidgid abc \"$@\"; }\nchown abc:abc /config\n"
            )
            ssh_config.write_text("AllowUsers abc\n")
            crontab.write_text("# abc desktop crontab\n")

            result = subprocess.run(
                [
                    "python3",
                    DESKTOP_USER_REWRITER,
                    "--root",
                    root,
                    "--user",
                    "taltech",
                ],
                check=False,
                capture_output=True,
                text=True,
            )

            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                'as_taltech() { s6-setuidgid taltech "$@"; }\n'
                "chown taltech:taltech /config\n",
                service.read_text(),
            )
            self.assertEqual("AllowUsers taltech\n", ssh_config.read_text())
            self.assertFalse(crontab.exists())
            self.assertEqual(
                "# taltech desktop crontab\n",
                (crontab.with_name("taltech")).read_text(),
            )

        for invalid_user in ("", "root", "UPPER", "9starts-with-digit", "has space"):
            result = subprocess.run(
                ["python3", DESKTOP_USER_REWRITER, "--user", invalid_user],
                check=False,
                capture_output=True,
                text=True,
            )
            self.assertEqual(64, result.returncode, (invalid_user, result.stderr))

    def test_selkies_installs_headers_for_pinned_native_extensions(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()

        self.assertIn("python3-dev", content)
        self.assertIn("libxkbcommon-dev", content)

    def test_selkies_verifies_installed_versions_through_package_metadata(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()

        self.assertIn("from importlib.metadata import version", content)
        self.assertIn("version(\"pixelflux\")", content)
        self.assertIn("version(\"pcmflux\")", content)
        self.assertNotIn("pixelflux.__version__", content)
        self.assertNotIn("pcmflux.__version__", content)

    def test_selkies_clears_stale_wayland_runtime_before_startup(self) -> None:
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()

        self.assertIn("xdg_runtime=/config/.XDG", init)
        self.assertIn('! -d "${xdg_runtime}"', init)
        self.assertIn('find "${xdg_runtime}" -xdev -mindepth 1 -delete', init)

    def test_selkies_creates_private_pixelflux_runtime_directory(self) -> None:
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()

        self.assertIn("install -d -o abc -g abc -m 0700 /run/pixelflux", init)

    def test_selkies_has_exact_ivar_lab_wallpaper_on_every_lts(self) -> None:
        background = (
            SELKIES_FILES / "etc" / "dconf" / "db" / "local.d" / "90-selkies-background"
        )

        self.assertTrue(IVAR_WALLPAPER.is_file())
        image = IVAR_WALLPAPER.read_bytes()
        self.assertEqual(IVAR_WALLPAPER_SHA256, hashlib.sha256(image).hexdigest())
        self.assertEqual(b"\x89PNG\r\n\x1a\n", image[:8])
        self.assertEqual((1920, 1080), struct.unpack(">II", image[16:24]))

        self.assertTrue(background.is_file())
        self.assertIn("/usr/share/backgrounds/taltech/ivar-lab.png", background.read_text())
        for dockerfile in (SELKIES_DOCKERFILE, SELKIES_COMPAT_DOCKERFILE):
            content = dockerfile.read_text()
            self.assertIn(
                "COPY files/usr/share/backgrounds/taltech/ "
                "/usr/share/backgrounds/taltech/",
                content,
            )
            self.assertNotIn("ubuntu-mate-wallpapers-", content)

    def test_selkies_uses_an_installed_dark_theme_on_every_lts(self) -> None:
        mate_defaults = (
            ROOT / "files" / "etc" / "dconf" / "db" / "local.d" / "mate-desktop.conf"
        ).read_text()
        marco_defaults = (
            ROOT / "files" / "etc" / "dconf" / "db" / "local.d" / "mate-other.conf"
        ).read_text()

        self.assertIn("gtk-theme='Yaru-dark'", mate_defaults)
        self.assertNotIn("gtk-theme='Materia-dark'", mate_defaults)
        self.assertIn("theme='Yaru-dark'", marco_defaults)
        self.assertNotIn("theme='Materia-dark'", marco_defaults)
        for dockerfile in (SELKIES_DOCKERFILE, SELKIES_COMPAT_DOCKERFILE):
            self.assertIn("yaru-theme-gtk", dockerfile.read_text())

    def test_selkies_migrates_only_blank_or_stock_light_window_theme(self) -> None:
        helper = SELKIES_FILES / "defaults" / "start-mate-session.sh"
        content = helper.read_text()

        self.assertIn("org.mate.Marco.general theme", content)
        self.assertIn('[[ ${marco_theme} == "\'\'" || ${marco_theme} == "\'Yaru\'" ]]', content)
        self.assertIn("gsettings set org.mate.Marco.general theme 'Yaru-dark'", content)
        self.assertNotIn("Materia-dark", content)

    def test_selkies_initializes_only_blank_persisted_wallpaper(self) -> None:
        helper = SELKIES_FILES / "defaults" / "start-mate-session.sh"
        content = helper.read_text()

        self.assertIn('if [[ ${picture_filename} == "\'\'" ]]; then', content)
        self.assertIn("/usr/share/backgrounds/taltech/ivar-lab.png", content)
        self.assertIn("exec /usr/bin/mate-session", content)
        for name in ("startwm.sh", "startwm_wayland.sh"):
            startwm = (SELKIES_FILES / "defaults" / name).read_text()
            self.assertIn("/defaults/start-mate-session.sh", startwm)

    def test_selkies_requires_web_credentials_and_has_no_remote_root_path(self) -> None:
        content = SELKIES_DOCKERFILE.read_text()
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()
        ssh_config = (
            SELKIES_FILES
            / "etc"
            / "ssh"
            / "sshd_config.d"
            / "10-container-desktop.conf"
        ).read_text()

        self.assertIn("START_DOCKER=false", content)
        self.assertIn("DISABLE_SUDO=true", content)
        self.assertIn("gpasswd --delete abc sudo", content)
        self.assertIn("passwd --lock abc", content)
        self.assertIn("usermod --shell /bin/bash abc", content)
        self.assertIn("CUSTOM_USER", init)
        self.assertIn("PASSWORD", init)
        self.assertIn("must be set", init)
        self.assertIn("chown root:abc /run/s6/container_environment/PASSWORD", init)
        self.assertIn("chmod 0640 /run/s6/container_environment/PASSWORD", init)
        self.assertIn("PasswordAuthentication no", ssh_config)
        self.assertIn("KbdInteractiveAuthentication no", ssh_config)
        self.assertIn("PermitRootLogin no", ssh_config)
        self.assertIn("PubkeyAuthentication yes", ssh_config)

    def test_selkies_ssh_state_and_s6_services_are_native(self) -> None:
        init = SELKIES_S6_ROOT / "init-taltech-selkies" / "run"
        ssh_run = SELKIES_S6_ROOT / "svc-sshd" / "run"
        startwm = SELKIES_FILES / "defaults" / "startwm_wayland.sh"

        for path in (init, ssh_run, startwm):
            self.assertTrue(path.is_file(), path)
            self.assertTrue(path.stat().st_mode & stat.S_IXUSR, path)

        init_content = init.read_text()
        self.assertIn("state_root=/var/lib/taltech-desktop", init_content)
        self.assertIn('ssh_secret_dir="${state_root}/ssh"', init_content)
        self.assertNotIn("/config/.container-secrets", init_content)
        self.assertTrue(
            (SELKIES_S6_ROOT / "init-selkies" / "dependencies.d" / "init-taltech-selkies").is_file()
        )
        for service in ("init-taltech-selkies", "svc-sshd"):
            self.assertTrue((SELKIES_S6_ROOT / "user" / "contents.d" / service).is_file())

        startwm_content = startwm.read_text()
        self.assertIn("Xwayland :1", startwm_content)
        self.assertIn("mate-session", startwm_content)

    def test_selkies_repairs_persisted_runtime_directory_ownership(self) -> None:
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()

        self.assertIn('chown -h abc:abc "${xdg_runtime}"', init)
        self.assertIn("chown -h abc:abc /config/.ssh", init)
        self.assertIn('chmod 0700 "${xdg_runtime}"', init)
        self.assertIn("chmod 0700 /config/.ssh", init)

    def test_selkies_repairs_persisted_cache_ownership_safely(self) -> None:
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()

        self.assertIn("cache_root=/config/.cache", init)
        self.assertIn('! -d "${cache_root}"', init)
        self.assertIn('find "${cache_root}" -xdev -exec chown -h abc:abc {} +', init)
        self.assertNotIn('chown -R abc:abc "${cache_root}"', init)

    def test_selkies_repairs_persisted_desktop_config_ownership_safely(self) -> None:
        init = (SELKIES_S6_ROOT / "init-taltech-selkies" / "run").read_text()

        self.assertIn("-L /config/.config", init)
        self.assertIn(
            "find /config/.config -xdev -exec chown -h abc:abc {} +", init
        )
        self.assertNotIn("chown -hR abc:abc /config/.config", init)


if __name__ == "__main__":
    unittest.main()
