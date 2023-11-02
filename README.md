# Ubuntu Desktop Docker

[![Ubuntu version](https://img.shields.io/badge/Ubuntu-20.04-informational?logo=ubuntu)](https://releases.ubuntu.com/focal/)
[![Ubuntu version](https://img.shields.io/badge/Ubuntu-22.04-informational?logo=ubuntu)](https://releases.ubuntu.com/jammy/)
[![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/TalTech-IVAR-Lab/ubuntu-desktop-docker/docker_build.yml?branch=main&logo=GitHub)](https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker/actions)
[![Docker Image Size (latest by date)](https://img.shields.io/docker/image-size/taltechivarlab/ubuntu-desktop?logo=docker)](https://hub.docker.com/r/taltechivarlab/ubuntu-desktop)

> Based on the [linuxserver/rdesktop:ubuntu-mate][rdesktop_github] image by [linuxserver.io][lsio]

Dockerized Ubuntu Desktop environment with RDP and SSH access used by [TalTech IVAR Lab][taltech_ivar_lab]. Primarily intended as a base image for our [ROS Desktop][ros_desktop_github] images.

## Why and how

Learn why this project was created and how it is useful by reading our [Motivation doc][docs_motivation].

## What's included

In addition to what is already in [linuxserver/rdesktop:ubuntu-mate][rdesktop_github], our image applies the following modifications:

- [OpenSSH] server
- Command line packages:
  - [Terminator] as the default terminal application
  - [Zsh] with [preconfigured plugins][presto-prezto] for the default _abc_ user
  - Utilities:
      - [htop] process monitor
      - [neofetch] system information tool
      - [nmap] network mapping tool
- GUI packages:
  - [Materia] theme with [Kora] icon pack
  - [Plank] dock
- Custom [xrdp] login screen styling:
  - Darker colors to match the default desktop theme
  - Updated xrdp logo
- Desktop look:
  ![desktop screenshot from ubuntu desktop docker](https://raw.githubusercontent.com/TalTech-IVAR-Lab/ubuntu-desktop-docker/main/docs/images/desktop.png "Default desktop environment in this Docker image")

## Usage

### Quick start

Once you have [installed Docker][docs_install_docker], to launch the container directly:

```bash
docker run -d \
  --name=ubuntu-desktop \
  -e PUID=1000 \
  -e PGID=1000 \
  -e TZ=Europe/Tallinn \
  -p 3390:3389 `# rdp` \
  -p 2222:22 `# ssh` \
  --shm-size="1gb" \
  --security-opt seccomp=unconfined \
  --restart unless-stopped \
  taltechivarlab/ubuntu-desktop:22.04
```

Once the container has started, you must `ssh` into it (default password is `abc`):

```bash
ssh abc@localhost -p 2222
```

...and change _abc_ user's default password following the displayed instructions.

After that, you can use login _abc_ and the newly set password to log in to the container using any remote desktop client.

> 💡 When inside the container, you can switch your default shell to [Zsh][presto-prezto_demo] by running the following
> command in the terminal:
>
> ```bash
> sudo usermod --shell $(command -v zsh) abc
> ```

> ☝ You can [stop][docker_stop] and [restart][docker_start] the created container from Docker without losing your data.
> It is equivalent to system shutdown from the containerized Ubuntu's point of view. However, keep in mind that [_deleting_][docker_rm] your container will destroy all the data and software contained inside.

### Advanced usage

For more advanced use cases, such as opening additional ports and enabling hardware graphics acceleration, please refer to the [Advanced Usage][docs_advanced_usage] doc.

## Building locally

If you want to build this image locally instead of pulling it from [Dockerhub], clone this repository and run the build:

```bash
docker build --file Dockerfile_Jammy -t taltechivarlab/ubuntu-desktop:22.04 .
```

In case you want to build a multi-architecture image (e.g. to run it on a Raspberry Pi), you can build for multiple platforms using the [Docker Buildx][docker_buildx] backend (by specifying them in the `--platform` flag):

```bash
docker buildx build --platform=linux/amd64,linux/arm64 --file Dockerfile_Jammy -t taltechivarlab/ubuntu-desktop:22.04 --output=oci .
```

## Contributing

The project is in early stages of development, so we are not yet accepting contributions from outside our university organization. 



[taltech_ivar_lab]: https://ivar.taltech.ee/
[ros_desktop_github]: https://github.com/TalTech-IVAR-Lab/ros-desktop-docker
[lsio]: https://www.linuxserver.io/
[rdesktop_github]: https://github.com/linuxserver/docker-rdesktop
[rdesktop_github_hardware_acceleration]: https://github.com/linuxserver/docker-rdesktop#hardware-acceleration-ubuntu-container-only
[openssh]: https://www.openssh.com/
[build-essential]: https://linuxhint.com/install-build-essential-ubuntu/
[terminator]: https://gnome-terminator.org/
[zsh]: https://www.zsh.org/
[htop]: https://htop.dev/
[neofetch]: https://github.com/dylanaraps/neofetch
[nmap]: https://nmap.org
[presto-prezto]: https://github.com/JGroxz/presto-prezto
[presto-prezto_demo]: https://github.com/JGroxz/presto-prezto#demo
[materia]: https://github.com/nana-4/materia-theme
[kora]: https://github.com/bikass/kora
[plank]: https://launchpad.net/plank
[xrdp]: http://xrdp.org/
[Dockerhub]: https://hub.docker.com/r/taltechivarlab/ubuntu-desktop
[docker_buildx]: https://www.docker.com/blog/how-to-rapidly-build-multi-architecture-images-with-buildx/#
[docker_stop]: https://docs.docker.com/engine/reference/commandline/stop/
[docker_start]: https://docs.docker.com/engine/reference/commandline/start/
[docker_rm]: https://docs.docker.com/engine/reference/commandline/rm/
[docs_advanced_usage]: docs/ADVANCED_USAGE.md
[docs_install_docker]: docs/INSTALLING_DOCKER.md
[docs_motivation]: docs/MOTIVATION.md