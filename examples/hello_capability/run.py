"""
Hello Capability - Complete Genesis v0.1 Demonstration

This script demonstrates the complete Genesis lifecycle:
Intent → Plan → DNA → Artifact → Registry

Design: Shows all architectural components working together.
"""

from datetime import datetime
from pathlib import Path

from genesis.capabilities.artifact import CapabilityArtifact
from genesis.capabilities.manifest import Capability, CreatorType, Provenance
from genesis.capabilities.registry import CapabilityRegistry
from genesis.capabilities.validator import CapabilityValidator
from genesis.core.lifecycle import LifecycleManager, LifecycleState
from genesis.evaluation.evaluator import Evaluator
from genesis.execution.backend import SubprocessBackend
from genesis.observability.events import Event, EventEmitter, EventType
from genesis.planning.intent import IntentRequest
from genesis.planning.planner import DeterministicPlanner
from genesis.security.gates import ApprovalGate


def main() -> None:
    """
    Run complete Genesis lifecycle demonstration.
    
    This proves the v0.1 architecture end-to-end.
    """
    print("\n" + "="*70)
    print("GENESIS v0.1 - COMPLETE LIFECYCLE DEMONSTRATION")
    print("Intent → Plan → DNA → Artifact → Registry")
    print("="*70 + "\n")
    
    # Initialize components
    event_emitter = EventEmitter()
    lifecycle = LifecycleManager("hello-world@0.1.0")
    
    # ============================================================
    # STEP 1: INTENT
    # ============================================================
    print("[INTENT] User submits goal...")
    intent = IntentRequest(
        description="Create a greeting capability",
        requirements={
            "input": "name (string)",
            "output": "greeting message (string)"
        },
        constraints={
            "no_network": True,
            "no_filesystem": True
        }
    )
    print(f"  Description: {intent.description}")
    print(f"  Requirements: {intent.requirements}")
    print(f"  Constraints: {intent.constraints}")
    
    # ============================================================
    # STEP 2: PLANNING
    # ============================================================
    print("\n[PLANNING] Transforming intent into capability plan...")
    lifecycle.transition(LifecycleState.PLANNING)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_PLANNING_STARTED,
        timestamp=datetime.now(),
        capability_id="hello-world@0.1.0",
        actor="deterministic-planner",
        payload={"intent": intent.description}
    ))
    
    planner = DeterministicPlanner()
    plan = planner.plan(intent)
    
    lifecycle.transition(LifecycleState.PLANNED)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_PLANNED,
        timestamp=datetime.now(),
        capability_id="hello-world@0.1.0",
        actor="deterministic-planner",
        payload={"plan": plan.to_dict()}
    ))
    
    print(f"  ✓ Plan created: {plan.name}@{plan.version}")
    print(f"    Type: {plan.capability_type.value}")
    print(f"    Runtime: {plan.runtime.type}")
    print(f"    Entrypoint: {plan.runtime.entrypoint}")
    print(f"    Permissions (deny-by-default):")
    print(f"      - filesystem.read: {plan.permissions.filesystem_read}")
    print(f"      - filesystem.write: {plan.permissions.filesystem_write}")
    print(f"      - network.outbound: {plan.permissions.network_outbound}")
    print(f"      - process.spawn: {plan.permissions.process_spawn}")
    
    # ============================================================
    # STEP 3: DNA GENERATION
    # ============================================================
    print("\n[MANIFEST] Generating Capability DNA...")
    provenance = Provenance(
        created_by=CreatorType.GENESIS,  # Typed enum
        created_at=datetime.now(),
        parent_capabilities=[]  # No parents (leaf capability)
    )
    
    capability_dna = Capability.from_plan(plan, provenance)
    
    print(f"  ✓ Capability DNA created: {capability_dna.capability_id}")
    print(f"    API Version: {capability_dna.api_version}")
    print(f"    Provenance:")
    print(f"      - createdBy: {capability_dna.provenance.created_by.value}")
    print(f"      - createdAt: {capability_dna.provenance.created_at.isoformat()}")
    print(f"      - parentCapabilities: {capability_dna.provenance.parent_capabilities}")
    
    # ============================================================
    # STEP 4: VALIDATION
    # ============================================================
    print("\n[VALIDATION] Validating Capability DNA...")
    lifecycle.transition(LifecycleState.VALIDATING)
    
    validator = CapabilityValidator()
    validation_result = validator.validate(capability_dna)
    
    if validation_result.valid:
        lifecycle.transition(LifecycleState.VALIDATED)
        event_emitter.emit(Event(
            event_type=EventType.CAPABILITY_VALIDATED,
            timestamp=datetime.now(),
            capability_id=capability_dna.capability_id,
            actor="validator",
            payload={"valid": True}
        ))
        print("  ✓ Validation PASSED")
        if validation_result.warnings:
            print(f"  Warnings: {len(validation_result.warnings)}")
            for warning in validation_result.warnings:
                print(f"    - {warning}")
    else:
        print(f"  ✗ Validation FAILED: {validation_result.errors}")
        return
    
    # ============================================================
    # STEP 5: ARTIFACT CONSTRUCTION
    # ============================================================
    print("\n[ARTIFACT] Constructing capability artifact...")
    lifecycle.transition(LifecycleState.BUILDING)
    
    artifact = CapabilityArtifact.build(
        capability_dna=capability_dna,
        implementation_path=None,  # v0.1: No actual implementation
        evaluation_results={}
    )
    
    lifecycle.transition(LifecycleState.BUILT)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_BUILT,
        timestamp=datetime.now(),
        capability_id=artifact.artifact_id,
        actor="artifact-builder",
        payload={"artifact_id": artifact.artifact_id}
    ))
    
    print(f"  ✓ Artifact built: {artifact.artifact_id}")
    print(f"    Size: {artifact.metadata.size_bytes} bytes")
    print(f"    Checksums: {list(artifact.metadata.checksums.keys())}")
    
    # ============================================================
    # STEP 6: EXECUTION (Test Mode)
    # ============================================================
    print("\n[EXECUTION] Running tests via SubprocessBackend...")
    print("  (SubprocessBackend provides process isolation, NOT hardened sandbox)")
    lifecycle.transition(LifecycleState.TESTING)
    
    backend = SubprocessBackend(timeout=10)
    test_result = backend.execute(artifact, mode="test")
    
    lifecycle.transition(LifecycleState.TESTED)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_TESTED,
        timestamp=datetime.now(),
        capability_id=artifact.artifact_id,
        actor="subprocess-backend",
        payload={"success": test_result.success, "mode": "test"}
    ))
    
    if test_result.success:
        print("  ✓ Tests PASSED")
        print(f"    stdout: {test_result.stdout.strip()}")
    else:
        print(f"  ✗ Tests FAILED: {test_result.stderr}")
        return
    
    # ============================================================
    # STEP 7: EVALUATION
    # ============================================================
    print("\n[EVALUATION] Evaluating capability quality...")
    lifecycle.transition(LifecycleState.EVALUATING)
    
    evaluator = Evaluator()
    eval_result = evaluator.evaluate(artifact, test_result)
    
    lifecycle.transition(LifecycleState.EVALUATED)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_EVALUATED,
        timestamp=datetime.now(),
        capability_id=artifact.artifact_id,
        actor="evaluator",
        payload={"score": eval_result.score, "passed": eval_result.passed}
    ))
    
    print(f"  ✓ Evaluation complete: Score {eval_result.score}/100")
    if eval_result.issues:
        print(f"  Issues: {eval_result.issues}")
    
    # ============================================================
    # STEP 8: HUMAN APPROVAL GATE
    # ============================================================
    print("\n[SECURITY] Human approval required (ALL capabilities in v0.1)...")
    lifecycle.transition(LifecycleState.AWAITING_APPROVAL)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_AWAITING_APPROVAL,
        timestamp=datetime.now(),
        capability_id=artifact.artifact_id,
        actor="security-gate",
        payload={"reason": "All capabilities require approval in v0.1"}
    ))
    
    approval_gate = ApprovalGate()
    approval_decision = approval_gate.request_approval(artifact, eval_result)
    
    print(f"  Approval decision: {'APPROVED' if approval_decision.approved else 'REJECTED'}")
    print(f"  Reason: {approval_decision.reason}")
    print(f"  Actor: {approval_decision.actor}")
    
    if approval_decision.approved:
        lifecycle.transition(LifecycleState.APPROVED)
        event_emitter.emit(Event(
            event_type=EventType.CAPABILITY_APPROVED,
            timestamp=datetime.now(),
            capability_id=artifact.artifact_id,
            actor=approval_decision.actor,
            payload={"reason": approval_decision.reason}
        ))
    else:
        lifecycle.transition(LifecycleState.REJECTED)
        event_emitter.emit(Event(
            event_type=EventType.CAPABILITY_REJECTED,
            timestamp=datetime.now(),
            capability_id=artifact.artifact_id,
            actor=approval_decision.actor,
            payload={"reason": approval_decision.reason}
        ))
        print("  ✗ Capability REJECTED")
        return
    
    # ============================================================
    # STEP 9: REGISTRATION
    # ============================================================
    print("\n[REGISTRY] Registering capability artifact...")
    
    registry = CapabilityRegistry()
    registry.register(artifact)
    
    lifecycle.transition(LifecycleState.REGISTERED)
    event_emitter.emit(Event(
        event_type=EventType.CAPABILITY_REGISTERED,
        timestamp=datetime.now(),
        capability_id=artifact.artifact_id,
        actor="registry",
        payload={"registry_path": str(registry.registry_path)}
    ))
    
    print(f"  ✓ Capability REGISTERED: {artifact.artifact_id}")
    print(f"    Location: {registry.registry_path / artifact.artifact_id}")
    
    # ============================================================
    # VERIFICATION
    # ============================================================
    print("\n[VERIFICATION] Verifying registration...")
    
    retrieved = registry.get(artifact.name, artifact.version)
    if retrieved:
        print(f"  ✓ Capability retrieved successfully")
        print(f"    ID: {retrieved.artifact_id}")
        print(f"    Name: {retrieved.name}")
        print(f"    Version: {retrieved.version}")
        print(f"    Type: {retrieved.capability_dna.capability_type}")
    else:
        print("  ✗ Capability not found in registry")
        return
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*70)
    print("✓ GENESIS v0.1 LIFECYCLE COMPLETE")
    print("="*70)
    print(f"\nLifecycle States Traversed: {len(lifecycle.history)}")
    print("Path: " + " → ".join(s.value for s in lifecycle.history))
    print(f"\nFinal State: {lifecycle.current_state.value}")
    print(f"Artifact: {artifact.artifact_id}")
    print(f"Registry: {registry.registry_path}")
    print(f"Events: logs/events.jsonl")
    print("\n" + "="*70)
    print("Architecture Demonstrated:")
    print("  ✓ Intent → Specification (DeterministicPlanner)")
    print("  ✓ Declarative Capability DNA (no shell commands)")
    print("  ✓ Typed Provenance (HUMAN | GENESIS | IMPORTED)")
    print("  ✓ JSON Schema Validation")
    print("  ✓ Capability Artifact Concept")
    print("  ✓ Execution Boundary (SubprocessBackend)")
    print("  ✓ Human Approval Gate")
    print("  ✓ Artifact Registry")
    print("  ✓ Unified Event System")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
