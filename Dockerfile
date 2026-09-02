# syntax=docker/dockerfile:1.7

# Pinned build inputs. uv supplies the lockfile tooling; current_selkies is used
# only as the matching browser frontend donor.
ARG SELKIES_RUNTIME_BASE=ghcr.io/linuxserver/baseimage-selkies@sha256:bdbdb9fa0b7505e6d8b4ed2a357e711b7bd53ab96e7f9f11a3d3bbfecafb3663
ARG UV_IMAGE=ghcr.io/astral-sh/uv@sha256:0f36cb9361a3346885ca3677e3767016687b5a170c1a6b88465ec14aefec90aa

FROM ${UV_IMAGE} AS uv

# Current LinuxServer frontend, copied as static assets into the Noble runtime.
# The digest is multi-architecture and was built from Selkies revision 348bc4f.
FROM ghcr.io/linuxserver/baseimage-selkies@sha256:7f4f69e5184e3e1876e96ca0c5d66bc3ef5ffe3d47a910cbf6366fe59db3e972 AS current_selkies

# Last LinuxServer Noble Selkies multi-architecture release. Its compositor and
# service stack remain the Ubuntu-specific foundation while the complete
# Selkies application stack is upgraded below as one pinned unit.
FROM ${SELKIES_RUNTIME_BASE}

ARG BUILD_DATE
ARG VERSION
ARG UBUNTU_VERSION=24.04
ARG EXPECTED_UBUNTU_CODENAME=noble
ARG SELKIES_REVISION=348bc4f61da66198573e7e57db9a266aca1991d5
ARG DESKTOP_USER=ivar

# Image metadata and secure runtime defaults shared by Noble and Resolute.
LABEL org.opencontainers.image.title="TalTech IVAR Lab Ubuntu Desktop (Selkies)" \
      org.opencontainers.image.description="Ubuntu ${UBUNTU_VERSION} MATE desktop over Selkies with SSH" \
      org.opencontainers.image.source="https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.version="${VERSION}"

ENV DEBIAN_FRONTEND=noninteractive \
    DESKTOP_USER=${DESKTOP_USER} \
    HOME=/config \
    NVIDIA_DRIVER_CAPABILITIES=all \
    PIXELFLUX_WAYLAND=true \
    SELKIES_IS_MANUAL_RESOLUTION_MODE=true \
    SELKIES_MANUAL_WIDTH=1920 \
    SELKIES_MANUAL_HEIGHT=1080 \
    SELKIES_SCALING_DPI=96 \
    SELKIES_FRAMERATE=60 \
    SELKIES_COMMAND_ENABLED=false \
    SELKIES_ENABLE_SHARING=false \
    SELKIES_ENABLE_COLLAB=false \
    SELKIES_ENABLE_SHARED=false \
    START_DOCKER=false \
    DISABLE_SUDO=true \
    SSH_PORT=22 \
    TITLE="TalTech Ubuntu ${UBUNTU_VERSION}"

# Validate the selected Ubuntu lane, install the MATE desktop/tooling, and
# remove inherited password and privilege-escalation paths from the abc account.
RUN set -eu; \
    . /etc/os-release; \
    case "${VERSION_CODENAME}" in \
      noble|resolute) ;; \
      *) echo "Native Selkies image requires Ubuntu Noble or Resolute, got ${VERSION_CODENAME}" >&2; exit 64 ;; \
    esac; \
    if [ "${VERSION_CODENAME}" != "${EXPECTED_UBUNTU_CODENAME}" ]; then \
      echo "Expected Ubuntu ${EXPECTED_UBUNTU_CODENAME}, got ${VERSION_CODENAME}" >&2; \
      exit 64; \
    fi; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      build-essential \
      caja-open-terminal \
      cmatrix \
      dbus-x11 \
      dconf-cli \
      git \
      htop \
      iproute2 \
      iputils-ping \
      mate-applet-brisk-menu \
      mate-applets \
      mate-desktop-environment-core \
      mate-system-monitor \
      mate-terminal \
      mate-tweak \
      mesa-utils \
      mesa-vulkan-drivers \
      mozo \
      nano \
      netcat-openbsd \
      nmap \
      openssh-server \
      papirus-icon-theme \
      plank \
      python-is-python3 \
      terminator \
      vim \
      x11-xserver-utils \
      xwayland \
      yaru-theme-gtk \
      zsh; \
    gpasswd --delete abc sudo || true; \
    usermod --shell /bin/bash abc; \
    passwd --lock abc; \
    rm -f /etc/sudoers.d/abc /etc/ssh/ssh_host_*; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install the current Selkies backend and its PixelFlux/PCMFlux dependencies
# from one frozen compatibility set. Upgrading only PixelFlux breaks the old
# backend API, so the backend, encoders, and frontend move together.
ADD --checksum=sha256:c18f7292cf895f44769e19347d9acb9296a907aa0067fe813d1dd2e7d0413f5d \
    https://github.com/selkies-project/selkies/archive/348bc4f61da66198573e7e57db9a266aca1991d5.tar.gz \
    /tmp/selkies.tar.gz
COPY --from=uv /uv /usr/local/bin/uv
COPY pyproject.toml uv.lock /tmp/selkies-lock/

# Build the runtime Python environment from the cross-platform uv lock while
# retaining LinuxServer's system Python packages (notably GI bindings).
RUN set -eu; \
    apt-get update; \
    apt-get install -y --no-install-recommends \
      libxkbcommon-dev \
      python3-dev \
      python3-venv; \
    rm -rf /lsiopy /tmp/selkies-src; \
    mkdir -p /tmp/selkies-src; \
    tar -xzf /tmp/selkies.tar.gz -C /tmp/selkies-src --strip-components=1; \
    python3 -m venv --system-site-packages /lsiopy; \
    cd /tmp/selkies-lock; \
    uv export --locked --no-dev --no-emit-project --format requirements.txt \
      --output-file /tmp/selkies-runtime.txt; \
    uv pip sync --python /lsiopy/bin/python --require-hashes --no-cache \
      /tmp/selkies-runtime.txt; \
    uv pip install --python /lsiopy/bin/python --no-cache --no-deps \
      --no-build-isolation /tmp/selkies-src; \
    test "$(/lsiopy/bin/python -c 'from importlib.metadata import version; print(version("pixelflux"))')" = "2.0.0"; \
    test "$(/lsiopy/bin/python -c 'from importlib.metadata import version; print(version("pcmflux"))')" = "2.0.0"; \
    /lsiopy/bin/python -c 'from selkies.media_pipeline import CaptureSettings, ScreenCapture; assert CaptureSettings and ScreenCapture'; \
    apt-get clean; \
    rm -rf /var/lib/apt/lists/* /tmp/*

# Import the matching browser frontend, then overlay TalTech desktop defaults,
# services, wallpaper, and the GPU verification helper.
COPY --from=current_selkies /usr/share/selkies/ /usr/share/selkies/

COPY files/etc/dconf/ /etc/dconf/
COPY files/usr/local/bin/taltech-verify-gpu /usr/local/bin/taltech-verify-gpu
COPY files/usr/share/backgrounds/taltech/ /usr/share/backgrounds/taltech/
COPY files/config/.config/ /defaults/config/.config/
COPY selkies-files/ /
COPY build-scripts/configure-desktop-user.py /tmp/configure-desktop-user.py

# Rewrite the inherited LinuxServer account to the configured desktop user and
# prepare root-owned persistent state after all templates are in place.
RUN set -eu; \
    /usr/bin/python3 /tmp/configure-desktop-user.py --user "${DESKTOP_USER}"; \
    if [ "${DESKTOP_USER}" != abc ]; then \
      if getent passwd "${DESKTOP_USER}" >/dev/null 2>&1; then \
        echo "DESKTOP_USER account already exists: ${DESKTOP_USER}" >&2; exit 64; \
      fi; \
      if getent group "${DESKTOP_USER}" >/dev/null 2>&1; then \
        echo "DESKTOP_USER group already exists: ${DESKTOP_USER}" >&2; exit 64; \
      fi; \
      groupmod --new-name "${DESKTOP_USER}" abc; \
      usermod --login "${DESKTOP_USER}" abc; \
    fi; \
    rm -f /tmp/configure-desktop-user.py; \
    dconf update; \
    install -d -o root -g root -m 0700 /var/lib/taltech-desktop

# Runtime interfaces and persistent storage.
EXPOSE 22 3001
VOLUME /config /var/lib/taltech-desktop
