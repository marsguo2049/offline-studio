# Offline Studio v0.1

Historical bootstrap design. UI ownership and application boundaries were updated
in v0.2; see [repository-boundaries.md](repository-boundaries.md).

Approved direction: a unified local AI workbench backed by independent repositories.

The first release extends the existing ComfyUI UI through an adapter, keeping its
story, comic, batch and settings routes. A translation page runs the independent
Word translator in isolated subprocesses. A shared local settings file supplies
LM Studio and ComfyUI addresses. Tutorial and research links remain external,
explicitly labelled links. No weights, documents or generated media enter Git.

The workbench runs on 127.0.0.1:7870 to coexist with the legacy port 7860.
Existing applications and their data stay in place. New workbench jobs live in
ignored data/. Each translation has its own input, config, glossary, progress,
log and output directories. Existing translation progress is not imported.

Translation supports upload, inspect, terminology extraction/audit, translate,
resume and render/download. Only one translation command runs at a time; jobs
interrupted by a workbench restart can be resumed. GPU scheduling across tools
remains manual in v0.1. The translator's current prompts target academic art
history English-to-Chinese; this is stated in the UI.

Dependencies are pinned in integrations.lock.json. No source trees are copied
into this repository. The ComfyUI adapter depends on its pinned internal handler
and HTML markers; contract tests detect upstream incompatibility. Future work
can move shared UI ownership here after those interfaces become stable.

Validation: offline unit/integration tests, a synthetic DOCX through the real
translator inspect/render path, HTTP origin/path checks, desktop/mobile browser
inspection and Git publication checks. Real model inference is not required
for bootstrap validation and must not be claimed without being run.
