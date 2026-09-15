import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('privacy_check', Path(__file__).resolve().parents[1] / 'scripts/privacy_check.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_publication_gate_rejects_runtime_files_and_credentials():
    assert module.scan('data/settings.json', b'{}')
    assert module.scan('sample.docx', b'binary')
    assert module.scan('example.py', ('ghp_' + 'x' * 36).encode())
    assert module.scan('notes.md', ('C:' + '\\Users\\' + 'private\\document').encode())
    assert not module.scan('README.md', b'Offline Studio uses localhost.\n')
