import json
import threading
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from offline_studio.config import DEFAULTS
from offline_studio.server import create_server, workbench_html


def test_ui_contract():
    source = workbench_html(DEFAULTS)
    for text in ['data-view="batch"', 'data-view="comic"', 'data-view="story"',
                 'href="/translate"', '/studio-assets/settings.js', 'my-llm']:
        assert text in source
    assert source.index('settings.js') < source.index('/static/app.js')
    assert '批量首尾帧视频' in source
    assert 'id="batch-first-files"' in source
    assert 'id="lm-url"' in source


def test_aggregate_owns_creative_page():
    from offline_studio.ui import ASSETS
    page = (ASSETS / 'creative.html').read_text(encoding='utf-8')
    assert '<!-- COMFYUI_BATCH -->' in page
    assert 'id="view-story"' in page and 'id="view-comic"' in page


@pytest.fixture
def server(tmp_path):
    instance = create_server(tmp_path, Path('missing.py'), 0)
    thread = threading.Thread(target=instance.serve_forever, daemon=True)
    thread.start()
    yield instance
    instance.shutdown()
    instance.server_close()


def test_http_routes_and_settings_persistence(server):
    base = f'http://127.0.0.1:{server.server_port}'
    for route in ['/', '/translate', '/static/style.css', '/static/app.js',
                  '/studio-assets/translate.js', '/api/projects', '/api/batch/jobs', '/api/comic/jobs']:
        with urlopen(base + route) as response:
            assert response.status == 200
    request = Request(base + '/api/studio/settings',
                      data=json.dumps({**DEFAULTS, 'model':'local-test-model'}).encode(),
                      headers={'Content-Type':'application/json', 'Origin':base})
    with urlopen(request) as response:
        assert json.load(response)['model'] == 'local-test-model'
    with urlopen(base + '/') as response:
        assert b'local-test-model' in response.read()


def test_http_rejects_cross_origin_and_remote_host(server):
    base = f'http://127.0.0.1:{server.server_port}'
    for origin in ['http://evil.test', None]:
        headers = {'Content-Type':'application/json'}
        if origin:
            headers['Origin'] = origin
        with pytest.raises(HTTPError) as error:
            urlopen(Request(base + '/api/studio/settings', data=b'{}', headers=headers))
        assert error.value.code == 400
    with pytest.raises(HTTPError):
        urlopen(Request(base + '/api/translation/jobs', headers={'Host':'evil.test'}))


def test_aggregate_does_not_serve_standalone_shell(server):
    base = f'http://127.0.0.1:{server.server_port}'
    for asset in ['index.html', 'batch.html', 'preview.js', 'comfy.js']:
        with pytest.raises(HTTPError) as error:
            urlopen(base + '/static/' + asset)
        assert error.value.code == 404


def test_video_pair_preview_is_available_in_aggregate(server):
    base = f'http://127.0.0.1:{server.server_port}'
    payload = {'files':[{'name':'first.png','role':'first'},
                        {'name':'tail-2.png','role':'last'}, {'name':'tail-10.png','role':'last'}]}
    request = Request(base + '/api/batch/video-preview', data=json.dumps(payload).encode(),
                      headers={'Content-Type':'application/json', 'Origin':base})
    with urlopen(request) as response:
        result = json.load(response)
    assert len(result['pairs']) == 2
    assert result['pairs'][0]['last']['name'] == 'tail-2.png'


def test_different_ports_cannot_share_data_directory(tmp_path):
    first = create_server(tmp_path, Path('missing.py'), 0)
    try:
        with pytest.raises(OSError, match='data directory'):
            second = create_server(tmp_path, Path('missing.py'), 0)
            second.server_close()
        other = create_server(tmp_path / 'other', Path('missing.py'), 0)
        other.server_close()
    finally:
        first.server_close()
    restarted = create_server(tmp_path, Path('missing.py'), 0)
    restarted.server_close()
