# Repository boundaries and separate applications

The user requested separate ComfyUI-only and aggregate applications, both locally
and on GitHub, while publishing the new batch first/last-frame video capability.

## Ownership

- comfyui-py-workflow owns the ComfyUI execution library, workflow templates,
  batch controller and reusable batch UI. Its standalone app is ComfyUI Workbench
  on port 7860: batch images, first/last-frame videos and ComfyUI settings only.
- offline-studio owns the aggregate creative UI and HTTP orchestration, document
  translation, LM Studio settings and learning/research links. Its app uses 7870.
- Existing ComfyUI-related story planning/execution Python APIs stay compatible;
  the aggregate story/comic user interface belongs to offline-studio. This avoids
  breaking existing CLI workflows during the UI ownership transition.
- The apps use independent data roots. No existing user data is moved or deleted.

## Public previews

Each repository builds its own docs/ preview from its own local HTML. The ComfyUI
preview shows no LM Studio or translation controls. Offline Studio includes all
creative tools and a translation preview. All previews prohibit network API calls
with CSP, disable real actions and use only explicit public synthetic examples.
Batch image/video selection remains interactive without backend requests.

## Implementation and validation

1. Preserve the user's pending batch video changes and the current creative UI.
2. Implement the ComfyUI-only handler, page, preview and boundary tests.
3. Give Offline Studio its own creative page/handler; reuse the new batch module.
4. Build separate previews, document entry points and retain old data in place.
5. Test UI/API isolation, pairing preview and both builds; review code and scan
   staged publication content for private data before either GitHub push.
6. Publish ComfyUI first, pin that exact commit in Offline Studio, update the local
   installed backend, then publish and verify both Pages sites and CI runs.

Ruling: directly related ComfyUI workflow helper APIs remain backward compatible;
only the standalone UI and public product identity are narrowed. Unrelated apps
and aggregate HTTP/UI ownership belong exclusively to Offline Studio.
