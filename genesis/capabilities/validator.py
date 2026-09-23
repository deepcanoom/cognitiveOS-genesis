"""
Capability Validator

Validates Capability DNA against JSON Schema and semantic rules.

Design Principles:
- Fail-fast validation (errors stop processing immediately)
- Layered validation: Schema -> Semantic -> Security
- Clear error messages for debugging
- Extensible for future validation rules

Best Practices:
- Single Responsibility: Only validates, doesn't transform
- Open/Closed: Easy to add new validation rules
- Dependency Injection: Schema path configurable
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import jsonschema
import yaml

from genesis.capabilities.manifest import Capability


@dataclass
class ValidationResult:
    """
    Result of capability validation.
    
    Design: Explicit result object instead of exceptions for non-critical
    validation failures allows partial validation and better error reporting.
    """
    
    valid: bool
    errors: list[str]
    warnings: list[str]
    
    def __bool__(self) -> bool:
        """Allow `if result:` checks."""
        return self.valid
    
    @classmethod
    def success(cls, warnings: list[str] | None = None) -> "ValidationResult":
        """Create successful validation result."""
        return cls(valid=True, errors=[], warnings=warnings or [])
    
    @classmethod
    def failure(cls, errors: list[str]) -> "ValidationResult":
        """Create failed validation result."""
        return cls(valid=False, errors=errors, warnings=[])


class CapabilityValidator:
    """
    Validates Capability DNA manifests.
    
    Validation Layers:
    1. Schema Validation: JSON Schema conformance
    2. Semantic Validation: Business rule checks
    3. Security Validation: Permission policy checks
    
    Usage:
        validator = CapabilityValidator()
        result = validator.validate(capability)
        if not result.valid:
            print(f"Validation failed: {result.errors}")
    
    Scalability:
    - Schema cached after first load
    - Validation is stateless (thread-safe)
    - Can be parallelized for batch validation
    """
    
    def __init__(self, schema_path: Path | None = None) -> None:
        """
        Initialize validator.
        
        Args:
            schema_path: Path to JSON Schema file. If None, uses default.
        """
        if schema_path is None:
            # Default schema location
            schema_path = Path(__file__).parent.parent.parent / "schemas" / "capability.schema.json"
        
        self.schema_path = schema_path
        self._schema: dict[str, Any] | None = None
    
    @property
    def schema(self) -> dict[str, Any]:
        """
        Load and cache JSON Schema.
        
        Design: Lazy loading + caching for performance.
        """
        if self._schema is None:
            with open(self.schema_path) as f:
                self._schema = json.load(f)
        return self._schema
    
    def validate(self, capability: Capability) -> ValidationResult:
        """
        Validate capability manifest.
        
        Args:
            capability: Capability to validate
            
        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        
        # Convert to dict for schema validation
        manifest_dict = capability.to_dict()
        
        # Layer 1: Schema validation
        schema_errors = self._validate_schema(manifest_dict)
        errors.extend(schema_errors)
        
        # Layer 2: Semantic validation
        if not schema_errors:  # Only if schema valid
            semantic_errors, semantic_warnings = self._validate_semantics(capability)
            errors.extend(semantic_errors)
            warnings.extend(semantic_warnings)
        
        # Layer 3: Security validation
        if not errors:  # Only if previous layers valid
            security_warnings = self._validate_security(capability)
            warnings.extend(security_warnings)
        
        if errors:
            return ValidationResult.failure(errors)
        else:
            return ValidationResult.success(warnings)
    
    def validate_from_yaml(self, yaml_path: Path) -> ValidationResult:
        """
        Validate capability from YAML file.
        
        Args:
            yaml_path: Path to capability.yaml
            
        Returns:
            ValidationResult
        """
        try:
            with open(yaml_path) as f:
                data = yaml.safe_load(f)
            
            # Schema validation first
            schema_errors = self._validate_schema(data)
            if schema_errors:
                return ValidationResult.failure(schema_errors)
            
            # Parse into Capability object
            capability = Capability.from_dict(data)
            
            # Full validation
            return self.validate(capability)
            
        except FileNotFoundError:
            return ValidationResult.failure([f"File not found: {yaml_path}"])
        except yaml.YAMLError as e:
            return ValidationResult.failure([f"YAML parsing error: {e}"])
        except Exception as e:
            return ValidationResult.failure([f"Validation error: {e}"])
    
    def _validate_schema(self, manifest_dict: dict[str, Any]) -> list[str]:
        """
        Validate against JSON Schema.
        
        Design: Uses jsonschema library for standard compliance.
        Returns list of errors for consistent error handling.
        """
        errors: list[str] = []
        
        try:
            jsonschema.validate(instance=manifest_dict, schema=self.schema)
        except jsonschema.ValidationError as e:
            # Format error message
            path = ".".join(str(p) for p in e.path) if e.path else "root"
            errors.append(f"Schema validation failed at {path}: {e.message}")
        except jsonschema.SchemaError as e:
            errors.append(f"Invalid schema: {e.message}")
        
        return errors
    
    def _validate_semantics(
        self, 
        capability: Capability
    ) -> tuple[list[str], list[str]]:
        """
        Validate semantic business rules.
        
        Rules:
        - No self-references in dependencies
        - No obvious circular dependencies
        - Valid parent capability references
        - Reasonable permission combinations
        
        Returns:
            Tuple of (errors, warnings)
        """
        errors: list[str] = []
        warnings: list[str] = []
        
        # Check self-references (also checked in Capability.__post_init__)
        for dep_type, deps in capability.dependencies.items():
            for dep in deps:
                dep_name = dep.split("@")[0] if "@" in dep else dep
                if dep_name == capability.name:
                    errors.append(
                        f"Self-reference detected: capability cannot depend on itself ({dep})"
                    )
        
        # Validate parent capability references
        for parent in capability.provenance.parent_capabilities:
            if "@" not in parent:
                errors.append(
                    f"Invalid parent reference: {parent}. Must be 'name@version' format."
                )
            else:
                parent_name = parent.split("@")[0]
                if parent_name == capability.name:
                    errors.append(
                        f"Invalid parent: capability cannot be its own parent ({parent})"
                    )
        
        # Warning: Capability with all permissions
        perms = capability.permissions
        fs = perms.get("filesystem", {})
        net = perms.get("network", {})
        proc = perms.get("process", {})
        
        if (
            fs.get("read") and fs.get("write") and 
            net.get("outbound") and 
            proc.get("spawn")
        ):
            warnings.append(
                "Capability requests all permissions. "
                "Consider principle of least privilege."
            )
        
        # Warning: No tests specified
        eval_spec = capability.evaluation
        if not eval_spec.get("tests"):
            warnings.append("No tests specified in evaluation section.")
        
        return errors, warnings
    
    def _validate_security(self, capability: Capability) -> list[str]:
        """
        Security-focused validation checks.
        
        These are warnings, not errors, as they don't prevent registration
        but highlight security concerns for human review.
        
        Returns:
            List of security warnings
        """
        warnings: list[str] = []
        
        perms = capability.permissions
        
        # Network + filesystem write is risky
        if (
            perms.get("network", {}).get("outbound") and
            perms.get("filesystem", {}).get("write")
        ):
            warnings.append(
                "Security: Capability can both access network and write files. "
                "Review for potential data exfiltration."
            )
        
        # Process spawn is generally risky
        if perms.get("process", {}).get("spawn"):
            warnings.append(
                "Security: Capability can spawn child processes. "
                "Ensure this is necessary."
            )
        
        return warnings


def validate_capability(capability: Capability) -> ValidationResult:
    """
    Convenience function for capability validation.
    
    Args:
        capability: Capability to validate
        
    Returns:
        ValidationResult
    """
    validator = CapabilityValidator()
    return validator.validate(capability)


def validate_capability_yaml(yaml_path: Path) -> ValidationResult:
    """
    Convenience function for YAML validation.
    
    Args:
        yaml_path: Path to capability.yaml
        
    Returns:
        ValidationResult
    """
    validator = CapabilityValidator()
    return validator.validate_from_yaml(yaml_path)
