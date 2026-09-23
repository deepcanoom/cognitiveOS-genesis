"""Execution boundary abstraction."""

from genesis.execution.backend import ExecutionBackend, ExecutionResult, SubprocessBackend

__all__ = ["ExecutionBackend", "SubprocessBackend", "ExecutionResult"]
