"""
Planning Layer - Intent to Specification Transformation

This module provides the core Genesis capability: transforming high-level user
intent into concrete capability specifications.

Components:
- IntentRequest: User's high-level goal
- CapabilityPlan: Planned capability before manifestation
- CapabilityPlanner: Protocol for planning strategies
- DeterministicPlanner: Rule-based planner (v0.1)

Future:
- LLMPlanner: AI-powered planning
- MultiAgentPlanner: Collaborative planning
- RecursivePlanner: Capabilities that plan capabilities
"""

from genesis.planning.intent import IntentRequest
from genesis.planning.plan import CapabilityPlan, CapabilityType, RuntimeSpec
from genesis.planning.planner import CapabilityPlanner, DeterministicPlanner

__all__ = [
    "IntentRequest",
    "CapabilityPlan",
    "CapabilityType",
    "RuntimeSpec",
    "CapabilityPlanner",
    "DeterministicPlanner",
]
