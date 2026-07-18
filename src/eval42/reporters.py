"""Machine-readable JSON and human-readable Markdown reports."""

from __future__ import annotations

import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from eval42.errors import ReportError
from eval42.schema import validate_instance


def write_reports(
    report: dict[str, Any],
    output_dir: str | Path,
    formats: Iterable[str],
) -> dict[str, Path]:
    validate_instance(report, "report")
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    written: dict[str, Path] = {}
    for format_name in formats:
        if format_name == "json":
            path = directory / "report.json"
            path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        elif format_name == "markdown":
            path = directory / "report.md"
            path.write_text(render_markdown(report), encoding="utf-8")
        else:
            raise ReportError(f"unsupported report format {format_name!r}")
        written[format_name] = path
    return written


def load_report(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    try:
        report = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"cannot load report {source}: {exc}") from exc
    if not isinstance(report, dict):
        raise ReportError("report root must be an object")
    validate_instance(report, "report")
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# Eval42 report: {report['run']['project_name']}",
        "",
        f"- Result: **{summary['gate'].upper()}**",
        f"- Revision: `{report['run']['revision']}`",
        f"- Cases: {summary['completed_cases']}/{summary['total_cases']} completed",
        f"- Completion rate: {summary['completion_rate']:.1%}",
        "",
        "## Metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
    ]
    metrics = summary.get("metrics", {})
    if metrics:
        lines.extend(f"| `{name}` | {_format(value)} |" for name, value in sorted(metrics.items()))
    else:
        lines.append("| _none_ | — |")
    lines.extend(["", "## Gates", "", "| Metric | Status | Detail |", "|---|---|---|"])
    gates = report.get("gates", [])
    if gates:
        lines.extend(
            f"| `{gate['metric']}` | {gate['status']} | {gate.get('message', '')} |"
            for gate in gates
        )
    else:
        lines.append("| _none_ | — | — |")
    failures = [case for case in report["cases"] if case["status"] != "completed"]
    lines.extend(["", "## Execution errors", ""])
    if failures:
        lines.extend(
            f"- `{case['case_id']}`: {case.get('error', {}).get('message', 'unknown error')}"
            for case in failures
        )
    else:
        lines.append("None.")
    lines.append("")
    return "\n".join(lines)


def _format(value: Any) -> str:
    return f"{value:.6g}" if isinstance(value, float) else str(value)
