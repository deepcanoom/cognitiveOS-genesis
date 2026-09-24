"""
Capability Plan Model

Represents a planned capability before manifestation into Capability DNA.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class CapabilityType(StrEnum):
    """Type of capability."""

    SIMPLE = "simple"  # Single-purpose, non-composite
    COMPOSITE = "composite"  # Composed from other capabilities (v0.2+)
    SERVICE = "service"  # Long-running service (future)


@dataclass
class RuntimeSpec:
    """
    Runtime specification for capability execution.

    Describes HOW the capability should be executed (declaratively).
    """

    type: str  # e.g., "python", "node", "binary"
    entrypoint: str  # e.g., "module:function" or "module:Class.method"
    version_constraint: str | None = None  # e.g., ">=3.11"

    def __post_init__(self) -> None:
        """Validate runtime spec."""
        if not self.type:
            raise ValueError("Runtime type cannot be empty")
        if not self.entrypoint:
            raise ValueError("Runtime entrypoint cannot be empty")

        # Validate entrypoint format: module:function or module:Class.method
        if ":" not in self.entrypoint:
            raise ValueError(f"Entrypoint must be 'module:function' format, got: {self.entrypoint}")


@dataclass
class PermissionSet:
    """
    Permission declarations for capability.

    Deny-by-default model: all permissions default to most restrictive.
    """

    filesystem_read: bool = False
    filesystem_write: bool = False
    network_outbound: bool = False
    process_spawn: bool = False

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation for manifest."""
        return {
            "filesystem": {
                "read": self.filesystem_read,
                "write": self.filesystem_write,
            },
            "network": {
                "outbound": self.network_outbound,
            },
            "process": {
                "spawn": self.process_spawn,
            },
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PermissionSet":
        """Create from dictionary representation."""
        fs = data.get("filesystem", {})
        net = data.get("network", {})
        proc = data.get("process", {})

        return cls(
            filesystem_read=fs.get("read", False),
            filesystem_write=fs.get("write", False),
            network_outbound=net.get("outbound", False),
            process_spawn=proc.get("spawn", False),
        )


@dataclass
class Dependency:
    """
    Capability dependency reference.

    Represents a dependency on another capability, model, or tool.
    """

    type: str  # "capability", "model", "tool"
    name: str
    version_constraint: str  # e.g., "1.0.0" or ">=1.0.0"

    def __post_init__(self) -> None:
        """Validate dependency."""
        if self.type not in ("capability", "model", "tool"):
            raise ValueError(f"Invalid dependency type: {self.type}")
        if not self.name:
            raise ValueError("Dependency name cannot be empty")
        if not self.version_constraint:
            raise ValueError("Dependency version constraint cannot be empty")

    def to_ref(self) -> str:
        """Convert to reference string: name@version."""
        return f"{self.name}@{self.version_constraint}"


@dataclass
class CapabilityPlan:
    """
    Planned capability before manifestation into Capability DNA.

    This is the output of the CapabilityPlanner. It represents a complete
    specification that can be converted into a Capability DNA manifest.

    Example:
        plan = CapabilityPlan(
            name="hello-world",
            version="0.1.0",
            description="Simple greeting capability",
            capability_type=CapabilityType.SIMPLE,
            runtime=RuntimeSpec(
                type="python",
                entrypoint="hello.main:greet",
                version_constraint=">=3.11"
            ),
            permissions=PermissionSet(),  # deny-by-default
            dependencies=[]
        )
    """

    name: str
    version: str
    description: str
    capability_type: CapabilityType
    runtime: RuntimeSpec
    permissions: PermissionSet
    dependencies: list[Dependency] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate capability plan."""
        # Validate name (lowercase alphanumeric + hyphens)
        if not self.name or not self.name.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"Invalid capability name: {self.name}. "
                "Must be lowercase alphanumeric with hyphens."
            )

        # Validate version (semantic versioning)
        parts = self.version.split(".")
        if len(parts) != 3 or not all(p.isdigit() for p in parts):
            raise ValueError(f"Invalid version: {self.version}. Must be semantic version (X.Y.Z)")

        if not self.description:
            raise ValueError("Capability description cannot be empty")

        # Validate no self-references in dependencies
        for dep in self.dependencies:
            if dep.type == "capability" and dep.name == self.name:
                raise ValueError(f"Capability cannot depend on itself: {self.name}")

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "capability_type": self.capability_type.value,
            "runtime": {
                "type": self.runtime.type,
                "entrypoint": self.runtime.entrypoint,
                "version_constraint": self.runtime.version_constraint,
            },
            "permissions": self.permissions.to_dict(),
            "dependencies": [
                {
                    "type": dep.type,
                    "name": dep.name,
                    "version_constraint": dep.version_constraint,
                }
                for dep in self.dependencies
            ],
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "CapabilityPlan":
        """Create from dictionary representation."""
        runtime_data = data["runtime"]
        runtime = RuntimeSpec(
            type=runtime_data["type"],
            entrypoint=runtime_data["entrypoint"],
            version_constraint=runtime_data.get("version_constraint"),
        )

        permissions = PermissionSet.from_dict(data.get("permissions", {}))

        dependencies = [
            Dependency(
                type=dep["type"],
                name=dep["name"],
                version_constraint=dep["version_constraint"],
            )
            for dep in data.get("dependencies", [])
        ]

        return cls(
            name=data["name"],
            version=data["version"],
            description=data["description"],
            capability_type=CapabilityType(data["capability_type"]),
            runtime=runtime,
            permissions=permissions,
            dependencies=dependencies,
            metadata=data.get("metadata", {}),
        )

    def __repr__(self) -> str:
        return f"CapabilityPlan(name={self.name!r}, version={self.version!r})"
