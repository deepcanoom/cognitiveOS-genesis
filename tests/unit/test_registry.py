"""
Tests for Capability Registry

Tests registry storage, retrieval, and index management.
"""

import json
from datetime import datetime
from pathlib import Path

import pytest

from genesis.capabilities.artifact import CapabilityArtifact
from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.capabilities.registry import CapabilityRegistry, RegistryMetadata


@pytest.fixture
def temp_registry(tmp_path):
    """Create a temporary registry for testing."""
    registry_path = tmp_path / "test_registry"
    return CapabilityRegistry(registry_path=registry_path)


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
        description="Test capability for registry",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
    )

    return CapabilityArtifact.build(capability_dna=capability, implementation_path=None)


def test_registry_metadata_creation():
    """Test RegistryMetadata creation."""
    metadata = RegistryMetadata(total_capabilities=10, last_updated="2024-01-01T00:00:00")

    assert metadata.total_capabilities == 10
    assert metadata.last_updated == "2024-01-01T00:00:00"
    assert metadata.registry_version == "0.1.0"


def test_registry_metadata_to_dict():
    """Test RegistryMetadata serialization."""
    metadata = RegistryMetadata(
        total_capabilities=5, last_updated="2024-01-01T00:00:00", registry_version="0.2.0"
    )

    data = metadata.to_dict()

    assert data["totalCapabilities"] == 5
    assert data["lastUpdated"] == "2024-01-01T00:00:00"
    assert data["registryVersion"] == "0.2.0"


def test_registry_initialization(temp_registry):
    """Test registry initialization creates directory structure."""
    assert temp_registry.registry_path.exists()
    assert temp_registry.registry_path.is_dir()


def test_registry_default_path():
    """Test registry uses default path when none specified."""
    registry = CapabilityRegistry()
    assert registry.registry_path == Path("capabilities/registry")


def test_register_artifact(temp_registry, sample_artifact):
    """Test registering a capability artifact."""
    temp_registry.register(sample_artifact)

    # Verify artifact directory created
    artifact_dir = temp_registry.registry_path / sample_artifact.artifact_id
    assert artifact_dir.exists()

    # Verify files created
    assert (artifact_dir / "capability.yaml").exists()
    assert (artifact_dir / "artifact.yaml").exists()
    assert (artifact_dir / "provenance.json").exists()


def test_register_artifact_updates_index(temp_registry, sample_artifact):
    """Test registering artifact updates index."""
    temp_registry.register(sample_artifact)

    # Verify index updated
    assert sample_artifact.artifact_id in temp_registry._index["artifacts"]

    artifact_info = temp_registry._index["artifacts"][sample_artifact.artifact_id]
    assert artifact_info["name"] == "test-capability"
    assert artifact_info["version"] == "0.1.0"


def test_register_artifact_idempotent(temp_registry, sample_artifact):
    """Test re-registering same artifact is idempotent."""
    temp_registry.register(sample_artifact)

    # Re-register should not raise error
    temp_registry.register(sample_artifact)

    # Should still only have one entry
    assert len(temp_registry.list_artifacts()) == 1


def test_register_different_version_same_name(temp_registry):
    """Test registering different versions of same capability."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    # Register v0.1.0
    cap_v1 = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test-cap",
        version="0.1.0",
        description="Version 1",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
    )
    artifact_v1 = CapabilityArtifact.build(capability_dna=cap_v1)

    # Register v0.2.0
    cap_v2 = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test-cap",
        version="0.2.0",
        description="Version 2",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
    )
    artifact_v2 = CapabilityArtifact.build(capability_dna=cap_v2)

    temp_registry.register(artifact_v1)
    temp_registry.register(artifact_v2)

    # Should have both versions
    assert len(temp_registry.list_artifacts()) == 2
    assert temp_registry.exists("test-cap", "0.1.0")
    assert temp_registry.exists("test-cap", "0.2.0")


def test_register_with_implementation(temp_registry):
    """Test registering artifact with implementation."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="with-impl",
        version="0.1.0",
        description="Has implementation",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="hello_world:main",
        runtime_version_constraint=">=3.8",
    )

    impl_path = Path("capabilities/examples/hello_world")
    artifact = CapabilityArtifact.build(capability_dna=capability, implementation_path=impl_path)

    temp_registry.register(artifact)

    # Verify implementation copied
    artifact_dir = temp_registry.registry_path / artifact.artifact_id
    impl_dir = artifact_dir / "implementation"
    assert impl_dir.exists()
    assert (impl_dir / "__init__.py").exists()


def test_register_with_evaluation_results(temp_registry):
    """Test registering artifact with evaluation results."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="with-eval",
        version="0.1.0",
        description="Has evaluation",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.8",
    )

    eval_results = {"score": 95, "passed": True}
    artifact = CapabilityArtifact.build(capability_dna=capability, evaluation_results=eval_results)

    temp_registry.register(artifact)

    # Verify evaluation saved
    artifact_dir = temp_registry.registry_path / artifact.artifact_id
    eval_file = artifact_dir / "evaluation.json"
    assert eval_file.exists()

    with open(eval_file) as f:
        saved_eval = json.load(f)
    assert saved_eval["score"] == 95


def test_get_artifact(temp_registry, sample_artifact):
    """Test retrieving registered artifact."""
    temp_registry.register(sample_artifact)

    retrieved = temp_registry.get("test-capability", "0.1.0")

    assert retrieved is not None
    assert retrieved.artifact_id == sample_artifact.artifact_id
    assert retrieved.name == "test-capability"
    assert retrieved.version == "0.1.0"


def test_get_nonexistent_artifact(temp_registry):
    """Test getting non-existent artifact returns None."""
    result = temp_registry.get("nonexistent", "1.0.0")
    assert result is None


def test_exists(temp_registry, sample_artifact):
    """Test checking if artifact exists."""
    assert not temp_registry.exists("test-capability", "0.1.0")

    temp_registry.register(sample_artifact)

    assert temp_registry.exists("test-capability", "0.1.0")
    assert not temp_registry.exists("test-capability", "0.2.0")


def test_list_empty_registry(temp_registry):
    """Test listing empty registry."""
    capabilities = temp_registry.list_artifacts()
    assert capabilities == []


def test_list_registry(temp_registry, sample_artifact):
    """Test listing registered capabilities."""
    temp_registry.register(sample_artifact)

    capabilities = temp_registry.list_artifacts()

    assert len(capabilities) == 1
    assert capabilities[0]["name"] == "test-capability"
    assert capabilities[0]["version"] == "0.1.0"


def test_list_versions(temp_registry):
    """Test listing versions of a capability."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    # Register multiple versions
    for version in ["0.1.0", "0.2.0", "0.3.0"]:
        cap = Capability(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name="multi-version",
            version=version,
            description=f"Version {version}",
            provenance=provenance,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="test:main",
            runtime_version_constraint=">=3.8",
        )
        artifact = CapabilityArtifact.build(capability_dna=cap)
        temp_registry.register(artifact)

    versions = temp_registry.list_versions("multi-version")

    # Should be sorted newest first
    assert versions == ["0.3.0", "0.2.0", "0.1.0"]


def test_list_versions_nonexistent(temp_registry):
    """Test listing versions of non-existent capability."""
    versions = temp_registry.list_versions("nonexistent")
    assert versions == []


def test_index_persistence(temp_registry, sample_artifact):
    """Test index persists across registry instances."""
    temp_registry.register(sample_artifact)

    # Create new registry instance with same path
    new_registry = CapabilityRegistry(registry_path=temp_registry.registry_path)

    # Should load existing index
    assert new_registry.exists("test-capability", "0.1.0")
    assert len(new_registry.list_artifacts()) == 1


def test_index_rebuild_on_corruption(tmp_path, sample_artifact):
    """Test index rebuilds if corrupted."""
    registry_path = tmp_path / "test_registry"
    registry = CapabilityRegistry(registry_path=registry_path)

    # Register artifact
    registry.register(sample_artifact)

    # Corrupt index
    with open(registry.index_path, "w") as f:
        f.write("invalid json{{{")

    # Create new registry - should rebuild index
    new_registry = CapabilityRegistry(registry_path=registry_path)

    # Should still find the artifact via rebuild
    assert new_registry.exists("test-capability", "0.1.0")


def test_integrity_checksum_saved(temp_registry):
    """Test integrity checksums are saved."""
    provenance = Provenance(
        created_by=CreatorType.GENESIS, created_at=datetime.now(), parent_capabilities=[]
    )

    capability = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="with-checksum",
        version="0.1.0",
        description="Has checksum",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="hello_world:main",
        runtime_version_constraint=">=3.8",
    )

    impl_path = Path("capabilities/examples/hello_world")
    artifact = CapabilityArtifact.build(capability_dna=capability, implementation_path=impl_path)

    temp_registry.register(artifact)

    # Verify integrity file created
    artifact_dir = temp_registry.registry_path / artifact.artifact_id
    integrity_file = artifact_dir / "integrity.sha256"
    assert integrity_file.exists()

    # Verify checksum content
    with open(integrity_file) as f:
        content = f.read()
    assert "with-checksum@0.1.0" in content
    assert len(content.split()[0]) == 64  # SHA256 length
