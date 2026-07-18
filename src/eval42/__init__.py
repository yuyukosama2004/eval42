"""Public API for Eval42."""

from eval42._version import __version__
from eval42.adapters.base import Adapter
from eval42.config import LoadedConfig, load_config
from eval42.loader import load_dataset
from eval42.runner import RunOptions, RunOutcome, run_evaluation

__all__ = [
    "Adapter",
    "LoadedConfig",
    "RunOptions",
    "RunOutcome",
    "__version__",
    "load_config",
    "load_dataset",
    "run_evaluation",
]
