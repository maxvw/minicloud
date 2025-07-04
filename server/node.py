import dataclasses
import random
import json

from typing import List, Optional


@dataclasses.dataclass
class Node:
    id: str
    name: str
    vcpu: int
    memory: int
    base_vm: str
    disk_size: int = 10
    skip_ip: bool = False
    extra_args: Optional[List[str]] = dataclasses.field(default_factory=list)
    interface: Optional[str] = None
    mac_addr: Optional[str] = None
    user_data: Optional[str] = None
    ipv4: Optional[str] = None

    def new(params):
        node_id = "i-%06x" % random.randrange(16**6)
        return Node(id=node_id, **params)

    def from_json(str):
        return Node(**json.loads(str))

    def to_json(self):
        return json.dumps(dataclasses.asdict(self))
