import subprocess
import logging
import json
import time
import os

from signal import SIGUSR2

from .cloud_init import CloudInit

STARTUP_TIME_LIMIT = 5
SHUTDOWN_TIME_LIMIT = 15


class Tart:
    def vm_exists(node):
        result = subprocess.run(
            ["tart", "get", node.id], capture_output=True, check=False
        )
        return result.returncode == 0

    def vm_running(node):
        args = ["tart", "get", node.id, "--format", "json"]
        result = subprocess.run(args, capture_output=True, check=False)
        if result.returncode != 0:
            return False
        result_json = result.stdout.decode("utf-8").strip()
        result_dict = json.loads(result_json)
        return result_dict["Running"] == True

    def maybe_get_ip(node):
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

    def start(node):
        if Tart.vm_running(node):
            node = Tart.maybe_get_ip(node)
            return node

        # Create cloud-init (CIDATA) disk image
        iso_path = CloudInit.create(node)

        # If there is a custom mac address we need to update the config.json
        # as there is no tart command for this.
        if node.mac_addr:
            config_path = os.path.expanduser(
                "~/.tart/vms/{}/config.json".format(node.id)
            )
            with open(config_path, "r") as openfile:
                config_dict = json.load(openfile)
            config_dict["macAddress"] = node.mac_addr.lower()
            with open(config_path, "w") as outfile:
                json.dump(config_dict, outfile)

        # tart run stays running, so this can probably be improved but its good
        # enough for my use-case, for now
        logging.info("[{}] attempting to start".format(node.id))
        args = ["tart", "run", node.id, "--disk", iso_path, "--no-graphics"]
        if node.interface:
            args.extend(["--net-bridged", node.interface])
        result = subprocess.Popen(args, stdout=subprocess.DEVNULL)
        # TODO: Handle errors
        # print(result)

        # We're waiting for the VM to report back with status Running
        # but if it takes too long we will just assume it'll be alright, for now
        # TODO: Look into scenario where it doesn't switch to running, but not
        # sure how likely this will be. I know for macOS VMs there is a 2 VM
        # limit but for Linux I don't believe there is.
        start_boot_time = time.time()
        while time.time() - start_boot_time < STARTUP_TIME_LIMIT:
            if Tart.vm_running(node):
                break
            time.sleep(1)

        logging.info("[{}] started machine".format(node.id))
        node = Tart.maybe_get_ip(node)
        return node

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

        node = Tart.start(node)
        return node

    def stop(node):
        # NOTE: Tart by default appears to forcefully stop the VM, however I
        # noticed in their codebase that sending USR2 will request a stop
        # instead which should trigger a graceful shutdown.
        result = subprocess.run(
            ["pgrep", "-f", node.id], capture_output=True, check=False
        )
        if result.returncode == 0:
            pid = result.stdout
            logging.info(
                "[{}] attempting to stop machine (pid={})".format(node.id, int(pid))
            )
            os.kill(int(pid), SIGUSR2)

            # Here we give the VM a max amount of time to shutdown gracefully
            # but if the VM doesn't shut down within this time it will be
            # stopped forcefully.
            start_shutdown_time = time.time()
            while time.time() - start_shutdown_time < SHUTDOWN_TIME_LIMIT:
                if not Tart.vm_running(node):
                    break
                time.sleep(1)

        # If the VM is still running, it's time to force it to shut down.
        if Tart.vm_running(node):
            logging.info("[{}] forcing machine to stop".format(node.id))
            result = subprocess.run(
                ["tart", "stop", node.id, "--timeout", "1"],
                capture_output=True,
                check=False,
            )

        logging.info("[{}] stopped machine".format(node.id))

    def delete(node):
        Tart.stop(node)

        logging.info("[{}] deleting machine".format(node.id))
        result = subprocess.run(
            ["tart", "delete", node.id], capture_output=True, check=False
        )
        # TODO: Handle errors ?
        # print(result)
        return node
