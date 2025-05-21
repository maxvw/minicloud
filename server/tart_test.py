import unittest
import os
from unittest.mock import patch, MagicMock, PropertyMock, DEFAULT, call

from .tart import Tart
from .node import Node

class response(dict):
    __getattr__= dict.__getitem__

class TestTart(unittest.TestCase):
  def setUp(self):
      self.node = Node.new({
        "name": "test-machine",
        "base_vm": "ghcr.io/cirruslabs/debian:bookworm",
        "vcpu": 1,
        "memory": 512,
      })

      self.cloud_init_dir = os.path.expanduser("~/.tart/vms/{}/cloud-init".format(self.node.id))
      self.cloud_init_iso = self.cloud_init_dir + ".iso"

      # We are going to mock our subprocess calls because otherwise the
      # test suite will take too long to complete.
      patcher = patch.multiple('subprocess',
          run=DEFAULT,
          Popen=DEFAULT,
          new_callable=PropertyMock)
      self.mock = patcher.start()
      self.addCleanup(patcher.stop)


  def test_vm_exists(self):
    self.mock['run'].side_effect = [
      response({'returncode': 0}),
    ]
    self.assertTrue(Tart.vm_exists(self.node))
    self.assertEqual(self.mock['run'].call_count, 1)
    self.mock['run'].assert_called_with(['tart', 'get', self.node.id], capture_output=True, check=False)

  def test_vm_doesnt_exist(self):
    self.mock['run'].side_effect = [
      response({'returncode': 1}),
    ]
    self.assertFalse(Tart.vm_exists(self.node))
    self.assertEqual(self.mock['run'].call_count, 1)
    self.mock['run'].assert_called_with(['tart', 'get', self.node.id], capture_output=True, check=False)

  def test_create(self):
    self.mock['run'].side_effect = [
      response({'returncode': 0}),
      response({'returncode': 0}),
      response({'returncode': 0, 'stdout': '{"Running": false}'.encode('utf-8')}),
      response({'returncode': 0}),
      response({'returncode': 0, 'stdout': '{"Running": true}'.encode('utf-8')}),
      response({'returncode': 0, 'stdout': '4.3.2.1'.encode('utf-8')}),
    ]

    self.mock['Popen'].side_effect = [
      response({})
    ]

    node = Tart.create(self.node)
    self.assertEqual(node.ipv4, "4.3.2.1")

    self.mock['run'].assert_has_calls([
      call(['tart', 'clone', "ghcr.io/cirruslabs/debian:bookworm", self.node.id], capture_output=True, check=False),
      call(['tart', 'set', self.node.id, "--disk-size", str(node.disk_size), "--memory", str(node.memory), "--cpu", str(node.vcpu)], capture_output=True, check=False),
      call(['tart', 'get', self.node.id, "--format", "json"], capture_output=True, check=False),
      call(["hdiutil", "makehybrid", "-iso", "-joliet", "-ov", "-default-volume-name", "cidata", "-o", self.cloud_init_iso, self.cloud_init_dir], capture_output=True, check=False),
      call(['tart', 'get', self.node.id, "--format", "json"], capture_output=True, check=False),
      call(['tart', 'ip', self.node.id, "--wait", "5"], capture_output=True, check=False),
    ])

  def test_create_already_running(self):
    self.mock['run'].side_effect = [
      response({'returncode': 0}),
      response({'returncode': 0}),
      response({'returncode': 0, 'stdout': '{"Running": true}'.encode('utf-8')}),
      response({'returncode': 0, 'stdout': '4.3.2.1'.encode('utf-8')}),
    ]

    node = Tart.create(self.node)
    self.assertEqual(node.ipv4, "4.3.2.1")

    self.mock['run'].assert_has_calls([
      call(['tart', 'clone', "ghcr.io/cirruslabs/debian:bookworm", self.node.id], capture_output=True, check=False),
      call(['tart', 'set', self.node.id, "--disk-size", str(node.disk_size), "--memory", str(node.memory), "--cpu", str(node.vcpu)], capture_output=True, check=False),
      call(['tart', 'get', self.node.id, "--format", "json"], capture_output=True, check=False),
      call(['tart', 'ip', self.node.id, "--wait", "5"], capture_output=True, check=False),
    ])

if __name__ == '__main__':
  unittest.main()
