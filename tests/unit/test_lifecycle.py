"""
Tests for Lifecycle State Machine.

Tests state transitions, invalid transitions, and terminal states.
"""

import pytest

from genesis.core.lifecycle import LifecycleManager, LifecycleState


def test_initial_state_is_draft():
    """A new LifecycleManager starts in DRAFT."""
    manager = LifecycleManager("greeting@0.1.0")
    assert manager.current_state == LifecycleState.DRAFT
    assert manager.history == [LifecycleState.DRAFT]


def test_happy_path_full_transition_chain():
    """The full lifecycle can traverse all states in order."""
    manager = LifecycleManager("greeting@0.1.0")
    happy_path = [
        LifecycleState.PLANNING,
        LifecycleState.PLANNED,
        LifecycleState.VALIDATING,
        LifecycleState.VALIDATED,
        LifecycleState.BUILDING,
        LifecycleState.BUILT,
        LifecycleState.TESTING,
        LifecycleState.TESTED,
        LifecycleState.EVALUATING,
        LifecycleState.EVALUATED,
        LifecycleState.AWAITING_APPROVAL,
        LifecycleState.APPROVED,
        LifecycleState.REGISTERED,
    ]
    for state in happy_path:
        manager.transition(state)

    assert manager.current_state == LifecycleState.REGISTERED
    assert manager.history == [LifecycleState.DRAFT, *happy_path]


def test_rejection_path_from_awaiting_approval():
    """A rejected capability goes to REJECTED, which is terminal."""
    manager = LifecycleManager("greeting@0.1.0")
    manager.transition(LifecycleState.PLANNING)
    manager.transition(LifecycleState.PLANNED)
    manager.transition(LifecycleState.VALIDATING)
    manager.transition(LifecycleState.VALIDATED)
    manager.transition(LifecycleState.BUILDING)
    manager.transition(LifecycleState.BUILT)
    manager.transition(LifecycleState.TESTING)
    manager.transition(LifecycleState.TESTED)
    manager.transition(LifecycleState.EVALUATING)
    manager.transition(LifecycleState.EVALUATED)
    manager.transition(LifecycleState.AWAITING_APPROVAL)
    manager.transition(LifecycleState.REJECTED)

    assert manager.current_state == LifecycleState.REJECTED
    # REJECTED is terminal: no further transition allowed
    assert manager.can_transition_to(LifecycleState.PLANNING) is False
    assert manager.TRANSITIONS[LifecycleState.REJECTED] == []


def test_invalid_transition_raises():
    """Skipping states raises ValueError."""
    manager = LifecycleManager("greeting@0.1.0")
    with pytest.raises(ValueError, match="Invalid transition"):
        manager.transition(LifecycleState.REGISTERED)
    # State unchanged after failed transition
    assert manager.current_state == LifecycleState.DRAFT


def test_backward_transition_is_invalid():
    """Cannot go back to a previous state."""
    manager = LifecycleManager("greeting@0.1.0")
    manager.transition(LifecycleState.PLANNING)
    with pytest.raises(ValueError, match="Invalid transition"):
        manager.transition(LifecycleState.DRAFT)


def test_can_transition_to_reports_validity():
    """can_transition_to distinguishes valid from invalid targets."""
    manager = LifecycleManager("greeting@0.1.0")
    assert manager.can_transition_to(LifecycleState.PLANNING) is True
    assert manager.can_transition_to(LifecycleState.APPROVED) is False


def test_all_states_have_transition_table_entry():
    """Every LifecycleState is a key in TRANSITIONS (exhaustive machine)."""
    for state in LifecycleState:
        assert state in LifecycleManager.TRANSITIONS
