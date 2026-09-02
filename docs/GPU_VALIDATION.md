# GPU validation matrix

GPU support is accepted per image, host GPU, driver, architecture, and
remote-session path. Device visibility or a successful `nvidia-smi` call alone
is not evidence that applications in Selkies use hardware rendering.

## Acceptance procedure

For each image/host combination:

1. Record the host OS, kernel, GPU model, driver version, container runtime, image tag, image digest, and architecture.
2. Start the container with the required device access:
   - NVIDIA: `--gpus all`
   - Intel/AMD/DRM: `--device=/dev/dri:/dev/dri`
3. Open a real Selkies browser session for the image lane.
4. In a terminal inside that session, run `taltech-verify-gpu`.
5. Require `GPU_ACCELERATION=PASS` and retain the reported OpenGL vendor, renderer, and version.
6. For ROS images, start RViz/RViz2 in the same session, load a robot model, and confirm responsive hardware-rendered interaction without renderer fallback or process errors.
7. Restart and recreate the container with the same volumes, then repeat the verifier to catch device-group and session-start regressions.

Use `EXPECTED_RENDERER_REGEX` to bind a run to the intended GPU when a host has several renderers:

```bash
EXPECTED_RENDERER_REGEX='NVIDIA|AMD|Intel' taltech-verify-gpu
```

## Required matrix

| Image | Remote path | amd64 NVIDIA | amd64 Intel/AMD | arm64 DRM | ROS GUI check |
|---|---|---|---|---|---|
| Ubuntu 20.04 Focal | Selkies/Wayland | Passed (rendering + H.264/NVENC, 2026-08-30) | Pending | Pending | Noetic RViz pending |
| Ubuntu 22.04 Jammy | Selkies/Wayland | Passed (rendering + H.264/NVENC, 2026-08-30) | Pending | Pending | Humble RViz2 pending |
| Ubuntu 24.04 Noble | Selkies/Wayland | Passed (rendering + H.264/NVENC, 2026-08-29) | Pending | Pending | Jazzy on Selkies partial |
| Ubuntu 26.04 Resolute | Selkies/Wayland | Passed (rendering + H.264/NVENC, 2026-08-30) | Pending | Pending | ROS image deferred |

A build-only or device-visibility result remains **Pending**. Mark a cell passed
only after the renderer passes inside the real remote session. Application
rendering and remote-stream encoding are separate claims and must be recorded
separately.

## Verified runs

### Four-lane H.264/NVENC result — amd64 NVIDIA

All four published Ubuntu lanes passed on `lab-001` with the NVIDIA GeForce
RTX 4090 D and driver `580.126.09`. A browser session activated each Selkies
stream; the backend reported `NVENC Encoder initialized successfully`,
`Mode: H264 (NVENC)`, and `Res: 1920x1080`. Captured elementary streams were
then probed and fully decoded with FFmpeg. H.264/NVENC proof: `PASS`.

| Ubuntu | Tested image | Decoded stream evidence | Peak sampled encoder use |
|---|---|---|---|
| Focal 20.04 | `taltech/ubuntu-desktop-selkies:focal-candidate-v26` (`sha256:aa05c948e046615825d90b384f139428f86c0293ad3e12c6050e720abfaa88d2`) | H.264 High, yuv420p, 1920×1080, 1,497 decoded frames | 7% |
| Jammy 22.04 | `taltech/ubuntu-desktop-selkies:jammy-review-v3` (`sha256:454766567db6e78ba479bbdb7b5177829998650986fb746bee57c796c845a4b3`) | H.264 High, yuv420p, 1920×1080, 1,495 decoded frames | 13% |
| Noble 24.04 | `taltech/ubuntu-desktop-selkies:noble-matched-v8` (`sha256:8e76a77b1d8b5a6472665ab353479dade28507db92a8e832d8c0289d6bd2f780`) | H.264 High, yuv420p, 1920×1080, approximately 20 seconds; clean FFmpeg decode | 7% |
| Resolute 26.04 | `taltech/ubuntu-desktop-selkies:resolute-review-v2` (`sha256:032719e41ef74d002259c84f03ffcb5c596ca870e0bb28d307302a33dd8d72a5`) | H.264 High, yuv420p, 1920×1080, 1,467 decoded frames | 7% |

This proves hardware-backed NVIDIA application rendering and NVENC H.264 for
these exact amd64 image/host combinations. It does not prove a zero-copy path,
sustained delivery at the configured maximum frame rate, Intel/AMD encoding,
or arm64 behavior.

### Ubuntu 24.04 Noble — amd64 NVIDIA Selkies/Wayland

- Date: 2026-08-29
- Host: `lab-001`, Ubuntu 25.04, kernel `6.14.0-37-generic`, `x86_64`
- GPU: NVIDIA GeForce RTX 4090 D
- NVIDIA driver: `580.126.09`
- NVIDIA Container Toolkit: `1.20.0`
- Docker Engine: `29.2.1`
- Image tag: `taltech/ubuntu-desktop-selkies:noble-matched-v8`
- Image ID: `sha256:8e76a77b1d8b5a6472665ab353479dade28507db92a8e832d8c0289d6bd2f780`
- Remote-session path: Selkies/Wayland with Xwayland, MATE, 1920×1080 at 60 FPS
- OpenGL renderer: `NVIDIA GeForce RTX 4090 D/PCIe/SSE2`
- Result: `GPU_ACCELERATION=PASS`
- Runtime evidence: Selkies and Xwayland appeared as NVIDIA graphics clients;
  PulseAudio reported `server=pulseaudio,sink=output`; parsed Selkies settings
  had `use_cpu=False`; the backend initialized NVENC H.264; the captured stream
  was successfully decoded
- Persistence: user state, SSH host identity, key-only SSH, and GPU validation
  survived container recreation with the same volumes

This establishes hardware application rendering and NVENC H.264 for this exact
image, host, and Selkies session. Zero-copy operation remains unverified. It
does not establish the pending Intel/AMD or arm64 cells.

### ROS 2 Jazzy RViz2 — amd64 NVIDIA Selkies/Wayland

- Date: 2026-08-29
- Host, GPU, driver, runtime, and remote-session path: same `lab-001`
  Selkies/Wayland configuration recorded above
- Image tag: `taltech/ros-desktop-selkies:jazzy-v1`
- Image ID: `sha256:3f3090928451bcc9bf85686d82bb3b5bf1f9a0b2af251b1c438330db319163a7`
- OpenGL vendor: `NVIDIA Corporation`
- OpenGL renderer: `NVIDIA GeForce RTX 4090 D/PCIe/SSE2`
- OpenGL version: `4.6.0 NVIDIA 580.126.09`
- Result: ROS environment and persistent workspace checks passed; a local ROS
  2 talker and one-shot `/chatter` subscriber exchanged data; the GPU verifier
  passed; RViz2 remained alive for the 20-second smoke window
- Persistence: the `/config` marker and root-owned SSH host key survived
  recreation
- After recreation, the harness repeated web authentication and ROS/DDS checks;
  each passed again
- Startup without web credentials exposed no web or SSH listeners
- External key-only SSH was verified after installing the test client's public
  key

This is a **partial** ROS GUI result. It establishes Jazzy startup, basic DDS,
hardware OpenGL, and RViz2 process stability in the tested Selkies session, but
robot-model interaction remains untested. This ROS-specific smoke did not
separately repeat the encoder capture; the base image's NVENC result is recorded
above, while zero-copy operation remains unverified.

### Ubuntu 24.04 Noble — amd64 NVIDIA XRDP

This is a historical result from the project-owned Noble XRDP candidate. The
published Noble lane now uses Selkies; this record remains useful for comparing
the two remote-session paths.

- Date: 2026-08-29
- Host: `lab-001`, Ubuntu 25.04, kernel `6.14.0-37-generic`, `x86_64`
- GPU: NVIDIA GeForce RTX 4090 D
- NVIDIA driver: `580.126.09`
- NVIDIA Container Toolkit: `1.20.0`
- Docker Engine: `29.2.1`
- Image tag: `taltechivarlab/ubuntu-desktop:test-24.04`
- Image ID: `sha256:b1e91b9d89c8629095d143411da56b4845669cb0911f7622d688f45140616b84`
- Source candidate identity: `30ceb70af9aa4df123ed8d040215fd7b5edd0144959c88375d112d73da0b1e0a`
- Remote-session path: FreeRDP client to a real XRDP/MATE session on display `:10.0`
- OpenGL vendor: `Mesa`
- OpenGL renderer: `zink Vulkan 1.4(NVIDIA GeForce RTX 4090 D (NVIDIA_PROPRIETARY))`
- OpenGL version: `4.6 (Core Profile) Mesa 25.2.8-0ubuntu0.24.04.2`
- Result: `GPU_ACCELERATION=PASS` in two consecutive rounds, including container recreation with the same persistent volumes

The renderer is Mesa Zink over the NVIDIA Vulkan driver, not a software renderer such as llvmpipe. This proves hardware rendering for this exact host/image/XRDP combination; it does not establish the pending Intel/AMD, arm64, or other Ubuntu-version cells.

### ROS 2 Jazzy RViz2 — amd64 NVIDIA XRDP (historical base candidate)

- Date: 2026-08-29
- Host, GPU, driver, runtime, and remote-session path: same `lab-001` configuration recorded above
- Image tag: `taltechivarlab/ros-desktop:test-jazzy`
- Image ID: `sha256:f4939704b3ce9097c2c73f399b6f9a46d7dbf3f29f013f2dde681614a5b5f327`
- ROS source candidate identity: `d6cafdb9a70f5f60f8ec286cf414eea4bf3ad450168651abfc7f286e96a95f75`
- Base source candidate identity: `30ceb70af9aa4df123ed8d040215fd7b5edd0144959c88375d112d73da0b1e0a`
- OpenGL renderer: `zink Vulkan 1.4(NVIDIA GeForce RTX 4090 D (NVIDIA_PROPRIETARY))`
- RViz2 OpenGL report: `4.6 (GLSL 4.6)`
- Result: `GPU_ACCELERATION=PASS`; RViz2 remained alive in the real XRDP/MATE session for the 20-second smoke window and terminated cleanly

This verifies that RViz2 starts and retains a hardware-rendered OpenGL context in this exact Jazzy/Noble/NVIDIA XRDP combination. The full ROS GUI matrix cell remains partial until a robot model is loaded and interactive rendering is checked; it does not establish Humble, Noetic, Intel/AMD, or arm64 behavior.
