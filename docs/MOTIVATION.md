# Motivation

This page explains the reasons behind the creation of the [taltechivarlab/ubuntu-desktop][ubuntu_desktop_github] Docker image (and other images based on it). 


## 📦 What are containers?

Containers are an approach to packaging software in an isolated, standardized and easy-to-distribute form. They can be likened to [virtual machines (VMs)][what_is_a_vm], which allow to run multiple operating systems (OSs) on a single physical host machine, with software inside those environments being isolated from the host OS. However, in contrast to VMs, containers are not required to have the entire OS inside them — instead, they use the host OS's [kernel][what_is_a_kernel] for their code execution needs. This makes containers much smaller and often [faster than virtual machines][docker_vs_vm_performance].

Just like with VMs, containers can be given direct access to the host machine's storage and devices (such as [GPUs][container_gpus]).

All these points are explained in much greater detail in [this blogpost by Docker][what_is_a_container].


## 🐳 Why Docker containers are good?

[Docker] is an [open source][docker_open_source] platform for developing and distributing containers, which is steadily gaining traction as the standard environment for running production software. Adopting it has the following benefits:

- Docker provides a multiplatform [engine][docker_engine], which allows to easily run the same containers on Linux, Windows and macOS hosts. 
- It has an official online registry for sharing container images called [Docker Hub][dockerhub], which provides free storage for public container images.
- Docker container images implement a [layer caching mechanism][docker_layer_caching], which allows to save a lot of time when pulling images with common base from remote repositories as well as when building them.
- And [many others][why_docker]...


## 🧪 How TalTech IVAR Lab uses containers?

In our [laboratory][taltech_ivar_lab] we often work with complex software such as ROS, which normally requires time-consuming installation and an environment with the specific set of tools and pre-configured settings. Doing this setup manually every time when we need a fresh ROS installation is a tedious task that is prone to human error, and packaging it in a VM still poses problems with distribution. 

Thus, we have decided to package our default development environment in a [Docker image][ubuntu_desktop_github] instead. This brings multiple benefits:

- We can get it up and running on any computer in minutes ([install Docker][docs_installing_docker] + pull and run the image). This is especially easy on Linux hosts, where the whole procedure takes [just 5 commands in a terminal][docs_installing_docker_linux].

- If something goes wrong in the environment, simply starting a new container from the same image provides a clean slate to work with, no repetitive setup required. This encourages experimentation and learning.

- The content of the image and any of its derivatives can be easily managed and updated through their Dockerfiles hosted in Git repositories (e.g. [Dockerfile of taltechivarlab/ubuntu-desktop][ubuntu_desktop_github_dockerfile]).

- It is easy to distribute: all our images are published on Dockerhub under our [taltechivarlab][taltechivarlab_dockerhub] account and can be started with a single `docker run` command.

With this, we hope that you now have a better understanding of what containers are and why using them is [worth a try 😉][ubuntu_desktop_github_usage]



[ubuntu_desktop_github]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker

[container_gpus]: ADVANCED_USAGE.md#enabling-hardware-graphics-acceleration
[what_is_a_vm]: https://www.redhat.com/en/topics/virtualization/what-is-a-virtual-machine
[what_is_a_container]: https://www.docker.com/resources/what-container/
[what_is_a_kernel]: https://en.wikipedia.org/wiki/Kernel_(operating_system)
[docker_vs_vm_performance]: https://www.sciencedirect.com/science/article/pii/S1877050920311315

[docker]: https://www.docker.com/
[docker_open_source]: https://www.docker.com/community/open-source/
[docker_engine]: https://docs.docker.com/engine/
[docker_layer_caching]: https://docs.docker.com/build/building/cache/
[why_docker]: https://www.docker.com/why-docker/
[oci]: https://opencontainers.org/

[taltech_ivar_lab]: https://ivar.taltech.ee/
[docs_installing_docker]: INSTALLING_DOCKER.md
[docs_installing_docker_linux]: INSTALLING_DOCKER.md#-linux
[dockerhub]: https://hub.docker.com/
[taltechivarlab_dockerhub]: https://hub.docker.com/u/taltechivarlab
[ubuntu_desktop_github_usage]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker#usage
[ubuntu_desktop_github_dockerfile]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker/blob/main/Dockerfile
