# Contributing

Public pull requests are welcome. This repository is about evidence quality, privacy, and reproducibility, so contributions should be small, attributable, and public-safe.

## Evidence Rules

- Do not commit raw private transcripts, prompts, assistant responses, tool arguments, tool outputs, local usernames, private paths, cookies, API keys, credentials, customer/user data, or private repository details.
- Prefer aggregate metadata, anonymized tables, sanitized manifests, scripts, tests, or short reproducible notes.
- Include enough reproduction detail for review: platform, Codex version if known, model, reasoning effort, command shape, JSONL/event fields inspected, cutoff timestamps, phase basis, and sanitized output summaries.
- State whether evidence is contributor-reported, independently reproduced, or maintainer-verified.
- If you include qualitative judgments, state the rubric and limitations.

## Contribution Shape

- For small documentation or script fixes, edit the relevant file directly in a focused PR.
- For substantial external evidence, add a named folder under `evidence/external/<contributor>-<topic>-<date>/`.
- Add or update `CREDITS.md` with the contributor, GitHub handle, source PR/commit, artifact link, and review status.
- Keep the main README concise. Put detailed tables and long analysis in the evidence artifact, then link to it from the README.

## Verification

- Run relevant local tests when possible:

```powershell
python -m unittest discover -s tests
```

- If you cannot run tests or analyzers, state exactly what was not run and why in the PR body.
- Maintainers may restructure submitted evidence for privacy, readability, or attribution while preserving contributor credit.
