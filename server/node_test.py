import unittest

from .node import Node

NODE_JSON = '{"id": "i-f4aba2", "name": "test-machine", "vcpu": 2, "memory": 1024, "base_vm": "ghcr.io/cirruslabs/debian:bookworm", "disk_size": 10, "skip_ip": false, "extra_args": [], "interface": null, "mac_addr": null, "user_data": null, "ipv4": null}'


class TestNode(unittest.TestCase):
    def test_validate_missing(self):
        with self.assertRaises(TypeError):
            node = Node.new({})

    def test_new_with_defaults(self):
        node = Node.new({
            "name": "test-machine",
            "base_vm": "ghcr.io/cirruslabs/debian:bookworm",
            "vcpu": 2,
            "memory": 1024,
        })
        self.assertEqual(node.name, "test-machine")
        self.assertEqual(node.base_vm, "ghcr.io/cirruslabs/debian:bookworm")
        self.assertEqual(node.vcpu, 2)
        self.assertEqual(node.memory, 1024)
        self.assertEqual(node.disk_size, 10)
        self.assertFalse(node.skip_ip)
        self.assertEqual(node.extra_args, [])
        self.assertEqual(node.interface, None)
        self.assertEqual(node.mac_addr, None)
        self.assertEqual(node.user_data, None)
        self.assertEqual(node.ipv4, None)

    def test_to_json(self):
        node = Node.new({
            "name": "test-machine",
            "base_vm": "ghcr.io/cirruslabs/debian:bookworm",
            "vcpu": 2,
            "memory": 1024,
        })
        node.id = "i-f4aba2"

        self.assertEqual(Node.to_json(node), NODE_JSON)

    def test_from_json(self):
        node = Node.from_json(NODE_JSON)
        self.assertEqual(node.id, "i-f4aba2")
        self.assertEqual(node.name, "test-machine")
        self.assertEqual(node.base_vm, "ghcr.io/cirruslabs/debian:bookworm")
        self.assertEqual(node.vcpu, 2)
        self.assertEqual(node.memory, 1024)
        self.assertEqual(node.disk_size, 10)
        self.assertFalse(node.skip_ip)
        self.assertEqual(node.extra_args, [])
        self.assertEqual(node.interface, None)
        self.assertEqual(node.mac_addr, None)
        self.assertEqual(node.user_data, None)
        self.assertEqual(node.ipv4, None)


if __name__ == "__main__":
    unittest.main()
