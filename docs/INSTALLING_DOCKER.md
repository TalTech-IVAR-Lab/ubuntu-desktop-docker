# Installing Docker

In order to run containers like [taltechivarlab/ubuntu-desktop][ubuntu_desktop_github] on your machine, you will need to install [Docker Engine][docker_engine].

Installation steps are already detailed well in the official guides, so here we will only provide links to those and a short TL;DR for each platform.


## 🪟 Windows

**Guide:** [install Docker Desktop with WSL backend][docker_desktop_windows]

### TL;DR:

1. Install [Windows Subsystem for Linux (WSL2)][wsl2]
2. Download & install [Docker Desktop for Windows][docker_desktop_windows_detailed]
3. Launch Docker Desktop


## 🍎 Mac

**Guide:** [install Docker Desktop][docker_desktop_mac]

### TL;DR:

1. Download and install [Docker Desktop for Mac][docker_desktop_mac_detailed]
2. Launch Docker Desktop


## 🐧 Linux

**Guide:** [install Docker Engine][docker_engine_linux]

### TL;DR:

The commands differ depending on the Linux distribution, so if you want to install it manually, your best bet is checking the [official guide for your distro][docker_engine_linux]. However, Docker provides a [convenience installation script][docker_engine_convenience_script] which works on most Linux distributions. With the script, installation steps become the following:

1. Download the installation script:
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   ```   

2. Run the installation script:
   
   > ⚠️ Before you install, it's a good practice to check if the contents of the downloaded `get-docker.sh` match the ones of the [original installation script from Docker's GitHub][get_docker_github]. 
   
   ```bash
   sudo sh get-docker.sh
   ```

3. _(optional)_ Add your user to the `docker` group.
   
   > ℹ️ This will allow you to run `docker ...` commands without typing `sudo` in front every time you use them.
   
   1. Add `docker` group to your system:
      ```bash
      sudo groupadd docker
      ```

      > 💡 If you want to learn more about how group and user permissions work in Linux, we highly recommend watching [this video tutorial by NetworkChuck][linux_permissions_networkchuck].
      
   2. Add your user to this group:
      ```bash
      sudo usermod -aG docker $USER
      ```
      
   3. Log out and back in for group changes to take effect.


## Testing your installation

To test your Docker installation, run the [official hello-world container][docker_hello_world] from your terminal:
```bash
docker run hello-world
```

> ℹ️ If your Docker is running correctly, this command will result in a confirmation message with some additional info about how Docker got it done.



[ubuntu_desktop_github]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker
[docker_engine]: https://docs.docker.com/engine/

[docker_desktop_windows]: https://docs.docker.com/desktop/windows/install/
[wsl2]: https://learn.microsoft.com/en-us/windows/wsl/install
[docker_desktop_windows_detailed]: https://docs.docker.com/desktop/install/windows-install/#install-docker-desktop-on-windows

[docker_desktop_mac]: https://docs.docker.com/desktop/mac/install/
[docker_desktop_mac_detailed]: https://docs.docker.com/desktop/install/mac-install/#install-and-run-docker-desktop-on-mac

[docker_engine_linux]: https://docs.docker.com/desktop/mac/install/
[docker_engine_convenience_script]: https://docs.docker.com/engine/install/debian/#install-using-the-convenience-script
[get_docker]: https://get.docker.com/com/engine/install/debian/#install-using-the-convenience-script
[get_docker_github]: https://github.com/docker/docker-install/blob/master/install.sh
[linux_permissions_networkchuck]: https://www.youtube.com/watch?v=jwnvKOjmtEA

[docker_hello_world]: https://hub.docker.com/_/hello-world
