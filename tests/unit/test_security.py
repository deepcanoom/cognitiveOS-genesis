"""
Tests for Security Gates

Tests approval gate and approval providers.
"""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

from genesis.capabilities.artifact import CapabilityArtifact
from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.evaluation.evaluator import EvaluationResult
from genesis.security.gates import (
    ApprovalDecision,
    ApprovalGate,
    InteractiveApprovalProvider,
    TestApprovalProvider,
)


@pytest.fixture
def sample_artifact():
    """Create a sample artifact for testing."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test-capability",
        version="0.1.0",
        description="Test capability",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
        permissions={
            "filesystem.read": False,
            "filesystem.write": False,
            "network.outbound": False,
            "process.spawn": False,
        },
    )

    return CapabilityArtifact.build(capability_dna=capability, implementation_path=None)


@pytest.fixture
def sample_evaluation():
    """Create a sample evaluation result."""
    return EvaluationResult(
        score=95, passed=True, test_results={"status": "passed", "test_count": 10}, issues=[]
    )


def test_approval_decision_creation():
    """Test ApprovalDecision dataclass."""
    decision = ApprovalDecision(approved=True, reason="Test approval", actor="test:automated")

    assert decision.approved is True
    assert decision.reason == "Test approval"
    assert decision.actor == "test:automated"


def test_test_approval_provider_approves(sample_artifact, sample_evaluation):
    """Test TestApprovalProvider auto-approves with test actor."""
    provider = TestApprovalProvider()
    decision = provider.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True
    assert decision.actor == "test:automated"
    assert "testing" in decision.reason.lower() or "demo" in decision.reason.lower()


def test_interactive_approval_provider_approve(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider with yes response."""
    provider = InteractiveApprovalProvider(reviewer_identity="human:test@example.com")

    with patch("builtins.input", return_value="yes"):
        decision = provider.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True
    assert decision.actor == "human:test@example.com"
    assert "Approved by human" in decision.reason


def test_interactive_approval_provider_reject(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider with no response."""
    provider = InteractiveApprovalProvider(reviewer_identity="human:test@example.com")

    with patch("builtins.input", side_effect=["no", "Security concerns"]):
        decision = provider.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is False
    assert decision.actor == "human:test@example.com"
    assert "Security concerns" in decision.reason


def test_interactive_approval_provider_retry_on_invalid(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider retries on invalid input."""
    provider = InteractiveApprovalProvider()

    # First input invalid, second input valid
    with patch("builtins.input", side_effect=["maybe", "invalid", "yes"]):
        decision = provider.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True


def test_interactive_approval_provider_default_identity(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider uses default identity."""
    provider = InteractiveApprovalProvider()

    with patch("builtins.input", return_value="yes"):
        decision = provider.request_approval(sample_artifact, sample_evaluation)

    assert decision.actor == "human:operator"


def test_approval_gate_default_provider(sample_artifact, sample_evaluation):
    """Test ApprovalGate uses TestApprovalProvider by default."""
    gate = ApprovalGate()
    decision = gate.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True
    assert decision.actor == "test:automated"


def test_approval_gate_with_test_provider(sample_artifact, sample_evaluation):
    """Test ApprovalGate with explicit TestApprovalProvider."""
    provider = TestApprovalProvider()
    gate = ApprovalGate(provider=provider)

    decision = gate.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True
    assert decision.actor == "test:automated"


def test_approval_gate_with_interactive_provider(sample_artifact, sample_evaluation):
    """Test ApprovalGate with InteractiveApprovalProvider."""
    provider = InteractiveApprovalProvider(reviewer_identity="human:alice@example.com")
    gate = ApprovalGate(provider=provider)

    with patch("builtins.input", return_value="yes"):
        decision = gate.request_approval(sample_artifact, sample_evaluation)

    assert decision.approved is True
    assert decision.actor == "human:alice@example.com"


def test_approval_gate_delegates_to_provider(sample_artifact, sample_evaluation):
    """Test ApprovalGate properly delegates to provider."""
    # Mock provider
    mock_provider = MagicMock()
    mock_provider.request_approval.return_value = ApprovalDecision(
        approved=False, reason="Mock rejection", actor="mock:provider"
    )

    gate = ApprovalGate(provider=mock_provider)
    decision = gate.request_approval(sample_artifact, sample_evaluation)

    # Verify delegation
    mock_provider.request_approval.assert_called_once_with(sample_artifact, sample_evaluation)
    assert decision.approved is False
    assert decision.actor == "mock:provider"


def test_interactive_provider_displays_capability_info(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider displays capability information."""
    provider = InteractiveApprovalProvider()

    with patch("builtins.print") as mock_print, patch("builtins.input", return_value="yes"):
        provider.request_approval(sample_artifact, sample_evaluation)

    # Verify information was displayed
    print_calls = [str(call) for call in mock_print.call_args_list]
    output = " ".join(print_calls)

    assert "test-capability@0.1.0" in output
    assert "95" in output  # evaluation score


def test_interactive_provider_shows_permissions(sample_artifact, sample_evaluation):
    """Test InteractiveApprovalProvider displays permission details."""
    # Create artifact with some permissions enabled
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="network-capability",
        version="0.1.0",
        description="Capability with network access",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
        permissions={
            "filesystem.read": True,
            "filesystem.write": False,
            "network.outbound": True,
            "process.spawn": False,
        },
    )

    artifact = CapabilityArtifact.build(capability_dna=capability, implementation_path=None)

    provider = InteractiveApprovalProvider()

    with patch("builtins.print") as mock_print, patch("builtins.input", return_value="yes"):
        provider.request_approval(artifact, sample_evaluation)

    # Verify permissions were shown
    print_calls = [str(call) for call in mock_print.call_args_list]
    output = " ".join(print_calls)

    assert "Filesystem Read" in output
    assert "Network Outbound" in output


def test_actor_prefix_distinguishes_approval_types():
    """Test actor prefixes clearly distinguish approval types."""
    # Test provider uses "test:" prefix
    test_decision = ApprovalDecision(approved=True, reason="Test", actor="test:automated")
    assert test_decision.actor.startswith("test:")

    # Human provider uses "human:" prefix
    human_decision = ApprovalDecision(
        approved=True, reason="Human approved", actor="human:alice@example.com"
    )
    assert human_decision.actor.startswith("human:")

    # This prevents confusion between automated and human approval
    assert test_decision.actor != human_decision.actor
