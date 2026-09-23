"""
Execution Backend - Process Isolation

Design: Abstract execution boundary, NOT hardened sandbox.
v0.1: SubprocessBackend provides process isolation only.
"""

import subprocess
from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ExecutionResult:
    """Result of capability execution."""

    success: bool
    stdout: str
    stderr: str
    returncode: int
    metadata: dict[str, Any]


class ExecutionBackend(Protocol):
    """
    Execution boundary protocol.

    Design: Protocol allows different isolation strategies.
    """

    def execute(
        self,
        artifact: Any,  # CapabilityArtifact
        **kwargs: Any
    ) -> ExecutionResult:
        """Execute capability in isolated boundary."""
        ...


class SubprocessBackend:
    """
    Subprocess-based execution backend.

    IMPORTANT: This is NOT a hardened security sandbox.
    Provides: Process isolation
    Does NOT provide: OS-level permission enforcement

    Permission declarations are policy, not enforcement.
    """

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout

    def execute(
        self,
        artifact: Any,
        mode: str = "run",
        **kwargs: Any
    ) -> ExecutionResult:
        """
        Execute capability in subprocess.

        Args:
            artifact: CapabilityArtifact to execute
            mode: "run" or "test"

        Returns:
            ExecutionResult
        """
        try:
            # For v0.1 demo: simulate execution
            # Real implementation would invoke Python with entrypoint

            if mode == "test":
                # Simulate test execution
                result = subprocess.run(
                    ["python", "-c", "print('Tests passed')"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )
            else:
                # Simulate capability execution
                result = subprocess.run(
                    ["python", "-c", "print('Capability executed')"],
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False
                )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                metadata={"mode": mode, "backend": "subprocess"}
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timeout after {self.timeout}s",
                returncode=-1,
                metadata={"mode": mode, "backend": "subprocess", "timeout": True}
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=str(e),
                returncode=-1,
                metadata={"mode": mode, "backend": "subprocess", "error": str(e)}
            )
