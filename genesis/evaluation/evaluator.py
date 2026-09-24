"""
Capability Evaluator

Assesses capability quality and readiness.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class EvaluationResult:
    """Result of capability evaluation."""

    passed: bool
    score: int  # 0-100
    test_results: dict[str, Any]
    issues: list[str]

    @classmethod
    def success(cls, score: int = 100) -> "EvaluationResult":
        """Create successful evaluation."""
        return cls(passed=True, score=score, test_results={"status": "passed"}, issues=[])


class Evaluator:
    """
    Evaluates capability quality.

    v0.1: Basic test result assessment.
    Future: Behavioral analysis, performance benchmarks.
    """

    def evaluate(
        self,
        artifact: Any,  # CapabilityArtifact
        execution_result: Any,  # ExecutionResult
    ) -> EvaluationResult:
        """
        Evaluate capability based on test execution.

        v0.1: Simple pass/fail based on test results.
        """
        if execution_result.success:
            return EvaluationResult.success(score=100)
        else:
            return EvaluationResult(
                passed=False,
                score=0,
                test_results={"status": "failed", "error": execution_result.stderr},
                issues=[execution_result.stderr],
            )
