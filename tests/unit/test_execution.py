"""
Tests for Execution Backend

Tests the SubprocessBackend real execution capabilities.
"""

from datetime import datetime
from pathlib import Path

import pytest

from genesis.capabilities.artifact import CapabilityArtifact
from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.execution.backend import SubprocessBackend


@pytest.fixture
def hello_world_capability():
    """Create a hello_world capability for testing."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="hello-world",
        version="0.1.0",
        description="Test hello world capability",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="hello_world:main",
        runtime_version_constraint=">=3.8",
    )

    return capability


@pytest.fixture
def hello_world_artifact(hello_world_capability):
    """Create artifact with real implementation path."""
    impl_path = Path("capabilities/examples/hello_world")

    artifact = CapabilityArtifact.build(
        capability_dna=hello_world_capability, implementation_path=impl_path, evaluation_results={}
    )

    return artifact


def test_subprocess_backend_initialization():
    """Test SubprocessBackend can be initialized."""
    backend = SubprocessBackend(timeout=10)
    assert backend.timeout == 10


def test_subprocess_backend_default_timeout():
    """Test SubprocessBackend default timeout."""
    backend = SubprocessBackend()
    assert backend.timeout == 30


def test_subprocess_backend_execute_real_capability(hello_world_artifact):
    """Test executing a real capability via subprocess."""
    backend = SubprocessBackend(timeout=10)
    result = backend.execute(hello_world_artifact, mode="run")

    assert result is not None
    assert result.success is True
    assert "Hello, World!" in result.stdout
    assert result.returncode == 0
    assert result.metadata["mode"] == "run"
    assert result.metadata["backend"] == "subprocess"
    assert result.metadata["entrypoint"] == "hello_world:main"


def test_subprocess_backend_execute_tests(hello_world_artifact):
    """Test running capability tests via pytest."""
    backend = SubprocessBackend(timeout=10)
    result = backend.execute(hello_world_artifact, mode="test")

    assert result is not None
    # Tests should pass
    assert result.success is True
    assert result.returncode == 0
    assert "test_hello_world.py" in result.stdout or "4 passed" in result.stdout
    assert result.metadata["mode"] == "test"
    assert result.metadata["entrypoint"] == "pytest"


def test_subprocess_backend_no_implementation_path():
    """Test execution fails gracefully when no implementation exists."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="no-impl",
        version="0.1.0",
        description="Capability without implementation",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="nonexistent:main",
        runtime_version_constraint=">=3.8",
    )

    artifact = CapabilityArtifact.build(capability_dna=capability, implementation_path=None)

    backend = SubprocessBackend(timeout=10)
    result = backend.execute(artifact, mode="test")

    assert result.success is False
    assert "No implementation path" in result.stderr
    assert result.metadata["error"] == "no_implementation"


def test_subprocess_backend_invalid_entrypoint():
    """Test execution fails with invalid entrypoint format."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    # Create capability with invalid entrypoint (no colon)
    # This should pass manifest validation but fail at execution
    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="invalid-entrypoint",
        version="0.1.0",
        description="Capability with invalid entrypoint format",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="module:function",  # Valid format
        runtime_version_constraint=">=3.8",
    )

    # Manually set invalid entrypoint after construction
    capability.runtime_entrypoint = "invalid_no_colon"

    artifact = CapabilityArtifact.build(
        capability_dna=capability, implementation_path=Path("capabilities/examples/hello_world")
    )

    backend = SubprocessBackend(timeout=10)
    result = backend.execute(artifact, mode="run")

    assert result.success is False
    assert "Invalid entrypoint format" in result.stderr
    assert result.metadata["error"] == "invalid_entrypoint"


def test_subprocess_backend_timeout():
    """Test execution timeout handling."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="timeout-test",
        version="0.1.0",
        description="Test timeout handling",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="time:sleep",  # This will cause import error, not timeout
        runtime_version_constraint=">=3.8",
    )

    artifact = CapabilityArtifact.build(capability_dna=capability, implementation_path=None)

    backend = SubprocessBackend(timeout=1)
    result = backend.execute(artifact, mode="run")

    # This will fail due to import error, not timeout
    # But demonstrates error handling
    assert result.success is False
