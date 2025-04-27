# Create a custom base image
This document is based on how [the default tart images are created](https://github.com/cirruslabs/linux-image-templates/).

## 1. Download a Cloud image
I'm using Debian in my example, but other distros have their own cloud images
ready for use. Just remember you need arm64 to run it on a Mac that is powered
by Apple Silicon.

```bash
curl -LO https://cloud.debian.org/images/cloud/bookworm/latest/debian-12-generic-arm64.qcow2
```

## 2. Convert qcow2 to raw
This requires `qemu-img` to be installed, qemu is not needed to generally run
minicloud but it is required to create your custom base image.

```bash
qemu-img convert -p -f qcow2 -O raw debian-12-generic-arm64.qcow2 image.raw
```

## 3. Create the base virtual machine
This creates an empty linux based machine named `debian:12`, which seems like
a fitting name in this example. It then moves the `image.raw` we created in the
previous step to the `TART_HOME` directory (which defaults to `~/.tart/`).

```bash
tart create --linux debian:12
mv image.raw ~/.tart/vms/debian:12/disk.img
```

## 4. Create a cloud-init ISO named cidata
To create this manually you could do the following:

```
mkdir cloud-init
touch cloud-init/meta-data
touch cloud-init/network-config
touch cloud-init/user-data
```

Those files also need some contents, here are some examples

Example `meta-data`

```yaml
local-hostname: debian
```

Example `network-config` (this originates from the tart linux vm)


```yaml
#cloud-config
network:
  version: 2
  ethernets:
    all:
      match:
        name: en*
      dhcp4: true

      # Work around macOS DHCP server treating "hw_address" and "identifier" fields
      # in /var/db/dhcpd_leases the same way and putting client identifier (which is
      # a DUID/IAID) into the "hw_address" field, making it impossible to locate the
      # corresponding entry given a MAC-address in "tart ip".
      dhcp-identifier: mac
```

And then finally `user-data` can contain whatever you want, but it should setup
a user we can use to connect with. I am using a simple user/password because in
the next step I will configure the image using packer and the tart provider.

```yaml
#cloud-config
package_reboot_if_required: false
package_update: true
package_upgrade: true

users:
  - name: packer
    plain_text_passwd: packer
    sudo: ALL=(ALL) NOPASSWD:ALL
    lock_passwd: false
    shell: /bin/bash

ssh_pwauth: true
disable_root: true
```

When you have created these 3 files in the `cloud-init` directory you can run
the following command to create an ISO with volume id/name `cidata`:

```bash
hdiutil \
  makehybrid
  -iso \
  -joliet \
  -ov \
  -default-volume-name cidata\
  -o cloud-init.iso \
  ./cloud-init
```

## 5. Customise the base image using Packer
Cirruslabs, creators of tart, were kind enough to create a packer provider to
help build images. This is what we will be using next to customise it to our
liking. An example packer config can be found below:

```hcl
packer {
  required_plugins {
    tart = {
      version = ">= 1.11.1"
      source  = "github.com/cirruslabs/tart"
    }
  }
}

source "tart-cli" "tart" {
  vm_name      = "debian:12"
  cpu_count    = 2
  memory_gb    = 8
  disk_size_gb = 10
  ssh_username = "packer"
  ssh_password = "packer"
  ssh_timeout  = "120s"
  always_pull  = false
  disable_vnc  = true
  headless     = true

  # Note that we include the cloud-init.iso from the previous step here!
  run_extra_args = ["--disk", "cloud-init.iso"]
}

build {
  sources = ["source.tart-cli.tart"]

  # Wait for cloud-init to complete first
  provisioner "shell" {
    inline = [
      "echo Waiting for cloud-init to complete",
      "/usr/bin/cloud-init status --wait",
    ]
  }

  # [ DO WHATEVER YOU WANT ]

  # Remove packer user and reset cloud-init for next time
  provisioner "shell" {
    execute_command = "chmod +x {{ .Path }}; sudo env {{ .Vars }} {{ .Path }} ; rm -f {{ .Path }}"
    skip_clean      = true

    inline = [
      "echo Cleaning up packer user",
      "rm -f /etc/sudoers.d/90-cloud-init-users",
      "cloud-init clean",
      "/usr/sbin/userdel -r -f packer",
      "/sbin/shutdown -hP now",
    ]
  }
}

```

Then run `packer init .` and `packer build yourfile.pkr.hcl` and that should
start the `debian:12` virtual machine we created, run cloud-init and any other
provisioning you wanted, finally do a small cleanup and terminate leaving you
with your base `debian:12` image.

Now you can use `debian:12` as your base vm for any new machine you create.
