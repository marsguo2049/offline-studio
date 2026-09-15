"""Run one translator command with all mutable paths scoped to one job."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path


def main() -> int:
    source, directory, action = sys.argv[1:4]
    root = Path(directory).resolve()
    spec = importlib.util.spec_from_file_location('studio_translator', source)
    if spec is None or spec.loader is None:
        raise RuntimeError('Translator module could not be loaded')
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    module.ROOT = root
    module.CONFIG_PATH = root / 'config.json'
    for name in ('INPUT', 'OUTPUT', 'PROGRESS', 'GLOSSARY', 'LOG'):
        setattr(module, f'{name}_DIR', root / ('logs' if name == 'LOG' else name.lower()))
    sys.argv = ['translate_docx.py', action, str(root / 'input' / 'document.docx')]
    return module.main()


if __name__ == '__main__':
    raise SystemExit(main())
