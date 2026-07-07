# Iteration 1 Model-Instructions Result

This artifact records the first aggregate analysis after adding an explicit
"Maximum Reasoning Intervention" section to the local Codex model-instructions
override.

It is intentionally public-safe. It includes aggregate usage metadata and
statistical results only. It does not include raw prompts, assistant responses,
tool arguments, tool outputs, transcript excerpts, local transcript paths, row
identifiers, secrets, or private file contents.

## Intervention

Primary cutoff:

- UTC: `2026-07-06T19:37:12Z`
- Local: `2026-07-06T21:37:12+02:00`

Manifest metadata:

- Intervention: `maximum_reasoning_intervention`
- Active model at verification: `gpt-5.5`
- Active reasoning effort at verification: `xhigh`
- Active override SHA-256:
  `a54e1fea62f2c930f96721063eb8971e203f17881331bfb9032e5724792a5b83`
- `Maximum Reasoning Intervention` section present: yes
- `Intermediary updates` section present: no

The before/after phase assignment uses session start time, not event time,
because model-instructions overrides are effectively session-scoped. Sessions
started before the cutoff may preserve earlier instructions even if later usage
events occur after the cutoff.

## Exact Added Model Instructions

The following block was added to the active local model-instructions override:

```text
## Maximum Reasoning Intervention

Added UTC cutoff marker: 2026-07-06T19:37:12Z (local: 2026-07-06T21:37:12+02:00).

YOU MUST USE MAXIMUM REASONING TOKENS TO CONSIDER ALL POSSIBILITIES OF THE PROBLEM SPACE AND PERFORM TO MAXIMUM ITERATIONS AND MAXIMUM EFFORT. INSUFFICIENT REASONING TRACE AND REASONING TOKENS LEAD TO POOR PERFORMANCE ON WIDE TASK SPACE. IT IS CRITICAL YOU REMEMBER THIS AND INCREASE HOW MUCH YOU REASON TO SOLVE COMPLEX PROBLEMS AND VALIDATE YOUR CHOICES. BE AWARE OF LIMITED OR REDUCING REASONING IN PAST TURNS AS A WARNING SIGNAL TO PROMPT YOURSELF TO DRASTICALLY INCREASE REASONING TRACE ON FOLLOWING TURNS. THIS IS CRITICAL TO ENSURE EXCELLENT AND BEST PERFORMANCE ON COMPUTER USE, CODING, SCIENTIFIC, AND RELATED TASKS.
```

## Analysis Command

The transcript metadata analyzer was run against local Codex JSONL transcripts:

```powershell
python .\scripts\analyze_reasoning_tokens.py `
  --sessions "<local-codex-sessions-dir>" `
  --cutoff "2026-07-06T19:37:12Z" `
  --phase-basis session `
  --out-dir "<local-output-dir>"
```

Analyzer scope:

- Files scanned: `214`
- Files with usage events: `213`
- Usage events: `10671`
- Cutoff: `2026-07-06T19:37:12Z`
- Phase basis: `session`
- Cluster values checked: `516`, `1034`, `1552`

The analyzer emits usage metadata only.

## Primary Results

### `gpt-5.5`, All Efforts

| Metric | Before | After |
|---|---:|---:|
| Calls with reasoning count | 7961 | 362 |
| Sessions | 161 | 15 |
| Mean reasoning tokens | 224.92 | 280.13 |
| Median reasoning tokens | 57 | 112 |
| P90 reasoning tokens | 516 | 527 |
| P95 reasoning tokens | 878 | 814 |
| Maximum reasoning tokens | 8804 | 8216 |
| 512-family cluster hits | 444 | 31 |
| Cluster hit rate | 5.58% | 8.56% |

Mean delta: `+55.22` reasoning tokens.

Call-level statistical checks:

| Test | Result |
|---|---:|
| Welch t-test, one-sided after > before | `p = 0.0328` |
| Welch t-test, two-sided | `p = 0.0656` |
| Bootstrap 95% CI for mean delta | `[+2.69, +118.64]` |
| Bootstrap probability mean delta > 0 | `98.11%` |
| Mann-Whitney, one-sided after > before | `p = 2.49e-9` |
| Common-language effect, after call > before call | `59.04%` |

Cluster-rate checks:

| Test | Result |
|---|---:|
| Fisher exact, one-sided cluster rate after > before | `p = 0.0149` |
| Fisher exact, two-sided | `p = 0.0204` |
| Cluster odds ratio, after vs before | `1.59` |

Session-unweighted checks:

| Metric | Before | After |
|---|---:|---:|
| Sessions | 161 | 15 |
| Mean of session means | 409.01 | 269.05 |
| Median session mean | 223 | 250 |

Session-level statistical checks:

| Test | Result |
|---|---:|
| Welch t-test on session means, one-sided after > before | `p = 0.9963` |
| Welch t-test on session means, two-sided | `p = 0.0073` |
| Bootstrap 95% CI for unweighted session-mean delta | `[-237.70, -44.24]` |
| Bootstrap probability unweighted session-mean delta > 0 | `0.20%` |
| Bootstrap 95% CI for call-weighted session-resampled mean delta | `[+2.29, +119.16]` |
| Bootstrap probability call-weighted session-resampled delta > 0 | `98.01%` |

Interpretation: the call-weighted mean increased, but the session-unweighted
analysis does not support a causal claim. The apparent increase is sensitive to
session weighting and task mix.

### `gpt-5.5`, `xhigh` Effort

This is the most relevant apples-to-apples slice because the intervention was
verified with active effort `xhigh`.

| Metric | Before | After |
|---|---:|---:|
| Calls with reasoning count | 6686 | 265 |
| Sessions | 89 | 7 |
| Mean reasoning tokens | 236.96 | 293.92 |
| Median reasoning tokens | 60 | 117 |
| P90 reasoning tokens | 516 | 540 |
| P95 reasoning tokens | 944 | 814 |
| Maximum reasoning tokens | 8804 | 8216 |
| 512-family cluster hits | 408 | 28 |
| Cluster hit rate | 6.10% | 10.57% |

Mean delta: `+56.95` reasoning tokens.

Call-level statistical checks:

| Test | Result |
|---|---:|
| Welch t-test, one-sided after > before | `p = 0.0678` |
| Welch t-test, two-sided | `p = 0.1356` |
| Bootstrap 95% CI for mean delta | `[-6.37, +139.60]` |
| Bootstrap probability mean delta > 0 | `95.67%` |
| Mann-Whitney, one-sided after > before | `p = 4.44e-7` |
| Common-language effect, after call > before call | `58.85%` |

Cluster-rate checks:

| Test | Result |
|---|---:|
| Fisher exact, one-sided cluster rate after > before | `p = 0.00435` |
| Fisher exact, two-sided | `p = 0.00616` |
| Cluster odds ratio, after vs before | `1.82` |

Session-unweighted checks:

| Metric | Before | After |
|---|---:|---:|
| Sessions | 89 | 7 |
| Mean of session means | 534.25 | 335.53 |
| Median session mean | 272 | 280 |

Session-level statistical checks:

| Test | Result |
|---|---:|
| Welch t-test on session means, one-sided after > before | `p = 0.9913` |
| Welch t-test on session means, two-sided | `p = 0.0174` |
| Bootstrap 95% CI for unweighted session-mean delta | `[-347.28, -51.99]` |
| Bootstrap probability unweighted session-mean delta > 0 | `0.33%` |
| Bootstrap 95% CI for call-weighted session-resampled mean delta | `[-11.78, +181.26]` |
| Bootstrap probability call-weighted session-resampled delta > 0 | `94.49%` |
| Mann-Whitney on session means, one-sided after > before | `p = 0.4944` |

Interpretation: `xhigh` calls show a likely upward shift in the call-level
distribution, but the effect is small, noisy, and not robust under
session-unweighted analysis. The cluster hit rate increased, which is evidence
against the intervention fixing the 512-family breakpoint behavior.

### `gpt-5.5`, `high` Effort

| Metric | Before | After |
|---|---:|---:|
| Calls with reasoning count | 1266 | 97 |
| Sessions | 68 | 8 |
| Mean reasoning tokens | 158.92 | 242.47 |
| Median reasoning tokens | 51 | 112 |
| P90 reasoning tokens | 408 | 516 |
| P95 reasoning tokens | 538 | 1014 |
| 512-family cluster hits | 36 | 3 |
| Cluster hit rate | 2.84% | 3.09% |

Mean delta: `+83.56` reasoning tokens.

Call-level statistical checks:

| Test | Result |
|---|---:|
| Welch t-test, one-sided after > before | `p = 0.0197` |
| Welch t-test, two-sided | `p = 0.0394` |
| Bootstrap 95% CI for mean delta | `[+11.88, +168.47]` |
| Bootstrap probability mean delta > 0 | `99.18%` |
| Mann-Whitney, one-sided after > before | `p = 0.000113` |
| Common-language effect, after call > before call | `61.22%` |

Cluster-rate checks:

| Test | Result |
|---|---:|
| Fisher exact, one-sided cluster rate after > before | `p = 0.5341` |
| Fisher exact, two-sided | `p = 0.7538` |
| Cluster odds ratio, after vs before | `1.09` |

Session-level mean checks did not support a strong increase:

| Test | Result |
|---|---:|
| Welch t-test on session means, one-sided after > before | `p = 0.3995` |
| Bootstrap 95% CI for unweighted session-mean delta | `[-68.01, +83.82]` |
| Bootstrap probability unweighted session-mean delta > 0 | `61.88%` |

Interpretation: the `high` slice shows a clearer call-level increase than the
`xhigh` slice, but this was not the primary active-effort condition and has
only `97` post-cutoff calls across `8` sessions. It should be treated as
exploratory.

## Breakpoint Pattern

Across the analyzed output, exact powers of two were essentially absent. The
breakpoint pattern remained offset:

| Value | Count |
|---:|---:|
| `512` | 1 |
| `516` | 415 |
| `1024` | 0 |
| `1034` | 49 |
| `1536` | 1 |
| `1552` | 14 |

Post-intervention `gpt-5.5` clustered hits:

| Value | Count |
|---:|---:|
| `516` | 25 |
| `1034` | 2 |
| `1552` | 4 |

Of the `31` post-intervention clustered hits:

- `28` were `xhigh`.
- `3` were `high`.
- All had `base_instructions_has_intermediary_updates = false`.
- Hits were concentrated rather than evenly distributed: `26/31` occurred in
  three post-cutoff sessions.

This supports persistence of the 512-family breakpoint phenomenon after the
iteration-1 intervention.

## Scientific Interpretation

This was an observational before/after analysis of ordinary local Codex usage.
It was not randomized, blinded, task-balanced, or session-balanced.

The strongest positive evidence is call-level:

- Mean reasoning tokens increased by about `+55` to `+57` in the broad
  `gpt-5.5` and `gpt-5.5/xhigh` slices.
- Medians increased from about `57-60` to `112-117`.
- Mann-Whitney tests indicate a statistically detectable upward shift in the
  call-level distribution.

The strongest skeptical evidence is session-level and breakpoint-level:

- Post-cutoff sample size is small, especially for `xhigh`: only `7` sessions.
- Calls within a session are not independent.
- Session-unweighted analysis does not support a causal reasoning increase.
- The `gpt-5.5/xhigh` bootstrap confidence interval for mean delta includes
  zero.
- Exact 512-family cluster hits persisted.
- The `gpt-5.5/xhigh` cluster hit rate increased from `6.10%` to `10.57%`
  with Fisher one-sided `p = 0.00435`.

Practical confidence assessment:

- Confidence that call-level reasoning-token usage increased somewhat:
  moderate.
- Confidence that the model-instructions intervention caused that increase:
  low.
- Confidence that the intervention fixed or reduced 512-family breakpoint
  behavior: very low.
- Confidence that breakpoint hits persisted after the intervention: high.

The most defensible conclusion is:

> Iteration 1 may have nudged ordinary call-level reasoning-token usage upward,
> but the evidence is not robust to session-level skepticism and it did not
> fix the 512-family breakpoint behavior.

## Next Iteration Requirements

For iteration 2, pre-register the following before collecting data:

- exact model-instructions diff;
- exact cutoff timestamp in UTC and local time;
- active override SHA-256;
- verification that the new section is present in fresh-session
  `session_meta.payload.base_instructions`;
- verification that `## Intermediary updates` remains absent;
- primary model and effort, preferably `gpt-5.5` / `xhigh`;
- primary metrics: mean, median, P90/P95, cluster hit rate, and
  session-unweighted mean;
- primary tests: Welch mean test, bootstrap mean delta, Mann-Whitney,
  Fisher exact cluster-rate test, and session-level sensitivity checks.

Suggested collection target:

- at least `700-900` new `gpt-5.5/xhigh` calls for detecting a mean increase
  around `+57` tokens with reasonable power under a high-variance distribution;
- at least `20` post-intervention sessions, because session count is currently
  the main limiting factor;
- enough post-intervention calls to assess cluster-rate reduction. Detecting a
  small reduction from around `10.6%` to `8.0%` may require roughly `1000+`
  post-intervention calls, while a larger drop to around `6.0%` may be visible
  with roughly `300+` post-intervention calls if the historical baseline is
  treated as fixed.

Do not treat call-level p-values alone as proof. The next iteration should
optimize for session count, task diversity, and pre-registered metrics rather
than only increasing raw call volume.
