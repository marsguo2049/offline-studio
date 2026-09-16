# Offline Studio

**A unified local AI workbench for documents, images, comics and video.**

[简体中文](README.zh-CN.md) · [Architecture](docs/repository-boundaries.md) · [UI preview](https://marsguo2049.github.io/offline-studio/#batch)

Offline Studio brings independent local applications into one browser interface:
batch image editing, story-to-comic, story-to-video and resumable Word translation.
The workbench owns navigation, shared service settings and the translation UI;
specialist repositories continue to own their execution engines.

## Start on Windows

Install Python 3.10+ and run `install.bat` while online. The installer downloads
the exact integration revisions in `integrations.lock.json` and installs Python
dependencies in `.venv`. Download models and configure LM Studio / ComfyUI separately.

Then double-click **`start-studio.bat`**, opening **http://127.0.0.1:7870/#batch**.
It can run alongside ComfyUI Workbench on port `7860`. Reopening the launcher
opens the existing studio instead of starting another server against its data.
Startup itself does not download models or contact cloud inference services.
Tutorial/research links open GitHub only when clicked.

If the existing repositories are already sibling directories:

```powershell
python scripts/install.py --local
```

Local mode uses those checkouts as-is; it does not enforce their pinned revisions.
On macOS/Linux, run `python3 scripts/install.py`, then `.venv/bin/offline-studio`
from the repository root. Windows is the primary locally validated platform.
Use `--minimal` during installation to omit optional PDF/OCR dependencies.
PyAV remains required because the creative backend imports its video module at startup.

## Tools

| Tool | Backend | Requirements |
| --- | --- | --- |
| Batch image editing | comfyui-py-workflow | ComfyUI + workflow models |
| Story comics / video | comfyui-py-workflow | LM Studio for planning; ComfyUI for generation |
| Word translation | local-llm-word-translator | LM Studio + a loaded local text model |

In **Service settings**, select your local model and save the settings. Translation
and creative tools share these settings. Upload a DOCX on the Translation page,
inspect it, optionally extract/audit terminology, translate, then export the
Chinese and bilingual Word documents. Translate again to resume saved progress.
Each job has its own glossary. The current translator's prompts target academic
art history English-to-Chinese; other domains need terminology review.

One translation command runs at a time. GPU scheduling across translation and
image/video generation is manual in v0.1; finish one workload before starting
another on memory-constrained GPUs. Closing the browser does not stop the server.
Stopping the server interrupts translation; saved progress can be resumed.

## Repository ecosystem

| Repository | Responsibility |
| --- | --- |
| **offline-studio** | Unified local workbench and application adapters |
| [comfyui-py-workflow](https://github.com/marsguo2049/comfyui-py-workflow) | ComfyUI execution, templates, image/video chains |
| [local-llm-word-translator](https://github.com/marsguo2049/local-llm-word-translator) | Translation, terminology and Word rendering |
| [multi-model-workflow-optimization](https://github.com/marsguo2049/multi-model-workflow-optimization) | Model selection, evaluation and workflow optimization research |
| [my-llm](https://github.com/marsguo2049/my-llm) | Deployment tutorials and learning notes |

## Separate local apps and previews

| Application | Local URL | Public preview | Scope |
| --- | --- | --- | --- |
| ComfyUI Workbench | http://127.0.0.1:7860/#batch | [ComfyUI preview](https://marsguo2049.github.io/comfyui-py-workflow/#batch) | Story video/comic, batch images/videos and their service settings |
| Offline Studio | http://127.0.0.1:7870/#batch | [Full workbench preview](https://marsguo2049.github.io/offline-studio/#batch) | ComfyUI tools, story/comic workflows, translation and LM Studio |

Offline Studio owns its creative HTML, scripts and aggregate HTTP layer. The batch
fragment, batch controller and batch JavaScript come from the pinned ComfyUI backend.
Both applications offer batch first/last-frame video: separate first/last image
sets, single-frame reuse, natural-order or basename pairing, duration, aspect ratio,
resolution, seed, progress and video downloads. This tool needs only ComfyUI.

Each preview is built from its own local app and contains no live API calls.
The full preview also has a [translation page](https://marsguo2049.github.io/offline-studio/translate.html).
All demonstration text is fictional; the bicycle media are the backend's existing
public examples, copied by explicit filename and verified byte-for-byte.
Run `python scripts/build_ui_preview.py` after installing the pinned integrations;
CI uses `--check`. `--comfy-root` supports a local development checkout.

After updating this repository, rerun `install.bat` and restart the local service.
Updated ComfyUI revisions install into separate versioned integration directories;
previous installations and user data are preserved.

## Local data

`data/` contains new creative jobs, translation inputs, outputs, progress, logs and
shared settings. It is ignored by Git, together with model environments and
downloaded integrations. Existing applications and their histories stay in place;
no existing private files are imported or published.

```powershell
.venv\Scripts\python.exe -m offline_studio.server --port 7870 --no-browser
.venv\Scripts\python.exe -m pytest -q
```

The server binds only to loopback. `--data-dir` selects a different data directory;
`--translator` selects a local `translate_docx.py`. The adapter relies on the pinned
ComfyUI batch fragment/API contract; update its pin only after the contract tests pass.
Tests use synthetic documents and no model inference.

## License

Original work is under the **PolyForm Noncommercial License 1.0.0**, matching the
creative backend's licensing direction. See [LICENSE](LICENSE) and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Third-party tools and models retain
their own licenses. This is an independent project, not affiliated with Comfy Org.
