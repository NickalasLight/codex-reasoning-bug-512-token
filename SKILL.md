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
- Dependency note: this guidance is self-contained and does not require external artifacts, project files, repository state, or operating-system-specific paths.
```
