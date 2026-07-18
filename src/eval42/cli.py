"""The dependency-light Eval42 command-line interface."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from eval42._version import __version__
from eval42.baseline import (
    baseline_from_report,
    compare_report_to_baseline,
    load_baseline,
    write_baseline,
)
from eval42.config import config_path, load_config
from eval42.errors import Eval42Error
from eval42.gates import UNTRUSTED
from eval42.loader import load_dataset
from eval42.reporters import load_report, render_markdown
from eval42.runner import run_evaluation


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eval42",
        description="CI-first evaluation for verifiable AI applications.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    run = subcommands.add_parser("run", help="run an evaluation")
    run.add_argument("config")

    validate = subcommands.add_parser("validate", help="validate config and dataset")
    validate.add_argument("config")

    dataset = subcommands.add_parser("dataset", help="dataset operations")
    dataset_commands = dataset.add_subparsers(dest="dataset_command", required=True)
    dataset_validate = dataset_commands.add_parser("validate", help="validate a JSONL dataset")
    dataset_validate.add_argument("dataset")

    baseline = subcommands.add_parser("baseline", help="baseline operations")
    baseline_commands = baseline.add_subparsers(dest="baseline_command", required=True)
    baseline_create = baseline_commands.add_parser("create", help="run and create a baseline")
    baseline_create.add_argument("config")
    baseline_create.add_argument("--output", required=True)
    baseline_compare = baseline_commands.add_parser("compare", help="compare report and baseline")
    baseline_compare.add_argument("current")
    baseline_compare.add_argument("baseline")

    report = subcommands.add_parser("report", help="render a JSON report as Markdown")
    report.add_argument("result")
    report.add_argument("--output")
    subcommands.add_parser("version", help="print the Eval42 version")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return _dispatch(args)
    except Eval42Error as exc:
        print(f"eval42: {exc}", file=sys.stderr)
        return 1


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "version":
        print(__version__)
        return 0
    if args.command == "run":
        outcome = run_evaluation(load_config(args.config))
        _print_run_summary(outcome.report, outcome.report_paths)
        return outcome.exit_code
    if args.command == "validate":
        config = load_config(args.config)
        cases = load_dataset(
            config_path(config, "dataset", "path"),
            include_tags=config.data["dataset"].get("include_tags", []),
            exclude_tags=config.data["dataset"].get("exclude_tags", []),
        )
        print(f"valid: {len(cases)} cases")
        return 0
    if args.command == "dataset" and args.dataset_command == "validate":
        cases = load_dataset(args.dataset)
        print(f"valid: {len(cases)} cases")
        return 0
    if args.command == "baseline" and args.baseline_command == "create":
        outcome = run_evaluation(load_config(args.config), compare_baseline=False)
        if outcome.exit_code == UNTRUSTED:
            raise Eval42Error("refusing to baseline an untrusted run")
        output = write_baseline(baseline_from_report(outcome.report), args.output)
        print(f"baseline written: {output}")
        return 0
    if args.command == "baseline" and args.baseline_command == "compare":
        comparison = compare_report_to_baseline(
            load_report(args.current),
            load_baseline(args.baseline),
        )
        print(json.dumps(comparison, ensure_ascii=False, indent=2))
        return 0
    if args.command == "report":
        markdown = render_markdown(load_report(args.result))
        if args.output:
            output = Path(args.output)
            output.parent.mkdir(parents=True, exist_ok=True)
            output.write_text(markdown, encoding="utf-8")
            print(f"report written: {output}")
        else:
            print(markdown, end="")
        return 0
    raise Eval42Error("unsupported command")


def _print_run_summary(report: dict[str, object], paths: dict[str, Path]) -> None:
    summary = report["summary"]
    assert isinstance(summary, dict)
    print(
        f"{summary['gate'].upper()}: "
        f"{summary['completed_cases']}/{summary['total_cases']} cases completed"
    )
    for format_name, path in paths.items():
        print(f"{format_name}: {path}")


if __name__ == "__main__":
    raise SystemExit(main())
