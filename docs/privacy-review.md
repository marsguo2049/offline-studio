# Publication privacy review

Date: 2026-09-16

Initial review result: the staged source/documentation set passed the scanner
with no findings. The file list and prose were also reviewed; runtime exclusions
were verified with Git. The final scan is repeated immediately before commit.

The initial publication is restricted to original application code, installation
scripts, tests, documentation, license notices and public integration revisions.

Before publication:

- Inspect the exact Git index with `scripts/privacy_check.py` after staging.
- Review source and prose manually for private material beyond pattern matches.
- Confirm `data/`, `.venv/`, downloaded `integrations/`, caches and package
  metadata are excluded from the index.
- Use a GitHub noreply commit email; do not publish a private email address.
- Re-run the scan after any changes to the staged content.

The scanner checks known credential patterns, private keys, secret assignments,
personal filesystem paths, email addresses, runtime directory names, unexpected
file types and large files. It reports locations and rule names without printing
the matching values. Pattern matching is not a guarantee that all sensitive prose
can be recognized; manual review remains part of the publication process.

All document tests use generated synthetic content. Browser test documents,
settings and logs stay in ignored local data. No user documents, private prompts,
model weights, private generated media or screenshots are included in this release.
The v0.2 preview adds only the ComfyUI repository's pre-existing public bicycle
sample media, verified against independently reviewed fixed SHA-256 values from
the already-published source, the pinned backend and the public-assets manifest.
Public GitHub repository names and commit hashes are intentional references.

Future releases should repeat the same review before pushing. GitHub Actions
also scans the checked-out index as a regression check; that post-push check does
not replace the pre-publication local review.
