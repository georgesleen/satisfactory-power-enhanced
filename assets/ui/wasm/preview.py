#!/usr/bin/env python3
"""Serve the built UI on loopback only."""

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("directory", type=Path)
parser.add_argument("--port", type=int, default=8080)
arguments = parser.parse_args()


server = ThreadingHTTPServer(
    ("127.0.0.1", arguments.port),
    partial(SimpleHTTPRequestHandler, directory=str(arguments.directory)),
)
print(f"UI preview: http://127.0.0.1:{arguments.port}/", flush=True)
try:
    server.serve_forever()
except KeyboardInterrupt:
    pass
finally:
    server.server_close()
