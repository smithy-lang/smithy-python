# Copyright 2023 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
import json
from collections.abc import Generator
from ctypes import c_int
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from multiprocessing import Event, Process, Value

# multiprocessing.Event and multiprocessing.Value are wrapper functions for classes in
# multiprocessing's submodules. As of Python 3.11, no type annotations are readily
# available.
from multiprocessing.synchronize import Event as MPEventClass
from socketserver import TCPServer
from threading import Thread

import pytest


class _IntegrationTestServerRequestHandler(BaseHTTPRequestHandler):
    """HTTP server that echos the request's path and query string in JSON

    Example response body:
    {
        "request_path": "/path?with=query",
        "headers": {
            "User-Agent": "Python-urllib/3.11",
            "'Host": "localhost:60001"
        },
        "http_version": "HTTP/1.1"
    }
    """

    protocol_version = "HTTP/1.1"

    def do_GET(self) -> None:
        content = {
            "request_path": self.path,
            "request_headers": {k: v for k, v in self.headers.items()},
            "http_version": self.request_version,
        }
        content_json = json.dumps(content).encode("utf-8")
        size = len(content_json)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-type", "application/json")
        self.send_header("Content-Length", f"{size}")
        self.end_headers()
        self.wfile.write(content_json)


def _run_integration_test_server(
    server_ready_event: MPEventClass,
    shutdown_event: MPEventClass,
    # todo: find way to type this despite https://github.com/python/typeshed/issues/8799
    port_number,
) -> None:
    with TCPServer(("localhost", 0), _IntegrationTestServerRequestHandler) as httpd:
        server_thread = Thread(target=httpd.serve_forever)
        server_thread.daemon = True
        server_thread.start()
        _, port = httpd.server_address
        port_number.value = port
        server_ready_event.set()
        shutdown_event.wait()
        httpd.shutdown()
        server_thread.join()


@pytest.fixture(scope="module")
def running_server() -> Generator[int, None, None]:
    """Runs a HTTP server that responds to GET requests with a JSON response

    The fixture value is the port number of the HTTP server on localhost.
    """
    server_ready_event = Event()
    shutdown_event = Event()
    port_number = Value(c_int)
    proc = Process(
        target=_run_integration_test_server,
        kwargs={
            "server_ready_event": server_ready_event,
            "shutdown_event": shutdown_event,
            "port_number": port_number,
        },
    )
    proc.start()
    # wait up to one second for http server to start
    server_ready_event.wait(timeout=1.0)
    yield int(port_number.value)
    shutdown_event.set()
    # wait for server process to terminate
    proc.join()
