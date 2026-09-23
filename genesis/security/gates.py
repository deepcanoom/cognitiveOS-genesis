"""
Approval Gates - Human-in-the-loop governance.

Design: v0.1 ALL capabilities require approval.
Future: Policy-based risk assessment.
"""

from dataclasses import dataclass
from typing import Any


@dataclass
class ApprovalDecision:
    """Result of approval request."""

    approved: bool
    reason: str
    actor: str


class ApprovalGate:
    """
    Human approval checkpoint.

    v0.1: ALL capabilities require explicit human approval.
    No automated approval.
    """

    def request_approval(
        self,
        artifact: Any,  # CapabilityArtifact
        evaluation: Any  # EvaluationResult
    ) -> ApprovalDecision:
        """
        Request human approval for capability registration.

        v0.1: Always returns pending approval (simulated).
        Real implementation would prompt human reviewer.
        """
        # Simulate automatic approval for v0.1 demo
        # Real implementation: interactive prompt or API call
        return ApprovalDecision(
            approved=True,
            reason="Approved for v0.1 demonstration",
            actor="system"
        )
