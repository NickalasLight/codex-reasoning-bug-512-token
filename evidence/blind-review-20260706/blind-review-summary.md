# Blind Multi-Reviewer Audit Summary

Reviewers: R1, R2, R3
Cases: 122

## Majority Concern Result

| Phase | Sampled | Majority Concern |
|---|---:|---:|
| before cutoff | 78 | 35/78 (44.9%) |
| after cutoff | 44 | 22/44 (50.0%) |

Fisher exact p-value for majority concern before vs after: `0.5701`.

## Agreement

| Label Type | Pairwise Agreement | Fleiss Kappa |
|---|---:|---:|
| Concern | 0.811 | 0.626 |
| Verdict | 0.770 | 0.604 |
| Category | 0.694 | 0.606 |

## Majority Category By Phase

| Category | Before | After |
|---|---:|---:|
| diagnostic/evidence collection | 20 | 7 |
| no_majority | 4 | 2 |
| routine progress/status or completed work | 18 | 11 |
| safety-critical or destructive operations | 5 | 2 |
| security, compliance, or secret-sensitive work | 14 | 11 |
| tooling/platform integration mistake or brittle orchestration | 17 | 11 |

## Rough Category-Mix Test

No-majority category cases are excluded from this rough category-mix test.

2-by-k chi-square: `chi^2 = 2.222`, `df = 4`, `p ~= 0.6950`.
