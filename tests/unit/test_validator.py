"""
Tests for Capability Validator.

Tests layered validation: schema -> semantic -> security.
"""

from datetime import datetime
from pathlib import Path

import pytest

from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.capabilities.validator import (
    CapabilityValidator,
    ValidationResult,
    validate_capability,
)

DENY_ALL_PERMISSIONS = {
    "filesystem": {"read": False, "write": False},
    "network": {"outbound": False},
    "process": {"spawn": False},
}


@pytest.fixture
def validator() -> CapabilityValidator:
    return CapabilityValidator()


def make_capability(
    name: str = "greeting",
    permissions: dict | None = None,
    dependencies: dict | None = None,
    parents: list[str] | None = None,
    evaluation: dict | None = None,
) -> Capability:
    provenance = Provenance(
        created_by=CreatorType.GENESIS,
        created_at=datetime.now(),
        parent_capabilities=parents or [],
    )
    # Default: full deny-by-default permission structure (schema requires it)
    default_permissions = {
        "filesystem": {"read": False, "write": False},
        "network": {"outbound": False},
        "process": {"spawn": False},
    }
    default_evaluation = {
        "tests": [{"type": "unit", "path": "tests/unit"}],
        "approval_gates": [{"type": "human", "required": True}],
    }
    return Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name=name,
        version="0.1.0",
        description="Test capability",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint="greeting.main:execute",
        runtime_version_constraint=">=3.11",
        permissions=permissions if permissions is not None else default_permissions,
        dependencies=dependencies or {},
        evaluation=evaluation if evaluation is not None else default_evaluation,
    )


def test_valid_capability_passes(validator: CapabilityValidator):
    result = validator.validate(make_capability())
    assert result.valid is True
    assert bool(result) is True
    assert result.errors == []


def test_self_reference_in_dependencies_fails(validator: CapabilityValidator):
    """Self-reference normally rejected at construction; verify via corrupted object."""
    cap = make_capability()
    # Bypass __post_init__ check by mutating after construction
    cap.dependencies = {"requires": ["greeting@0.1.0"]}
    result = validator.validate(cap)
    assert result.valid is False
    assert any("Self-reference" in e for e in result.errors)


def test_invalid_parent_reference_format_fails(validator: CapabilityValidator):
    """Provenance rejects bad parent format at construction; verify that guard."""
    with pytest.raises(ValueError, match="name@version"):
        make_capability(parents=["greeting"])


def test_self_parent_fails(validator: CapabilityValidator):
    result = validator.validate(make_capability(parents=["greeting@0.1.0"]))
    assert result.valid is False
    assert any("own parent" in e for e in result.errors)


def with_flag(base: dict, dotted_key: str, value: bool = True) -> dict:
    """Set a nested permission flag on a copy of a permissions dict."""
    import copy

    perms = copy.deepcopy(base)
    keys = dotted_key.split(".")
    node = perms
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
    return perms


def test_all_permissions_produces_warning(validator: CapabilityValidator):
    perms = with_flag(DENY_ALL_PERMISSIONS, "filesystem.read")
    perms = with_flag(perms, "filesystem.write")
    perms = with_flag(perms, "network.outbound")
    perms = with_flag(perms, "process.spawn")
    result = validator.validate(make_capability(permissions=perms))
    assert result.valid is True
    assert any("least privilege" in w for w in result.warnings)


def test_network_plus_filesystem_write_produces_security_warning(
    validator: CapabilityValidator,
):
    perms = with_flag(DENY_ALL_PERMISSIONS, "filesystem.write")
    perms = with_flag(perms, "network.outbound")
    result = validator.validate(make_capability(permissions=perms))
    assert result.valid is True
    assert any("exfiltration" in w for w in result.warnings)


def test_process_spawn_produces_security_warning(validator: CapabilityValidator):
    perms = with_flag(DENY_ALL_PERMISSIONS, "process.spawn")
    result = validator.validate(make_capability(permissions=perms))
    assert result.valid is True
    assert any("spawn" in w for w in result.warnings)


def test_no_tests_produces_warning(validator: CapabilityValidator):
    cap = make_capability()
    # Evaluation with empty tests list still satisfies schema, but warns semantically
    cap.evaluation = {"tests": [], "approval_gates": []}
    result = validator.validate(cap)
    assert any("No tests specified" in w for w in result.warnings)


def test_schema_rejection(validator: CapabilityValidator):
    """A capability that violates the JSON schema fails schema validation."""
    cap = make_capability()
    # Corrupt the kind after construction
    cap.kind = "NotACapability"
    result = validator.validate(cap)
    assert result.valid is False
    assert any("Schema validation failed" in e for e in result.errors)


def test_validate_from_yaml_missing_file(validator: CapabilityValidator):
    result = validator.validate_from_yaml(Path("does/not/exist.yaml"))
    assert result.valid is False
    assert any("File not found" in e for e in result.errors)


def test_validate_from_yaml_valid_file(validator: CapabilityValidator):
    import yaml

    cap = make_capability()
    yaml_path = Path("capability_test_tmp.yaml")
    yaml_path.write_text(yaml.safe_dump(cap.to_dict()), encoding="utf-8")
    try:
        result = validator.validate_from_yaml(yaml_path)
        assert result.valid is True
    finally:
        yaml_path.unlink()


def test_convenience_function():
    result = validate_capability(make_capability())
    assert isinstance(result, ValidationResult)
    assert result.valid is True


def test_validation_result_failure_factory():
    result = ValidationResult.failure(["boom"])
    assert result.valid is False
    assert result.errors == ["boom"]
