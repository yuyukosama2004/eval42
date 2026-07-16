"""Validate stable assumptions in the Eval42 development plan."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / "eval42-development-plan.md"

REQUIRED_TEXT = (
    "> 计划版本：v1.1",
    "a7f8bb216367a3ba7476e2591d3b8ce3bfad6719",
    "d2f9b11ef8d73f1c1f92fe966c5d2c18e21dcf47",
    "POST /api/merchant/ai/evaluate",
    "POST /api/v1/runs",
    "现有 50 条",
    "Command Adapter 不进入 v0.1.0",
    "case_hash",
    "token_count_kind",
    "## Phase 3：GroundedSeek HTTP 接入与 Gold Set",
)

FORBIDDEN_TEXT = (
    "POST /api/order/ai/eval",
    "PHONEMALL_EVAL_TOKEN",
    "JSON Schema 在 v0.1.0 后应版本化",
    "`EVAL-404` 实现通用 Command Adapter",
    "- [ ] 能运行 Command Adapter。",
)


def main() -> None:
    content = PLAN.read_text(encoding="utf-8")
    errors: list[str] = []

    for text in REQUIRED_TEXT:
        if text not in content:
            errors.append(f"missing required text: {text}")

    for text in FORBIDDEN_TEXT:
        if text in content:
            errors.append(f"stale text remains: {text}")

    fence_count = len(re.findall(r"(?m)^```", content))
    if fence_count % 2:
        errors.append(f"unbalanced fenced code blocks: {fence_count} markers")

    phase_numbers = [
        int(number)
        for number in re.findall(r"(?m)^## Phase ([0-7])：", content)
    ]
    if phase_numbers != list(range(8)):
        errors.append(f"unexpected phase sequence: {phase_numbers}")

    if errors:
        raise SystemExit("\n".join(errors))

    print(
        f"Validated {PLAN.name}: "
        f"{len(content)} characters, {fence_count // 2} fenced blocks, 8 phases."
    )


if __name__ == "__main__":
    main()
