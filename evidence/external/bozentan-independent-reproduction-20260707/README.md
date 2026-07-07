# Bozentan / Ilia Independent Local Reproduction

Source: PR [#3](https://github.com/NickalasLight/codex-reasoning-bug-512-token/pull/3), commit `020f0116c1ae7d15f4cf88efa4eebcfdbb1cff0d`.

This is a public-safe named external contribution artifact. It preserves Bozentan / Ilia's independent local reproduction analysis while keeping the main README concise. The evidence below is contributor-reported and maintainer-reviewed for public-safe aggregate inclusion. It excludes raw prompts beyond the benchmark, raw transcript text, tool outputs, local paths, usernames, secrets, and private repository details.

## Summary

| Check | Result |
|---|---:|
| Affected candy benchmark | 0/5 correct; all five wrong answers at 516 reasoning tokens |
| Basic removal retest | 5/5 correct; no 512-family cluster hits |
| Hardened override retest | 5/5 correct; no 512-family cluster hits |
| Historical 516-task replay | 9 better, 1 similar, 0 worse |

## Affected-State Candy Benchmark

The clearest preserved affected-state benchmark batch was a 5-shot run where all five attempts failed and all five landed on the exact clustered value:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | no | `29` | 516 | yes |
| 2 | no | `28` | 516 | yes |
| 3 | no | `27` | 516 | yes |
| 4 | no | `28` | 516 | yes |
| 5 | no | `27` | 516 | yes |

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 0 |
| Wrong runs | 5 |
| Exact 516 runs | 5 |
| 512-family cluster-hit runs | 5 |

## Basic Removal Retest

After removing the final `Intermediary updates` section from local Codex 5.5 instructions, a later 5-shot benchmark batch was clean:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | yes | `21` | 4971 | no |
| 2 | yes | `21` | 6436 | no |
| 3 | yes | `21` | 4660 | no |
| 4 | yes | `21` | 6468 | no |
| 5 | yes | `21` | 5331 | no |

| Metric | Value |
|---|---:|
| Runs | 5 |
| Correct runs | 5 |
| Wrong runs | 0 |
| Exact 516 runs | 0 |
| 512-family cluster-hit runs | 0 |

This matches the main workaround hypothesis: removing the whole final `Intermediary updates` section can stop the obvious candy-benchmark failure.

## Hardened Override Retest

On this install, cache-only removal was not durable. The contributor reported that Codex later refreshed `models_cache.json` and restored the bad section during active use. The more durable local setup used both:

- `model_instructions_file`, pointing at patched Codex 5.5 instructions with the final `Intermediary updates` section removed.
- `model_catalog_json`, pointing at a patched startup catalog with the same Codex 5.5 fields patched.

The patched catalog was written as UTF-8 without BOM. `models_cache.json` was then treated as transient cache maintenance, not as the source of truth. This hardened catalog setup is contributor-reported and should be validated separately before being treated as a general recommendation.

After that hardened setup, another 5-shot benchmark batch was also clean:

| Run | Correct | Final Answer | Reasoning Output Tokens | Cluster Hit |
|---:|---:|---:|---:|---:|
| 1 | yes | `21` | 7508 | no |
| 2 | yes | `21` | 5696 | no |
| 3 | yes | `21` | 4142 | no |
| 4 | yes | `21` | 4848 | no |
| 5 | yes | `21` | 3798 | no |

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

## Local Log Metadata

The same analyzer approach was also run over the contributor's local Codex session logs.

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

## Historical 516 Task Replay

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

The quality improvement was not only higher token usage. The replayed answers were usually more direct, more source-grounded, better at ranking root causes, and clearer about proof limits.

## Interpretation

The strongest practical finding from this install is that the basic instruction-section removal can fix the benchmark, but durability matters. If Codex refreshes model/cache state and restores the final `Intermediary updates` section, affected behavior may return unless patched instructions are loaded from a durable startup source.

## Limitations

- This is one local install and one local transcript corpus.
- The historical task replay was not an exact time-machine replay; current filesystem state may differ from the original task state.
- Replayed tasks were wrapped in a read-only audit guard.
- Hidden reasoning traces were unavailable, so task-quality comparison used final answers and recorded token metadata only.
- The `model_catalog_json` hardened setup is contributor-reported and should be validated separately.
