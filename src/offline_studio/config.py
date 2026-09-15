from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

DEFAULTS = {
    "lm_studio_url": "http://127.0.0.1:1234/v1",
    "comfyui_url": "http://127.0.0.1:8188",
    "model": "",
}


def validate_settings(value: dict) -> dict:
    result = {**DEFAULTS, **{k: value[k] for k in DEFAULTS if k in value}}
    for key in ("lm_studio_url", "comfyui_url"):
        url = str(result[key]).strip().rstrip("/")
        parsed = urlsplit(url)
        if (parsed.scheme != "http" or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                or parsed.username or parsed.password or parsed.query or parsed.fragment
                or parsed.path not in (("", "/v1") if key == "lm_studio_url" else ("",))):
            raise ValueError("服务地址必须是本机 HTTP 地址，LM Studio 可带 /v1。")
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ValueError("无效端口")
        result[key] = url
    result['model'] = str(result['model']).strip()[:200]
    return result


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def load_settings(path: Path) -> dict:
    return validate_settings(json.loads(path.read_text(encoding='utf-8')) if path.exists() else {})
