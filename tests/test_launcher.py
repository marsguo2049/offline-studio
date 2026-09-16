"""Double-clicking a running studio opens it without spawning another worker."""
import importlib.util
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading

import pytest


@pytest.mark.parametrize('matching', [True, False])
def test_launch_checks_service_identity_before_reopening(monkeypatch, matching):
    path = Path(__file__).resolve().parents[1] / 'scripts/launch.py'
    spec = importlib.util.spec_from_file_location('studio_launcher', path)
    launcher = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(launcher)

    class Handler(BaseHTTPRequestHandler):
        server_version = 'OfflineStudio/0.2' if matching else 'CPWComfyUIWorkbench/0.6'
        def do_GET(self):
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'<title>Offline Studio</title>')
        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    opened, started = [], []
    monkeypatch.setattr(launcher.webbrowser, 'open', lambda url: opened.append(url) or True)
    def run(command, **kwargs):
        started.append(command)
        return type('Result', (), {'returncode': 2})()
    monkeypatch.setattr(launcher.subprocess, 'run', run)
    try:
        result = launcher.main(['--port', str(server.server_port)])
        assert result == (0 if matching else 2)
        assert len(started) == (0 if matching else 1)
        assert opened == ([f'http://127.0.0.1:{server.server_port}/#batch'] if matching else [])
        if matching:
            opened.clear()
            assert launcher.main(['--port', str(server.server_port), '--no-browser']) == 0
            assert not opened and not started
            # A caller asking for different task storage must not silently reuse it.
            assert launcher.main(['--port', str(server.server_port), '--data-dir', 'different-data']) == 2
            assert len(started) == 1 and not opened
    finally:
        server.shutdown()
        server.server_close()
        worker.join()
