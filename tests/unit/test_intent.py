"""Tests for IntentRequest model."""

import pytest

from genesis.planning.intent import IntentRequest


def test_intent_creation() -> None:
    """Test basic intent creation."""
    intent = IntentRequest(
        description="Create a greeting capability",
        requirements={"input": "name"},
        constraints={"no_network": True}
    )
    
    assert intent.description == "Create a greeting capability"
    assert intent.requirements == {"input": "name"}
    assert intent.constraints == {"no_network": True}


def test_intent_empty_description_fails() -> None:
    """Test that empty description raises ValueError."""
    with pytest.raises(ValueError, match="Intent description cannot be empty"):
        IntentRequest(description="")


def test_intent_whitespace_description_fails() -> None:
    """Test that whitespace-only description raises ValueError."""
    with pytest.raises(ValueError, match="Intent description cannot be empty"):
        IntentRequest(description="   ")


def test_intent_too_long_description_fails() -> None:
    """Test that overly long description raises ValueError."""
    long_desc = "x" * 1001
    with pytest.raises(ValueError, match="Intent description too long"):
        IntentRequest(description=long_desc)


def test_intent_defaults() -> None:
    """Test intent with default empty requirements/constraints."""
    intent = IntentRequest(description="Simple capability")
    
    assert intent.description == "Simple capability"
    assert intent.requirements == {}
    assert intent.constraints == {}


def test_intent_to_dict() -> None:
    """Test intent serialization to dict."""
    intent = IntentRequest(
        description="Test capability",
        requirements={"input": "data"},
        constraints={"no_network": True}
    )
    
    data = intent.to_dict()
    
    assert data == {
        "description": "Test capability",
        "requirements": {"input": "data"},
        "constraints": {"no_network": True}
    }


def test_intent_from_dict() -> None:
    """Test intent deserialization from dict."""
    data = {
        "description": "Test capability",
        "requirements": {"input": "data"},
        "constraints": {"no_network": True}
    }
    
    intent = IntentRequest.from_dict(data)
    
    assert intent.description == "Test capability"
    assert intent.requirements == {"input": "data"}
    assert intent.constraints == {"no_network": True}


def test_intent_from_dict_minimal() -> None:
    """Test intent deserialization with only description."""
    data = {"description": "Minimal capability"}
    
    intent = IntentRequest.from_dict(data)
    
    assert intent.description == "Minimal capability"
    assert intent.requirements == {}
    assert intent.constraints == {}


def test_intent_repr() -> None:
    """Test intent string representation."""
    intent = IntentRequest(description="Test capability")
    
    repr_str = repr(intent)
    
    assert "IntentRequest" in repr_str
    assert "Test capability" in repr_str
