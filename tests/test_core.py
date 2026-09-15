import io
import json
import time
import zipfile
from pathlib import Path

import pytest

from offline_studio.config import validate_settings
from offline_studio.translation import TranslationJobs


def document():
    from docx import Document
    buffer = io.BytesIO()
    doc = Document()
    doc.add_paragraph('Introduction')
    doc.save(buffer)
    return buffer.getvalue()


def test_settings_reject_remote_and_credentials():
    for url in ['https://example.com', 'http://127.0.0.1.evil.test',
                'http://user:pass@localhost:1234', 'ftp://localhost',
                'http://localhost:1234/foo', 'http://localhost:1234/?key=x']:
        with pytest.raises(ValueError):
            validate_settings({'lm_studio_url': url})
    assert validate_settings({'lm_studio_url': 'http://localhost:1234/v1'})['lm_studio_url'] == 'http://localhost:1234/v1'


def test_upload_validates_document_and_isolates_filename(tmp_path):
    jobs = TranslationJobs(tmp_path, Path('missing.py'))
    with pytest.raises(ValueError):
        jobs.create('a.docx', b'not a zip')
    job = jobs.create('../../private.docx', document())
    assert (tmp_path / job['id'] / 'input' / 'document.docx').exists()
    assert job['name'] == 'private.docx'
    with pytest.raises(ValueError):
        jobs.get('../escape')
    with pytest.raises(ValueError):
        jobs.artifact(job['id'], '../job.json')


def test_restart_marks_running_job_interrupted(tmp_path):
    jobs = TranslationJobs(tmp_path, Path('missing.py'))
    job = jobs.create('a.docx', document())
    path = tmp_path / job['id'] / 'job.json'
    saved = json.loads(path.read_text(encoding='utf-8'))
    saved['status'] = 'running'
    path.write_text(json.dumps(saved), encoding='utf-8')
    restarted = TranslationJobs(tmp_path, Path('missing.py'))
    assert restarted.get(job['id'])['status'] == 'interrupted'


def test_real_translator_inspect_and_render(tmp_path):
    source = Path(__file__).resolve().parents[1] / 'integrations' / 'translator' / 'translate_docx.py'
    if not source.exists():
        source = Path(__file__).resolve().parents[2] / 'Local-Word-Translator' / 'translate_docx.py'
    assert source.exists(), 'Install the pinned translation integration before testing'
    jobs = TranslationJobs(tmp_path, source)
    job = jobs.create('sample.docx', document())
    for action in ['inspect', 'render']:
        if action == 'render':
            # Explicit synthetic translation fixture: inspect does not translate.
            # Exercise the real renderer without requesting model inference.
            manifest_path = next((tmp_path / job['id'] / 'progress').glob('*/manifest.json'))
            manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
            translations = {'items': {item['id']: {'translation':'引言', 'source':item['source'],
                'status':'completed', 'method':'test-fixture'} for item in manifest['items']}}
            manifest_path.with_name('translations.json').write_text(json.dumps(translations), encoding='utf-8')
        jobs.start(job['id'], action, validate_settings({}))
        deadline = time.monotonic() + 20
        while jobs.get(job['id'])['status'] == 'running' and time.monotonic() < deadline:
            time.sleep(.05)
        result = jobs.get(job['id'])
        assert result['status'] == 'completed', result['log'] + result['message']
    assert len(result['artifacts']) == 2
    assert zipfile.is_zipfile(jobs.artifact(job['id'], result['artifacts'][0]))
