"""
Capability Lifecycle State Machine

Design: Immutable state transitions, event emission on transitions.
"""

from enum import StrEnum


class LifecycleState(StrEnum):
    """Capability lifecycle states."""

    DRAFT = "DRAFT"
    PLANNING = "PLANNING"
    PLANNED = "PLANNED"
    VALIDATING = "VALIDATING"
    VALIDATED = "VALIDATED"
    BUILDING = "BUILDING"
    BUILT = "BUILT"
    TESTING = "TESTING"
    TESTED = "TESTED"
    EVALUATING = "EVALUATING"
    EVALUATED = "EVALUATED"
    AWAITING_APPROVAL = "AWAITING_APPROVAL"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    REGISTERED = "REGISTERED"


class LifecycleManager:
    """Manages capability lifecycle transitions."""

    # Valid state transitions
    TRANSITIONS: dict[LifecycleState, list[LifecycleState]] = {
        LifecycleState.DRAFT: [LifecycleState.PLANNING],
        LifecycleState.PLANNING: [LifecycleState.PLANNED],
        LifecycleState.PLANNED: [LifecycleState.VALIDATING],
        LifecycleState.VALIDATING: [LifecycleState.VALIDATED],
        LifecycleState.VALIDATED: [LifecycleState.BUILDING],
        LifecycleState.BUILDING: [LifecycleState.BUILT],
        LifecycleState.BUILT: [LifecycleState.TESTING],
        LifecycleState.TESTING: [LifecycleState.TESTED],
        LifecycleState.TESTED: [LifecycleState.EVALUATING],
        LifecycleState.EVALUATING: [LifecycleState.EVALUATED],
        LifecycleState.EVALUATED: [LifecycleState.AWAITING_APPROVAL],
        LifecycleState.AWAITING_APPROVAL: [
            LifecycleState.APPROVED,
            LifecycleState.REJECTED
        ],
        LifecycleState.APPROVED: [LifecycleState.REGISTERED],
        LifecycleState.REJECTED: [],  # Terminal
        LifecycleState.REGISTERED: [],  # Terminal
    }

    def __init__(self, capability_id: str) -> None:
        self.capability_id = capability_id
        self.current_state = LifecycleState.DRAFT
        self.history: list[LifecycleState] = [LifecycleState.DRAFT]

    def transition(self, new_state: LifecycleState) -> None:
        """Transition to new state if valid."""
        valid_transitions = self.TRANSITIONS.get(self.current_state, [])

        if new_state not in valid_transitions:
            raise ValueError(
                f"Invalid transition from {self.current_state} to {new_state}"
            )

        self.current_state = new_state
        self.history.append(new_state)

    def can_transition_to(self, new_state: LifecycleState) -> bool:
        """Check if transition is valid."""
        return new_state in self.TRANSITIONS.get(self.current_state, [])
