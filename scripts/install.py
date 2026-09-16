"""Online preparation only; normal workbench startup never downloads anything."""
from __future__ import annotations

import argparse
import io
import json
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import venv
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def fetch(name: str, item: dict) -> Path:
    # Keep previous ComfyUI revisions in place; upgrading must not overwrite a
    # running backend or discard locally inspected source trees.
    folder = f'comfyui-{item["commit"][:12]}' if name == 'comfyui' else name
    target = ROOT / 'integrations' / folder
    marker = target / '.studio-revision'
    if target.exists():
        if marker.exists() and marker.read_text().strip() == item['commit']:
            return target
        raise RuntimeError(f'{target} already exists with another revision; move it aside before installing.')
    url = f'https://codeload.github.com/{item["repository"]}/zip/{item["commit"]}'
    print(f'Downloading {name} at {item["commit"]}', flush=True)
    with urllib.request.urlopen(url, timeout=120) as response:
        archive_data = response.read()
    target.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=target.parent) as temporary:
        temporary = Path(temporary).resolve()
        with zipfile.ZipFile(io.BytesIO(archive_data)) as archive:
            for entry in archive.infolist():
                destination = (temporary / entry.filename).resolve()
                if not destination.is_relative_to(temporary):
                    raise ValueError('Unsafe archive path')
            archive.extractall(temporary)
        directories = list(temporary.iterdir())
        if len(directories) != 1 or not directories[0].is_dir():
            raise ValueError('Unexpected archive layout')
        shutil.move(str(directories[0]), str(target))
    marker.write_text(item['commit'] + '\n')
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--local', action='store_true', help='Use existing sibling repositories without copying them')
    parser.add_argument('--minimal', action='store_true', help='Skip optional PDF/OCR dependencies; required media support remains installed')
    args = parser.parse_args()
    manifest = json.loads((ROOT / 'integrations.lock.json').read_text())
    if args.local:
        comfy = ROOT.parent / 'comfyui-py-workflow'
        translator = ROOT.parent / 'Local-Word-Translator'
        if not (comfy / 'pyproject.toml').is_file() or not (translator / 'translate_docx.py').is_file():
            raise FileNotFoundError('Expected sibling comfyui-py-workflow and Local-Word-Translator repositories')
        print('Using local checkouts; their revisions may differ from integrations.lock.json.')
    else:
        comfy = fetch('comfyui', manifest['comfyui'])
        translator = fetch('translator', manifest['translator'])
    environment = ROOT / '.venv'
    if not environment.exists():
        venv.create(environment, with_pip=True)
    python = environment / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
    dependency = str(comfy) + ('' if args.minimal else '[all]')
    subprocess.run([str(python), '-m', 'pip', 'install', '-e', dependency, '-e', str(ROOT) + '[dev]'], check=True)
    print('Ready. Run start-studio.bat on Windows, or .venv/bin/offline-studio from this directory.')


if __name__ == '__main__':
    main()
