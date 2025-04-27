#!/usr/bin/env python3
import dataclasses
import json

from http.server import BaseHTTPRequestHandler

from .node import Node
from .tart import Tart
from .storage import Storage


class HttpHandler(BaseHTTPRequestHandler):
    @property
    def node_id(self):
        values = str(self.path).strip("/").split("/")
        if len(values) == 2 and values[0] == "machine":
            return values[1]
        else:
            return

    @property
    def json_body(self):
        content_length = int(self.headers["Content-Length"])
        post_data = self.rfile.read(content_length)
        return json.loads(post_data.decode("utf-8"))

    # READ /{id}
    def do_GET(self):
        if self.node_id == None:
            return self.error_response(400, "Bad Request")
        node = Storage.get(self.node_id)
        if node == None:
            return self.error_response(404, "Machine Not Found")
        self.ok_response(200, node)

    # CREATE /
    def do_POST(self):
        node = Node.new(self.json_body)
        result = Tart.create(node)
        Storage.set(node.id, result)
        self.ok_response(201, node)

    # UPDATE /{id}
    def do_PUT(self):
        self.error_response(501, "Not Implemented")

    # DELETE /{id}
    def do_DELETE(self):
        node = Storage.get(self.node_id)
        if node == None:
            return self.error_response(404, "Machine Not Found")
        result = Tart.delete(node)
        Storage.delete(node.id)
        self.ok_response(200, node)

    # RESPONSES
    def ok_response(self, status, node):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(node.to_json().encode(encoding="utf_8"))

    def error_response(self, status=404, message="Not Found"):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        json_str = json.dumps({"error": message})
        self.wfile.write(json_str.encode(encoding="utf_8"))
