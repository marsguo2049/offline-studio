"""Open the existing local workbench, or start it with this repository's Python."""
import argparse
from http.client import HTTPConnection, HTTPException
from pathlib import Path
import subprocess
import sys
import webbrowser

ROOT = Path(__file__).resolve().parents[1]
MODULE = 'offline_studio.server'
SERVER = 'OfflineStudio/'
TITLE = '<title>Offline Studio</title>'
DEFAULT_PORT = 7870


def running(port):
    connection = HTTPConnection('127.0.0.1', port, timeout=2)
    try:
        connection.request('GET', '/')
        response = connection.getresponse()
        return (response.status == 200 and
                response.getheader('Server', '').startswith(SERVER) and
                TITLE in response.read(16384).decode('utf-8'))
    except (OSError, ValueError, HTTPException):
        return False
    finally:
        connection.close()


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    parser.add_argument('--port', type=int, default=DEFAULT_PORT)
    parser.add_argument('--no-browser', action='store_true')
    args, extra = parser.parse_known_args(argv)
    # Explicit data directories, translator overrides and help retain CLI behavior.
    reusable = not extra
    url = f'http://127.0.0.1:{args.port}/#batch'

    def reopen():
        print(f'Workbench is already running: {url}', flush=True)
        if not args.no_browser and not webbrowser.open(url):
            print(f'Open this address in your browser: {url}', flush=True)
        return 0

    if reusable and running(args.port):
        return reopen()
    result = subprocess.run([sys.executable, '-m', MODULE, *argv], cwd=ROOT)
    if result.returncode and reusable and running(args.port):
        return reopen()
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
