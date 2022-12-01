# Installing Nvidia Container Runtime

If your host machine has an Nvidia GPU and you want to use it for [hardware graphics acceleration][docs_advanced_usage] inside your container, you will have to install [Nvidia container runtime][nvidia_container_runtime_github] on the host. We will not cover all the installation steps in this documentation, because Nvidia provides an [extensive official guide][nvidia_container_runtime_installation] on the subject matter, so please follow it to install the software. 

However, here are some tips which may be useful during the installation process:

- Before you can install the [runtime][nvidia_container_runtime_github], [install Docker][docs_installing_docker] and [Nvidia driver][nvidia_driver] on your host machine.


- If you have [Docker Desktop][docker_desktop] installed on the host, your [Nvidia container runtime][nvidia_container_runtime_github] installation may not work after completing the [guide][nvidia_container_runtime_installation], complaining that runtime cannot be found. This happens because Docker Desktop overrides [Docker’s default configuration file (_daemon.json_)][docker_configuration_file], and that file is not updated automatically during the installation. To make Docker see the new Nvidia runtime, you have to add this runtime in Docker Desktop’s settings (highlighted text):
  ![screenshot of Docker Desktop with the configuration file editing window open](https://raw.githubusercontent.com/TalTech-IVAR-Lab/ubuntu-desktop-docker/main/docs/images/docker_desktop_nvidia_runtime.png "Adding Nvidia runtime to the configuration file in Docker Desktop")
  > ℹ️ To access the menu displayed above, in Docker Desktop open _Settings_ (cog icon in the top right corner) and select _Docker Engine_ in the left sidebar menu.
  
  After the file is modified, click "Apply & Restart" and wait for Docker Engine to restart itself. After that, Nvidia runtime will become available to the containers.


- To confirm that the installation was successful, run the following command in your host machine's terminal:
  ```bash
  docker run --rm --gpus all nvidia/cuda:11.6.2-base-ubuntu20.04 nvidia-smi --list-gpus
  ```
  > ℹ️ The command above launches a test Nvidia Docker container and [lists the GPUs][nvidia-smi] available inside it.

  If you did everything right, you will see your GPU in the list of devices output by this command. Otherwise, the command will fail saying that the executable was not found - in this case, go through the [installation guide][nvidia_container_runtime_installation] again and check if you missed anything.
  


[docs_advanced_usage]: ADVANCED_USAGE.md
[docs_installing_docker]: INSTALLING_DOCKER.md
[nvidia_driver]: https://www.nvidia.com/download/index.aspx
[nvidia_container_runtime_github]: https://github.com/NVIDIA/nvidia-docker
[nvidia_container_runtime_installation]: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html#docker
[nvidia-smi]: https://developer.nvidia.com/nvidia-system-management-interface
[docker_desktop]: https://docs.docker.com/desktop/
[docker_configuration_file]: https://docs.docker.com/config/daemon/#configure-the-docker-daemon
