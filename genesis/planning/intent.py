"""
Intent Request Model

Represents user's high-level goal for capability creation.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class IntentRequest:
    """
    User's high-level goal for capability creation.
    
    The IntentRequest is the starting point of the Genesis lifecycle. It describes
    WHAT the user wants, not HOW to implement it.
    
    Example:
        intent = IntentRequest(
            description="Create a greeting capability that says hello to a name",
            requirements={
                "input": "name (string)",
                "output": "greeting message (string)"
            },
            constraints={
                "no_network": True,
                "no_filesystem": True
            }
        )
    
    Attributes:
        description: Natural language description of desired capability
        requirements: Structured requirements (inputs, outputs, behavior)
        constraints: Security and operational constraints
    """
    
    description: str
    requirements: dict[str, Any] = field(default_factory=dict)
    constraints: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        """Validate intent request."""
        if not self.description or not self.description.strip():
            raise ValueError("Intent description cannot be empty")
        
        if len(self.description) > 1000:
            raise ValueError("Intent description too long (max 1000 chars)")
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "description": self.description,
            "requirements": self.requirements,
            "constraints": self.constraints,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "IntentRequest":
        """Create from dictionary representation."""
        return cls(
            description=data["description"],
            requirements=data.get("requirements", {}),
            constraints=data.get("constraints", {}),
        )
    
    def __repr__(self) -> str:
        return f"IntentRequest(description={self.description!r})"
