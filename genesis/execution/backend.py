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
        **kwargs: Any,
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

    @staticmethod
    def _clean_env() -> dict[str, str]:
        """Environment for child processes without host test/coverage config."""
        import os

        env = os.environ.copy()
        # Prevent the child pytest from inheriting host coverage instrumentation
        env["COVERAGE_DISABLE"] = "1"
        env.pop("COVERAGE_PROCESS_START", None)
        env.pop("PYTEST_ADDOPTS", None)
        return env

    def execute(self, artifact: Any, mode: str = "run", **kwargs: Any) -> ExecutionResult:
        """
        Execute capability in subprocess.

        REAL IMPLEMENTATION: Invokes actual Python entrypoints via subprocess.
        No shell=True for security. Explicit Python interpreter invocation.

        Args:
            artifact: CapabilityArtifact to execute
            mode: "run" or "test"

        Returns:
            ExecutionResult with actual execution outcomes
        """
        try:
            # Extract entrypoint from artifact DNA
            entrypoint = artifact.capability_dna.runtime_entrypoint
            implementation_path = artifact.implementation_path

            if mode == "test":
                # Run tests using pytest if implementation exists
                if implementation_path and implementation_path.exists():
                    # Run pytest in the implementation directory
                    # Implementation parent dir goes on PYTHONPATH so the
                    # capability package is importable from its tests.
                    import os

                    env = self._clean_env()
                    env["PYTHONPATH"] = str(implementation_path)
                    result = subprocess.run(
                        ["python", "-m", "pytest", str(implementation_path), "-v", "--tb=short"],
                        capture_output=True,
                        text=True,
                        timeout=self.timeout,
                        check=False,
                        shell=False,  # NEVER use shell=True
                        env=env,
                    )
                else:
                    # No implementation to test
                    return ExecutionResult(
                        success=False,
                        stdout="",
                        stderr="No implementation path for testing",
                        returncode=-1,
                        metadata={
                            "mode": mode,
                            "backend": "subprocess",
                            "error": "no_implementation",
                        },
                    )
            else:
                # Run capability via Python entrypoint
                # Parse entrypoint: "module:function"
                if ":" not in entrypoint:
                    return ExecutionResult(
                        success=False,
                        stdout="",
                        stderr=f"Invalid entrypoint format: {entrypoint}. Expected 'module:function'",
                        returncode=-1,
                        metadata={
                            "mode": mode,
                            "backend": "subprocess",
                            "error": "invalid_entrypoint",
                        },
                    )

                module_name, function_name = entrypoint.split(":", 1)

                # Build Python execution command
                # Use -c to import and call the function
                python_code = f"from {module_name} import {function_name}; {function_name}()"

                cmd = ["python", "-c", python_code]

                # If implementation_path exists, set PYTHONPATH to include it
                env = None
                if implementation_path and implementation_path.exists():
                    import os

                    env = os.environ.copy()
                    # For directory, add parent so Python can import the module by name
                    # For file, add the file's parent directory
                    if implementation_path.is_dir():
                        env["PYTHONPATH"] = str(implementation_path.parent)
                    else:
                        env["PYTHONPATH"] = str(implementation_path.parent)

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                    check=False,
                    shell=False,  # NEVER use shell=True
                    env=env,
                )

            return ExecutionResult(
                success=result.returncode == 0,
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
                metadata={
                    "mode": mode,
                    "backend": "subprocess",
                    "entrypoint": entrypoint if mode == "run" else "pytest",
                },
            )

        except subprocess.TimeoutExpired:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution timeout after {self.timeout}s",
                returncode=-1,
                metadata={"mode": mode, "backend": "subprocess", "timeout": True},
            )
        except Exception as e:
            return ExecutionResult(
                success=False,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                returncode=-1,
                metadata={"mode": mode, "backend": "subprocess", "error": str(e)},
            )
