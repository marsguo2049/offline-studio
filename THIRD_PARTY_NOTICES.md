# Third-party components

- `comfyui-py-workflow`, copyright 2026 Mars Guo, is installed separately and
  retains its PolyForm Noncommercial 1.0.0 license and third-party notices.
  Offline Studio reuses its UI assets at runtime and extends its HTTP handler.
  The aggregate creative UI and handler were migrated from that project to this
  repository. The batch fragment and batch scripts remain maintained there.
  Adapted Comfy Org workflow templates in that project retain their MIT notices.
- `local-llm-word-translator` is installed separately from the pinned repository
  and retains its own LICENSE. This repository does not vendor its source.
- Python packages, ComfyUI, LM Studio, models and custom nodes remain subject to
  their respective terms. No model weights are distributed here.

The installer preserves each downloaded integration's license and notices.

The static preview copies only the backend's already-public bicycle sample media.
`docs/public-assets.json` records their hashes; tests compare them directly to the
pinned integration's public examples. No private runtime media are preview inputs.
