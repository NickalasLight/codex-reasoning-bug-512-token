# Codex 5.5 Reasoning-Token Collapse Evidence

Public-safe aggregate evidence for a suspected Codex 5.5 reasoning collapse pattern where some turns terminate around exact 512-family reasoning-token counts.

This repository intentionally avoids raw transcript disclosure. The evidence below is anonymized to aggregate usage metadata: model, phase, call count, reasoning-token counts, and exact cluster counts. It excludes user prompts, assistant responses, tool arguments, local usernames, private paths, and raw transcript lines.

## Suspected Pattern

Observed cluster values:

- `516`
- `1034`
- `1552`

Original suspected trigger:

- The final `## Intermediary updates` section in Codex 5.5 model/base instructions.

Local mitigation attempted:

- Removed the whole final `## Intermediary updates` section from the local Codex 5.5 model-instructions override.
- Verified the section was absent from the active model-instructions file.
- Verified the section was absent from current session `session_meta.payload.base_instructions`.

Important distinction:

- The string may appear in later chat transcripts because it is discussed as evidence.
- The checks above are specifically about whether the section is present in active base instructions, not whether the phrase appears in conversation/tool logs.

## Historical Transcript Metadata Check

The historical check used the repo analyzer:

```powershell
python .\scripts\analyze_reasoning_tokens.py `
  --sessions "<local-codex-sessions-dir>" `
  --cutoff "2026-07-06T16:27:04+02:00" `
  --phase-basis session `
  --out-dir "<local-output-dir>"
```

Cutoff:

- Local: `2026-07-06T16:27:04+02:00`
- UTC: `2026-07-06T14:27:04Z`

Why `--phase-basis session`:

- Model/base instruction changes are session-scoped in practice.
- Already-running sessions may preserve earlier context, so event-time alone can misclassify old-context turns as post-update turns.

Scope:

- Files scanned: `187`
- Files with usage events: `185`
- Usage events: `9205`
- Cluster thresholds: `516`, `1034`, `1552`

### Historical Results

| Phase | Model | Calls | Mean Reasoning Tokens | Cluster Hits | Hit Rate | 516 Hits | 1034 Hits | 1552 Hits |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before | `gpt-5.5` | 4507 | 227.31 | 258 | 5.73% | 224 | 30 | 4 |
| after | `gpt-5.5` | 2352 | 225.48 | 116 | 4.93% | 100 | 13 | 3 |
| before | `gpt-5.4` | 178 | 310.37 | 3 | 1.69% | 3 | 0 | 0 |
| before | `gpt-5.4-mini` | 9 | 938.44 | 0 | 0.00% | 0 | 0 | 0 |
| before | `gpt-5.3-codex-spark` | 2070 | 208.39 | 0 | 0.00% | 0 | 0 | 0 |
| after | `gpt-5.3-codex-spark` | 89 | 386.99 | 0 | 0.00% | 0 | 0 | 0 |

### Historical Finding

The historical metadata does not show a meaningful increase in average `gpt-5.5` reasoning tokens after the instruction-section removal.

For `gpt-5.5`:

| Metric | Before | After |
|---|---:|---:|
| Calls | 4507 | 2352 |
| Mean reasoning tokens | 227.31 | 225.48 |
| Exact cluster hits | 258 | 116 |
| Cluster hit rate | 5.73% | 4.93% |

Interpretation:

- Average reasoning-token usage was essentially flat.
- Exact 512-family cluster hits persisted after the attempted mitigation.
- The cluster hit rate decreased slightly, but not enough to conclude the mitigation fixed the pattern.
- This is metadata evidence only; it does not prove whether individual answers were correct or incorrect.

### Today-Only Event-Time Slice

This narrower slice includes only usage events that occurred on local date `2026-07-06`. The before/after phase still uses session start relative to the same cutoff: `2026-07-06T16:27:04+02:00` local time (`2026-07-06T14:27:04Z` UTC).

| Phase | Model | Calls Today | Mean Reasoning Tokens | Exact Cluster Hits | Cluster Hit Rate | 516 | 1034 | 1552 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before cutoff | `gpt-5.5` | 136 | 299.32 | 27 | 19.85% | 23 | 4 | 0 |
| after cutoff | `gpt-5.5` | 2587 | 227.56 | 134 | 5.18% | 115 | 16 | 3 |
| before cutoff | `gpt-5.4` | 0 | n/a | 0 | n/a | 0 | 0 | 0 |
| after cutoff | `gpt-5.4` | 0 | n/a | 0 | n/a | 0 | 0 | 0 |
| before cutoff | `gpt-5.4-mini` | 0 | n/a | 0 | n/a | 0 | 0 | 0 |
| after cutoff | `gpt-5.4-mini` | 0 | n/a | 0 | n/a | 0 | 0 | 0 |
| before cutoff | `gpt-5.3-codex-spark` | 0 | n/a | 0 | n/a | 0 | 0 | 0 |
| after cutoff | `gpt-5.3-codex-spark` | 89 | 386.99 | 0 | 0.00% | 0 | 0 | 0 |

Today-only interpretation:

- `gpt-5.4` and `gpt-5.4-mini` had zero usage events in this local-date slice, so they do not provide before/after evidence for the instruction-section change.
- The observable today-only before/after comparison is effectively `gpt-5.5`, plus post-cutoff `gpt-5.3-codex-spark`.
- The attempted mitigation targeted `gpt-5.5`; this slice does not show evidence that `gpt-5.4` or `gpt-5.4-mini` were affected by the change.

## Fresh 5-Shot Benchmark Eval

Command shape:

```text
codex exec --json --skip-git-repo-check --ephemeral -s read-only --disable memories -m gpt-5.5 -c model_reasoning_effort=high
```

Expected final answer:

```text
21
```

Affected-state rule:

- Affected: any run gives a wrong final answer and lands on `516`, `1034`, or `1552` reasoning output tokens.
- Not affected: all runs either answer correctly or do not combine a wrong answer with one of those clustered reasoning counts.

### Screenshot Summary

Historical cutoff: before/after is based on session start relative to `2026-07-06T16:27:04+02:00` local time (`2026-07-06T14:27:04Z` UTC).

| Historical Phase | Model | Calls | Mean Reasoning Tokens | Exact Cluster Hits | Cluster Hit Rate | 516 | 1034 | 1552 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| before cutoff | `gpt-5.5` | 4507 | 227.31 | 258 | 5.73% | 224 | 30 | 4 |
| after cutoff | `gpt-5.5` | 2352 | 225.48 | 116 | 4.93% | 100 | 13 | 3 |

Historical interpretation: average `gpt-5.5` reasoning-token use was essentially flat after the update, and exact 512-family cluster hits persisted.

### Benchmark Results

| Run | Correct | Final Answer | Reasoning Output Tokens | Output Tokens | Cluster Hit |
|---:|---:|---|---:|---:|---:|
| 1 | yes | `21 candies` | 4660 | 4961 | no |
| 2 | yes | `21` | 5178 | 5522 | no |
| 3 | yes | `21` | 7550 | 7867 | no |
| 4 | yes | `21 candies` | 10169 | 10498 | no |
| 5 | yes | `21` | 8219 | 8539 | no |

Aggregate:

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 5 |
| Wrong runs | 0 |
| Cluster-hit runs | 0 |
| Mean reasoning output tokens | 7155.2 |
| Median reasoning output tokens | 7550 |
| Minimum reasoning output tokens | 4660 |
| Maximum reasoning output tokens | 10169 |

### Benchmark Finding

The fresh 5-shot benchmark did not reproduce the strict affected-state failure:

- All five runs answered correctly.
- None landed on exact cluster values `516`, `1034`, or `1552`.
- The benchmark produced much larger reasoning traces than ordinary historical agent turns.

This does not resolve the historical concern. It only shows that the specific benchmark prompt, in this run, did not fail under the strict affected-state rule.

## Overall Finding

Current evidence suggests:

1. The suspected instruction section is absent from active base instructions.
2. Historical `gpt-5.5` turns still show exact 512-family reasoning-token hits after the update.
3. Mean `gpt-5.5` reasoning-token usage did not materially change after the update.
4. The fresh 5-shot benchmark did not reproduce the strict failure mode.
5. The remaining concern is normal agent turns that terminate at exact 512-family counts, especially where a fuller reasoning pass may have been needed to succeed.

## Next Evidence Pass

The next planned pass is an anonymized review of a random sample of historical 512-family hits. The goal is to classify whether each sampled turn likely needed more reasoning to succeed.

Planned public-safe output:

- sampled row id, not transcript path;
- model and phase;
- reasoning-token cluster value;
- task category;
- outcome classification;
- whether more reasoning likely would have helped;
- short anonymized rationale with no raw user/assistant transcript text.
