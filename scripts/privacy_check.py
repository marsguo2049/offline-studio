"""Inspect the exact Git index without printing matched sensitive values.

This is a focused publication gate, not a guarantee that arbitrary prose is safe.
Manually review new prose and files as well. Run after git add and before commit.
"""
from __future__ import annotations

import argparse
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
TEXT_SUFFIXES = {'.py', '.js', '.css', '.html', '.md', '.json', '.toml', '.yml', '.yaml', '.bat', '.txt'}


def scan(name: str, blob: bytes) -> list[dict]:
    path = PurePosixPath(name)
    issues = []
    if any(part in PRIVATE_PARTS for part in path.parts) or path.name in {'.env', 'config.local.json'}:
        issues.append({'file': name, 'rule': 'runtime-or-private-file'})
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
    entries = git('ls-files', '--stage', '-z').decode('utf-8').split('\0')
    findings, count = [], 0
    for entry in filter(None, entries):
        metadata, name = entry.split('\t', 1)
        mode, oid, stage = metadata.split()
        count += 1
        if mode != '100644' or stage != '0':
            findings.append({'file':name, 'rule':'unreviewed-index-mode'})
        findings.extend(scan(name, git('cat-file', 'blob', oid)))
    if not count:
        findings.append({'rule':'empty-index'})
    print(json.dumps({'staged_files':count, 'findings':findings,
                      'status':'PASS' if not findings else 'FAIL'}, ensure_ascii=False, indent=2))
    return 1 if findings else 0


if __name__ == '__main__':
    raise SystemExit(main())
