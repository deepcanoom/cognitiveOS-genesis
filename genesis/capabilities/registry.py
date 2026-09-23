"""
Capability Registry

Stores and retrieves capability artifacts.

Design Decisions:
- v0.1: File-based local storage (simple, no external dependencies)
- Interface designed for future database/distributed implementations
- Artifact-oriented (stores complete packages, not just DNA)

Scalability Considerations:
- File-based sufficient for <1000 capabilities
- Clear interface allows swapping to database (v0.2+)
- Index for fast lookups
- Future: Content-addressable storage, distributed registry

Best Practices:
- Repository Pattern: Abstract storage mechanism
- Single Responsibility: Only storage/retrieval, no validation/execution
- Defensive: Validates inputs, handles errors gracefully
"""

import json
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from genesis.capabilities.artifact import CapabilityArtifact
from genesis.capabilities.manifest import Capability


@dataclass
class RegistryMetadata:
    """
    Registry-level metadata.

    Design: Separate from capability metadata for registry operations.
    """

    total_capabilities: int
    last_updated: str
    registry_version: str = "0.1.0"

    def to_dict(self) -> dict[str, Any]:
        return {
            "totalCapabilities": self.total_capabilities,
            "lastUpdated": self.last_updated,
            "registryVersion": self.registry_version,
        }


class CapabilityRegistry:
    """
    Local file-based capability registry.

    Structure:
        capabilities/registry/
          index.json                    # Fast lookup
          hello-world@0.1.0/
            artifact.yaml              # Artifact metadata
            capability.yaml            # Capability DNA
            implementation/            # Code
            evaluation.json            # Test results
            provenance.json            # Detailed provenance
            integrity.sha256           # Checksums

    Design Philosophy:
    - Each artifact version is immutable once registered
    - Artifacts are self-contained (all metadata included)
    - Index enables fast queries without scanning filesystem

    Thread Safety:
    - v0.1: Single-threaded operations assumed
    - Future: Add locking for concurrent access

    Scalability Path:
    - v0.1: File-based (< 1000 capabilities)
    - v0.2: SQLite (< 100K capabilities)
    - v0.3: PostgreSQL/distributed (production scale)
    """

    def __init__(self, registry_path: Path | None = None) -> None:
        """
        Initialize registry.

        Args:
            registry_path: Root path for registry storage
        """
        if registry_path is None:
            registry_path = Path("capabilities/registry")

        self.registry_path = registry_path
        self.index_path = registry_path / "index.json"

        # Ensure registry directory exists
        self.registry_path.mkdir(parents=True, exist_ok=True)

        # Initialize or load index
        self._index: dict[str, Any] = self._load_index()

    def register(self, artifact: CapabilityArtifact) -> None:
        """
        Register a capability artifact.

        Design:
        - Immutable: Once registered, cannot be modified
        - Atomic: Either fully succeeds or fails (no partial state)
        - Idempotent: Re-registering same version is no-op

        Args:
            artifact: Capability artifact to register

        Raises:
            ValueError: If artifact already registered
            IOError: If storage fails
        """
        artifact_id = artifact.artifact_id

        # Check if already registered
        if self.exists(artifact.name, artifact.version):
            # Idempotent: allow re-registration of identical artifact
            existing = self.get(artifact.name, artifact.version)
            if existing and existing.artifact_id == artifact_id:
                return  # Already registered, no-op
            else:
                raise ValueError(
                    f"Artifact {artifact_id} already registered. "
                    "Artifacts are immutable."
                )

        # Create artifact directory
        artifact_dir = self.registry_path / artifact_id
        artifact_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Save capability DNA
            dna_path = artifact_dir / "capability.yaml"
            with open(dna_path, "w") as f:
                yaml.dump(artifact.capability_dna.to_dict(), f, sort_keys=False)

            # Save artifact metadata
            metadata_path = artifact_dir / "artifact.yaml"
            with open(metadata_path, "w") as f:
                yaml.dump(artifact.metadata.to_dict(), f, sort_keys=False)

            # Save provenance (detailed)
            provenance_path = artifact_dir / "provenance.json"
            with open(provenance_path, "w") as f:
                json.dump(artifact.capability_dna.provenance.to_dict(), f, indent=2)

            # Copy implementation if provided
            if artifact.implementation_path and artifact.implementation_path.exists():
                impl_dest = artifact_dir / "implementation"
                if artifact.implementation_path.is_dir():
                    shutil.copytree(artifact.implementation_path, impl_dest)
                else:
                    impl_dest.mkdir(exist_ok=True)
                    shutil.copy2(artifact.implementation_path, impl_dest)

            # Save evaluation results
            if artifact.metadata.evaluation_results:
                eval_path = artifact_dir / "evaluation.json"
                with open(eval_path, "w") as f:
                    json.dump(artifact.metadata.evaluation_results, f, indent=2)

            # Save integrity checksums
            if artifact.metadata.checksums:
                integrity_path = artifact_dir / "integrity.sha256"
                with open(integrity_path, "w") as f:
                    for _algo, checksum in artifact.metadata.checksums.items():
                        f.write(f"{checksum}  {artifact_id}\n")

            # Update index
            self._add_to_index(artifact)
            self._save_index()

        except Exception as e:
            # Rollback: remove artifact directory if registration failed
            if artifact_dir.exists():
                shutil.rmtree(artifact_dir)
            raise OSError(f"Failed to register artifact {artifact_id}: {e}") from e

    def get(self, name: str, version: str) -> CapabilityArtifact | None:
        """
        Retrieve capability artifact.

        Args:
            name: Capability name
            version: Capability version

        Returns:
            CapabilityArtifact if found, None otherwise
        """
        artifact_id = f"{name}@{version}"
        artifact_dir = self.registry_path / artifact_id

        if not artifact_dir.exists():
            return None

        try:
            # Load capability DNA
            dna_path = artifact_dir / "capability.yaml"
            with open(dna_path) as f:
                dna_dict = yaml.safe_load(f)
            capability_dna = Capability.from_dict(dna_dict)

            # Load artifact metadata
            metadata_path = artifact_dir / "artifact.yaml"
            with open(metadata_path) as f:
                from genesis.capabilities.artifact import ArtifactMetadata
                metadata_dict = yaml.safe_load(f)
                metadata = ArtifactMetadata.from_dict(metadata_dict)

            # Implementation path
            impl_path = artifact_dir / "implementation"
            if not impl_path.exists():
                impl_path = None

            return CapabilityArtifact(
                capability_dna=capability_dna,
                implementation_path=impl_path,
                metadata=metadata,
            )

        except Exception as e:
            raise OSError(f"Failed to load artifact {artifact_id}: {e}") from e

    def exists(self, name: str, version: str) -> bool:
        """Check if capability exists in registry."""
        artifact_id = f"{name}@{version}"
        return artifact_id in self._index.get("artifacts", {})

    def list(self) -> list[dict[str, Any]]:
        """
        List all registered capabilities.

        Returns:
            List of capability metadata dicts
        """
        return list(self._index.get("artifacts", {}).values())

    def list_versions(self, name: str) -> list[str]:
        """
        List all versions of a capability.

        Args:
            name: Capability name

        Returns:
            List of version strings, sorted newest first
        """
        versions = [
            artifact["version"]
            for artifact in self._index.get("artifacts", {}).values()
            if artifact["name"] == name
        ]

        # Sort by semantic version (newest first)
        def version_key(v: str) -> tuple[int, int, int]:
            major, minor, patch = v.split(".")
            return (int(major), int(minor), int(patch))

        return sorted(versions, key=version_key, reverse=True)

    def _load_index(self) -> dict[str, Any]:
        """Load registry index."""
        if not self.index_path.exists():
            return {"artifacts": {}, "metadata": {}}

        try:
            with open(self.index_path) as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Corrupted index, rebuild
            return self._rebuild_index()

    def _save_index(self) -> None:
        """Save registry index."""
        with open(self.index_path, "w") as f:
            json.dump(self._index, f, indent=2)

    def _add_to_index(self, artifact: CapabilityArtifact) -> None:
        """Add artifact to index."""
        artifacts = self._index.setdefault("artifacts", {})

        artifacts[artifact.artifact_id] = {
            "id": artifact.artifact_id,
            "name": artifact.name,
            "version": artifact.version,
            "description": artifact.capability_dna.description,
            "type": artifact.capability_dna.capability_type,
            "createdBy": artifact.capability_dna.provenance.created_by.value,
            "createdAt": artifact.metadata.created_at.isoformat(),
            "permissions": artifact.capability_dna.permissions,
        }

        # Update metadata
        from datetime import datetime
        self._index["metadata"] = {
            "totalCapabilities": len(artifacts),
            "lastUpdated": datetime.now().isoformat(),
            "registryVersion": "0.1.0",
        }

    def _rebuild_index(self) -> dict[str, Any]:
        """
        Rebuild index from filesystem.

        Design: Recovery mechanism if index gets corrupted.
        Scalability: Expensive for large registries (future: incremental rebuild).
        """
        index: dict[str, Any] = {"artifacts": {}, "metadata": {}}

        # Scan registry directory
        for artifact_dir in self.registry_path.iterdir():
            if not artifact_dir.is_dir():
                continue

            try:
                # Load capability DNA
                dna_path = artifact_dir / "capability.yaml"
                if not dna_path.exists():
                    continue

                with open(dna_path) as f:
                    dna_dict = yaml.safe_load(f)

                metadata = dna_dict.get("metadata", {})
                spec = dna_dict.get("spec", {})
                provenance = metadata.get("provenance", {})

                artifact_id = f"{metadata['name']}@{metadata['version']}"

                index["artifacts"][artifact_id] = {
                    "id": artifact_id,
                    "name": metadata["name"],
                    "version": metadata["version"],
                    "description": metadata.get("description", ""),
                    "type": spec.get("type", "simple"),
                    "createdBy": provenance.get("createdBy", "UNKNOWN"),
                    "createdAt": provenance.get("createdAt", ""),
                    "permissions": spec.get("permissions", {}),
                }
            except Exception:
                # Skip malformed artifacts
                continue

        return index
