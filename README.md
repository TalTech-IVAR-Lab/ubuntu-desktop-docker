# Ubuntu Desktop Docker

[![Ubuntu versions: 20.04, 22.04, 24.04, and 26.04](https://img.shields.io/badge/Ubuntu-20.04%20%7C%2022.04%20%7C%2024.04%20%7C%2026.04-informational?logo=ubuntu)](#image-roster)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/TalTech-IVAR-Lab/ubuntu-desktop-docker/docker_build.yml?branch=main&logo=GitHub)](https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker/actions)
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/taltechivarlab/ubuntu-desktop?logo=docker)](https://hub.docker.com/r/taltechivarlab/ubuntu-desktop)

> Ubuntu desktop containers for [TalTech IVAR Lab][taltech_ivar_lab], with a
> browser-native Selkies desktop across every supported Ubuntu LTS release.

These images provide persistent development desktops and form the base of our
[ROS Desktop][ros_desktop_github] images.

## Why and how

The [motivation document][docs_motivation] describes the original use case and
design goals.

## What's included

All images include:

- MATE desktop
- [OpenSSH] server
- Persistent user home under `/config`, with root-owned host keys in a separate state volume
- `PUID`/`PGID` user mapping inherited from the LinuxServer base
- Command line packages:
  - [Terminator] as the default terminal application
  - [Zsh]
  - Utilities:
      - [htop] process monitor
      - Neofetch on Focal/Jammy/Noble; Fastfetch on Resolute
      - [nmap] network mapping tool
- GUI packages:
  - Yaru Dark theme with the packaged Papirus Dark icon set
  - IVAR Lab Full HD wallpaper
  - [Plank] dock

All published images use Selkies over HTTPS with a pinned, matched
Selkies/PixelFlux/PCMFlux frontend and backend. `Dockerfile.compat` places that
stack over LinuxServer's Focal and Jammy Ubuntu+s6 bases; the main `Dockerfile`
builds the native Noble and Resolute lanes.

## Image roster

| Ubuntu | Tag | Intended ROS base |
|---|---|---|
| Ubuntu 26.04 Resolute | `26.04` | Future ROS 2 LTS images |
| Ubuntu 24.04 Noble | `24.04`, `latest` | ROS 2 Jazzy |
| Ubuntu 22.04 Jammy | `22.04` | ROS 2 Humble |
| Ubuntu 20.04 Focal | `20.04` | ROS Noetic (upstream EOL) |

Versioned tags select the corresponding Ubuntu release. `latest` points to
Ubuntu 24.04 Noble.

## Usage

### Quick start

Create a password file containing at least 12 characters and restrict it to the
current user:

```bash
umask 077
openssl rand -base64 32 > "$HOME/.taltech-selkies-password"
```

Then launch the required image tag on a trusted network or VPN. The example
uses Noble; `20.04`, `22.04`, and `26.04` use the same runtime interface:

```bash
docker run -d \
  --name=ubuntu-desktop \
  --gpus=all \
  --device=/dev/dri:/dev/dri \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Tallinn \
  -e CUSTOM_USER=taltech \
  -e PASSWORD_FILE=/run/secrets/selkies-password \
  -p 3001:3001 `# https` \
  -p 2222:22 `# ssh` \
  -v "$HOME/.taltech-selkies-password:/run/secrets/selkies-password:ro" \
  -v ubuntu-desktop-config:/config \
  -v ubuntu-desktop-state:/var/lib/taltech-desktop \
  --shm-size="1gb" \
  --restart unless-stopped \
  taltechivarlab/ubuntu-desktop:24.04
```

Open `https://HOST:3001/`. The self-signed certificate must be accepted by the
client or replaced at a reverse proxy. The desktop targets 1920×1080, 96 DPI,
and up to 60 FPS; actual delivery depends on the browser, GPU, and network.
Omit `--gpus=all` on non-NVIDIA hosts; retain the DRM mapping where available.
With the default `AUTO_GPU=true`, the first mapped `/dev/dri/renderD*` device is
used for both rendering and encoding so PixelFlux can use its zero-copy path.
On multi-GPU hosts, set both `DRINODE` and `DRI_NODE` to the same render device;
setting them to different devices deliberately enables CPU readback.

SSH is key-only. Add the desired public keys to
`/config/.ssh/authorized_keys`; web authentication does not unlock the Linux
account. The remote user has no passwordless sudo and no Docker socket.

The internal Linux desktop account defaults to `ivar`. To use a different
account name in a custom build, pass `--build-arg DESKTOP_USER=taltech`.
`DESKTOP_USER` is fixed at build time and is independent of `CUSTOM_USER`,
which controls only the Selkies web login. Changing it does not change the
persistent home path (`/config`) or the runtime `PUID`/`PGID` mapping.

Use all remote access only on a trusted network or behind a VPN. Do not publish
the ports directly to the Internet. The separate state volume keeps root-owned
host keys outside user-writable `/config`.

> ☝ You can [stop][docker_stop], [restart][docker_start], or replace the container without losing either named volume.
> Delete those volumes explicitly only when you intend to discard user data and regenerate the SSH host identity.

### Advanced usage

For more advanced use cases, such as opening additional ports and enabling
hardware graphics acceleration, refer to [Advanced Usage][docs_advanced_usage]
and the [GPU support notes][docs_gpu_validation].

### Under the hood

Focal and Jammy combine pinned Ubuntu+s6 bases with the pinned Selkies stack.
Noble and Resolute use pinned Selkies runtime bases. Selkies, PixelFlux, and
PCMFlux are treated as one compatibility set and must be upgraded and tested
together.

## Building locally

Build Focal and Jammy with `Dockerfile.compat`; build Noble and Resolute with
the main `Dockerfile`. The immutable base arguments below match the CI matrix:

```bash
docker build -f Dockerfile.compat \
  --build-arg EXPECTED_UBUNTU_CODENAME=focal \
  --build-arg UBUNTU_BASE_IMAGE=ghcr.io/linuxserver/baseimage-ubuntu@sha256:a784bc01de33e51655d8e179fac80077a055aee79d9b01c4c7839c6aebbc01ae \
  -t taltechivarlab/ubuntu-desktop:20.04 .
docker build -f Dockerfile.compat \
  --build-arg EXPECTED_UBUNTU_CODENAME=jammy \
  --build-arg UBUNTU_BASE_IMAGE=ghcr.io/linuxserver/baseimage-ubuntu@sha256:0d16f40efc3663125f1004b70feff091f2d13771f1cc005ea30c28bd777e05e2 \
  -t taltechivarlab/ubuntu-desktop:22.04 .
docker build -f Dockerfile -t taltechivarlab/ubuntu-desktop:24.04 .
docker build -f Dockerfile \
  --build-arg EXPECTED_UBUNTU_CODENAME=resolute \
  --build-arg SELKIES_RUNTIME_BASE=ghcr.io/linuxserver/baseimage-selkies@sha256:8bb0d9343b764034c048c2c3895127bfe885a824fcc93ad472281fdd6d4a582f \
  -t taltechivarlab/ubuntu-desktop:26.04 .
```

Use [Docker Buildx][docker_buildx] and `--platform` to build for multiple
architectures, such as `amd64` and `arm64`:

```bash
docker buildx build --platform=linux/amd64,linux/arm64 \
  -f Dockerfile.compat \
  --build-arg EXPECTED_UBUNTU_CODENAME=jammy \
  --build-arg UBUNTU_BASE_IMAGE=ghcr.io/linuxserver/baseimage-ubuntu@sha256:0d16f40efc3663125f1004b70feff091f2d13771f1cc005ea30c28bd777e05e2 \
  -t taltechivarlab/ubuntu-desktop:22.04 --output=oci .
```

### Updating the Selkies Python lock

`pyproject.toml` is the human-edited dependency policy; `uv.lock` is the
generated, cross-platform artifact lock. Update exact versions in
`pyproject.toml`, then regenerate and verify the lock with:

```bash
uv lock
uv lock --check
```

The Dockerfiles use a digest-pinned uv image to validate and export the lock with
artifact hashes, then sync it into their pre-created Python environments. This
preserves the native image's system-site-packages behavior and the compatibility
image's isolated Python/compiler environment. Do not hand-edit `uv.lock` or
replace the locked, hash-checked install with an unconstrained `pip install`.

## Contributing

Contributions are currently limited to members of the TalTech organization.

[taltech_ivar_lab]: https://ivar.taltech.ee/
[ros_desktop_github]: https://github.com/TalTech-IVAR-Lab/ros-desktop-docker
[openssh]: https://www.openssh.com/
[terminator]: https://gnome-terminator.org/
[zsh]: https://www.zsh.org/
[htop]: https://htop.dev/
[neofetch]: https://github.com/dylanaraps/neofetch
[nmap]: https://nmap.org
[plank]: https://launchpad.net/plank
[docker_buildx]: https://www.docker.com/blog/how-to-rapidly-build-multi-architecture-images-with-buildx/#
[docker_stop]: https://docs.docker.com/engine/reference/commandline/stop/
[docker_start]: https://docs.docker.com/engine/reference/commandline/start/
[docs_advanced_usage]: docs/ADVANCED_USAGE.md
[docs_gpu_validation]: docs/GPU_VALIDATION.md
[docs_motivation]: docs/MOTIVATION.md
