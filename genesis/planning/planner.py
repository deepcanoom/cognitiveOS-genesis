"""
Capability Planner - Intent to Plan Transformation

Provides the protocol and implementations for transforming IntentRequest
into CapabilityPlan.
"""

import re
from typing import Any, Protocol

from genesis.planning.intent import IntentRequest
from genesis.planning.plan import (
    CapabilityPlan,
    CapabilityType,
    Dependency,
    PermissionSet,
    RuntimeSpec,
)


class CapabilityPlanner(Protocol):
    """
    Protocol for capability planning strategies.

    A CapabilityPlanner transforms user intent into a concrete capability plan.
    Different implementations provide different planning strategies:

    - DeterministicPlanner: Rule-based (v0.1)
    - LLMPlanner: AI-powered planning (v0.4+)
    - MultiAgentPlanner: Collaborative planning (v0.6+)
    - RecursivePlanner: Capabilities plan capabilities (v0.8+)
    """

    def plan(self, intent: IntentRequest) -> CapabilityPlan:
        """
        Transform intent into capability plan.

        Args:
            intent: User's high-level goal

        Returns:
            Concrete capability plan ready for manifestation

        Raises:
            ValueError: If intent cannot be planned
        """
        ...


class DeterministicPlanner:
    """
    Deterministic rule-based capability planner.

    This is the v0.1 implementation that demonstrates the Intent -> Plan -> DNA
    flow without requiring LLM dependencies.

    Planning Strategy:
    1. Extract capability name from description
    2. Infer permissions from constraints
    3. Apply deny-by-default security model
    4. Generate minimal runtime spec

    Example:
        planner = DeterministicPlanner()
        plan = planner.plan(IntentRequest(
            description="Create a greeting capability",
            requirements={},
            constraints={"no_network": True, "no_filesystem": True}
        ))
    """

    def __init__(self) -> None:
        """Initialize deterministic planner."""
        pass

    def plan(self, intent: IntentRequest) -> CapabilityPlan:
        """
        Transform intent into capability plan using deterministic rules.

        Args:
            intent: User's high-level goal

        Returns:
            Concrete capability plan

        Raises:
            ValueError: If intent cannot be planned
        """
        # Extract capability name from description
        name = self._extract_name(intent.description)

        # Infer permissions from constraints (deny-by-default)
        permissions = self._infer_permissions(intent.constraints)

        # Generate runtime spec
        runtime = self._generate_runtime(name, intent.requirements)

        # Parse dependencies (if specified)
        dependencies = self._parse_dependencies(intent.requirements)

        # Generate description
        description = self._generate_description(intent)

        return CapabilityPlan(
            name=name,
            version="0.1.0",  # Default version for new capabilities
            description=description,
            capability_type=CapabilityType.SIMPLE,  # v0.1 only supports simple
            runtime=runtime,
            permissions=permissions,
            dependencies=dependencies,
            metadata={
                "planned_from_intent": True,
                "original_description": intent.description,
            },
        )

    def _extract_name(self, description: str) -> str:
        """
        Extract capability name from intent description.

        Rules:
        1. Look for "create a/an <NAME> capability" pattern
        2. Convert to lowercase with hyphens
        3. Default to "generated-capability" if cannot extract
        """
        # Try to extract name from common patterns
        patterns = [
            r"create\s+(?:a|an)\s+(\w+(?:\s+\w+)*)\s+capability",
            r"build\s+(?:a|an)\s+(\w+(?:\s+\w+)*)\s+capability",
            r"make\s+(?:a|an)\s+(\w+(?:\s+\w+)*)\s+capability",
        ]

        for pattern in patterns:
            match = re.search(pattern, description.lower())
            if match:
                name_words = match.group(1).split()
                # Convert to kebab-case
                return "-".join(name_words)

        # Default name
        return "generated-capability"

    def _infer_permissions(self, constraints: dict[str, Any]) -> PermissionSet:
        """
        Infer permissions from intent constraints.

        Deny-by-default: all permissions start as False.
        Only set to True if explicitly required by intent.

        Constraint keys:
        - no_network: False -> network allowed
        - no_filesystem: False -> filesystem allowed
        - require_network: True -> network allowed
        - require_filesystem_read: True -> filesystem read allowed
        - require_filesystem_write: True -> filesystem write allowed
        """
        # Start with deny-all
        permissions = PermissionSet()

        # Check for explicit requirements
        if constraints.get("require_network"):
            permissions.network_outbound = True

        if constraints.get("require_filesystem_read"):
            permissions.filesystem_read = True

        if constraints.get("require_filesystem_write"):
            permissions.filesystem_write = True

        if constraints.get("require_process_spawn"):
            permissions.process_spawn = True

        # no_X constraints are already handled by deny-by-default
        # (we only grant permissions explicitly)

        return permissions

    def _generate_runtime(self, name: str, requirements: dict[str, Any]) -> RuntimeSpec:
        """
        Generate runtime specification.

        For v0.1, always generates Python runtime with standard entrypoint.
        """
        # Convert name to module name (replace hyphens with underscores)
        module_name = name.replace("-", "_")

        # Standard entrypoint pattern
        entrypoint = f"{module_name}.main:execute"

        # Check for Python version requirement
        python_version = requirements.get("python_version", ">=3.11")

        return RuntimeSpec(
            type="python",
            entrypoint=entrypoint,
            version_constraint=python_version,
        )

    def _parse_dependencies(self, requirements: dict[str, Any]) -> list[Dependency]:
        """
        Parse dependencies from requirements.

        Looks for "dependencies" key in requirements dict.
        """
        deps = []

        if "dependencies" in requirements:
            for dep_spec in requirements["dependencies"]:
                if isinstance(dep_spec, dict):
                    deps.append(
                        Dependency(
                            type=dep_spec.get("type", "capability"),
                            name=dep_spec["name"],
                            version_constraint=dep_spec.get("version", ">=0.1.0"),
                        )
                    )
                elif isinstance(dep_spec, str):
                    # Parse "name@version" format
                    if "@" in dep_spec:
                        name, version = dep_spec.split("@", 1)
                        deps.append(
                            Dependency(
                                type="capability",
                                name=name,
                                version_constraint=version,
                            )
                        )

        return deps

    def _generate_description(self, intent: IntentRequest) -> str:
        """Generate capability description from intent."""
        # Use intent description as base
        desc = intent.description.strip()

        # Add requirements if specified
        if intent.requirements:
            req_summary = []
            if "input" in intent.requirements:
                req_summary.append(f"Input: {intent.requirements['input']}")
            if "output" in intent.requirements:
                req_summary.append(f"Output: {intent.requirements['output']}")

            if req_summary:
                desc += " | " + ", ".join(req_summary)

        # Truncate if too long
        if len(desc) > 256:
            desc = desc[:253] + "..."

        return desc
