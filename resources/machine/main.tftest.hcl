mock_provider "restapi" {
  mock_resource "restapi_object" {
    defaults = {
      id              = "i-123abc"
      create_response = <<EOT
      {
        "id": "i-123abc",
        "ipv4": "127.0.0.1"
      }
      EOT
    }
  }
}

variables {
  name      = "test-vm"
  base_vm   = "debian:12"
  vcpu      = 2
  memory    = 1024
  disk_size = 10
}

run "valid_plan" {
  command = plan
}

run "valid_apply" {
  command = apply

  assert {
    condition     = output.ipv4 == "127.0.0.1"
    error_message = "Did not return the expected ipv4 address"
  }

  assert {
    condition     = restapi_object.mod.id == "i-123abc"
    error_message = "Did not return the expected id"
  }

  assert {
    condition     = restapi_object.mod.path == "/machine"
    error_message = "Did not return the expected path"
  }
}

run "validate_name" {
  command = plan

  variables {
    name = "a-1"
  }
}

run "validate_name_length" {
  command = plan

  variables {
    name = "ab"
  }

  expect_failures = [var.name]
}

run "validate_name_characters" {
  command = plan

  variables {
    name = "æbç"
  }

  expect_failures = [var.name]
}


run "validate_vcpu" {
  command = plan

  variables {
    vcpu = 1
  }
}

run "validate_vcpu_min" {
  command = plan

  variables {
    vcpu = 0.5
  }

  expect_failures = [var.vcpu]
}

run "validate_vcpu_max" {
  command = plan

  variables {
    vcpu = 10
  }

  expect_failures = [var.vcpu]
}

run "validate_memory" {
  command = plan

  variables {
    memory = 512
  }
}

run "validate_memory_min" {
  command = plan

  variables {
    memory = 128
  }

  expect_failures = [var.memory]
}

run "validate_disk_size" {
  command = plan

  variables {
    disk_size = 10
  }
}

run "validate_disk_size_min" {
  command = plan

  variables {
    disk_size = 5
  }

  expect_failures = [var.disk_size]
}
