"""Adapter interface kept independent from target-project code."""

from __future__ import annotations

from abc import ABC, abstractmethod

from eval42.models import CaseResult, EvalCase


class Adapter(ABC):
    """Convert an Eval42 case into one target call and a normalized result."""

    version = "1"

    @abstractmethod
    def execute(self, case: EvalCase) -> CaseResult:
        """Execute a case or raise AdapterError."""
