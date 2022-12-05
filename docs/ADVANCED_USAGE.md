# Advanced usage

This page explains advanced usage scenarios for Docker images based on [taltechivarlab/ubuntu-desktop][ubuntu_desktop_github]. 

## Opening more network ports

If you intend to connect to the applications running inside this container from outside, you will likely need to open more ports than the default `docker run` command from our [README][ubuntu_desktop_github].

> 💡 If you know for sure which ports in your container you will connect to, you can specify them in the initial `docker run` command [using the `-p` flag][docker_expose_ports]. However, if you need to open the port _after_ the container was started, please read more below.

The port mappings are specified with the initial `docker run` call, and you cannot delete and recreate the container without losing the data inside. Instead, please follow [this answer from Stackoverflow][update_docker_port_in_flight_stackoverflow] or [this article][update_docker_port_in_flight] to modify the port mappings of already running container without destroying it.

Alternatively, you can run the container with the `--network=host` flag. This will make all ports of the container available to the host network, but [only works on Linux hosts][docker_network_host].

## Enabling hardware graphics acceleration

Hardware graphics acceleration can significantly speed up your container if you are working with graphics-intensive applications or run simulations which utilize GPU for parallel computing.

As our images are based on [linuxserver/rdesktop:ubuntu-mate][rdesktop_github], they support hardware graphics acceleration out of the box. To enable it, please refer to [the original docs from linuxserver.io][rdesktop_github_hardware_acceleration].

### TL;DR:

- On any systems with Nvidia GPUs, [install Nvidia container runtime][docs_installing_nvidia_container_runtime] on the host machine and run:
    
  ```bash
  docker run -d \
    `# all flags from the original run command here` \
    --gpus=all \
     taltechivarlab/ubuntu-desktop:20.04
  ```
  
   > 💡 You can verify that your Nvidia card was mounted successfully by running the `nvidia-smi --list-gpu` command in terminal inside the container. If everything went well, you will see your GPU in the list of devices output by this command. Otherwise, the command will fail.


- On Linux systems with ARM processors (e.g. Raspberry Pi):

  ```bash
  docker run -d \
    `# all flags from the original run command here` \
    --device=/dev/dri:/dev/dri \
     taltechivarlab/ubuntu-desktop:20.04
  ```



[ubuntu_desktop_github]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker

[docker_expose_ports]: https://docs.docker.com/engine/reference/run/#expose-incoming-ports
[update_docker_port_in_flight_stackoverflow]: https://stackoverflow.com/a/38783433
[update_docker_port_in_flight]: https://www.baeldung.com/linux/assign-port-docker-container#reconfigure-docker-in-flight
[docker_network_host]: https://docs.docker.com/network/host/

[docs_installing_nvidia_container_runtime]: INSTALLING_NVIDIA_CONTAINER_RUNTIME.md
[rdesktop_github]: https://github.com/linuxserver/docker-rdesktop
[rdesktop_github_hardware_acceleration]: https://github.com/linuxserver/docker-rdesktop#hardware-acceleration-ubuntu-container-only
