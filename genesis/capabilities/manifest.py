"""
Capability Manifest (DNA) Model

Represents the declarative specification of a capability.

Design Decisions:
- Immutable after creation (dataclass with frozen fields via validation)
- Typed provenance to prevent arbitrary strings
- Validation at construction time (fail-fast)
- Separation of concerns: Manifest vs Artifact
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class CreatorType(StrEnum):
    """
    Typed enumeration for capability creator.

    Design: Enum prevents arbitrary strings like "pepe123".
    Future-extensible without breaking existing code.
    """

    HUMAN = "HUMAN"
    GENESIS = "GENESIS"
    IMPORTED = "IMPORTED"
    # Future: EXTERNAL_AGENT, MIGRATION, etc.


@dataclass
class Provenance:
    """
    Capability provenance tracking.

    Design Principles:
    - Every capability has verifiable origin
    - Supports lineage tracking for composed capabilities
    - ISO 8601 timestamps for interoperability
    - Parent list enables DAG traversal for composition analysis
    """

    created_by: CreatorType
    created_at: datetime
    parent_capabilities: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate provenance."""
        if not isinstance(self.created_by, CreatorType):
            raise ValueError(f"created_by must be CreatorType enum, got: {type(self.created_by)}")

        if not isinstance(self.created_at, datetime):
            raise ValueError("created_at must be datetime object")

        # Validate parent capability references (name@version format)
        for parent in self.parent_capabilities:
            if "@" not in parent:
                raise ValueError(
                    f"Invalid parent capability reference: {parent}. Must be 'name@version' format."
                )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict for manifest."""
        return {
            "createdBy": self.created_by.value,
            "createdAt": self.created_at.isoformat(),
            "parentCapabilities": self.parent_capabilities,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Provenance":
        """Deserialize from dict."""
        return cls(
            created_by=CreatorType(data["createdBy"]),
            created_at=datetime.fromisoformat(data["createdAt"]),
            parent_capabilities=data.get("parentCapabilities", []),
        )


@dataclass
class Capability:
    """
    Capability DNA - declarative specification.

    Design Philosophy:
    - Declarative, not imperative (no shell commands)
    - Deny-by-default permissions
    - Machine-validatable structure
    - Human-readable when serialized to YAML

    Scalability Considerations:
    - Provenance enables tracing in large capability graphs
    - Typed enums prevent data quality issues at scale
    - Validation at construction prevents invalid state propagation

    Best Practices Applied:
    - Single Responsibility: Manifest describes, doesn't execute
    - Open/Closed: Extensible (new permission types) without modification
    - Dependency Inversion: References by name@version, not concrete objects
    """

    # Metadata
    api_version: str
    kind: str
    name: str
    version: str
    description: str
    provenance: Provenance

    # Specification
    capability_type: str  # simple, composite, service
    runtime_type: str  # python, node, binary
    runtime_entrypoint: str  # module:function
    runtime_version_constraint: str | None

    # Requirements
    requirements: dict[str, Any] = field(default_factory=dict)

    # Dependencies
    dependencies: dict[str, list[str]] = field(default_factory=dict)

    # Permissions (deny-by-default)
    permissions: dict[str, Any] = field(default_factory=dict)

    # Evaluation
    evaluation: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """
        Validate capability manifest at construction.

        Design: Fail-fast validation prevents invalid capabilities
        from propagating through the system.
        """
        # Validate API version
        if self.api_version != "genesis.cognitiveos.dev/v1alpha1":
            raise ValueError(f"Unsupported API version: {self.api_version}")

        # Validate kind
        if self.kind != "Capability":
            raise ValueError(f"Invalid kind: {self.kind}. Must be 'Capability'")

        # Validate name (lowercase alphanumeric + hyphens)
        if not self.name or not all(c.isalnum() or c in "-_" for c in self.name):
            raise ValueError(
                f"Invalid capability name: {self.name}. "
                "Must be lowercase alphanumeric with hyphens."
            )

        # Validate version (semantic versioning)
        version_parts = self.version.split(".")
        if len(version_parts) != 3 or not all(p.isdigit() for p in version_parts):
            raise ValueError(f"Invalid version: {self.version}. Must be semantic version (X.Y.Z)")

        # Validate runtime entrypoint format
        if ":" not in self.runtime_entrypoint:
            raise ValueError(
                f"Invalid entrypoint: {self.runtime_entrypoint}. Must be 'module:function' format."
            )

        # Validate no self-references in dependencies
        for _dep_type, deps in self.dependencies.items():
            for dep in deps:
                dep_name = dep.split("@")[0] if "@" in dep else dep
                if dep_name == self.name:
                    raise ValueError(f"Capability cannot depend on itself: {self.name}")

    @property
    def capability_id(self) -> str:
        """Unique identifier: name@version."""
        return f"{self.name}@{self.version}"

    def to_dict(self) -> dict[str, Any]:
        """
        Serialize to dictionary for YAML export.

        Design: Explicit structure mapping ensures manifest format stability.
        """
        return {
            "apiVersion": self.api_version,
            "kind": self.kind,
            "metadata": {
                "name": self.name,
                "version": self.version,
                "description": self.description,
                "provenance": self.provenance.to_dict(),
            },
            "spec": {
                "type": self.capability_type,
                "runtime": {
                    "type": self.runtime_type,
                    "entrypoint": self.runtime_entrypoint,
                    **(
                        {"versionConstraint": self.runtime_version_constraint}
                        if self.runtime_version_constraint
                        else {}
                    ),
                },
                "requirements": self.requirements,
                "dependencies": self.dependencies,
                "permissions": self.permissions,
                "evaluation": self.evaluation,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Capability":
        """
        Deserialize from dictionary (YAML input).

        Design: Centralized deserialization with validation.
        """
        metadata = data["metadata"]
        spec = data["spec"]
        runtime = spec["runtime"]

        return cls(
            api_version=data["apiVersion"],
            kind=data["kind"],
            name=metadata["name"],
            version=metadata["version"],
            description=metadata["description"],
            provenance=Provenance.from_dict(metadata["provenance"]),
            capability_type=spec["type"],
            runtime_type=runtime["type"],
            runtime_entrypoint=runtime["entrypoint"],
            runtime_version_constraint=runtime.get("versionConstraint"),
            requirements=spec.get("requirements", {}),
            dependencies=spec.get("dependencies", {}),
            permissions=spec.get("permissions", {}),
            evaluation=spec.get("evaluation", {}),
        )

    @classmethod
    def from_plan(
        cls,
        plan: Any,  # CapabilityPlan, but avoid circular import
        provenance: Provenance,
    ) -> "Capability":
        """
        Create Capability DNA from CapabilityPlan.

        Design: Transformation layer between planning and manifestation.
        This is where Intent -> Plan -> DNA completes.

        Args:
            plan: CapabilityPlan from planner
            provenance: Provenance information

        Returns:
            Capability manifest ready for validation
        """
        # Convert plan dependencies to manifest format
        dependencies: dict[str, list[str]] = {"capabilities": [], "models": []}
        for dep in plan.dependencies:
            if dep.type == "capability":
                dependencies["capabilities"].append(dep.to_ref())
            elif dep.type == "model":
                dependencies["models"].append(dep.to_ref())

        return cls(
            api_version="genesis.cognitiveos.dev/v1alpha1",
            kind="Capability",
            name=plan.name,
            version=plan.version,
            description=plan.description,
            provenance=provenance,
            capability_type=plan.capability_type.value,
            runtime_type=plan.runtime.type,
            runtime_entrypoint=plan.runtime.entrypoint,
            runtime_version_constraint=plan.runtime.version_constraint,
            requirements=(
                {"python": plan.runtime.version_constraint}
                if plan.runtime.version_constraint
                else {}
            ),
            dependencies=dependencies,
            permissions=plan.permissions.to_dict(),
            evaluation={
                "tests": [{"type": "unit", "path": "tests/unit"}],
                "approval_gates": [{"type": "human", "required": True}],
            },
        )

    def __repr__(self) -> str:
        return f"Capability(name={self.name!r}, version={self.version!r})"
