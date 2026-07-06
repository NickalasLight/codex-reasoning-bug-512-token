---
name: codex-reasoning-bug-512-token
description: Self-contained diagnostic and workaround guidance for the Codex 5.5 reasoning-collapse bug where reasoning becomes shallow or quantized around 512 reasoning output tokens, often observed as reasoning_output_tokens near 516. Use when Codex 5.5 reasoning quality degrades, reasoning appears capped/quantized, a user wants to run the 5-shot local Codex eval, or a user mentions the final "Intermediary updates" model-instruction section. No external artifact or project repository dependency is required.
---

# Codex Reasoning Bug 512 Token

## Bug

Codex 5.5 can enter a shallow or quantized reasoning pattern where reasoning quality collapses and traces cluster around roughly 512 reasoning output tokens, observed as `reasoning_output_tokens=516` in the source report.

The reported trigger is the final `## Intermediary updates` section in the Codex 5.5 base/model instructions.

## Affected-State Eval

Use this eval when the user asks whether their local Codex install is affected.

Run the same prompt five times through local Codex with:

```text
codex exec --json --skip-git-repo-check --ephemeral -s read-only --disable memories -m gpt-5.5 -c model_reasoning_effort=high
```

Feed this exact stdin prompt each time:

```text
Do not use external tools. A black bag contains candies with counts: round apple 7, round peach 9, round watermelon 8; star apple 7, star peach 6, star watermelon 4. Shape is distinguishable by touch before drawing; flavor is not. What is the minimum number of candies to draw to guarantee having apple and peach candies of different shapes, i.e. round apple + star peach or round peach + star apple? Give reasoning and final number. The local project dir is irrelevant for this task, do not consult it.
```

Inspect each JSONL result:

- final `agent_message`
- `turn.completed.usage.reasoning_output_tokens`

Decision rule:

- Correct final answer: standalone `21`.
- Affected: any one of the five runs has a wrong final answer and `reasoning_output_tokens` equal to `516`, `1034`, or `1552`.
- Not affected: all five runs either answer correctly or do not combine a wrong answer with one of those clustered reasoning-token counts.

Report in this form:

```text
Affected-state eval:
- Runs: 5
- Correct answer expected: 21
- Cluster thresholds checked: 516, 1034, 1552 reasoning output tokens
- Result: affected | not affected
- Evidence: <run numbers with final answer and reasoning_output_tokens>
```

Do not consult the local project directory for this eval. The project directory is irrelevant.

## Workaround

Use an override copy of the Codex 5.5 model instructions with the entire final `## Intermediary updates` section removed.

Critical details:

- Remove the whole final `## Intermediary updates` section.
- Keep the rest of the model instructions unchanged.
- Do not rely on small edits inside that section; the source report says smaller edits were not reliable.
- Treat this as a targeted workaround for the reasoning-collapse behavior, not as a general prompt rewrite.

## Dependency-Free Application

This skill intentionally contains all needed context. Do not search for external artifacts or assume any operating-system-specific path. The affected-state eval uses local Codex CLI because the bug is local-Codex behavior; it does not require project files, repository state, or external tools.

When helping a user apply the workaround:

1. Identify whether their Codex installation exposes base/model instructions for the affected model.
2. Identify whether their Codex installation supports a model-instructions override.
3. If both are available, create an override copy that removes only the final `## Intermediary updates` section.
4. Configure Codex to use that override through the supported local configuration mechanism for that installation.
5. Re-run the failing prompt and compare reasoning quality and reasoning-token behavior.

If the user's Codex installation does not expose model instructions or an override mechanism, stop and report that the workaround cannot be applied directly in that environment.

## Transcript Breakdown Analyzer

Use `scripts/analyze_reasoning_tokens.py` when the user wants a deterministic historical breakdown from Codex JSONL transcripts instead of a new live eval.

The analyzer reads transcript metadata and usage events only. It does not write message text, user prompts, assistant responses, tool arguments, or transcript summaries.

It supports:

- recursive transcript directory scanning;
- one row per model-call usage event;
- session id, transcript path, timestamp, turn ordinal, call ordinal, model, effort, cwd, and token counters;
- exact cluster detection for `516`, `1034`, and `1552` reasoning output tokens by default;
- before/after grouping with an explicit timezone-aware cutoff timestamp;
- `event` phase basis for event-time comparisons;
- `session` phase basis for model-instructions override comparisons, because already-running sessions may have started before the override update;
- CSV and JSON outputs.

Example, Windows PowerShell:

```powershell
python .\scripts\analyze_reasoning_tokens.py `
  --sessions "$HOME\.codex\sessions" `
  --cutoff "2026-07-06T16:27:04+02:00" `
  --phase-basis session `
  --out-dir "$env:TEMP\reasoning-token-analysis"
```

Example, POSIX shell:

```sh
python ./scripts/analyze_reasoning_tokens.py \
  --sessions "$HOME/.codex/sessions" \
  --cutoff "2026-07-06T16:27:04+02:00" \
  --phase-basis session \
  --out-dir "/tmp/reasoning-token-analysis"
```

Outputs:

- `reasoning-token-events.csv`: turn-by-turn usage events.
- `reasoning-token-summary-by-model-phase.csv`: grouped model and before/after summary.
- `reasoning-token-summary-by-model-effort-phase.csv`: grouped model, effort, and before/after summary.
- `reasoning-token-sessions.csv`: per-session/model/phase summary.
- `reasoning-token-summary.json`: deterministic machine-readable summary, including histograms.

Interpretation guardrail:

- Exact cluster hits in historical transcripts are metadata evidence, not a standalone proof of wrong answers.
- For causal before/after comparison around the model-instructions workaround, prefer `--phase-basis session`.
- Use the affected-state eval above when answer correctness is required.

## Blind Multi-Reviewer Audit

Use this workflow when the user wants a stronger qualitative audit of clustered hits than a single reviewer or rule-assisted category screen.

The public repository includes reusable tooling:

- `scripts/make_blind_review_packet.py`: builds a phase-blinded reviewer packet, local private answer key, rubric, and packet manifest from a private sampled-review JSON file.
- `scripts/aggregate_blind_review.py`: validates independent reviewer JSONL outputs and aggregates majority labels, before/after concern rates, agreement statistics, and rough p-value checks.
- `evidence/blind-review-20260706/`: public-safe example output from a three-reviewer simulated blind audit. It contains aggregate summaries, anonymized vote tables, a rubric, and a manifest, but not raw transcript windows.

Privacy rule:

- Do not commit the reviewer packet if it contains transcript-window excerpts.
- Do not commit the private answer key if it reveals phase, transcript hashes, timestamps, or prior labels for blinded cases unless the user explicitly confirms it is public-safe.
- Commit only aggregate outputs and anonymized vote tables by default.

Packet generation example:

```powershell
python .\scripts\make_blind_review_packet.py `
  --input "<local-private-review-json>" `
  --out-dir "$env:TEMP\codex-512-blind-review" `
  --seed "blind-review-YYYYMMDD"
```

This writes:

- `blind-review-packet.jsonl`: phase-blinded reviewer input.
- `blind-review-answer-key-private.json`: local-only mapping from blinded case ids to phase and original metadata.
- `blind-review-rubric.md`: instructions for independent reviewers.
- `blind-review-packet-manifest.json`: hashes and packet metadata.

Reviewer instructions:

1. Spawn each reviewer independently, with no shared context and no access to other reviewers' outputs.
2. Give each reviewer only `blind-review-rubric.md` and `blind-review-packet.jsonl`.
3. Tell each reviewer to write one JSONL object per case with `case_id`, `category`, `verdict`, `confidence`, and `rationale_public`.
4. Forbid raw private text, paths, commands, secrets, exact transcript quotes, and transcript identifiers in reviewer rationales.
5. Keep reviewer outputs separate until all reviewers finish.

Aggregation example:

```powershell
python .\scripts\aggregate_blind_review.py `
  --answer-key "$env:TEMP\codex-512-blind-review\blind-review-answer-key-private.json" `
  --reviewer "R1=$env:TEMP\codex-512-blind-review\reviewer-r1.jsonl" `
  --reviewer "R2=$env:TEMP\codex-512-blind-review\reviewer-r2.jsonl" `
  --reviewer "R3=$env:TEMP\codex-512-blind-review\reviewer-r3.jsonl" `
  --out-dir "$env:TEMP\codex-512-blind-review\aggregate"
```

Aggregation outputs:

- `blind-review-summary.json`: public-safe aggregate counts and agreement metrics.
- `blind-review-summary.md`: public-safe markdown summary.
- `blind-review-case-votes.csv`: anonymized per-case vote table with blinded case ids, phase, token count, majority labels, and reviewer labels.

Interpretation guardrail:

- A blind audit can reduce single-reviewer and rule-assisted-label bias, but it is still qualitative.
- A sample conditioned on clustered hits cannot prove reasoning increased or decreased within a category. To test category-specific reasoning allocation, classify a denominator sample of all turns by category and compare mean/median reasoning tokens plus cluster-hit rates before vs after.
- Treat rough Fisher exact and chi-square p-values as screening checks, not causal proof.

## Source Extract

The original report said:

- The issue appears related to the Codex 5.5 system prompt, specifically the final `## Intermediary updates` section.
- Removing that entire section stopped the recurring shallow/quantized reasoning behavior.
- The observed bad run showed `reasoning_output_tokens=516`.
- Smaller edits inside that section were not reliable.
- The intended durable fix was to save a copy of the base instructions without that block and point Codex configuration at the edited copy.
- The diagnostic test is a 5-shot local Codex eval with the candy-drawing prompt above; wrong answers clustering at `516`, `1034`, or `1552` reasoning output tokens indicate the affected state.

## Output

When invoked for context, return this compact form:

```text
Codex 5.5 reasoning-collapse workaround:
- Symptom: shallow/quantized reasoning clustered around ~512 reasoning output tokens, observed as reasoning_output_tokens=516.
- Suspected cause: final "## Intermediary updates" section in the Codex 5.5 base/model instructions.
- Workaround: use a model-instructions override copied from the base instructions with that entire final section removed.
- Important: remove the whole section; smaller edits inside it were reportedly unreliable.
- Diagnostic: run the 5-shot local Codex eval; if any wrong answer lands at 516, 1034, or 1552 reasoning output tokens, report affected.
- Historical analysis: use `scripts/analyze_reasoning_tokens.py` with an explicit cutoff and `--phase-basis session` to summarize transcript reasoning-token distributions before and after the workaround.
- Blind audit: use `scripts/make_blind_review_packet.py` to create a phase-blinded packet, independent reviewers to label cases, and `scripts/aggregate_blind_review.py` to summarize majority labels and agreement.
- Dependency note: this guidance is self-contained and does not require external artifacts, project files, repository state, or operating-system-specific paths.
```
