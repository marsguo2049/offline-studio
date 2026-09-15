# Offline Studio implementation plan

Goal: ship a runnable workbench and synchronize a clean public GitHub repository.
Architecture: compose the pinned ComfyUI server with a translation adapter;
independent subprocesses isolate the translator's module-level filesystem state.
Stack: Python 3.10+, standard-library HTTP server, vanilla HTML/CSS/JS.
Spec: design.md.

- [x] Add contract tests for loopback settings, path isolation, restart recovery,
  translation subprocess results, shared UI navigation and HTTP origin checks.
- [x] Implement config.py (load/save/validate settings), translation.py (job
  persistence and subprocess lifecycle), worker.py (load translator and redirect
  its directories), server.py (compose handlers), web/ (translation/settings bridge).
- [x] Run `python -m pytest -q`; exercise a synthetic DOCX without calling a model.
- [x] Add installation scripts, pinned integration manifest, bilingual README,
  ecosystem architecture, ignored runtime directories and GitHub Actions tests.
- [x] Inspect the live UI at desktop/mobile widths and fix observed problems.
- [x] Review code, run final checks, and prepare the clean GitHub publication.

Public artifacts are restricted to code, documentation, configuration examples,
tests and synthetic fixtures. Existing sibling repositories are read-only inputs.
