from __future__ import annotations

import io
import json
import re
import subprocess
import sys
import threading
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from .config import atomic_json, validate_settings

ACTIONS = {'inspect', 'terms', 'audit-terms', 'translate', 'render'}


class TranslationJobs:
    def __init__(self, root: Path, source: Path):
        self.root, self.source = root.resolve(), source.resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.RLock()
        self.active: str | None = None
        self.process: subprocess.Popen | None = None
        self.worker_thread: threading.Thread | None = None
        self.closing = False
        for path in self.root.glob('*/job.json'):
            job = json.loads(path.read_text(encoding='utf-8'))
            if job['status'] == 'running':
                job.update(status='interrupted', message='工作台已重启；可继续翻译。')
                atomic_json(path, job)

    def directory(self, job_id: str) -> Path:
        if not re.fullmatch(r'[a-f0-9]{32}', job_id):
            raise ValueError('无效任务编号')
        return self.root / job_id

    def create(self, filename: str, data: bytes) -> dict:
        name = filename.replace('\\', '/').split('/')[-1]
        if not name.lower().endswith('.docx') or len(data) > 50 * 1024 * 1024:
            raise ValueError('请选择不超过 50 MB 的 DOCX 文件。')
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                if 'word/document.xml' not in archive.namelist():
                    raise ValueError('文件不是 Word DOCX 文档。')
                if sum(info.file_size for info in archive.infolist()) > 250 * 1024 * 1024:
                    raise ValueError('解压后的文档超过 250 MB。')
        except zipfile.BadZipFile as exc:
            raise ValueError('文件不是有效 DOCX 文档。') from exc
        job_id = uuid.uuid4().hex
        directory = self.directory(job_id)
        (directory / 'input').mkdir(parents=True)
        (directory / 'input' / 'document.docx').write_bytes(data)
        atomic_json(directory / 'job.json', {
            'id': job_id, 'name': name[:240], 'status': 'ready', 'action': '',
            'created': datetime.now(timezone.utc).isoformat(), 'message': '文档已保存到本机。',
        })
        return self.get(job_id)

    def get(self, job_id: str) -> dict:
        directory = self.directory(job_id)
        job = json.loads((directory / 'job.json').read_text(encoding='utf-8'))
        job['artifacts'] = sorted(p.name for p in (directory / 'output').glob('*.docx'))
        log = directory / 'run.log'
        if log.exists():
            with log.open('rb') as stream:
                stream.seek(max(0, log.stat().st_size - 16000))
                job['log'] = stream.read().decode('utf-8', errors='replace')
        else:
            job['log'] = ''
        return job

    def list(self) -> list[dict]:
        jobs = [self.get(p.parent.name) for p in self.root.glob('*/job.json')]
        return sorted(jobs, key=lambda j: j['created'], reverse=True)

    def artifact(self, job_id: str, name: str) -> Path:
        if '/' in name or '\\' in name or not name.endswith('.docx'):
            raise ValueError('无效下载路径')
        directory = (self.directory(job_id) / 'output').resolve()
        path = (directory / name).resolve()
        if path.parent != directory:
            raise ValueError('无效下载路径')
        if not path.is_file():
            raise FileNotFoundError(name)
        return path

    def start(self, job_id: str, action: str, settings: dict) -> dict:
        if action not in ACTIONS:
            raise ValueError('不支持的翻译操作')
        settings = validate_settings(settings)
        if action in {'translate', 'terms', 'audit-terms'} and not settings['model']:
            raise ValueError('请先在服务设置中选择 LM Studio 模型。')
        if not self.source.is_file():
            raise FileNotFoundError('未找到翻译工具；请运行安装脚本或配置 --translator。')
        with self.lock:
            if self.closing or self.active:
                raise ValueError('已有翻译操作正在运行，请等待结束。')
            directory = self.directory(job_id)
            job = self.get(job_id)
            template = self.source.with_name('config.example.json')
            config = json.loads(template.read_text(encoding='utf-8'))
            config.update(server_url=settings['lm_studio_url'].removesuffix('/v1'), model=settings['model'])
            atomic_json(directory / 'config.json', config)
            job.update(status='running', action=action, message='正在处理，可关闭页面后回来查看。')
            self._save(job)
            self.active = job_id
            self.worker_thread = threading.Thread(target=self._run, args=(job_id, action), daemon=True)
            self.worker_thread.start()
            return job

    def _save(self, job: dict) -> None:
        atomic_json(self.directory(job['id']) / 'job.json', {k: v for k, v in job.items() if k not in {'log', 'artifacts'}})

    def _run(self, job_id: str, action: str) -> None:
        directory = self.directory(job_id)
        try:
            with (directory / 'run.log').open('wb') as log:
                with self.lock:
                    if self.closing:
                        raise RuntimeError('工作台正在关闭')
                    import os
                    env = {**os.environ, 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1'}
                    self.process = subprocess.Popen(
                        [sys.executable, '-m', 'offline_studio.worker', str(self.source), str(directory), action],
                        stdout=log, stderr=subprocess.STDOUT, env=env,
                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
                    )
                    process = self.process
                code = process.wait()
            job = self.get(job_id)
            job.update(status='completed' if code == 0 else 'failed',
                       message='操作完成。' if code == 0 else '操作未完成，请查看日志；翻译进度已保留。')
            self._save(job)
        except Exception as exc:
            job = self.get(job_id)
            job.update(status='failed', message=str(exc))
            self._save(job)
        finally:
            with self.lock:
                self.active = None
                self.process = None

    def close(self) -> None:
        with self.lock:
            self.closing = True
            if self.process and self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.process.kill()
                    self.process.wait(timeout=10)
        if self.worker_thread:
            self.worker_thread.join()
