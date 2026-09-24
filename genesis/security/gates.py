"""
Approval Gates - Human-in-the-loop governance.

Design: v0.1 ALL capabilities require approval.
Future: Policy-based risk assessment.
"""

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ApprovalDecision:
    """Result of approval request."""

    approved: bool
    reason: str
    actor: str  # Identity of approver (e.g., "human:alice@example.com", "test:automated")


class ApprovalProvider(Protocol):
    """
    Protocol for approval decision providers.

    Design: Abstraction allows different approval strategies:
    - Interactive (CLI prompt)
    - API-based (webhook, approval service)
    - Test/Demo (automated for testing)
    """

    def request_approval(
        self,
        artifact: Any,  # CapabilityArtifact
        evaluation: Any,  # EvaluationResult
    ) -> ApprovalDecision:
        """Request approval decision."""
        ...


class TestApprovalProvider:
    """
    Automated approval provider for testing and demos.

    IMPORTANT: This is for testing only.
    Actor is marked as "test:automated" to distinguish from human approval.
    """

    def request_approval(self, artifact: Any, evaluation: Any) -> ApprovalDecision:
        """Auto-approve for testing/demo with clear test actor."""
        return ApprovalDecision(
            approved=True, reason="Auto-approved for testing/demo", actor="test:automated"
        )


class InteractiveApprovalProvider:
    """
    Interactive CLI approval provider for human review.

    Design: Prompts human operator via CLI for explicit approval.
    Actor recorded with human: prefix to distinguish from automated.
    """

    def __init__(self, reviewer_identity: str = "human:operator"):
        """
        Initialize interactive provider.

        Args:
            reviewer_identity: Identity of human reviewer (e.g., "human:alice@example.com")
        """
        self.reviewer_identity = reviewer_identity

    def request_approval(self, artifact: Any, evaluation: Any) -> ApprovalDecision:
        """
        Prompt human for approval via CLI.

        Design: Interactive prompt with capability details.
        v0.1: Basic CLI prompt. Future: rich terminal UI.
        """
        print("\n" + "=" * 70)
        print("CAPABILITY APPROVAL REQUEST")
        print("=" * 70)
        print(f"\nCapability: {artifact.artifact_id}")
        print(f"Type: {artifact.capability_dna.capability_type}")
        print(f"Description: {artifact.capability_dna.description}")
        print(f"\nEvaluation Score: {evaluation.score}/100")
        print(f"Evaluation Status: {'PASSED' if evaluation.passed else 'FAILED'}")

        if evaluation.issues:
            print(f"\nIssues Found: {len(evaluation.issues)}")
            for issue in evaluation.issues:
                print(f"  - {issue}")

        print("\nPermissions Requested:")
        perms = artifact.capability_dna.permissions
        print(f"  - Filesystem Read: {perms.get('filesystem.read', False)}")
        print(f"  - Filesystem Write: {perms.get('filesystem.write', False)}")
        print(f"  - Network Outbound: {perms.get('network.outbound', False)}")
        print(f"  - Process Spawn: {perms.get('process.spawn', False)}")

        print("\n" + "=" * 70)

        # Prompt for approval
        while True:
            response = input("\nApprove this capability? [yes/no]: ").strip().lower()
            if response in ("yes", "y"):
                return ApprovalDecision(
                    approved=True, reason="Approved by human operator", actor=self.reviewer_identity
                )
            elif response in ("no", "n"):
                reason = input("Rejection reason: ").strip()
                return ApprovalDecision(
                    approved=False,
                    reason=reason or "Rejected by human operator",
                    actor=self.reviewer_identity,
                )
            else:
                print("Please enter 'yes' or 'no'")


class ApprovalGate:
    """
    Human approval checkpoint.

    v0.1: ALL capabilities require explicit approval.
    No automated approval in production.

    Design: Accepts ApprovalProvider to support different approval strategies
    (interactive, API-based, test/demo).
    """

    def __init__(self, provider: ApprovalProvider | None = None):
        """
        Initialize approval gate with provider.

        Args:
            provider: Approval decision provider. If None, uses TestApprovalProvider.
        """
        self.provider = provider or TestApprovalProvider()

    def request_approval(
        self,
        artifact: Any,  # CapabilityArtifact
        evaluation: Any,  # EvaluationResult
    ) -> ApprovalDecision:
        """
        Request approval via configured provider.

        v0.1: Delegates to provider (test/demo or human).
        Future: Add policy-based risk assessment.
        """
        return self.provider.request_approval(artifact, evaluation)
