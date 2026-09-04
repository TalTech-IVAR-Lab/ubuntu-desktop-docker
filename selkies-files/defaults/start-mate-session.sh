#!/usr/bin/env bash
set -euo pipefail

picture_filename=$(gsettings get org.mate.background picture-filename 2>/dev/null || printf "''")
if [[ ${picture_filename} == "''" ]]; then
    gsettings set org.mate.background picture-filename \
        '/usr/share/backgrounds/taltech/ivar-lab.png'
    gsettings set org.mate.background picture-options 'zoom'
fi

marco_theme=$(gsettings get org.mate.Marco.general theme 2>/dev/null || printf "''")
if [[ ${marco_theme} == "''" || ${marco_theme} == "'Yaru'" ]]; then
    gsettings set org.mate.Marco.general theme 'Yaru-dark'
fi

exec /usr/bin/mate-session
