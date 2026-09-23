"""Tests for CapabilityPlanner implementations."""

import pytest

from genesis.planning.intent import IntentRequest
from genesis.planning.plan import CapabilityType, PermissionSet
from genesis.planning.planner import DeterministicPlanner


def test_deterministic_planner_basic() -> None:
    """Test basic deterministic planning."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a greeting capability",
        requirements={},
        constraints={"no_network": True, "no_filesystem": True}
    )
    
    plan = planner.plan(intent)
    
    assert plan.name == "greeting"
    assert plan.version == "0.1.0"
    assert plan.capability_type == CapabilityType.SIMPLE
    assert plan.runtime.type == "python"
    assert "greeting" in plan.runtime.entrypoint


def test_deterministic_planner_permissions_deny_by_default() -> None:
    """Test that permissions default to deny-all."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a simple capability",
        constraints={}  # No explicit requirements
    )
    
    plan = planner.plan(intent)
    
    # All permissions should be False (deny-by-default)
    assert plan.permissions.filesystem_read is False
    assert plan.permissions.filesystem_write is False
    assert plan.permissions.network_outbound is False
    assert plan.permissions.process_spawn is False


def test_deterministic_planner_network_permission() -> None:
    """Test planning with network permission requirement."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a web scraper capability",
        constraints={"require_network": True}
    )
    
    plan = planner.plan(intent)
    
    assert plan.permissions.network_outbound is True
    assert plan.permissions.filesystem_read is False  # Still deny others


def test_deterministic_planner_filesystem_permissions() -> None:
    """Test planning with filesystem permission requirements."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a file processor capability",
        constraints={
            "require_filesystem_read": True,
            "require_filesystem_write": True
        }
    )
    
    plan = planner.plan(intent)
    
    assert plan.permissions.filesystem_read is True
    assert plan.permissions.filesystem_write is True
    assert plan.permissions.network_outbound is False  # Still deny others


def test_deterministic_planner_name_extraction_patterns() -> None:
    """Test various name extraction patterns."""
    planner = DeterministicPlanner()
    
    test_cases = [
        ("Create a hello world capability", "hello-world"),
        ("Build an AWS auditor capability", "aws-auditor"),
        ("Make a data transformer capability", "data-transformer"),
    ]
    
    for description, expected_name in test_cases:
        intent = IntentRequest(description=description)
        plan = planner.plan(intent)
        assert plan.name == expected_name


def test_deterministic_planner_fallback_name() -> None:
    """Test fallback name when pattern doesn't match."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(description="Do something useful")
    plan = planner.plan(intent)
    
    assert plan.name == "generated-capability"


def test_deterministic_planner_description_generation() -> None:
    """Test description generation from intent."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a greeting capability",
        requirements={
            "input": "name (string)",
            "output": "greeting (string)"
        }
    )
    
    plan = planner.plan(intent)
    
    assert "Create a greeting capability" in plan.description
    assert "Input:" in plan.description or "name" in plan.description.lower()


def test_deterministic_planner_dependencies() -> None:
    """Test parsing dependencies from requirements."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a composite capability",
        requirements={
            "dependencies": [
                {"name": "parser", "version": "1.0.0"},
                {"name": "analyzer", "version": ">=2.0.0"}
            ]
        }
    )
    
    plan = planner.plan(intent)
    
    assert len(plan.dependencies) == 2
    assert plan.dependencies[0].name == "parser"
    assert plan.dependencies[0].version_constraint == "1.0.0"
    assert plan.dependencies[1].name == "analyzer"


def test_deterministic_planner_dependency_string_format() -> None:
    """Test parsing dependencies in string format."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a capability with dependencies",
        requirements={
            "dependencies": ["parser@1.0.0", "analyzer@>=2.0.0"]
        }
    )
    
    plan = planner.plan(intent)
    
    assert len(plan.dependencies) == 2
    assert plan.dependencies[0].name == "parser"
    assert plan.dependencies[0].version_constraint == "1.0.0"


def test_deterministic_planner_runtime_spec() -> None:
    """Test runtime spec generation."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(
        description="Create a test capability",
        requirements={"python_version": ">=3.11"}
    )
    
    plan = planner.plan(intent)
    
    assert plan.runtime.type == "python"
    assert plan.runtime.version_constraint == ">=3.11"
    assert ":" in plan.runtime.entrypoint  # module:function format


def test_deterministic_planner_metadata() -> None:
    """Test that planning metadata is included."""
    planner = DeterministicPlanner()
    
    intent = IntentRequest(description="Create a test capability")
    plan = planner.plan(intent)
    
    assert "planned_from_intent" in plan.metadata
    assert plan.metadata["planned_from_intent"] is True
    assert "original_description" in plan.metadata
