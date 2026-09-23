"""Tests for Capability manifest model."""

from datetime import datetime

import pytest

from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.planning.plan import CapabilityPlan, CapabilityType, PermissionSet, RuntimeSpec


def test_provenance_creation() -> None:
    """Test provenance creation with typed creator."""
    prov = Provenance(
        created_by=CreatorType.GENESIS,
        created_at=datetime(2026, 9, 23, 10, 30, 0),
        parent_capabilities=[]
    )
    
    assert prov.created_by == CreatorType.GENESIS
    assert prov.created_at.year == 2026
    assert prov.parent_capabilities == []


def test_provenance_typed_creator_prevents_arbitrary_strings() -> None:
    """Test that creator must be CreatorType enum."""
    with pytest.raises((ValueError, TypeError)):
        Provenance(
            created_by="pepe123",  # type: ignore
            created_at=datetime.now(),
            parent_capabilities=[]
        )


def test_provenance_parent_validation() -> None:
    """Test parent capability reference validation."""
    with pytest.raises(ValueError, match="Invalid parent capability reference"):
        Provenance(
            created_by=CreatorType.HUMAN,
            created_at=datetime.now(),
            parent_capabilities=["invalid-format"]  # Missing @version
        )


def test_capability_creation() -> None:
    """Test basic capability creation."""
    prov = Provenance(
        created_by=CreatorType.HUMAN,
        created_at=datetime.now(),
        parent_capabilities=[]
    )
    
    cap = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test-capability",
        version="0.1.0",
        description="Test capability",
        provenance=prov,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test.main:execute",
        runtime_version_constraint=">=3.11",
        permissions={
            "filesystem": {"read": False, "write": False},
            "network": {"outbound": False},
            "process": {"spawn": False}
        }
    )
    
    assert cap.name == "test-capability"
    assert cap.version == "0.1.0"
    assert cap.capability_id == "test-capability@0.1.0"


def test_capability_invalid_api_version() -> None:
    """Test that invalid API version is rejected."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    with pytest.raises(ValueError, match="Unsupported API version"):
        Capability(
            api_version="invalid/v1",
            kind="Capability",
            name="test",
            version="0.1.0",
            description="Test",
            provenance=prov,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="test:main",
            runtime_version_constraint=None
        )


def test_capability_invalid_name() -> None:
    """Test that invalid names are rejected."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    with pytest.raises(ValueError, match="Invalid capability name"):
        Capability(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name="Invalid Name With Spaces",
            version="0.1.0",
            description="Test",
            provenance=prov,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="test:main",
            runtime_version_constraint=None
        )


def test_capability_invalid_version() -> None:
    """Test that invalid versions are rejected."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    with pytest.raises(ValueError, match="Invalid version"):
        Capability(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name="test",
            version="1.0",  # Not semantic version
            description="Test",
            provenance=prov,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="test:main",
            runtime_version_constraint=None
        )


def test_capability_invalid_entrypoint() -> None:
    """Test that invalid entrypoints are rejected."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    with pytest.raises(ValueError, match="Invalid entrypoint"):
        Capability(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name="test",
            version="0.1.0",
            description="Test",
            provenance=prov,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="python main.py",  # Shell command, not module:function
            runtime_version_constraint=None
        )


def test_capability_self_reference_rejected() -> None:
    """Test that self-referential dependencies are rejected."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    with pytest.raises(ValueError, match="cannot depend on itself"):
        Capability(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name="test-cap",
            version="0.1.0",
            description="Test",
            provenance=prov,
            capability_type="simple",
            runtime_type="python",
            runtime_entrypoint="test:main",
            runtime_version_constraint=None,
            dependencies={"capabilities": ["test-cap@0.1.0"]}
        )


def test_capability_from_plan() -> None:
    """Test creating Capability from CapabilityPlan."""
    plan = CapabilityPlan(
        name="hello-world",
        version="0.1.0",
        description="Greeting capability",
        capability_type=CapabilityType.SIMPLE,
        runtime=RuntimeSpec(
            type="python",
            entrypoint="hello.main:greet",
            version_constraint=">=3.11"
        ),
        permissions=PermissionSet(),
        dependencies=[]
    )
    
    prov = Provenance(CreatorType.GENESIS, datetime.now(), [])
    
    capability = Capability.from_plan(plan, prov)
    
    assert capability.name == "hello-world"
    assert capability.version == "0.1.0"
    assert capability.runtime_type == "python"
    assert capability.runtime_entrypoint == "hello.main:greet"
    assert capability.provenance.created_by == CreatorType.GENESIS


def test_capability_to_dict_roundtrip() -> None:
    """Test serialization/deserialization roundtrip."""
    prov = Provenance(CreatorType.HUMAN, datetime.now(), [])
    
    original = Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name="test",
        version="0.1.0",
        description="Test capability",
        provenance=prov,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="test:main",
        runtime_version_constraint=">=3.11"
    )
    
    # Serialize
    data = original.to_dict()
    
    # Deserialize
    restored = Capability.from_dict(data)
    
    assert restored.name == original.name
    assert restored.version == original.version
    assert restored.capability_id == original.capability_id
