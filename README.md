# MiniCloud
A small utility to help manage [tart](https://tart.run) virtual machines via
terraform using the restapi provider.

## Background
I manage my personal infra (local and cloud) using Terraform (and other tools)
and thought it would be nice if I could create virtual machines on my Mac Mini
(hidden in a closet) using Terraform as well. This keeps the maintenance of all
of my personal infrastructure in one place.

After spending some time looking at various tooling I ended up going with [tart](https://tart.run)
as a the main command line application to actually manage the VMs. It uses the
built-in Virtualization framework that Apple provides and is very easy in use
and surprisingly fast as well.

My MiniCloud project provides a very basic HTTP server around it so I can use
it combined with the [restapi terraform provider](https://github.com/Mastercard/terraform-provider-restapi)
to manage the virtual machines from my terraform codebase. Another feature I
added was the generation of a cloud-init disk image with the `cidata` label
which (depending on your Linux base image) will automatically be executed on
machine boot. This makes it easier to setup provisioning for the machines by
passing along `user_data` in terraform as well.

Tart provides some default images for guest vms themselves (macOS and Linux),
and tart can connect with OCI registries to push/pull any image. But their own
images did not appear to execute my cloud-init (presumably because cloud-init
already ran) so I ended up creating my own base image, which I tried to document
in the examples directory.

## Requirements
- [tart](https://tart.run) should be installed already
- python 3 (comes by default in macOS)
- hdiutil (comes by default in macOS)
- TCP port 8000 should be available (default port)

That's right, that's all! The python codebase only uses the standard library so
there is no need to deal with any additional dependencies or build processes.

## Usage
To install and start the minicloud launch-agent you can simple run:

```
$ git clone git@github.com:maxvw/minicloud.git
$ cd minicloud
$ bin/setup
```

Then to use it with terraform you can load the module from github as well, so
for example:

```terraform
terraform {
  required_providers {
    restapi = {
      source = "Mastercard/restapi"
      version = "2.0.1"
    }
  }
}

provider "restapi" {
  uri                  = "http://macmini:8000"
  debug                = true
  write_returns_object = true
  id_attribute         = "id"

  headers = {
    "Accept" = "application/json",
  }
}

module "machine1" {
  source    = "git@github.com:maxvw/minicloud.git//resources/machine?ref=main"
  base_vm   = "debian:12"
  name      = "my-first-machine"
  vcpu      = 2
  memory    = 1024
  disk_size = 10
  user_data = <<EOT
#cloud-config
runcmd:
  - ['echo', 'Hello']
EOT
}

output "machine1" {
  value = {
    ip_addr = module.machine1.ipv4
  }
}
```

> **NOTE:** The double `//` is required for terraform to navigate to a directory
> within the git repository. The ref=main can be replaced by a tag if/when I
> start tagging releases.

## API Endpoints
```
# Create new VM
POST /machine

# Get a VM
GET /machine/:id

# Delete a VM
DELETE /machine/:id

```

Creating a new machine expects a JSON payload that contains all the variables
mentioned in the terraform module. Some are nullable, you can check out the
module in `./resources/machine/main.tf`

> **NOTE:** Updating is currently not implemented as I had no use case for it
> yet in my personal project. Might come later.

## Final Notes
Currently this is very much just a fun project, not intended for any real world
production environments. There is no security, no testing, no performance
optimisations, no error handling, no real validations, and no guarantees. It's
very basic. But, it is fun!

_* Fun can not be guaranteed._

## Contributing
I don't expect anyone else to use this project, but if you do and/or would like
to contribute please feel free to create pull requests and I will gladly accept
any useful contributions.
