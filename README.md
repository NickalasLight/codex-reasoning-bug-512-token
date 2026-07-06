# Codex 5.5 Reasoning-Token Collapse Evidence

## Contributing Analysis or Repo Updates

Public pull requests are welcome. If you are not Nickalas Light and want to propose an update:

1. Fork this repository and create a focused branch in your fork.
2. Make the smallest reviewable change that captures your evidence, analysis, script fix, test, or documentation update.
3. Do not commit raw private transcripts, prompts, assistant responses, tool arguments, local usernames, private paths, cookies, API keys, or customer/user data.
4. Prefer public-safe aggregate evidence, anonymized tables, sanitized manifests, scripts, tests, or short reproducible notes.
5. Include enough reproduction detail in the PR body: platform, Codex version if known, model, reasoning effort, command shape, JSONL/event fields inspected, and sanitized output or artifact paths.
6. Run the relevant local tests or analyzer commands when possible. If you cannot run them, say exactly what was not run and why.
7. Open the PR against `NickalasLight/codex-reasoning-bug-512-token:main`.

You do not need direct write access to contribute. Maintainers will review public PRs before merging.

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

## Maximum Reasoning Intervention Cutoff

A later system-wide model-instructions intervention was added to test whether an explicit maximum-reasoning instruction changes future reasoning-token behavior.

Cutoff for later analysis:

- UTC: `2026-07-06T19:37:12Z`
- Local: `2026-07-06T21:37:12+02:00`

Current active override state at verification:

- Model: `gpt-5.5`
- Reasoning effort: `xhigh`
- Override hash: `a54e1fea62f2c930f96721063eb8971e203f17881331bfb9032e5724792a5b83`
- `Maximum Reasoning Intervention` section present: yes
- `Intermediary updates` section present: no

Public reference artifact:

- [`evidence/max-reasoning-intervention-20260706/manifest.json`](evidence/max-reasoning-intervention-20260706/manifest.json)

Future analysis task now in progress:

- Run normal Codex workflows for at least several hours after the cutoff before re-running transcript analysis.
- Treat `2026-07-06T19:37:12Z` as the primary cutoff for the maximum-reasoning intervention.
- Use `--phase-basis session` for the main before/after analysis because model-instructions changes are effectively session-scoped.
- Compare post-intervention `gpt-5.5` reasoning-token behavior against the pre-intervention baseline: mean, median, distribution, exact 512-family cluster hits, cluster-hit rate, and model/effort breakdowns.
- If clustered hits persist, run a follow-up qualitative audit on post-intervention hits using the existing blind-review packet and aggregation workflow.

Recommended later analyzer command:

```powershell
python .\scripts\analyze_reasoning_tokens.py `
  --sessions "<local-codex-sessions-dir>" `
  --cutoff "2026-07-06T19:37:12Z" `
  --phase-basis session `
  --out-dir "<local-output-dir>"
```

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

### Manual Ground-Truth Sample of 512-Family Hits

To test whether exact 512-family hits were merely harmless progress turns or cases where the agent likely should have reasoned deeper, a deterministic random sample was manually reviewed.

Sampling frame:

- Model: `gpt-5.5`
- Cluster values: `516`, `1034`, `1552`
- Phase basis: session start relative to `2026-07-06T16:27:04+02:00` local time (`2026-07-06T14:27:04Z` UTC)
- Population: `258` before-cutoff hits and `139` after-cutoff hits
- Sample rule: deterministic stratified random sample, `ceil(10%)` per phase
- Sample size: `26` before-cutoff hits and `14` after-cutoff hits
- Review basis: local transcript windows around each hit
- Public redaction: no raw transcript text, prompts, secrets, private paths, usernames, or tool outputs are included here

Methodology:

1. **Population construction.** Codex JSONL transcripts were scanned with `scripts/analyze_reasoning_tokens.py`. The analyzer emits usage metadata only and records one row per token-count event. Candidate rows were restricted to `model == gpt-5.5` and `reasoning_output_tokens in {516, 1034, 1552}`.
2. **Phase assignment.** Before/after labels were assigned from session start time, not event time. This is the appropriate basis for an instruction-context intervention because already-running sessions may preserve the pre-change prompt even if later events occur after the wall-clock cutoff.
3. **Stratification.** Sampling was stratified by phase so before and after cluster-hit populations were both represented. The before population had `258` eligible hits; the after population had `139` eligible hits.
4. **Randomization.** Within each phase, eligible rows were sorted into a stable order, then shuffled with deterministic seed `51220260706:<phase>`. The sample size was `ceil(10%)` of each phase population, yielding `26` before-cutoff samples and `14` after-cutoff samples.
5. **Review unit.** Each sampled row was reviewed as a local transcript window ending at the clustered token-count event. The reviewer considered nearby user intent, assistant response, tool calls, tool outputs, and whether the turn was substantive or merely a progress/status update.
6. **Classification.** Each review unit received one mutually exclusive judgment: `no`, `probably`, `yes`, or `unclear`. `yes + probably` is treated as the primary concern signal because both indicate cases where the clustered trace likely under-served the task.
7. **Category assignment.** Each reviewed row was assigned to a task category based on the nearby transcript window. Categories are intentionally coarse to avoid overfitting a small sample and to keep the public evidence anonymized.
8. **Redaction policy.** The public table reports aggregate counts and ratios only. It excludes raw transcript text, prompts, assistant answers, command outputs, secrets, local paths, usernames, repository-private details, and exact row identifiers.
9. **Limitations.** This is a single-reviewer qualitative audit of local transcript windows, not a blinded multi-rater study. It can identify plausible failure categories and before/after differences, but it cannot prove causal impact or correctness of every sampled turn.

Classification definitions:

- `yes`: the local evidence showed an avoidable mistake, failure, or unsafe/under-reasoned handling where deeper reasoning was likely needed.
- `probably`: the turn involved safety, compliance, destructive operations, or complex integration where deeper reasoning was likely warranted, even if no definitive error was visible in the local window.
- `no`: the hit was attached to a routine status/progress/update turn, or the nearby work appeared complete and adequately handled.
- `unclear`: the local window was insufficient for a defensible judgment.

#### Manual Review Results

| Phase | Population Hits | Sampled Hits | No | Probably | Yes | Unclear | Yes + Probably / Sample |
|---|---:|---:|---:|---:|---:|---:|---:|
| before cutoff | 258 | 26 | 20 | 4 | 2 | 0 | 6/26 (23.1%) |
| after cutoff | 139 | 14 | 10 | 3 | 0 | 1 | 3/14 (21.4%) |
| combined | 397 | 40 | 30 | 7 | 2 | 1 | 9/40 (22.5%) |

#### Manual Review By Category

| Category | Before Sampled | After Sampled | Total Sampled | No | Probably | Yes | Unclear | Yes + Probably / Category Sample | Share of All Sample |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Routine progress/status or completed work | 20 | 10 | 30 | 30 | 0 | 0 | 0 | 0/30 (0.0%) | 30/40 (75.0%) |
| Safety-critical or destructive operations | 1 | 3 | 4 | 0 | 4 | 0 | 0 | 4/4 (100.0%) | 4/40 (10.0%) |
| Security, compliance, or secret-sensitive work | 3 | 0 | 3 | 0 | 3 | 0 | 0 | 3/3 (100.0%) | 3/40 (7.5%) |
| Tooling/platform integration mistake or brittle orchestration | 2 | 0 | 2 | 0 | 0 | 2 | 0 | 2/2 (100.0%) | 2/40 (5.0%) |
| Complex progress turn with insufficient local evidence | 0 | 1 | 1 | 0 | 0 | 0 | 1 | 0/1 (0.0%) | 1/40 (2.5%) |
| **Total** | **26** | **14** | **40** | **30** | **7** | **2** | **1** | **9/40 (22.5%)** | **40/40 (100.0%)** |

Finding from ratio context:

- In raw sample terms, `9/40` reviewed cluster hits (`22.5%`) were classified as `yes` or `probably` needing deeper reasoning.
- Before and after are nearly the same in-context: `6/26` (`23.1%`) before vs `3/14` (`21.4%`) after.
- The category split shows why aggregate rates matter: most sampled cluster hits, `30/40` (`75.0%`), were routine progress/status or already-completed work, but the remaining suspicious categories had high within-category concern rates.
- The strongest evidence is not that every 512-family hit is bad; it is that the mitigation did not remove a persistent minority of clustered hits in high-risk or complex contexts.

#### Categories Where More Reasoning Was Likely Useful

| Category | Before | After | Total | Notes |
|---|---:|---:|---:|---|
| Safety-critical or destructive operations | 1 | 3 | 4 | OS install/partitioning, first-boot bootstrap, or live database deletion planning. These turns were not necessarily wrong, but the risk profile warranted deeper reasoning than a clustered trace suggests. |
| Security, compliance, or secret-sensitive work | 3 | 0 | 3 | Dating-platform/legal planning, non-API retrieval discussion, and secret-bearing API workflow. These needed stronger policy and data-handling reasoning. |
| Tooling/platform integration mistake or brittle orchestration | 2 | 0 | 2 | Cases where nearby evidence showed shell/platform mismatch or failed integration handling that deeper reasoning likely could have prevented or recovered from better. |
| Complex progress turn with insufficient local evidence | 0 | 1 | 1 | The local window was too thin to call it a failure, but the task was complex enough to remain suspicious. |
| Routine progress/status or completed work | 20 | 10 | 30 | Most sampled hits were not obvious failures; they often landed on progress updates, status reports, or already-completed work. |

Manual-review interpretation:

- The before/after sampled rates are very close: `23.1%` before vs `21.4%` after for `yes + probably`.
- The sample does not show a meaningful improvement in whether clustered turns needed deeper reasoning after the instruction-section removal.
- The after-cutoff sample had no definite `yes` cases, but the sample is small and task mix changed; this should not be read as proof of a fix.
- The most defensible signal is categorical: clustered traces are often harmless progress/status turns, but a non-trivial minority occur on turns where deeper reasoning was likely warranted.
- The attempted mitigation did not eliminate that minority pattern.

### Larger 30% Follow-Up Screen

After the manual 10% audit, a larger deterministic before/after screen was run to stress-test the category finding. This pass used the same transcript-window extraction approach and sampled `ceil(30%)` of clustered `gpt-5.5` hits per phase.

Important caveat:

- This larger pass is a rule-assisted sensitivity screen, not a replacement for the manual 10% ground-truth audit above.
- It is intentionally more conservative about high-risk context than the manual audit.
- Because additional local transcripts existed by the time this follow-up ran, the after-cutoff clustered-hit population had grown from `139` to `146`.

Follow-up sampling frame:

- Model: `gpt-5.5`
- Cluster values: `516`, `1034`, `1552`
- Phase basis: session start relative to `2026-07-06T16:27:04+02:00` local time (`2026-07-06T14:27:04Z` UTC)
- Population: `258` before-cutoff hits and `146` after-cutoff hits
- Sample rule: deterministic stratified random sample, `ceil(30%)` per phase
- Sample size: `78` before-cutoff hits and `44` after-cutoff hits

#### Larger Follow-Up Results

| Phase | Population Hits | Sampled Hits | No | Probably | Yes | Unclear | Yes + Probably / Sample |
|---|---:|---:|---:|---:|---:|---:|---:|
| before cutoff | 258 | 78 | 25 | 30 | 11 | 12 | 41/78 (52.6%) |
| after cutoff | 146 | 44 | 6 | 19 | 5 | 14 | 24/44 (54.5%) |
| combined | 404 | 122 | 31 | 49 | 16 | 26 | 65/122 (53.3%) |

#### Larger Follow-Up By Category

| Category | Before Sampled | After Sampled | Total Sampled | No | Probably | Yes | Unclear | Yes + Probably / Category Sample | Share of Follow-Up Sample |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Diagnostic/evidence collection | 14 | 18 | 32 | 0 | 0 | 6 | 26 | 6/32 (18.8%) | 32/122 (26.2%) |
| Safety-critical or destructive operations | 9 | 6 | 15 | 0 | 15 | 0 | 0 | 15/15 (100.0%) | 15/122 (12.3%) |
| Routine progress/status or completed work | 25 | 6 | 31 | 31 | 0 | 0 | 0 | 0/31 (0.0%) | 31/122 (25.4%) |
| Security, compliance, or secret-sensitive work | 21 | 13 | 34 | 0 | 34 | 0 | 0 | 34/34 (100.0%) | 34/122 (27.9%) |
| Tooling/platform integration mistake or brittle orchestration | 9 | 1 | 10 | 0 | 0 | 10 | 0 | 10/10 (100.0%) | 10/122 (8.2%) |
| **Total** | **78** | **44** | **122** | **31** | **49** | **16** | **26** | **65/122 (53.3%)** | **122/122 (100.0%)** |

#### Larger Follow-Up Category-Shift Check

The larger follow-up answers two different questions:

1. Did the share of concerning clustered hits change after the mitigation?
2. Did the category mix of clustered hits change after the mitigation?

The answer is different for each question. The concerning-hit share did not meaningfully change, but the category composition did shift.

Rough statistical checks:

- Concern-rate check: `yes + probably` before vs after is `41/78` (`52.6%`) vs `24/44` (`54.5%`), Fisher exact `p ~= 0.85`.
- Overall category-mix check: 2-by-5 chi-square over category counts gives `chi^2 ~= 12.52`, `df = 4`, `p ~= 0.014`.
- These p-values are rough screening checks, not a formal causal model. The larger pass is rule-assisted, categories are coarse, and the category tests are not independent of task mix.

| Category | Before Share | After Share | Change | Rough p-value | Finding |
|---|---:|---:|---:|---:|---|
| Diagnostic/evidence collection | 14/78 (17.9%) | 18/44 (40.9%) | +23.0 pp | `p ~= 0.009` | Strongest observed category increase; likely real in this sample, but still task-mix-sensitive. |
| Routine progress/status or completed work | 25/78 (32.1%) | 6/44 (13.6%) | -18.4 pp | `p ~= 0.030` | Moderate observed decrease; suggestive uncorrected, weaker after conservative multiple-comparison correction. |
| Tooling/platform integration mistake/brittle orchestration | 9/78 (11.5%) | 1/44 (2.3%) | -9.3 pp | `p ~= 0.093` | Directional decrease only; sample is too small for a firm finding. |
| Security, compliance, or secret-sensitive work | 21/78 (26.9%) | 13/44 (29.5%) | +2.6 pp | `p ~= 0.83` | No meaningful category-share change detected. |
| Safety-critical or destructive operations | 9/78 (11.5%) | 6/44 (13.6%) | +2.1 pp | `p ~= 0.78` | No meaningful category-share change detected. |

Sample-size interpretation:

- The larger sample is probably large enough to detect large composition shifts, especially the diagnostic/evidence increase.
- It is not large enough to make strong claims about smaller categories such as tooling/platform mistakes or safety-critical turns.
- It is large enough to rule out a large before/after improvement in the `yes + probably` concern rate for this sample, because that rate is nearly unchanged and the rough p-value is high.
- The category-shift signal should not be interpreted as increased reasoning in those categories. This screen is conditioned on already-clustered hits; it does not include the denominator of all turns by category.

Follow-up interpretation:

- The larger screen does not show a before/after improvement in concerning clustered hits: `41/78` (`52.6%`) before vs `24/44` (`54.5%`) after for `yes + probably`.
- The category composition changed more than the concern rate. Post-cutoff clustered hits were more often diagnostic/evidence turns and less often routine progress/status turns.
- The larger pass flags more cases than the manual 10% audit because it uses rule-assisted labels and treats high-risk context conservatively.
- The direction is consistent with the manual audit: the mitigation did not remove clustered hits from contexts where deeper reasoning appeared warranted.
- The blind multi-reviewer audit below is stronger evidence for category labels and did not replicate this category-shift signal. Treat this section as an exploratory rule-assisted screen.
- To test whether reasoning increased inside specific categories, a separate denominator pass would be needed: classify a sample of all turns by category, then compare mean/median reasoning tokens and cluster-hit rates per category before vs after.

### Blind Multi-Reviewer Audit

A simulated blind multi-reviewer audit was run on the same `122`-case larger sample. The goal was to reduce single-reviewer and rule-assisted-label bias.

Protocol:

- Three independent reviewer agents: `R1`, `R2`, `R3`.
- Reviewers were spawned without this conversation context and were instructed not to inspect other reviewer outputs, the repo README, prior aggregate results, or answer-key files.
- Reviewers received only a local rubric and a phase-blinded packet of anonymized case summaries.
- Reviewers did not see before/after phase, prior labels, aggregate statistics, or each other's votes.
- Public artifacts include aggregate counts and anonymized vote tables only. Raw transcript windows, reviewer rationales, prompts, tool outputs, local paths, usernames, and secrets are excluded.

Reusable audit tooling:

- [`scripts/make_blind_review_packet.py`](scripts/make_blind_review_packet.py): creates a local phase-blinded reviewer packet, private answer key, rubric, and packet manifest.
- [`scripts/aggregate_blind_review.py`](scripts/aggregate_blind_review.py): validates independent reviewer JSONL outputs and produces public-safe aggregate summaries, agreement metrics, and anonymized vote tables.

Public proof artifacts:

- [`evidence/blind-review-20260706/blind-review-summary.md`](evidence/blind-review-20260706/blind-review-summary.md)
- [`evidence/blind-review-20260706/blind-review-summary.json`](evidence/blind-review-20260706/blind-review-summary.json)
- [`evidence/blind-review-20260706/blind-review-case-votes.csv`](evidence/blind-review-20260706/blind-review-case-votes.csv)
- [`evidence/blind-review-20260706/blind-review-rubric.md`](evidence/blind-review-20260706/blind-review-rubric.md)
- [`evidence/blind-review-20260706/audit-manifest.json`](evidence/blind-review-20260706/audit-manifest.json)

#### Blind Audit Majority Concern Result

`Concern` means the reviewer verdict was `yes` or `probably`. The table below uses reviewer-majority labels per case.

| Phase | Sampled Hits | Majority Concern | Majority No Concern | No Majority | Majority Concern Rate |
|---|---:|---:|---:|---:|---:|
| before cutoff | 78 | 35 | 43 | 0 | 35/78 (44.9%) |
| after cutoff | 44 | 22 | 21 | 1 | 22/44 (50.0%) |

Rough before/after concern-rate check:

- Fisher exact `p ~= 0.570`.
- This does not show a meaningful before/after improvement.

#### Blind Audit Agreement

| Label Type | Pairwise Agreement | Fleiss Kappa |
|---|---:|---:|
| Concern | 0.811 | 0.626 |
| Verdict | 0.770 | 0.604 |
| Category | 0.694 | 0.606 |

Interpretation:

- Agreement is moderate to substantial for concern labels.
- The reviewer-majority concern rate is lower than the rule-assisted screen but still high: `57/122` (`46.7%`) of sampled clustered hits had a majority `yes` or `probably` concern label.
- Before/after remains flat or slightly worse after cutoff: `44.9%` before vs `50.0%` after.

#### Blind Audit Category Check

| Majority Category | Before | After |
|---|---:|---:|
| Diagnostic/evidence collection | 20 | 7 |
| Routine progress/status or completed work | 18 | 11 |
| Safety-critical or destructive operations | 5 | 2 |
| Security, compliance, or secret-sensitive work | 14 | 11 |
| Tooling/platform integration mistake or brittle orchestration | 17 | 11 |
| No category majority | 4 | 2 |

Rough category-mix check:

- 2-by-k chi-square over majority category counts, excluding no-majority category cases: `chi^2 ~= 2.22`, `df = 4`, `p ~= 0.695`.
- The blind audit does not support a meaningful category-composition shift.
- This weakens the earlier rule-assisted category-shift finding. The robust finding is not category movement; it is persistence of concerning clustered hits after the mitigation.

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

## Independent Local Reproduction And Hardened Override Check

An independent local Codex install was tested against the same candy benchmark and local transcript metadata. The results below are public-safe aggregates only: no prompts beyond the benchmark, raw transcript text, tool outputs, local paths, usernames, secrets, or private repository details are included.

### Affected-State Candy Benchmark

The clearest preserved affected-state benchmark batch was a 5-shot run where all five attempts failed and all five landed on the exact clustered value:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | no | `29` | 516 | yes |
| 2 | no | `28` | 516 | yes |
| 3 | no | `27` | 516 | yes |
| 4 | no | `28` | 516 | yes |
| 5 | no | `27` | 516 | yes |

Aggregate:

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 0 |
| Wrong runs | 5 |
| Exact 516 runs | 5 |
| 512-family cluster-hit runs | 5 |

### Basic Removal Retest

After removing the bad final update-status section from the local Codex 5.5 instructions, a later 5-shot benchmark batch was clean:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | yes | `21` | 4971 | no |
| 2 | yes | `21` | 6436 | no |
| 3 | yes | `21` | 4660 | no |
| 4 | yes | `21` | 6468 | no |
| 5 | yes | `21` | 5331 | no |

Aggregate:

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 5 |
| Wrong runs | 0 |
| Exact 516 runs | 0 |
| 512-family cluster-hit runs | 0 |

This matched the main workaround hypothesis: removing the whole bad final update-status section can stop the obvious candy-benchmark failure.

### Hardened Override Retest

On this install, cache-only removal was not durable. Codex later refreshed `models_cache.json` and restored the bad section during active use. The more durable local setup used both:

- `model_instructions_file`, pointing at patched Codex 5.5 instructions with the bad final update-status section removed.
- `model_catalog_json`, pointing at a patched startup catalog with the same Codex 5.5 fields patched.

The patched catalog was written as UTF-8 without BOM. `models_cache.json` was then treated as transient cache maintenance, not as the source of truth.

After that hardened setup, another 5-shot benchmark batch was also clean:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | yes | `21` | 7508 | no |
| 2 | yes | `21` | 5696 | no |
| 3 | yes | `21` | 4142 | no |
| 4 | yes | `21` | 4848 | no |
| 5 | yes | `21` | 3798 | no |

Aggregate:

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 5 |
| Wrong runs | 0 |
| Exact 516 runs | 0 |
| 512-family cluster-hit runs | 0 |
| Mean reasoning output tokens | 5198.4 |
| Median reasoning output tokens | 4848 |
| Minimum reasoning output tokens | 3798 |
| Maximum reasoning output tokens | 7508 |

### Local Log Metadata

The same analyzer approach was also run over the local Codex session logs on that install.

For `gpt-5.5` reasoning events:

| Metric | Value |
|---|---:|
| Reasoning events | 614068 |
| Exact 516 events | 23976 |
| Exact 516 rate | 3.9045% |
| 512-family events (`516`, `1034`, `1552`) | 26462 |
| 512-family rate | 4.3093% |
| Mean reasoning output tokens | 192.8529 |

Turn-level view:

| Metric | Value |
|---|---:|
| Turns with usage | 9485 |
| Turns with at least one exact 516 call | 6658 |
| Turns with at least one exact 516 call rate | 70.1950% |
| Turns whose final recorded model call ended at 516 | 2904 |
| Final-call exact 516 rate | 30.6168% |

### Historical 516 Task Replay

To check whether the fix changed only token counts or also observable task quality, 10 real historical tasks were selected from local logs. Each selected task had at least one historical `gpt-5.5` model call with `reasoning_output_tokens == 516`. The tasks were replayed once each after the hardened override setup, using read-only/ephemeral execution.

Selection and privacy rules:

- The sample used real local historical tasks, not synthetic prompts.
- Only public-safe aggregate metadata is reported here.
- Raw prompts, assistant responses, tool arguments, tool outputs, paths, usernames, secrets, and private repository details are excluded.
- Quality was judged from observable final answers only; hidden reasoning traces were not available.

Aggregate replay results:

| Metric | Value |
|---|---:|
| Historical selected tasks | 10 |
| Historical model calls inside selected tasks | 129 |
| Historical exact 516 hits inside selected tasks | 14 |
| Historical 512-family hits inside selected tasks | 15 |
| New replay tasks with exact 516 | 0/10 |
| New replay tasks with 512-family hit | 0/10 |
| New replay mean reasoning output tokens | 2661.8 |
| New replay median reasoning output tokens | 2845 |
| New replay minimum reasoning output tokens | 846 |
| New replay maximum reasoning output tokens | 4004 |

Observable quality review:

| Verdict | Count |
|---|---:|
| New answer better | 9 |
| New answer similar | 1 |
| New answer worse | 0 |

The quality improvement was not only higher token usage. The replayed answers were usually more direct, more source-grounded, better at ranking root causes, and clearer about proof limits. The strongest practical finding from this install is that the basic removal can fix the benchmark, but durability matters: if Codex refreshes the model cache and restores the bad section, the affected behavior can return unless the patched instructions/catalog are used as the startup source of truth.

Limitations:

- This is one local install and one local transcript corpus.
- The historical task replay was not an exact time-machine replay; current filesystem state may differ from the original task state.
- Replayed tasks were wrapped in a read-only audit guard.
- Hidden reasoning traces were unavailable, so task-quality comparison used final answers and recorded token metadata only.

## Overall Finding

Current evidence suggests:

1. The suspected instruction section is absent from active base instructions.
2. Historical `gpt-5.5` turns still show exact 512-family reasoning-token hits after the update.
3. Mean `gpt-5.5` reasoning-token usage did not materially change after the update.
4. The fresh 5-shot benchmark did not reproduce the strict failure mode.
5. Manual, rule-assisted, and blind multi-reviewer audits all fail to show a meaningful before/after improvement in concerning clustered hits.
6. The blind multi-reviewer audit does not replicate the earlier rule-assisted category-shift signal.
7. The remaining concern is normal agent turns that terminate at exact 512-family counts, especially where a fuller reasoning pass may have been needed to succeed.

## Further Evidence Work

Useful follow-up work would be a denominator pass over all sampled turns, not only clustered hits. That would classify a phase-balanced sample of all turns by category, then compare mean/median reasoning tokens and cluster-hit rates per category before vs after.

Planned public-safe output:

- sampled row id, not transcript path;
- model and phase;
- reasoning-token cluster value;
- task category;
- outcome classification;
- whether more reasoning likely would have helped;
- no raw user/assistant transcript text.
