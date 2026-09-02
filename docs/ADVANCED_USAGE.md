# Advanced usage

This page explains advanced usage scenarios for Docker images based on [taltechivarlab/ubuntu-desktop][ubuntu_desktop_github]. 

## Opening more network ports

If you intend to connect to the applications running inside this container from outside, you will likely need to open more ports than the default `docker run` command from our [README][ubuntu_desktop_github].

Specify the required mappings in the initial `docker run` command [using the
`-p` flag][docker_expose_ports]. To change them later, stop and remove the
container, then recreate it with the same named `/config` and
`/var/lib/taltech-desktop` volumes and the new mappings. Do not edit Docker's
internal container metadata in place.

Alternatively, you can run the container with the `--network=host` flag. This will make all ports of the container available to the host network, but [only works on Linux hosts][docker_network_host].

## Enabling hardware graphics acceleration

Hardware graphics acceleration can significantly speed up your container if you are working with graphics-intensive applications or run simulations which utilize GPU for parallel computing.

All published image lanes use Selkies over HTTPS. Noble and Resolute use the
native Selkies image path; Focal and Jammy use the compatibility path over the
corresponding LinuxServer Ubuntu+s6 base. Device visibility alone is
insufficient: acceptance requires the renderer check to pass inside the actual
remote session.

### TL;DR:

- On any systems with Nvidia GPUs, [install Nvidia container runtime][docs_installing_nvidia_container_runtime] on the host machine and run:
    
  ```bash
  docker run -d \
    `# all flags from the original run command here` \
    --gpus=all \
     taltechivarlab/ubuntu-desktop:24.04
  ```
  
   `nvidia-smi` proves that the device and compute runtime are visible, but it
   does not prove that the desktop application uses hardware rendering.


- On Intel/AMD DRM hosts and ARM systems such as Raspberry Pi:

  ```bash
  docker run -d \
    `# all flags from the original run command here` \
    --device=/dev/dri:/dev/dri \
     taltechivarlab/ubuntu-desktop:24.04
  ```

### Verifying accelerated desktop rendering

Open the browser desktop for the selected image tag. Launch a terminal inside
that actual remote session and run:

```bash
taltech-verify-gpu
```

The verifier reports the render nodes, NVIDIA runtime state, OpenGL vendor,
renderer, and version. It rejects known software paths including `llvmpipe`,
`softpipe`, `swrast`, `lavapipe`, SwiftShader, OpenSWR, and generic software
rasterizers. Set `EXPECTED_RENDERER_REGEX` when a specific GPU must be selected:

```bash
EXPECTED_RENDERER_REGEX='NVIDIA|AMD|Intel' taltech-verify-gpu
```

Run this separately for NVIDIA (`--gpus all`) and Intel/AMD
(`--device=/dev/dri:/dev/dri`) hosts. Focal, Jammy, Noble, and Resolute Selkies
on amd64 with NVIDIA have passed the application-rendering and H.264/NVENC
gates on `lab-001`. These results do not establish zero-copy operation.
Intel/AMD and arm64 combinations remain pending. Record exact results in the
[GPU validation matrix][gpu_validation].



[ubuntu_desktop_github]: https://github.com/TalTech-IVAR-Lab/ubuntu-desktop-docker

[docker_expose_ports]: https://docs.docker.com/engine/reference/run/#expose-incoming-ports
[docker_network_host]: https://docs.docker.com/network/host/

[docs_installing_nvidia_container_runtime]: INSTALLING_NVIDIA_CONTAINER_RUNTIME.md
[gpu_validation]: GPU_VALIDATION.md
