"""Shared test setup: tests never touch the live web.

- block_live_web runs for every test and fails any network connection that isn't to this
  computer (127.0.0.1), so an accidental real request fails loudly instead of quietly passing.
- local_server serves the hand-made pages in tests/fixtures/pages/ from this computer.
"""

import socket
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import pytest

PAGES = Path(__file__).resolve().parent / "fixtures" / "pages"
LOCAL_HOSTS = ("127.0.0.1", "::1")


@pytest.fixture(autouse=True)
def block_live_web(monkeypatch):
    real_connect = socket.socket.connect

    def connect_local_only(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in LOCAL_HOSTS:
            raise RuntimeError(f"tests must not touch the live web (tried to connect to {host})")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", connect_local_only)


class PageHandler(BaseHTTPRequestHandler):
    """Serves fixture pages. /slow waits 2 seconds; any unknown path is a 404."""

    last_user_agent = None
    requested_paths = []  # every path asked for, so tests can count downloads

    def do_GET(self):
        PageHandler.last_user_agent = self.headers.get("User-Agent")
        PageHandler.requested_paths.append(self.path)
        if self.path == "/slow":
            time.sleep(2)  # longer than the short timeout the test uses
            try:
                self.send_page(200, b"<p>Too late</p>")
            except OSError:
                pass  # the test already gave up and closed the connection
            return

        page = PAGES / Path(self.path).name
        if page.suffix == ".html" and page.is_file():
            self.send_page(200, page.read_bytes())
        else:
            self.send_page(404, b"<p>Not found</p>")

    def send_page(self, status, body):
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass  # keep test output quiet


@pytest.fixture(scope="session")
def local_server():
    # Port 0 asks the operating system for any free port.
    server = ThreadingHTTPServer(("127.0.0.1", 0), PageHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield SimpleNamespace(url=f"http://127.0.0.1:{server.server_port}", handler=PageHandler)
    server.shutdown()
    server.server_close()
