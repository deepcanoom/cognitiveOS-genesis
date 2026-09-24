"""
Tests for Capability Artifact

Tests artifact construction, integrity verification, and metadata.
"""

from datetime import datetime
from pathlib import Path

import pytest

from genesis.capabilities.artifact import ArtifactMetadata, CapabilityArtifact
from genesis.capabilities.manifest import Capability, CreatorType, Provenance


@pytest.fixture
def sample_capability():
    """Create a sample capability for testing."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    return Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test-capability",
        version="0.1.0",
        description="Test capability for artifact tests",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test_module:main",
        runtime_version_constraint=">=3.8",
    )


def test_artifact_metadata_creation():
    """Test ArtifactMetadata construction."""
    metadata = ArtifactMetadata(
        artifact_id="test@1.0.0",
        created_at=datetime.now(),
        size_bytes=1024,
        checksums={"sha256": "abc123"},
    )

    assert metadata.artifact_id == "test@1.0.0"
    assert metadata.size_bytes == 1024
    assert metadata.checksums["sha256"] == "abc123"


def test_artifact_metadata_serialization():
    """Test ArtifactMetadata to_dict/from_dict roundtrip."""
    metadata = ArtifactMetadata(
        artifact_id="test@1.0.0",
        created_at=datetime(2024, 1, 1, 12, 0, 0),
        size_bytes=2048,
        checksums={"sha256": "def456"},
        evaluation_results={"score": 95},
    )

    data = metadata.to_dict()

    assert data["artifactId"] == "test@1.0.0"
    assert data["sizeBytes"] == 2048
    assert data["checksums"]["sha256"] == "def456"
    assert data["evaluationResults"]["score"] == 95

    # Roundtrip
    restored = ArtifactMetadata.from_dict(data)
    assert restored.artifact_id == metadata.artifact_id
    assert restored.size_bytes == metadata.size_bytes
    assert restored.checksums == metadata.checksums
    assert restored.evaluation_results == metadata.evaluation_results


def test_artifact_build_with_implementation(sample_capability):
    """Test building artifact with real implementation."""
    impl_path = Path("capabilities/examples/hello_world")

    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability,
        implementation_path=impl_path,
        evaluation_results={"test_passed": True},
    )

    assert artifact.artifact_id == "test-capability@0.1.0"
    assert artifact.name == "test-capability"
    assert artifact.version == "0.1.0"
    assert artifact.implementation_path == impl_path
    assert artifact.metadata.size_bytes > 0
    assert "sha256" in artifact.metadata.checksums
    assert len(artifact.metadata.checksums["sha256"]) == 64  # SHA256 hex length
    assert artifact.metadata.evaluation_results["test_passed"] is True


def test_artifact_build_without_implementation(sample_capability):
    """Test building artifact without implementation."""
    artifact = CapabilityArtifact.build(capability_dna=sample_capability, implementation_path=None)

    assert artifact.artifact_id == "test-capability@0.1.0"
    assert artifact.implementation_path is None
    assert artifact.metadata.size_bytes == 0
    assert len(artifact.metadata.checksums) == 0


def test_artifact_verify_integrity_success(sample_capability):
    """Test integrity verification succeeds for valid artifact."""
    impl_path = Path("capabilities/examples/hello_world")

    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=impl_path
    )

    # Should verify successfully
    assert artifact.verify_integrity() is True


def test_artifact_verify_integrity_no_implementation(sample_capability):
    """Test integrity verification fails when no implementation."""
    artifact = CapabilityArtifact.build(capability_dna=sample_capability, implementation_path=None)

    # Should fail - no implementation to verify
    assert artifact.verify_integrity() is False


def test_artifact_verify_integrity_missing_path(sample_capability):
    """Test integrity verification fails when implementation path doesn't exist."""
    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=Path("nonexistent/path")
    )

    # Should fail - path doesn't exist
    assert artifact.verify_integrity() is False


def test_artifact_verify_integrity_no_checksum(sample_capability):
    """Test integrity verification with no checksum."""
    impl_path = Path("capabilities/examples/hello_world")

    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=impl_path
    )

    # Clear checksums
    artifact.metadata.checksums.clear()

    # Should pass when no checksum to verify
    assert artifact.verify_integrity() is True


def test_artifact_id_mismatch_raises_error(sample_capability):
    """Test artifact construction fails when IDs don't match."""
    metadata = ArtifactMetadata(
        artifact_id="wrong-name@1.0.0",  # Doesn't match capability
        created_at=datetime.now(),
        size_bytes=0,
    )

    with pytest.raises(ValueError, match="Artifact ID mismatch"):
        CapabilityArtifact(
            capability_dna=sample_capability, implementation_path=None, metadata=metadata
        )


def test_artifact_properties(sample_capability):
    """Test artifact property accessors."""
    artifact = CapabilityArtifact.build(capability_dna=sample_capability, implementation_path=None)

    assert artifact.artifact_id == "test-capability@0.1.0"
    assert artifact.name == "test-capability"
    assert artifact.version == "0.1.0"


def test_artifact_to_dict(sample_capability):
    """Test artifact serialization to dict."""
    impl_path = Path("capabilities/examples/hello_world")

    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=impl_path
    )

    data = artifact.to_dict()

    assert "capability" in data
    assert "implementation" in data
    assert "metadata" in data

    # Capability DNA has nested metadata structure
    assert data["capability"]["metadata"]["name"] == "test-capability"
    assert data["implementation"]["path"] == str(impl_path)
    assert data["metadata"]["artifactId"] == "test-capability@0.1.0"
    assert data["metadata"]["sizeBytes"] > 0


def test_artifact_repr(sample_capability):
    """Test artifact string representation."""
    artifact = CapabilityArtifact.build(capability_dna=sample_capability, implementation_path=None)

    repr_str = repr(artifact)
    assert "CapabilityArtifact" in repr_str
    assert "test-capability@0.1.0" in repr_str


def test_artifact_checksum_deterministic(sample_capability):
    """Test that checksums are deterministic for same content."""
    impl_path = Path("capabilities/examples/hello_world")

    # Build two artifacts from same implementation
    artifact1 = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=impl_path
    )

    artifact2 = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=impl_path
    )

    # Checksums should be identical
    assert artifact1.metadata.checksums == artifact2.metadata.checksums
    assert artifact1.metadata.size_bytes == artifact2.metadata.size_bytes


def test_artifact_evaluation_results(sample_capability):
    """Test artifact stores evaluation results."""
    eval_results = {"score": 95, "passed": True, "issues": [], "test_count": 10}

    artifact = CapabilityArtifact.build(
        capability_dna=sample_capability, implementation_path=None, evaluation_results=eval_results
    )

    assert artifact.metadata.evaluation_results == eval_results
    assert artifact.metadata.evaluation_results["score"] == 95
    assert artifact.metadata.evaluation_results["test_count"] == 10


def test_artifact_tamper_detection(tmp_path: Path):
    """Modified artifact content must cause integrity verification failure.

    Security invariant: any change to packaged implementation bytes is
    detectable through the SHA256 checksum.
    """
    # Create a small implementation in a temp dir
    impl_dir = tmp_path / "impl"
    impl_dir.mkdir()
    (impl_dir / "main.py").write_text("RESULT = 'original'", encoding="utf-8")

    provenance = Provenance(
        created_by=CreatorType.GENESIS,
        created_at=datetime.now(),
        parent_capabilities=[],
    )
    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="tamper-test",
        version="0.1.0",
        description="Tamper detection test",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="main:execute",
        runtime_version_constraint=">=3.8",
    )

    artifact = CapabilityArtifact.build(
        capability_dna=capability,
        implementation_path=impl_dir,
    )
    assert artifact.verify_integrity() is True

    # Tamper: modify the implementation content
    (impl_dir / "main.py").write_text("RESULT = 'tampered'", encoding="utf-8")

    assert artifact.verify_integrity() is False
