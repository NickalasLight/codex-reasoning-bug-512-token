#!/usr/bin/env python3
"""Analyze reasoning-token usage in Codex JSONL transcripts.

The script emits usage metadata only. It does not print or write transcript
message text, tool arguments, assistant answers, user prompts, or summaries.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CLUSTER_VALUES = (516, 1034, 1552)
EVENTS_CSV = "reasoning-token-events.csv"
SUMMARY_CSV = "reasoning-token-summary-by-model-phase.csv"
SUMMARY_EFFORT_CSV = "reasoning-token-summary-by-model-effort-phase.csv"
SESSIONS_CSV = "reasoning-token-sessions.csv"
SUMMARY_JSON = "reasoning-token-summary.json"
EVENT_FIELDS = [
    "transcript_path",
    "transcript_name",
    "session_id",
    "session_start_utc",
    "cwd",
    "cli_version",
    "model_provider",
    "event_timestamp_utc",
    "event_phase",
    "session_phase",
    "phase",
    "phase_basis",
    "event_kind",
    "model",
    "effort",
    "turn_index",
    "turn_id",
    "call_index",
    "call_in_turn",
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
    "total_tokens",
    "cumulative_input_tokens",
    "cumulative_output_tokens",
    "cumulative_reasoning_output_tokens",
    "cumulative_total_tokens",
    "model_context_window",
    "cluster_hit",
    "cluster_value",
    "base_instructions_has_intermediary_updates",
]


@dataclass
class SessionMeta:
    transcript_path: str
    transcript_name: str
    session_id: str
    session_start_utc: str
    cwd: str
    cli_version: str
    model_provider: str
    session_model: str
    base_instructions_has_intermediary_updates: bool


@dataclass
class UsageRow:
    transcript_path: str
    transcript_name: str
    session_id: str
    session_start_utc: str
    cwd: str
    cli_version: str
    model_provider: str
    event_timestamp_utc: str
    event_phase: str
    session_phase: str
    phase: str
    phase_basis: str
    event_kind: str
    model: str
    effort: str
    turn_index: int
    turn_id: str
    call_index: int
    call_in_turn: int
    input_tokens: int | None
    cached_input_tokens: int | None
    output_tokens: int | None
    reasoning_output_tokens: int | None
    total_tokens: int | None
    cumulative_input_tokens: int | None
    cumulative_output_tokens: int | None
    cumulative_reasoning_output_tokens: int | None
    cumulative_total_tokens: int | None
    model_context_window: int | None
    cluster_hit: bool
    cluster_value: int | None
    base_instructions_has_intermediary_updates: bool


def parse_iso_datetime(value: str, *, require_timezone: bool = False) -> datetime:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = normalized[:-1] + "+00:00"
    parsed = datetime.fromisoformat(normalized)
    if require_timezone and parsed.tzinfo is None:
        raise ValueError(
            "timestamp must include a timezone offset, for example "
            "2026-07-06T16:27:04+02:00 or 2026-07-06T14:27:04Z"
        )
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def format_utc(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def as_int(value: Any) -> int | None:
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def walk_strings(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from walk_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from walk_strings(child)


def has_intermediary_updates_marker(base_instructions: Any) -> bool:
    for text in walk_strings(base_instructions):
        if "## Intermediary updates" in text:
            return True
    return False


def iter_jsonl_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if path.is_file():
            files.append(path)
        elif path.is_dir():
            files.extend(path.rglob("*.jsonl"))
        else:
            raise FileNotFoundError(f"input path does not exist: {path}")
    return sorted(set(files), key=lambda item: str(item).lower())


def first_string(*values: Any) -> str:
    for value in values:
        if value is not None and value != "":
            return str(value)
    return ""


def usage_from_event(obj: dict[str, Any]) -> tuple[str, dict[str, Any], dict[str, Any], int | None] | None:
    event_type = obj.get("type")
    payload = obj.get("payload")
    payload = payload if isinstance(payload, dict) else {}

    if event_type == "event_msg" and payload.get("type") == "token_count":
        info = payload.get("info")
        info = info if isinstance(info, dict) else {}
        usage = info.get("last_token_usage")
        total_usage = info.get("total_token_usage")
        return (
            "event_msg.token_count",
            usage if isinstance(usage, dict) else {},
            total_usage if isinstance(total_usage, dict) else {},
            as_int(info.get("model_context_window")),
        )

    candidate = payload if payload else obj
    candidate_type = first_string(event_type, candidate.get("type"))
    if candidate_type in {"turn.completed", "turn_completed"}:
        usage = candidate.get("usage")
        return (
            "turn.completed",
            usage if isinstance(usage, dict) else {},
            {},
            as_int(candidate.get("model_context_window")),
        )

    return None


def classify_phase(timestamp_utc: datetime | None, cutoff_utc: datetime | None) -> str:
    if cutoff_utc is None or timestamp_utc is None:
        return "uncut"
    if timestamp_utc < cutoff_utc:
        return "before"
    return "after"


def analyze_file(
    path: Path,
    *,
    cutoff_utc: datetime | None,
    phase_basis: str,
    cluster_values: set[int],
) -> tuple[SessionMeta, list[UsageRow], list[dict[str, Any]]]:
    session = SessionMeta(
        transcript_path=str(path),
        transcript_name=path.name,
        session_id="",
        session_start_utc="",
        cwd="",
        cli_version="",
        model_provider="",
        session_model="",
        base_instructions_has_intermediary_updates=False,
    )
    rows: list[UsageRow] = []
    errors: list[dict[str, Any]] = []
    session_start_dt: datetime | None = None

    current_model = ""
    current_effort = ""
    current_cwd = ""
    turn_id = ""
    turn_index = 0
    call_index = 0
    call_in_turn = 0

    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                obj = json.loads(stripped)
            except json.JSONDecodeError as exc:
                errors.append(
                    {
                        "path": str(path),
                        "line": line_number,
                        "error": f"json decode error: {exc.msg}",
                    }
                )
                continue

            event_type = obj.get("type")
            payload = obj.get("payload")
            payload = payload if isinstance(payload, dict) else {}

            if event_type == "session_meta":
                session_id = first_string(
                    payload.get("session_id"),
                    payload.get("id"),
                    session.session_id,
                )
                session_timestamp = ""
                if payload.get("timestamp"):
                    try:
                        session_start_dt = parse_iso_datetime(str(payload["timestamp"]))
                        session_timestamp = format_utc(session_start_dt)
                    except ValueError:
                        session_timestamp = str(payload["timestamp"])
                session = SessionMeta(
                    transcript_path=str(path),
                    transcript_name=path.name,
                    session_id=session_id,
                    session_start_utc=session_timestamp,
                    cwd=first_string(payload.get("cwd"), session.cwd),
                    cli_version=first_string(payload.get("cli_version"), session.cli_version),
                    model_provider=first_string(payload.get("model_provider"), session.model_provider),
                    session_model=first_string(payload.get("model"), session.session_model),
                    base_instructions_has_intermediary_updates=has_intermediary_updates_marker(
                        payload.get("base_instructions")
                    ),
                )
                current_model = first_string(current_model, session.session_model)
                current_cwd = first_string(current_cwd, session.cwd)
                continue

            if event_type == "turn_context":
                turn_index += 1
                call_in_turn = 0
                turn_id = first_string(payload.get("turn_id"), turn_index)
                current_model = first_string(payload.get("model"), current_model, session.session_model)
                current_effort = first_string(payload.get("effort"), current_effort)
                current_cwd = first_string(payload.get("cwd"), current_cwd, session.cwd)
                continue

            usage_event = usage_from_event(obj)
            if usage_event is None:
                continue

            event_kind, usage, total_usage, context_window = usage_event
            timestamp_utc: datetime | None = None
            if obj.get("timestamp"):
                try:
                    timestamp_utc = parse_iso_datetime(str(obj["timestamp"]))
                except ValueError:
                    timestamp_utc = None

            call_index += 1
            call_in_turn += 1
            reasoning = as_int(usage.get("reasoning_output_tokens"))
            event_phase = classify_phase(timestamp_utc, cutoff_utc)
            session_phase = classify_phase(session_start_dt, cutoff_utc)
            phase = session_phase if phase_basis == "session" else event_phase
            cluster_hit = reasoning in cluster_values if reasoning is not None else False
            rows.append(
                UsageRow(
                    transcript_path=str(path),
                    transcript_name=path.name,
                    session_id=first_string(session.session_id, path.stem),
                    session_start_utc=session.session_start_utc,
                    cwd=first_string(current_cwd, session.cwd),
                    cli_version=session.cli_version,
                    model_provider=session.model_provider,
                    event_timestamp_utc=format_utc(timestamp_utc),
                    event_phase=event_phase,
                    session_phase=session_phase,
                    phase=phase,
                    phase_basis=phase_basis,
                    event_kind=event_kind,
                    model=first_string(usage.get("model"), payload.get("model"), current_model, session.session_model, "unknown"),
                    effort=first_string(payload.get("effort"), current_effort),
                    turn_index=turn_index,
                    turn_id=turn_id,
                    call_index=call_index,
                    call_in_turn=call_in_turn,
                    input_tokens=as_int(usage.get("input_tokens")),
                    cached_input_tokens=as_int(usage.get("cached_input_tokens")),
                    output_tokens=as_int(usage.get("output_tokens")),
                    reasoning_output_tokens=reasoning,
                    total_tokens=as_int(usage.get("total_tokens")),
                    cumulative_input_tokens=as_int(total_usage.get("input_tokens")),
                    cumulative_output_tokens=as_int(total_usage.get("output_tokens")),
                    cumulative_reasoning_output_tokens=as_int(total_usage.get("reasoning_output_tokens")),
                    cumulative_total_tokens=as_int(total_usage.get("total_tokens")),
                    model_context_window=context_window,
                    cluster_hit=cluster_hit,
                    cluster_value=reasoning if cluster_hit else None,
                    base_instructions_has_intermediary_updates=session.base_instructions_has_intermediary_updates,
                )
            )

    return session, rows, errors


def nearest_rank(values: list[int], percentile: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    rank = max(1, math.ceil((percentile / 100.0) * len(ordered)))
    return ordered[rank - 1]


def round_float(value: float | None) -> float | None:
    if value is None:
        return None
    return round(value, 4)


def summarize_group(rows: list[UsageRow], cluster_values: list[int]) -> dict[str, Any]:
    reasoning_values = [row.reasoning_output_tokens for row in rows if row.reasoning_output_tokens is not None]
    reasoning_values_int = [int(value) for value in reasoning_values]
    cluster_counts = Counter(value for value in reasoning_values_int if value in cluster_values)
    timestamps = sorted(row.event_timestamp_utc for row in rows if row.event_timestamp_utc)
    histogram = Counter(reasoning_values_int)

    summary: dict[str, Any] = {
        "call_count": len(rows),
        "session_count": len({(row.transcript_path, row.session_id) for row in rows}),
        "reasoning_count": len(reasoning_values_int),
        "reasoning_total": sum(reasoning_values_int) if reasoning_values_int else 0,
        "reasoning_min": min(reasoning_values_int) if reasoning_values_int else None,
        "reasoning_mean": round_float(sum(reasoning_values_int) / len(reasoning_values_int))
        if reasoning_values_int
        else None,
        "reasoning_median": nearest_rank(reasoning_values_int, 50),
        "reasoning_p90": nearest_rank(reasoning_values_int, 90),
        "reasoning_p95": nearest_rank(reasoning_values_int, 95),
        "reasoning_max": max(reasoning_values_int) if reasoning_values_int else None,
        "cluster_hits": sum(cluster_counts.values()),
        "cluster_hit_rate": round_float(sum(cluster_counts.values()) / len(reasoning_values_int))
        if reasoning_values_int
        else None,
        "first_event_utc": timestamps[0] if timestamps else "",
        "last_event_utc": timestamps[-1] if timestamps else "",
        "reasoning_histogram": {str(key): histogram[key] for key in sorted(histogram)},
    }
    for value in cluster_values:
        summary[f"cluster_{value}"] = cluster_counts[value]
    return summary


def grouped_summaries(
    rows: list[UsageRow],
    *,
    keys: tuple[str, ...],
    cluster_values: list[int],
) -> list[dict[str, Any]]:
    groups: dict[tuple[str, ...], list[UsageRow]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(getattr(row, key)) for key in keys)].append(row)

    summaries: list[dict[str, Any]] = []
    for key_values in sorted(groups):
        entry = {key: value for key, value in zip(keys, key_values)}
        entry.update(summarize_group(groups[key_values], cluster_values))
        summaries.append(entry)
    return summaries


def session_summaries(rows: list[UsageRow], cluster_values: list[int]) -> list[dict[str, Any]]:
    keys = ("transcript_path", "session_id", "phase", "model")
    groups: dict[tuple[str, ...], list[UsageRow]] = defaultdict(list)
    for row in rows:
        groups[tuple(str(getattr(row, key)) for key in keys)].append(row)

    summaries: list[dict[str, Any]] = []
    for key_values in sorted(groups):
        grouped = groups[key_values]
        first = grouped[0]
        entry = {
            "transcript_path": first.transcript_path,
            "transcript_name": first.transcript_name,
            "session_id": first.session_id,
            "session_start_utc": first.session_start_utc,
            "phase": first.phase,
            "model": first.model,
            "efforts": ",".join(sorted({row.effort for row in grouped if row.effort})),
            "cwd": first.cwd,
            "cli_version": first.cli_version,
            "model_provider": first.model_provider,
            "base_instructions_has_intermediary_updates": first.base_instructions_has_intermediary_updates,
        }
        entry.update(summarize_group(grouped, cluster_values))
        entry.pop("reasoning_histogram", None)
        summaries.append(entry)
    return summaries


def dataclass_to_csv_row(row: UsageRow) -> dict[str, Any]:
    return {
        "transcript_path": row.transcript_path,
        "transcript_name": row.transcript_name,
        "session_id": row.session_id,
        "session_start_utc": row.session_start_utc,
        "cwd": row.cwd,
        "cli_version": row.cli_version,
        "model_provider": row.model_provider,
        "event_timestamp_utc": row.event_timestamp_utc,
        "event_phase": row.event_phase,
        "session_phase": row.session_phase,
        "phase": row.phase,
        "phase_basis": row.phase_basis,
        "event_kind": row.event_kind,
        "model": row.model,
        "effort": row.effort,
        "turn_index": row.turn_index,
        "turn_id": row.turn_id,
        "call_index": row.call_index,
        "call_in_turn": row.call_in_turn,
        "input_tokens": row.input_tokens,
        "cached_input_tokens": row.cached_input_tokens,
        "output_tokens": row.output_tokens,
        "reasoning_output_tokens": row.reasoning_output_tokens,
        "total_tokens": row.total_tokens,
        "cumulative_input_tokens": row.cumulative_input_tokens,
        "cumulative_output_tokens": row.cumulative_output_tokens,
        "cumulative_reasoning_output_tokens": row.cumulative_reasoning_output_tokens,
        "cumulative_total_tokens": row.cumulative_total_tokens,
        "model_context_window": row.model_context_window,
        "cluster_hit": row.cluster_hit,
        "cluster_value": row.cluster_value,
        "base_instructions_has_intermediary_updates": row.base_instructions_has_intermediary_updates,
    }


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: "" if row.get(key) is None else row.get(key) for key in fieldnames})


def write_outputs(
    *,
    out_dir: Path,
    input_paths: list[Path],
    files_scanned: list[Path],
    files_with_events: list[Path],
    cutoff_utc: datetime | None,
    cluster_values: list[int],
    sessions: list[SessionMeta],
    rows: list[UsageRow],
    parse_errors: list[dict[str, Any]],
    phase_basis: str,
) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    event_rows = [dataclass_to_csv_row(row) for row in rows]
    summary_by_model_phase = grouped_summaries(
        rows,
        keys=("phase", "model"),
        cluster_values=cluster_values,
    )
    summary_by_model_effort_phase = grouped_summaries(
        rows,
        keys=("phase", "model", "effort"),
        cluster_values=cluster_values,
    )
    per_session = session_summaries(rows, cluster_values)

    summary_fields = [
        "phase",
        "model",
        "effort",
        "call_count",
        "session_count",
        "reasoning_count",
        "reasoning_total",
        "reasoning_min",
        "reasoning_mean",
        "reasoning_median",
        "reasoning_p90",
        "reasoning_p95",
        "reasoning_max",
        "cluster_hits",
        "cluster_hit_rate",
        *[f"cluster_{value}" for value in cluster_values],
        "first_event_utc",
        "last_event_utc",
    ]
    session_fields = [
        "transcript_path",
        "transcript_name",
        "session_id",
        "session_start_utc",
        "phase",
        "model",
        "efforts",
        "cwd",
        "cli_version",
        "model_provider",
        "base_instructions_has_intermediary_updates",
        "call_count",
        "session_count",
        "reasoning_count",
        "reasoning_total",
        "reasoning_min",
        "reasoning_mean",
        "reasoning_median",
        "reasoning_p90",
        "reasoning_p95",
        "reasoning_max",
        "cluster_hits",
        "cluster_hit_rate",
        *[f"cluster_{value}" for value in cluster_values],
        "first_event_utc",
        "last_event_utc",
    ]

    write_csv(out_dir / EVENTS_CSV, event_rows, EVENT_FIELDS)
    write_csv(out_dir / SUMMARY_CSV, summary_by_model_phase, [field for field in summary_fields if field != "effort"])
    write_csv(out_dir / SUMMARY_EFFORT_CSV, summary_by_model_effort_phase, summary_fields)
    write_csv(out_dir / SESSIONS_CSV, per_session, session_fields)

    summary_json = {
        "analysis_version": 1,
        "input_paths": [str(path) for path in input_paths],
        "cutoff_utc": format_utc(cutoff_utc),
        "phase_basis": phase_basis,
        "phase_rule": (
            "phase uses session_start_utc; event_phase and session_phase are also emitted"
            if phase_basis == "session"
            else "phase uses event_timestamp_utc; event_phase and session_phase are also emitted"
        )
        if cutoff_utc
        else "uncut: no cutoff supplied",
        "cluster_values": cluster_values,
        "files_scanned": len(files_scanned),
        "files_with_usage_events": len(files_with_events),
        "usage_event_count": len(rows),
        "session_count": len({(row.transcript_path, row.session_id) for row in rows}),
        "session_meta_count": len(sessions),
        "parse_error_count": len(parse_errors),
        "summary_by_model_phase": summary_by_model_phase,
        "summary_by_model_effort_phase": summary_by_model_effort_phase,
        "sessions": per_session,
        "parse_errors": parse_errors,
        "outputs": {
            "events_csv": str(out_dir / EVENTS_CSV),
            "summary_csv": str(out_dir / SUMMARY_CSV),
            "summary_effort_csv": str(out_dir / SUMMARY_EFFORT_CSV),
            "sessions_csv": str(out_dir / SESSIONS_CSV),
            "summary_json": str(out_dir / SUMMARY_JSON),
        },
        "privacy_note": "Only usage metadata is emitted; transcript message text is not written.",
    }
    with (out_dir / SUMMARY_JSON).open("w", encoding="utf-8") as handle:
        json.dump(summary_json, handle, indent=2, sort_keys=True)
        handle.write("\n")
    return summary_json


def run_analysis(
    *,
    input_paths: list[Path],
    out_dir: Path,
    cutoff_utc: datetime | None,
    phase_basis: str,
    cluster_values: list[int],
) -> dict[str, Any]:
    files = iter_jsonl_files(input_paths)
    sessions: list[SessionMeta] = []
    rows: list[UsageRow] = []
    parse_errors: list[dict[str, Any]] = []
    files_with_events: list[Path] = []

    for path in files:
        session, file_rows, errors = analyze_file(
            path,
            cutoff_utc=cutoff_utc,
            phase_basis=phase_basis,
            cluster_values=set(cluster_values),
        )
        sessions.append(session)
        rows.extend(file_rows)
        parse_errors.extend(errors)
        if file_rows:
            files_with_events.append(path)

    return write_outputs(
        out_dir=out_dir,
        input_paths=input_paths,
        files_scanned=files,
        files_with_events=files_with_events,
        cutoff_utc=cutoff_utc,
        cluster_values=cluster_values,
        sessions=sessions,
        rows=rows,
        parse_errors=parse_errors,
        phase_basis=phase_basis,
    )


def parse_cluster_values(value: str) -> list[int]:
    parsed = sorted({int(part.strip()) for part in value.split(",") if part.strip()})
    if not parsed:
        raise argparse.ArgumentTypeError("at least one cluster value is required")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    default_sessions = Path.home() / ".codex" / "sessions"
    parser = argparse.ArgumentParser(
        description=(
            "Analyze Codex transcript reasoning-token usage by turn, model, and "
            "before/after phase. Outputs usage metadata only."
        )
    )
    parser.add_argument(
        "--sessions",
        nargs="+",
        type=Path,
        default=[default_sessions],
        help=f"Transcript JSONL file or directory paths. Default: {default_sessions}",
    )
    parser.add_argument(
        "--cutoff",
        help=(
            "Timezone-aware ISO timestamp for before/after classification, "
            "for example 2026-07-06T16:27:04+02:00 or 2026-07-06T14:27:04Z. "
            "Without this, all rows are phase=uncut."
        ),
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("reasoning-token-analysis"),
        help="Directory for CSV and JSON outputs. Default: ./reasoning-token-analysis",
    )
    parser.add_argument(
        "--phase-basis",
        choices=("event", "session"),
        default="event",
        help=(
            "Which timestamp controls the summary phase column. Use 'session' "
            "for model-instructions override comparisons because existing "
            "sessions may have started before the update. Event and session "
            "phase columns are always emitted. Default: event"
        ),
    )
    parser.add_argument(
        "--cluster-values",
        type=parse_cluster_values,
        default=list(DEFAULT_CLUSTER_VALUES),
        help="Comma-separated exact reasoning token counts to flag. Default: 516,1034,1552",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    cutoff_utc = None
    if args.cutoff:
        try:
            cutoff_utc = parse_iso_datetime(args.cutoff, require_timezone=True)
        except ValueError as exc:
            parser.error(str(exc))

    try:
        summary = run_analysis(
            input_paths=args.sessions,
            out_dir=args.out_dir,
            cutoff_utc=cutoff_utc,
            phase_basis=args.phase_basis,
            cluster_values=args.cluster_values,
        )
    except (OSError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1

    print(f"files_scanned={summary['files_scanned']}")
    print(f"files_with_usage_events={summary['files_with_usage_events']}")
    print(f"usage_event_count={summary['usage_event_count']}")
    print(f"cutoff_utc={summary['cutoff_utc'] or 'none'}")
    print(f"outputs={summary['outputs']['summary_json']}")
    for item in summary["summary_by_model_phase"]:
        print(
            "phase={phase} model={model} calls={call_count} "
            "reasoning_mean={reasoning_mean} cluster_hits={cluster_hits}".format(**item)
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
