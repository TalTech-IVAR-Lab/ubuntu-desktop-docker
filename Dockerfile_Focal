# LSIO image with Ubuntu 20.04 (latest available)
FROM linuxserver/rdesktop:ubuntu-mate-version-77a977e9

# Update repositories
RUN apt update -y

# Utilities
RUN apt install -y nano vim
RUN apt install -y git
RUN apt install -y iputils-ping iproute2 nmap

# Desktop theme
RUN apt install -y materia-gtk-theme
RUN apt install -y mate-tweak
RUN apt install -y mozo

# Dock
RUN apt install -y plank

# Kora icon pack
RUN git clone https://github.com/bikass/kora.git
RUN cp -r kora/kora /usr/share/icons/

# Default desktop configuration
COPY files/etc/dconf/ /etc/dconf/
RUN dbus-launch dconf update

# Add "Open in Terminal" to the context menu in Caja file explorer
RUN apt install -y caja-open-terminal

# Default wallpaper (a symlink to make it easy to override in the inheriting Docker images)
RUN ln -s "/usr/share/backgrounds/ubuntu-mate-photos/nasa-53884.jpg" "/usr/share/backgrounds/default.wallpaper"

# Default apps configuration
COPY files/config/.config/ /config/.config/

# Patch XRDP config (custom login screen styling)
COPY files/etc/xrdp/ /etc/xrdp/
COPY files/usr/share/xrdp/ /usr/share/xrdp/

# OpenSSH (based on https://github.com/antoineco/sshd-s6-docker)
RUN apt install -y openssh-server
COPY files/etc/services.d/sshd/ /etc/services.d/sshd/

# Terminator (instead of MATE Terminal)
RUN apt remove -y mate-terminal
RUN apt install -y terminator

# Neofetch
RUN apt install -y neofetch

# htop
RUN apt install -y htop

# Matrix easter egg
RUN apt install -y cmatrix

# Python 3 alias
RUN apt install -y python-is-python3

# Standard software build dependencies
RUN apt install -y build-essential

# Pre-configured Zsh (through the installation script)
# Note: here we give the abc user a temporary passwordless access to sudo, as the installation script uses sudo internally
RUN chown abc:abc /config && chmod 755 /config
RUN echo "abc ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers
USER abc
RUN HOME=/config && curl -fsSL https://raw.githubusercontent.com/JGroxz/presto-prezto/main/presto-prezto.sh | bash
USER root
RUN sed -i '/abc ALL=(ALL) NOPASSWD: ALL/d' /etc/sudoers

# Expire the default user password
# This forces the user to change the default password through SSH before using the remote desktop connection
RUN passwd --expire abc
