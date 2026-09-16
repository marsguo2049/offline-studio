# Repository boundaries and separate applications

- comfyui-py-workflow owns ComfyUI execution, workflows, story videos, story
  comics, batch image editing and batch first/last-frame videos. Its Workbench
  on port 7860 includes the LM Studio settings needed for story planning.
- offline-studio on port 7870 aggregates those creative workflows with document
  translation, shared settings and learning/research links.
- Both repositories maintain their own local application shell and public UI
  preview. Offline Studio pins the reusable ComfyUI backend to an exact commit.
- ComfyUI's original story and comic history remains in outputs/offline-studio;
  its newer batch jobs use outputs/comfyui-workbench/batch-jobs. Offline Studio
  keeps its own data/ tree. No user data is moved or deleted.
- Public previews disable uploads and model requests, use synthetic examples
  and pre-existing public samples, and enforce connect-src 'none'.

Story and comic are first-class ComfyUI workflows. Their use of LM Studio for
planning does not exclude them from the ComfyUI repository. Translation and
general research/learning navigation belong to the aggregate application.

Before each publication, run tests and both preview checks, review the exact
staged content for sensitive/private data, then synchronize GitHub and verify
CI, Pages and local application entry points.
