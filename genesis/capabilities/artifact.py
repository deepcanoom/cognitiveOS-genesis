"""
Capability Artifact Model

Represents a distributable capability package.

Design Philosophy:
- Artifact = DNA + Implementation + Provenance + Integrity
- Separation: DNA (specification) vs Artifact (package)
- Prepares for future distribution, signing, verification

Scalability:
- Artifact model enables capability marketplace/registry
- Integrity metadata supports supply chain security
- Clear separation supports caching, CDN distribution
"""

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

from genesis.capabilities.manifest import Capability


@dataclass
class ArtifactMetadata:
    """
    Metadata about the capability artifact.

    Design: Separate metadata from DNA allows artifact-level
    information without polluting capability specification.
    """

    artifact_id: str  # name@version
    created_at: datetime
    size_bytes: int
    checksums: dict[str, str] = field(default_factory=dict)  # algorithm: hash
    evaluation_results: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Serialize to dict."""
        return {
            "artifactId": self.artifact_id,
            "createdAt": self.created_at.isoformat(),
            "sizeBytes": self.size_bytes,
            "checksums": self.checksums,
            "evaluationResults": self.evaluation_results,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ArtifactMetadata":
        """Deserialize from dict."""
        return cls(
            artifact_id=data["artifactId"],
            created_at=datetime.fromisoformat(data["createdAt"]),
            size_bytes=data["sizeBytes"],
            checksums=data.get("checksums", {}),
            evaluation_results=data.get("evaluationResults", {}),
        )


@dataclass
class CapabilityArtifact:
    """
    Complete capability artifact package.

    Components:
    - capability_dna: The declarative specification
    - implementation_path: Location of implementation code
    - metadata: Artifact-level metadata

    Design Rationale:

    1. Why separate from Capability DNA?
       - DNA is portable specification
       - Artifact is complete deployable package
       - Enables DNA versioning independent of implementation

    2. Scalability benefits:
       - Artifacts can be cached, CDN-distributed
       - Integrity verification before execution
       - Support for signed/verified artifacts (future)

    3. Best practices:
       - Immutable after creation
       - Self-contained (includes all metadata)
       - Supports offline verification
    """

    capability_dna: Capability
    implementation_path: Path | None
    metadata: ArtifactMetadata

    def __post_init__(self) -> None:
        """Validate artifact construction."""
        # Verify artifact ID matches capability
        expected_id = self.capability_dna.capability_id
        if self.metadata.artifact_id != expected_id:
            raise ValueError(
                f"Artifact ID mismatch: metadata says {self.metadata.artifact_id}, "
                f"but DNA is {expected_id}"
            )

    @property
    def artifact_id(self) -> str:
        """Unique identifier: name@version."""
        return self.metadata.artifact_id

    @property
    def name(self) -> str:
        """Capability name."""
        return self.capability_dna.name

    @property
    def version(self) -> str:
        """Capability version."""
        return self.capability_dna.version

    def verify_integrity(self) -> bool:
        """
        Verify artifact integrity via checksums.

        Design: Basic integrity check. Future: cryptographic signatures.

        Returns:
            True if integrity verified, False otherwise
        """
        if not self.implementation_path or not self.implementation_path.exists():
            return False

        # Verify SHA256 if present
        if "sha256" in self.metadata.checksums:
            expected = self.metadata.checksums["sha256"]
            actual = self._compute_checksum(self.implementation_path, "sha256")
            return actual == expected

        return True  # No checksum to verify

    def _compute_checksum(self, path: Path, algorithm: str = "sha256") -> str:
        """
        Compute checksum of implementation directory.

        Design: Recursive checksum for directory trees.
        Scalability: For large implementations, consider content-addressable storage.
        """
        hasher = hashlib.new(algorithm)

        if path.is_file():
            hasher.update(path.read_bytes())
        elif path.is_dir():
            # Sort for deterministic ordering
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    hasher.update(file_path.read_bytes())

        return hasher.hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Serialize artifact to dict."""
        return {
            "capability": self.capability_dna.to_dict(),
            "implementation": {
                "path": str(self.implementation_path) if self.implementation_path else None
            },
            "metadata": self.metadata.to_dict(),
        }

    @classmethod
    def build(
        cls,
        capability_dna: Capability,
        implementation_path: Path | None = None,
        evaluation_results: dict[str, Any] | None = None,
    ) -> "CapabilityArtifact":
        """
        Build a capability artifact from components.

        Design: Factory method for artifact construction with automatic
        metadata generation.

        Args:
            capability_dna: Validated capability manifest
            implementation_path: Path to implementation code
            evaluation_results: Test/evaluation outcomes

        Returns:
            Complete capability artifact
        """
        # Compute checksums
        checksums = {}
        size_bytes = 0

        if implementation_path and implementation_path.exists():
            checksums["sha256"] = cls._compute_checksum_static(
                implementation_path, "sha256"
            )
            size_bytes = cls._compute_size(implementation_path)

        metadata = ArtifactMetadata(
            artifact_id=capability_dna.capability_id,
            created_at=datetime.now(),
            size_bytes=size_bytes,
            checksums=checksums,
            evaluation_results=evaluation_results or {},
        )

        return cls(
            capability_dna=capability_dna,
            implementation_path=implementation_path,
            metadata=metadata,
        )

    @staticmethod
    def _compute_checksum_static(path: Path, algorithm: str = "sha256") -> str:
        """Static method for checksum computation (for build factory)."""
        hasher = hashlib.new(algorithm)

        if path.is_file():
            hasher.update(path.read_bytes())
        elif path.is_dir():
            for file_path in sorted(path.rglob("*")):
                if file_path.is_file():
                    hasher.update(file_path.read_bytes())

        return hasher.hexdigest()

    @staticmethod
    def _compute_size(path: Path) -> int:
        """Compute total size of implementation."""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(
                f.stat().st_size
                for f in path.rglob("*")
                if f.is_file()
            )
        return 0

    def __repr__(self) -> str:
        return f"CapabilityArtifact(id={self.artifact_id!r})"
