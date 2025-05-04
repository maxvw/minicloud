import subprocess
import logging
import os

from .cloud_init import CloudInit


class Tart:
    def vm_exists(node):
        result = subprocess.run(
            ["tart", "get", node.id], capture_output=True, check=False
        )
        return result.returncode == 0

    def start(node):
        # Create cloud-init (CIDATA) disk image
        iso_path = CloudInit.create(node)

        # tart run stays running, so this can probably be improved but its good
        # enough for my use-case, for now
        logging.info("[{}] attempting to start".format(node.id))
        args = ["tart", "run", node.id, "--disk", iso_path, "--no-graphics"]
        if node.interface:
            args.extend(["--net-bridged", node.interface])
        result = subprocess.Popen(args, stdout=subprocess.DEVNULL)
        # TODO: Handle errors
        # print(result)

        # Try to get the assigned IP
        if not node.skip_ip:
            logging.info("[{}] waiting for ipv4 address".format(node.id))
            args = ["tart", "ip", node.id, "--wait", "5"]
            if node.interface:
                args.extend(["--resolver", "arp"])
            result = subprocess.run(args, capture_output=True, check=False)
            ipv4_addr = result.stdout.decode("utf-8").strip()
            logging.info("[{}] now available with ipv4 {}".format(node.id, ipv4_addr))
            # TODO: Handle errors
            # print(result)
        else:
            logging.info(
                "[{}] received skip_ip, so NOT waiting for ipv4 address".format(node.id)
            )

    def create(node):
        logging.info(
            "[{}] creating new machine based on {}".format(node.id, node.base_vm)
        )
        result = subprocess.run(
            ["tart", "clone", node.base_vm, node.id], capture_output=True, check=False
        )
        # TODO: Handle errors
        # print(result)

        logging.info(
            "[{}] setting cpu={} memory={} disk-size={}".format(
                node.id, node.vcpu, node.memory, node.disk_size
            )
        )
        result = subprocess.run(
            [
                "tart",
                "set",
                node.id,
                "--disk-size",
                str(node.disk_size),
                "--memory",
                str(node.memory),
                "--cpu",
                str(node.vcpu),
            ],
            capture_output=True,
            check=False,
        )
        # TODO: Handle errors
        # print(result)

        # Create cloud-init (CIDATA) disk image
        iso_path = CloudInit.create(node)

        # tart run stays running, so this can probably be improved but its good
        # enough for my use-case, for now
        logging.info("[{}] attempting to start".format(node.id))
        args = ["tart", "run", node.id, "--disk", iso_path, "--no-graphics"]
        if node.interface:
            args.extend(["--net-bridged", node.interface])
        result = subprocess.Popen(args, stdout=subprocess.DEVNULL)
        # <Popen: returncode: None args: ['tart', 'run', 'max-vps']>
        # TODO: Handle errors
        # print(result)

        # Try to get the assigned IP
        if not node.skip_ip:
            logging.info("[{}] waiting for ipv4 address".format(node.id))
            args = ["tart", "ip", node.id, "--wait", "5"]
            if node.interface:
                args.extend(["--resolver", "arp"])
            result = subprocess.run(args, capture_output=True, check=False)
            ipv4_addr = result.stdout.decode("utf-8").strip()
            logging.info("[{}] now available with ipv4 {}".format(node.id, ipv4_addr))
            # TODO: Handle errors
            # print(result)
            node.ipv4 = ipv4_addr
        else:
            logging.info(
                "[{}] received skip_ip, so NOT waiting for ipv4 address".format(node.id)
            )

        return node

    def delete(node):
        logging.info("[{}] attempting to stop machine".format(node.id))
        result = subprocess.run(
            ["tart", "stop", node.id], capture_output=True, check=False
        )
        # TODO: Handle errors ?
        # print(result)

        logging.info("[{}] deleting machine".format(node.id))
        result = subprocess.run(
            ["tart", "delete", node.id], capture_output=True, check=False
        )
        # TODO: Handle errors ?
        # print(result)
        return node
