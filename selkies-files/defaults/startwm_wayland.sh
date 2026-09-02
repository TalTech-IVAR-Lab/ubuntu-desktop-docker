#!/usr/bin/env bash
set -euo pipefail

setterm blank 0 || true
setterm powerdown 0 || true
gsettings set org.mate.Marco.general compositing-manager false || true

WAYLAND_DISPLAY=wayland-1 Xwayland :1 &
xwayland_pid=$!
trap 'kill "${xwayland_pid}" 2>/dev/null || true' EXIT
sleep 2

dbus-launch --exit-with-session /defaults/start-mate-session.sh > /dev/null 2>&1
