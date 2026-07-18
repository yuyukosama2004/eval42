"""Stable exception hierarchy for callers and the CLI."""


class Eval42Error(Exception):
    """Base class for expected Eval42 failures."""


class ConfigError(Eval42Error):
    """The evaluation configuration is invalid."""


class DatasetError(Eval42Error):
    """The dataset cannot be loaded or validated."""


class AdapterError(Eval42Error):
    """A target system call failed."""

    def __init__(
        self,
        message: str,
        *,
        error_type: str = "adapter_error",
        retryable: bool = False,
    ) -> None:
        super().__init__(message)
        self.error_type = error_type
        self.retryable = retryable


class BaselineError(Eval42Error):
    """A baseline cannot be created or compared."""


class ReportError(Eval42Error):
    """A report cannot be loaded or written."""
