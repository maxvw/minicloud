terraform {
  required_providers {
    restapi = {
      source  = "Mastercard/restapi"
      version = "2.0.1"
    }
  }
}

variable "name" {
  type        = string
  nullable    = false
  description = "A name to easily describe your virtual machine"

  validation {
    condition     = length(var.name) >= 3
    error_message = "The name should be at least 3 characters"
  }

  validation {
    condition     = can(regex("^[0-9A-Za-z-_]+$", var.name))
    error_message = "The name only allowed the following characters: a-z, A-Z, 0-9 and -_"
  }
}

variable "vcpu" {
  default     = 1
  nullable    = false
  description = "How much processors should be assigned to your virtual machine"

  validation {
    condition     = var.vcpu >= 1 && var.vcpu <= 8
    error_message = "The vcpu value should be between 1 and 8"
  }
}

variable "memory" {
  default     = 512
  nullable    = false
  description = "How much memory should be assigned to your virtual machine"

  validation {
    condition     = var.memory >= 512
    error_message = "The memory value should be at least 512"
  }
}

variable "disk_size" {
  default     = 20
  nullable    = false
  description = "How much disk space (in gigabyte) should be assigned to your virtual machine"

  validation {
    condition     = var.disk_size >= 10
    error_message = "The disk_size value should be at least 10"
  }
}

variable "base_vm" {
  type        = string
  nullable    = false
  description = <<EOT
Specify the base_vm name in tart that will be cloned for your new virtual machine

Note that some functionality depends on the base_vm support it, for example
the custom user_data does not work with the default tart debian image but it
can work with a custom made image.

See the examples directory for an example to create your own base image.
  EOT
}

variable "user_data" {
  type        = string
  default     = null
  nullable    = true
  description = <<EOT
A cloud-init/user-data script that should run on first boot.

Note that the default tart debian image does not suppor this, but it can work
with a custom made image.

See the examples directory for an example to create your own base image.
  EOT
}

variable "interface" {
  type        = string
  default     = null
  nullable    = true
  description = <<EOT
The network interface on the host machine you want to use for bridged networking.

Note that this is a bit unreliable for Linux as it depends on the ARP resolver
which is not available by default. This is not something I am personally using
so have not explored much further. For more details see:

https://tart.run/faq/#resolving-the-vms-ip-when-using-bridged-networking
  EOT
}

variable "skip_ip" {
  default     = false
  description = <<EOT
When using bridged mode (specified using `interface`) tart requires ARP to work
to obtain the IP address for the machine. This does not work guaranteed with
linux vms so this flag can skip getting the ip address.

This does mean you need to find the IP yourself, for example in the DHCP server
or by having it log onto your VPN or something.
EOT
}

variable "mac_addr" {
  type        = string
  nullable    = true
  default     = null
  description = <<EOT
Overwrite the generated mac address for the network interface.

By default tart will generate a mac address for your virtual machine and store
it in the config.json - with this option you can override that.
EOT

  validation {
    condition = (
      var.mac_addr == null ||
      can(regex("^([0-9A-Fa-f]{2}[:]){5}([0-9A-Fa-f]{2})$", var.mac_addr))
    )

    error_message = "The mac_addr requires a colon separated hexadecimal value, e.g. a1:b2:c3:d4:e5:f6"
  }
}

resource "restapi_object" "mod" {
  path                      = "/machine"
  ignore_all_server_changes = true

  force_new = [
    var.name,
    var.vcpu,
    var.memory,
    var.disk_size,
    coalesce(var.user_data, "empty_user_data"),
    coalesce(var.interface, "empty_interface"),
    coalesce(var.mac_addr, "empty_mac_addr"),
  ]

  data = jsonencode({
    "name"      = var.name,
    "vcpu"      = var.vcpu,
    "memory"    = var.memory,
    "base_vm"   = var.base_vm,
    "disk_size" = var.disk_size,
    "user_data" = var.user_data,
    "interface" = var.interface,
    "skip_ip"   = var.skip_ip,
    "mac_addr"  = var.mac_addr,
  })
}

output "id" {
  value = restapi_object.mod.id
}

output "ipv4" {
  value = jsondecode(restapi_object.mod.create_response).ipv4
}
