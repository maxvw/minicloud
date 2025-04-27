import subprocess
import logging
import time
import os


class CloudInit:
    def create(node):
        cloud_init_dir = os.path.expanduser("~/.tart/vms/{}/cloud-init".format(node.id))
        iso_path = cloud_init_dir + ".iso"

        if not os.path.exists(cloud_init_dir):
            logging.info("[{}] creating cloud-init dir".format(node.id))
            os.makedirs(cloud_init_dir)

        if os.path.exists(iso_path):
            # NOTE: We only need to create it once
            return iso_path

        # Write meta-data file for CIDATA
        logging.info("[{}] writing cloud-init/meta-data file".format(node.id))
        with open(os.path.join(cloud_init_dir, "meta-data"), "w") as f:
            f.write(
                """
local-hostname: {}
""".lstrip().format(
                    node.name
                )
            )

        # Write user-data file for CIDATA
        if node.user_data:
            logging.info("[{}] writing cloud-init/user-data file".format(node.id))
            with open(os.path.join(cloud_init_dir, "user-data"), "w") as f:
                f.write(node.user_data)

        # Write network-config file for CIDATA
        logging.info("[{}] writing cloud-init/network-data file".format(node.id))
        with open(os.path.join(cloud_init_dir, "network-config"), "w") as f:
            f.write(
                """
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
""".lstrip().format(
                    node.id
                )
            )

        # Create ISO
        logging.info("[{}] creating cloud-init.iso (volume: cidata)".format(node.id))
        result = subprocess.run(
            [
                "hdiutil",
                "makehybrid",
                "-iso",
                "-joliet",
                "-ov",
                "-default-volume-name",
                "cidata",
                "-o",
                iso_path,
                cloud_init_dir,
            ],
            capture_output=True,
            check=False,
        )
        # TODO: Handle errors
        # CompletedProcess(args=['hdiutil', 'makehybrid', '-iso', '-joliet', '-ov', '-default-volume-name', 'cidata', '-o', '/Users/max/.tart/vms/debian:12/cloud-init.iso', '/Users/max/.tart/vms/debian:12/cloud-init'], returncode=0, stdout=b'Creating hybrid image...\n', stderr=b'\n')
        # print(result)

        return iso_path
