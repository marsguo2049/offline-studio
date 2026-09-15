from __future__ import annotations

import argparse
import html
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit

from comfyui_py_workflow.local_ui import StudioRequestHandler, SingleInstanceHTTPServer, WEB_ROOT
from comfyui_py_workflow.studio import OfflineStudio
from comfyui_py_workflow.batch_studio import BatchStudio
from comfyui_py_workflow.comic_studio import ComicStudio

from .config import atomic_json, load_settings, validate_settings
from .translation import TranslationJobs
from .locking import DataDirectoryLock

ASSETS = Path(__file__).with_name('web')
NAVIGATION = '''<a class="nav-item studio-link" href="/translate">▧ 文档翻译</a>
<p class="nav-caption">学习与研究 · 在线链接</p>
<a class="nav-item studio-link" href="https://github.com/marsguo2049/my-llm" target="_blank" rel="noopener">↗ 大模型笔记</a>
<a class="nav-item studio-link" href="https://github.com/marsguo2049/multi-model-workflow-optimization" target="_blank" rel="noopener">↗ 工作流优化研究</a>'''


def workbench_html(settings: dict) -> str:
    source = (WEB_ROOT / 'index.html').read_text(encoding='utf-8')
    if '</nav>' not in source or '<script src="/static/app.js"></script>' not in source:
        raise RuntimeError('ComfyUI UI contract changed; install the pinned integration version.')
    source = source.replace('</nav>', NAVIGATION + '</nav>', 1)
    source = source.replace('本地创作工作台', '本地 AI 工作台').replace('<small>ComfyUI Py Workflow</small>', '<small>Offline Studio · 0.1</small>')
    source = source.replace('</head>', '<link rel="stylesheet" href="/studio-assets/studio.css"></head>')
    source = source.replace('value="http://127.0.0.1:1234/v1"', f'value="{html.escape(settings["lm_studio_url"], quote=True)}"')
    source = source.replace('value="http://127.0.0.1:8188"', f'value="{html.escape(settings["comfyui_url"], quote=True)}"')
    if settings['model']:
        model = html.escape(settings['model'], quote=True)
        source = source.replace('<option value="">等待检测</option>', f'<option value="{model}">{model}</option>')
    return source.replace('<script src="/static/app.js"></script>', '<script src="/studio-assets/settings.js"></script>\n<script src="/static/app.js"></script>')


class Handler(StudioRequestHandler):
    settings_path: Path
    translations: TranslationJobs

    def _local_request(self, mutation: bool = False) -> None:
        host = self.headers.get('Host', '')
        allowed = {f'{name}:{self.server.server_port}' for name in ('127.0.0.1', 'localhost', '[::1]')}
        if host not in allowed:
            raise PermissionError('Only local workbench requests are accepted')
        origin = self.headers.get('Origin')
        if mutation and origin != f'http://{host}':
            raise PermissionError('Same-origin requests are required')

    def do_GET(self) -> None:
        try:
            self._local_request()
            parsed = urlsplit(self.path)
            if parsed.path in {'/', '/index.html'}:
                body = workbench_html(load_settings(self.settings_path)).encode('utf-8')
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('Cache-Control', 'no-store')
                self.end_headers()
                self.wfile.write(body)
            elif parsed.path == '/translate':
                self._send_file(ASSETS / 'translate.html', cache=False)
            elif parsed.path.startswith('/studio-assets/'):
                name = parsed.path.removeprefix('/studio-assets/')
                if name not in {'studio.css', 'settings.js', 'translate.js'}:
                    raise FileNotFoundError(name)
                self._send_file(ASSETS / name, cache=False)
            elif parsed.path == '/api/studio/settings':
                self._send_json(load_settings(self.settings_path))
            elif parsed.path == '/api/translation/jobs':
                self._send_json({'jobs': self.translations.list(), 'available': self.translations.source.is_file()})
            elif parsed.path == '/api/translation/job':
                self._send_json(self.translations.get(self._query(parsed, 'id')))
            elif parsed.path == '/translation-download':
                path = self.translations.artifact(self._query(parsed, 'id'), self._query(parsed, 'name'))
                self._send_file(path, cache=False)
            else:
                super().do_GET()
        except Exception as exc:
            self._send_error(exc)

    def do_POST(self) -> None:
        try:
            self._local_request(mutation=True)
            parsed = urlsplit(self.path)
            if parsed.path == '/api/studio/settings':
                settings = validate_settings(self._read_json())
                atomic_json(self.settings_path, settings)
                self._send_json(settings)
            elif parsed.path == '/api/translation/upload':
                self._send_json(self.translations.create(self._query(parsed, 'filename'), self._read_body(50 * 1024 * 1024)), status=201)
            elif parsed.path == '/api/translation/start':
                body = self._read_json()
                self._send_json(self.translations.start(str(body['id']), str(body['action']), load_settings(self.settings_path)), status=202)
            else:
                super().do_POST()
        except Exception as exc:
            self._send_error(exc)

    def do_HEAD(self) -> None:
        try:
            self._local_request()
            super().do_HEAD()
        except Exception as exc:
            self._send_error(exc)

    def _read_body(self, max_bytes: int = 20 * 1024 * 1024) -> bytes:
        self.connection.settimeout(30)
        data = super()._read_body(max_bytes)
        if len(data) != int(self.headers.get('Content-Length', '0')):
            raise ValueError('Incomplete request body')
        return data


class WorkbenchServer(SingleInstanceHTTPServer):
    directory_lock: DataDirectoryLock | None = None

    def server_close(self) -> None:
        try:
            super().server_close()
        finally:
            translations = getattr(self.RequestHandlerClass, 'translations', None)
            if translations:
                translations.close()
            # Retain the directory lock if worker cleanup raises.
            if self.directory_lock:
                self.directory_lock.close()


def create_server(data: Path, translator: Path, port: int = 7870) -> WorkbenchServer:
    # Lock data before job recovery, even when two instances use different ports.
    class InstanceHandler(Handler):
        pass
    directory_lock = DataDirectoryLock(data)
    try:
        server = WorkbenchServer(('127.0.0.1', port), InstanceHandler)
    except Exception:
        directory_lock.close()
        raise
    server.directory_lock = directory_lock
    try:
        InstanceHandler.settings_path = data / 'settings.json'
        InstanceHandler.translations = TranslationJobs(data / 'translation', translator)
        InstanceHandler.studio = OfflineStudio(data / 'creative')
        InstanceHandler.batch = BatchStudio(data / 'creative' / 'batch-jobs')
        InstanceHandler.comic = ComicStudio(data / 'creative' / 'comic-jobs')
    except Exception:
        server.server_close()
        raise
    return server


def main() -> None:
    parser = argparse.ArgumentParser(description='Offline Studio — unified local AI workbench')
    parser.add_argument('--port', type=int, default=7870)
    parser.add_argument('--data-dir', type=Path, default=Path.cwd() / 'data')
    parser.add_argument('--translator', type=Path)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()
    translator = args.translator or Path.cwd() / 'integrations' / 'translator' / 'translate_docx.py'
    if args.translator is None and not translator.exists():
        translator = Path.cwd().parent / 'Local-Word-Translator' / 'translate_docx.py'
    try:
        server = create_server(args.data_dir.resolve(), translator, args.port)
    except (OSError, ValueError) as exc:
        parser.exit(2, f'无法启动工作台：{exc}\n')
    url = f'http://127.0.0.1:{server.server_port}/#batch'
    print(f'Offline Studio: {url}', flush=True)
    if not args.no_browser:
        threading.Timer(.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == '__main__':
    main()
