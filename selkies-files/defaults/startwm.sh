#!/usr/bin/env bash
set -euo pipefail

if command -v nvidia-smi >/dev/null 2>&1 \
    && compgen -G '/dev/dri/*' >/dev/null \
    && [[ "${DISABLE_ZINK,,}" == "false" ]]; then
    export LIBGL_KOPPER_DRI2=1
    export MESA_LOADER_DRIVER_OVERRIDE=zink
    export GALLIUM_DRIVER=zink
fi

setterm blank 0 || true
setterm powerdown 0 || true
gsettings set org.mate.Marco.general compositing-manager false || true
exec dbus-launch --exit-with-session /defaults/start-mate-session.sh > /dev/null 2>&1
