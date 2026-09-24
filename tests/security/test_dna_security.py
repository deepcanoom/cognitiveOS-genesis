"""
Security tests: DNA security invariants.

Verifies that Capability DNA cannot smuggle executable shell commands
and that dangerous declarations are surfaced for human review.
"""

from datetime import datetime

from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.capabilities.validator import CapabilityValidator


def make_dna(name: str = "sec-dna", entrypoint: str = "mod:func") -> Capability:
    provenance = Provenance(
        created_by=CreatorType.GENESIS,
        created_at=datetime.now(),
        parent_capabilities=[],
    )
    return Capability(
        api_version="genesis.cognitiveos.dev/v1alpha1",
        kind="Capability",
        name=name,
        version="0.1.0",
        description="Security DNA test",
        provenance=provenance,
        capability_type="simple",
        runtime_type="python",
        runtime_entrypoint=entrypoint,
        runtime_version_constraint=">=3.11",
        permissions={
            "filesystem": {"read": False, "write": False},
            "network": {"outbound": False},
            "process": {"spawn": False},
        },
        evaluation={"tests": [], "approval_gates": [{"type": "human", "required": True}]},
    )


def test_dna_rejects_shell_like_entrypoint():
    """Entrypoints without module:function format are rejected."""
    with __import__("pytest").raises(ValueError, match="entrypoint"):
        make_dna(entrypoint="rm -rf /")


def test_dna_rejects_self_dependency():
    """A capability cannot depend on itself: validator surfaces it as error."""
    cap = make_dna()
    # Mutate after construction (bypasses __post_init__ guard) to reach the validator
    cap.dependencies = {"capabilities": ["sec-dna@0.1.0"]}
    result = CapabilityValidator().validate(cap)
    assert result.valid is False
    assert any("Self-reference" in e for e in result.errors)


def test_dna_registration_requires_approval_gate_in_manifest():
    """Every registered DNA declares a human approval gate."""
    import yaml

    manifest_path = __import__("pathlib").Path(
        "capabilities/registry/greeting@0.1.0/capability.yaml"
    )
    if not manifest_path.exists():
        __import__("pytest").skip("demo registry artifact not present")

    with open(manifest_path) as f:
        data = yaml.safe_load(f)

    gates = data["spec"]["evaluation"]["approval_gates"]
    human_required = any(
        gate.get("type") == "human" and gate.get("required") is True for gate in gates
    )
    assert human_required, "Registered capability must require human approval"


def test_validator_surfaces_spawn_permission_for_review():
    """Process spawn is flagged as a security warning for human review."""
    cap = make_dna()
    cap.permissions = {
        "filesystem": {"read": False, "write": False},
        "network": {"outbound": False},
        "process": {"spawn": True},
    }
    cap.evaluation = {"tests": [], "approval_gates": []}
    result = CapabilityValidator().validate(cap)
    assert any("spawn" in w for w in result.warnings)
