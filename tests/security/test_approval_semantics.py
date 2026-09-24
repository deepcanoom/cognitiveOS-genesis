"""
Security tests: Approval semantics.

Verifies that approval actors are explicit and that test/simulated
approval is never represented as human approval.
"""

from datetime import datetime

from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.security.gates import (
    ApprovalGate,
    InteractiveApprovalProvider,
    TestApprovalProvider,
)


def make_artifact_stub():
    provenance = Provenance(
        created_by=CreatorType.GENESIS,
        created_at=datetime.now(),
        parent_capabilities=[],
    )
    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="sec-test",
        version="0.1.0",
        description="Security test capability",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="sec_test:main",
        runtime_version_constraint=">=3.11",
    )

    class StubEvaluation:
        score = 90
        passed = True
        issues: list[str] = []

    class StubArtifact:
        artifact_id = "sec-test@0.1.0"
        capability_dna = capability

    return StubArtifact(), StubEvaluation()


def test_test_provider_actor_is_explicitly_test():
    """TestApprovalProvider must identify as test, never as human."""
    provider = TestApprovalProvider()
    artifact, evaluation = make_artifact_stub()
    decision = provider.request_approval(artifact, evaluation)

    assert decision.approved is True
    assert decision.actor.startswith("test:")
    assert not decision.actor.startswith("human")


def test_interactive_provider_actor_is_human(monkeypatch):
    """InteractiveApprovalProvider records a human actor."""
    provider = InteractiveApprovalProvider(reviewer_identity="human:alice@example.com")
    artifact, evaluation = make_artifact_stub()

    # Simulate 'y' at the approval prompt
    monkeypatch.setattr("builtins.input", lambda _prompt: "y")
    decision = provider.request_approval(artifact, evaluation)

    assert decision.approved is True
    assert decision.actor == "human:alice@example.com"
    assert decision.actor.startswith("human:")


def test_interactive_provider_rejection_records_reason(monkeypatch):
    """Rejection requires a reason and records human actor."""
    provider = InteractiveApprovalProvider()
    artifact, evaluation = make_artifact_stub()

    responses = iter(["n", "suspicious permissions"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))
    decision = provider.request_approval(artifact, evaluation)

    assert decision.approved is False
    assert decision.reason == "suspicious permissions"
    assert decision.actor.startswith("human:")


def test_interactive_provider_rejects_invalid_input_then_accepts(monkeypatch):
    """Invalid input loops until a valid yes/no answer."""
    provider = InteractiveApprovalProvider()
    artifact, evaluation = make_artifact_stub()

    responses = iter(["maybe", "y"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(responses))
    decision = provider.request_approval(artifact, evaluation)

    assert decision.approved is True


def test_approval_gate_delegates_to_provider():
    """ApprovalGate passes through the provider's decision unchanged."""
    gate = ApprovalGate(provider=TestApprovalProvider())
    artifact, evaluation = make_artifact_stub()
    decision = gate.request_approval(artifact, evaluation)
    assert decision.actor == "test:automated"


def test_approval_gate_default_is_test_provider():
    """Default provider is test provider (safe default for demos/tests only)."""
    gate = ApprovalGate()
    artifact, evaluation = make_artifact_stub()
    decision = gate.request_approval(artifact, evaluation)
    assert decision.actor.startswith("test:")
