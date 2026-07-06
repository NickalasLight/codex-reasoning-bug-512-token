#!/usr/bin/env python3
"""Aggregate independent blind-review JSONL outputs.

Inputs are local-only reviewer JSONL files plus a private answer key that maps
blinded case ids back to phase and token metadata. Outputs intentionally exclude
raw transcript text and reviewer rationales.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


ALLOWED_VERDICTS = {"no", "probably", "yes", "unclear"}
CONCERN_VERDICTS = {"probably", "yes"}
ALLOWED_CATEGORIES = {
    "routine progress/status or completed work",
    "diagnostic/evidence collection",
    "safety-critical or destructive operations",
    "security, compliance, or secret-sensitive work",
    "tooling/platform integration mistake or brittle orchestration",
    "other/unclear",
}


def load_answer_key(path: Path) -> dict[str, dict[str, Any]]:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    key = {row["case_id"]: row for row in rows}
    if len(key) != len(rows):
        raise ValueError("answer key has duplicate case_id values")
    return key


def load_review_jsonl(path: Path, expected_case_ids: set[str]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        case_id = row.get("case_id")
        if not isinstance(case_id, str):
            raise ValueError(f"{path}:{line_number}: missing string case_id")
        if case_id in rows:
            raise ValueError(f"{path}:{line_number}: duplicate case_id {case_id}")
        verdict = row.get("verdict")
        category = row.get("category")
        if verdict not in ALLOWED_VERDICTS:
            raise ValueError(f"{path}:{line_number}: invalid verdict {verdict!r}")
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(f"{path}:{line_number}: invalid category {category!r}")
        rows[case_id] = row

    missing = sorted(expected_case_ids - set(rows))
    extra = sorted(set(rows) - expected_case_ids)
    if missing or extra:
        raise ValueError(f"{path}: case_id mismatch; missing={missing[:5]} extra={extra[:5]}")
    return rows


def majority(values: list[str]) -> str:
    counts = Counter(values)
    top_count = counts.most_common(1)[0][1]
    winners = sorted(value for value, count in counts.items() if count == top_count)
    if len(winners) == 1:
        return winners[0]
    return "no_majority"


def concern(verdict: str) -> str:
    if verdict in CONCERN_VERDICTS:
        return "concern"
    if verdict == "no":
        return "no_concern"
    return "unclear"


def agreement_rate(votes_by_case: dict[str, list[str]]) -> float:
    if not votes_by_case:
        return 0.0
    agree = 0
    total = 0
    for votes in votes_by_case.values():
        for i, left in enumerate(votes):
            for right in votes[i + 1 :]:
                total += 1
                if left == right:
                    agree += 1
    return agree / total if total else 0.0


def fleiss_kappa(votes_by_case: dict[str, list[str]], labels: list[str]) -> float | None:
    if not votes_by_case:
        return None
    reviewer_counts = {len(votes) for votes in votes_by_case.values()}
    if len(reviewer_counts) != 1:
        return None
    reviewer_count = reviewer_counts.pop()
    if reviewer_count < 2:
        return None

    n_cases = len(votes_by_case)
    label_totals = Counter()
    p_i_sum = 0.0
    for votes in votes_by_case.values():
        counts = Counter(votes)
        label_totals.update(counts)
        p_i_sum += (sum(count * count for count in counts.values()) - reviewer_count) / (
            reviewer_count * (reviewer_count - 1)
        )
    p_bar = p_i_sum / n_cases
    p_e = sum((label_totals[label] / (n_cases * reviewer_count)) ** 2 for label in labels)
    if math.isclose(1.0, p_e):
        return None
    return (p_bar - p_e) / (1.0 - p_e)


def fisher_two_sided(a: int, b: int, c: int, d: int) -> float:
    row_1 = a + b
    row_2 = c + d
    col_1 = a + c
    col_2 = b + d
    total = row_1 + row_2
    low = max(0, col_1 - row_2)
    high = min(row_1, col_1)
    denom = math.comb(total, row_1)

    def hypergeom(k: int) -> float:
        return math.comb(col_1, k) * math.comb(col_2, row_1 - k) / denom

    observed = hypergeom(a)
    return sum(hypergeom(k) for k in range(low, high + 1) if hypergeom(k) <= observed + 1e-15)


def normal_survival_two_sided(z: float) -> float:
    return 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(z) / math.sqrt(2.0))))


def chi_square_2xk(rows: list[tuple[int, int]]) -> tuple[float, int, float]:
    before_total = sum(before for before, _after in rows)
    after_total = sum(after for _before, after in rows)
    grand_total = before_total + after_total
    chi_square = 0.0
    used_cols = 0
    for before, after in rows:
        col_total = before + after
        if col_total == 0:
            continue
        used_cols += 1
        expected_before = before_total * col_total / grand_total
        expected_after = after_total * col_total / grand_total
        if expected_before:
            chi_square += (before - expected_before) ** 2 / expected_before
        if expected_after:
            chi_square += (after - expected_after) ** 2 / expected_after

    df = max(used_cols - 1, 0)
    if df == 0:
        return chi_square, df, 1.0
    if df == 4:
        p_value = math.exp(-chi_square / 2.0) * (1.0 + chi_square / 2.0)
    else:
        # Wilson-Hilferty normal approximation to chi-square survival.
        z = ((chi_square / df) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * df))) / math.sqrt(2.0 / (9.0 * df))
        p_value = 1.0 - 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))
    return chi_square, df, p_value


def ratio_text(count: int, total: int) -> str:
    pct = (count / total * 100.0) if total else 0.0
    return f"{count}/{total} ({pct:.1f}%)"


def parse_reviewer_arg(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise argparse.ArgumentTypeError("reviewer must be NAME=PATH")
    name, path = value.split("=", 1)
    name = name.strip()
    if not name:
        raise argparse.ArgumentTypeError("reviewer name cannot be empty")
    return name, Path(path)


def build_summary(answer_key: dict[str, dict[str, Any]], reviews: dict[str, dict[str, dict[str, Any]]]) -> dict[str, Any]:
    case_ids = sorted(answer_key)
    reviewer_names = sorted(reviews)

    case_rows: list[dict[str, Any]] = []
    verdict_votes_by_case: dict[str, list[str]] = {}
    category_votes_by_case: dict[str, list[str]] = {}
    concern_votes_by_case: dict[str, list[str]] = {}

    for case_id in case_ids:
        verdict_votes = [reviews[name][case_id]["verdict"] for name in reviewer_names]
        category_votes = [reviews[name][case_id]["category"] for name in reviewer_names]
        concern_votes = [concern(verdict) for verdict in verdict_votes]
        verdict_votes_by_case[case_id] = verdict_votes
        category_votes_by_case[case_id] = category_votes
        concern_votes_by_case[case_id] = concern_votes

        case_rows.append(
            {
                "case_id": case_id,
                "phase": answer_key[case_id]["phase"],
                "reasoning_output_tokens": answer_key[case_id]["reasoning_output_tokens"],
                "verdict_votes": dict(zip(reviewer_names, verdict_votes)),
                "category_votes": dict(zip(reviewer_names, category_votes)),
                "majority_verdict": majority(verdict_votes),
                "majority_concern": majority(concern_votes),
                "majority_category": majority(category_votes),
            }
        )

    by_reviewer = {}
    for name in reviewer_names:
        verdict_counts = Counter(reviews[name][case_id]["verdict"] for case_id in case_ids)
        category_counts = Counter(reviews[name][case_id]["category"] for case_id in case_ids)
        concern_counts = Counter(concern(reviews[name][case_id]["verdict"]) for case_id in case_ids)
        by_reviewer[name] = {
            "rows": len(reviews[name]),
            "verdict_counts": dict(sorted(verdict_counts.items())),
            "category_counts": dict(sorted(category_counts.items())),
            "concern_counts": dict(sorted(concern_counts.items())),
        }

    majority_verdict_counts = Counter(row["majority_verdict"] for row in case_rows)
    majority_category_counts = Counter(row["majority_category"] for row in case_rows)
    majority_concern_counts = Counter(row["majority_concern"] for row in case_rows)

    phase_counts: dict[str, Counter[str]] = defaultdict(Counter)
    phase_category_counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in case_rows:
        phase = row["phase"]
        phase_counts[phase][row["majority_concern"]] += 1
        phase_counts[phase]["sampled"] += 1
        phase_category_counts[phase][row["majority_category"]] += 1

    before_concern = phase_counts["before"]["concern"]
    before_no = phase_counts["before"]["no_concern"] + phase_counts["before"]["unclear"]
    after_concern = phase_counts["after"]["concern"]
    after_no = phase_counts["after"]["no_concern"] + phase_counts["after"]["unclear"]
    concern_p = fisher_two_sided(before_concern, before_no, after_concern, after_no)

    category_labels = sorted(set(majority_category_counts) - {"no_majority"})
    chi_rows = [(phase_category_counts["before"][label], phase_category_counts["after"][label]) for label in category_labels]
    chi_square, chi_df, chi_p = chi_square_2xk(chi_rows)

    return {
        "case_count": len(case_ids),
        "reviewers": reviewer_names,
        "by_reviewer": by_reviewer,
        "majority_counts": {
            "verdict": dict(sorted(majority_verdict_counts.items())),
            "concern": dict(sorted(majority_concern_counts.items())),
            "category": dict(sorted(majority_category_counts.items())),
        },
        "phase_counts": {phase: dict(sorted(counts.items())) for phase, counts in sorted(phase_counts.items())},
        "phase_category_counts": {
            phase: dict(sorted(counts.items())) for phase, counts in sorted(phase_category_counts.items())
        },
        "agreement": {
            "verdict_pairwise": agreement_rate(verdict_votes_by_case),
            "category_pairwise": agreement_rate(category_votes_by_case),
            "concern_pairwise": agreement_rate(concern_votes_by_case),
            "verdict_fleiss_kappa": fleiss_kappa(verdict_votes_by_case, sorted(ALLOWED_VERDICTS)),
            "category_fleiss_kappa": fleiss_kappa(category_votes_by_case, sorted(ALLOWED_CATEGORIES)),
            "concern_fleiss_kappa": fleiss_kappa(concern_votes_by_case, ["concern", "no_concern", "unclear"]),
        },
        "rough_tests": {
            "majority_concern_fisher_exact_p": concern_p,
            "majority_category_chi_square": chi_square,
            "majority_category_chi_square_df": chi_df,
            "majority_category_chi_square_p": chi_p,
        },
        "case_rows": case_rows,
    }


def write_case_votes(summary: dict[str, Any], out_path: Path) -> None:
    reviewers = summary["reviewers"]
    fieldnames = (
        ["case_id", "phase", "reasoning_output_tokens", "majority_verdict", "majority_concern", "majority_category"]
        + [f"{reviewer}_verdict" for reviewer in reviewers]
        + [f"{reviewer}_category" for reviewer in reviewers]
    )
    with out_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in summary["case_rows"]:
            csv_row = {
                "case_id": row["case_id"],
                "phase": row["phase"],
                "reasoning_output_tokens": row["reasoning_output_tokens"],
                "majority_verdict": row["majority_verdict"],
                "majority_concern": row["majority_concern"],
                "majority_category": row["majority_category"],
            }
            for reviewer in reviewers:
                csv_row[f"{reviewer}_verdict"] = row["verdict_votes"][reviewer]
                csv_row[f"{reviewer}_category"] = row["category_votes"][reviewer]
            writer.writerow(csv_row)


def write_markdown(summary: dict[str, Any], out_path: Path) -> None:
    phase = summary["phase_counts"]
    before_total = phase.get("before", {}).get("sampled", 0)
    after_total = phase.get("after", {}).get("sampled", 0)
    before_concern = phase.get("before", {}).get("concern", 0)
    after_concern = phase.get("after", {}).get("concern", 0)
    lines = [
        "# Blind Multi-Reviewer Audit Summary",
        "",
        f"Reviewers: {', '.join(summary['reviewers'])}",
        f"Cases: {summary['case_count']}",
        "",
        "## Majority Concern Result",
        "",
        "| Phase | Sampled | Majority Concern |",
        "|---|---:|---:|",
        f"| before cutoff | {before_total} | {ratio_text(before_concern, before_total)} |",
        f"| after cutoff | {after_total} | {ratio_text(after_concern, after_total)} |",
        "",
        f"Fisher exact p-value for majority concern before vs after: `{summary['rough_tests']['majority_concern_fisher_exact_p']:.4f}`.",
        "",
        "## Agreement",
        "",
        "| Label Type | Pairwise Agreement | Fleiss Kappa |",
        "|---|---:|---:|",
    ]
    for label, agreement_key, kappa_key in [
        ("Concern", "concern_pairwise", "concern_fleiss_kappa"),
        ("Verdict", "verdict_pairwise", "verdict_fleiss_kappa"),
        ("Category", "category_pairwise", "category_fleiss_kappa"),
    ]:
        agreement = summary["agreement"][agreement_key]
        kappa = summary["agreement"][kappa_key]
        kappa_text = "n/a" if kappa is None else f"{kappa:.3f}"
        lines.append(f"| {label} | {agreement:.3f} | {kappa_text} |")

    lines.extend(
        [
            "",
            "## Majority Category By Phase",
            "",
            "| Category | Before | After |",
            "|---|---:|---:|",
        ]
    )
    labels = sorted(set(summary["phase_category_counts"].get("before", {})) | set(summary["phase_category_counts"].get("after", {})))
    for label in labels:
        lines.append(
            f"| {label} | {summary['phase_category_counts'].get('before', {}).get(label, 0)} | "
            f"{summary['phase_category_counts'].get('after', {}).get(label, 0)} |"
        )

    lines.extend(
        [
            "",
            "## Rough Category-Mix Test",
            "",
            "No-majority category cases are excluded from this rough category-mix test.",
            "",
            f"2-by-k chi-square: `chi^2 = {summary['rough_tests']['majority_category_chi_square']:.3f}`, "
            f"`df = {summary['rough_tests']['majority_category_chi_square_df']}`, "
            f"`p ~= {summary['rough_tests']['majority_category_chi_square_p']:.4f}`.",
            "",
        ]
    )
    out_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answer-key", type=Path, required=True)
    parser.add_argument("--reviewer", action="append", type=parse_reviewer_arg, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()

    answer_key = load_answer_key(args.answer_key)
    expected_case_ids = set(answer_key)
    reviews = {
        name: load_review_jsonl(path, expected_case_ids)
        for name, path in args.reviewer
    }
    args.out_dir.mkdir(parents=True, exist_ok=True)
    summary = build_summary(answer_key, reviews)

    public_summary = dict(summary)
    case_rows = public_summary.pop("case_rows")
    (args.out_dir / "blind-review-summary.json").write_text(
        json.dumps(public_summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    write_case_votes({**summary, "case_rows": case_rows}, args.out_dir / "blind-review-case-votes.csv")
    write_markdown(summary, args.out_dir / "blind-review-summary.md")
    print(
        json.dumps(
            {
                "cases": summary["case_count"],
                "reviewers": summary["reviewers"],
                "out_dir": str(args.out_dir),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
