import dataclasses
import json
import dbm
import os

from .node import Node

# Determine database directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
nodes_file = os.path.join(parent_dir, "db/nodes")


class Storage:
    def list():
        with dbm.open(nodes_file, "c") as db:
            return db.keys()

    def get(id):
        with dbm.open(nodes_file, "c") as db:
            if id not in db:
                return None
            return Node.from_json(db[id])
        return None

    def set(id, node):
        with dbm.open(nodes_file, "c") as db:
            db[id] = node.to_json()
        return node

    def delete(id):
        with dbm.open(nodes_file, "c") as db:
            if id in db:
                del db[id]
