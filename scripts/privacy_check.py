"""Inspect the exact Git index without printing matched sensitive values.

This is a focused publication gate, not a guarantee that arbitrary prose is safe.
Manually review new prose and files as well. Run after git add and before commit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path, PurePosixPath

RULES = {
    'credential-token': re.compile(r'(?:gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|sk-[A-Za-z0-9_-]{20,}|hf_[A-Za-z0-9]{20,}|AKIA[A-Z0-9]{16})'),
    'private-key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'personal-windows-path': re.compile(r'(?i)[A-Z]:[\\/](?:Users|Local-LLM|City2049)[\\/]'),
    'personal-unix-path': re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
    'secret-assignment': re.compile(r'''(?i)(?:api[_-]?key|access[_-]?token|password|client[_-]?secret)\s*["']?\s*[:=]\s*["'][A-Za-z0-9_+/=-]{16,}["']'''),
    'email-address': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'),
}
PRIVATE_PARTS = {'.venv', 'data', 'integrations', 'input', 'output', 'outputs', 'progress', 'glossary', 'logs', 'models', '__pycache__'}
TEXT_SUFFIXES = {'.py', '.js', '.css', '.html', '.md', '.json', '.toml', '.yml', '.yaml', '.bat', '.txt', '.svg'}

# Independently reviewed public samples from comfyui-py-workflow a76329af.
# Never regenerate these approvals from a developer's local media directory.
APPROVED_PUBLIC_ASSETS = {
    'docs/assets/bicycle-frame-0001.png': 'b8382e69100c40401423f641c852c1ea5dc1c44baea714c6edf3e1fcdd450781',
    'docs/assets/bicycle-frame-0002.png': 'd23cfc6b058d731a1b48e15783d5dcaa96613f3f10719cc551efdb5dcface718',
    'docs/assets/bicycle-frame-0003.png': 'c403918bf00a83fd80980d0af6890f54dbb678fb69bce7b173f8fe10392ccf59',
    'docs/assets/bicycle-final-10s.mp4': 'e0342a96c5dbc951be2711705cbd44fde6e9966b9d9b773e6c572475c1be9558',
}


def scan(name: str, blob: bytes, public_assets: dict | None = None) -> list[dict]:
    path = PurePosixPath(name)
    issues = []
    if any(part in PRIVATE_PARTS for part in path.parts) or path.name in {'.env', 'config.local.json'}:
        issues.append({'file': name, 'rule': 'runtime-or-private-file'})
    if public_assets and name in public_assets:
        if public_assets[name] != APPROVED_PUBLIC_ASSETS.get(name) or hashlib.sha256(blob).hexdigest() != public_assets[name]:
            return issues + [{'file': name, 'rule': 'public-media-hash-mismatch'}]
        # Provenance tests additionally require byte-for-byte equality to the
        # pinned backend's pre-existing public bicycle sample, never local jobs.
        return issues
    if path.suffix not in TEXT_SUFFIXES and path.name not in {'LICENSE', '.gitignore', '.gitattributes'}:
        issues.append({'file': name, 'rule': 'unreviewed-file-type'})
    if len(blob) > 1024 * 1024:
        issues.append({'file': name, 'rule': 'large-file'})
    try:
        text = blob.decode('utf-8')
    except UnicodeDecodeError:
        return issues + [{'file': name, 'rule': 'binary-or-non-utf8'}]
    for rule, pattern in RULES.items():
        for match in pattern.finditer(text):
            if rule == 'email-address' and match.group().endswith('@users.noreply.github.com'):
                continue
            issues.append({'file': name, 'line': text.count('\n', 0, match.start()) + 1, 'rule': rule})
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--git', default='git', help='Git executable path')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    command = [args.git, '-c', f'safe.directory={root.as_posix()}', '-C', str(root)]
    def git(*arguments):
        return subprocess.check_output(command + list(arguments))
    public_assets = json.loads(git('show', ':docs/public-assets.json'))
    entries = git('ls-files', '--stage', '-z').decode('utf-8').split('\0')
    findings, count = [], 0
    for entry in filter(None, entries):
        metadata, name = entry.split('\t', 1)
        mode, oid, stage = metadata.split()
        count += 1
        if mode != '100644' or stage != '0':
            findings.append({'file':name, 'rule':'unreviewed-index-mode'})
        findings.extend(scan(name, git('cat-file', 'blob', oid), public_assets))
    if not count:
        findings.append({'rule':'empty-index'})
    print(json.dumps({'staged_files':count, 'findings':findings,
                      'status':'PASS' if not findings else 'FAIL'}, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
