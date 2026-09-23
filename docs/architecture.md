# CognitiveOS Genesis - Architecture

**Version**: 0.1.0  
**Status**: Implementation  
**Date**: 2026-09-23

---

## Table of Contents

1. [Overview](#overview)
2. [Core Principles](#core-principles)
3. [System Architecture](#system-architecture)
4. [Component Design](#component-design)
5. [Data Flow](#data-flow)
6. [Security Architecture](#security-architecture)
7. [Future Evolution](#future-evolution)

---

## Overview

Genesis is a **governed capability creation engine** for recursive AI systems. It transforms high-level intent into validated, secure, and governed capabilities through an explicit lifecycle.

### The Genesis Vision

Genesis demonstrates that AI systems can **create new capabilities** while maintaining:
- **Governance**: Explicit approval gates and security controls
- **Transparency**: Observable lifecycle with provenance tracking
- **Safety**: Deny-by-default permissions and honest security posture
- **Recursion**: Architecture designed for capabilities that create capabilities

### v0.1 Scope

This version proves the complete governed lifecycle from **Intent → Registry** using a deterministic planner (no LLM required).

**What v0.1 Demonstrates**:
```
User Intent
  ↓
Capability Planner (deterministic)
  ↓
Capability Plan
  ↓
Capability DNA (declarative manifest)
  ↓
Validation & Artifact Construction
  ↓
Controlled Execution Boundary
  ↓
Evaluation
  ↓
Human Approval Gate
  ↓
Artifact Registry
```

---

## Core Principles

### 1. Intent-Driven Architecture

**Capabilities emerge from intent, not manual assembly.**

```python
# User provides high-level intent
intent = IntentRequest(
    description="Create a greeting capability",
    requirements={"input": "name", "output": "greeting"},
    constraints={"no_network": True}
)

# Genesis transforms intent into specification
planner = DeterministicPlanner()
plan = planner.plan(intent)

# Plan becomes Capability DNA
dna = generate_manifest_from_plan(plan)
```

**Why This Matters**: Future versions will use LLM-based planners, enabling Genesis to autonomously design capabilities from natural language goals.

### 2. Declarative Capability DNA

**Capabilities describe WHAT they need, not HOW to execute.**

```yaml
# CORRECT - Declarative
runtime:
  type: python
  entrypoint: hello.main:greet

requirements:
  python: ">=3.11"

permissions:
  filesystem:
    read: false
    write: false
```

**NOT**:
```yaml
# INCORRECT - Imperative shell commands
lifecycle:
  run: "python main.py"  # ← RCE vulnerability
```

**Critical Distinction**:
- **Capability DNA**: Describes resources and constraints
- **Execution Backend**: Interprets DNA and controls execution

This separation prevents capability manifests from becoming remote code execution interfaces.

### 3. Capability DNA ≠ Capability Artifact

**Separation of Concerns**:

```
Capability DNA (specification)
  +
Implementation (code)
  +
Provenance (origin metadata)
  +
Evaluation Result (test outcomes)
  +
Integrity Metadata (checksums)
  =
Capability Artifact (distributable package)
```

**Registry stores Artifacts, not just DNA.**

### 4. Provenance Tracking

**Every capability records its origin.**

```yaml
provenance:
  createdBy: GENESIS  # Enum: HUMAN | GENESIS | IMPORTED
  createdAt: "2026-09-23T10:30:00Z"
  parentCapabilities: []  # Future: capability composition lineage
```

**Use Cases**:
- Audit trails: "Why does this capability exist?"
- Reproducibility: "Can I recreate this?"
- Evolution tracking: "What's the lineage?"
- Recursive analysis: "Which capabilities spawned others?"

### 5. Execution Boundary (Not Security Sandbox)

**Honest Security Posture**: v0.1 provides execution isolation, **NOT** hardened sandboxing.

```python
# Abstract interface
class ExecutionBackend(Protocol):
    def execute(self, artifact: CapabilityArtifact) -> ExecutionResult: ...

# v0.1 implementation
class SubprocessBackend(ExecutionBackend):
    """Process-level isolation (not hardened sandbox)."""
```

**v0.1 Reality**:
- ✅ Process isolation via subprocess
- ❌ NOT a hardened security sandbox
- ❌ Does NOT enforce filesystem/network restrictions at OS level
- ✅ Suitable for demonstration and trusted capabilities

**Future**: `ContainerBackend` will provide hardened isolation.

**Critical Terminology**:
- Use: "Execution Boundary"
- Not: "Security Sandbox" (unless technically accurate)

### 6. Permission Declaration ≠ OS-Level Enforcement

**v0.1 Permission Model**:

```yaml
permissions:
  filesystem:
    read: false
    write: false
  network:
    outbound: false
  process:
    spawn: false  # Capability cannot spawn children
                  # (Genesis CAN execute capability in subprocess)
```

**What This Means**:
- ✅ Permission declarations express **intended authorization policy**
- ✅ Deny-by-default model implemented
- ✅ Permission validation performed
- ❌ SubprocessBackend does NOT enforce filesystem/network restrictions at OS level

**Documentation Standard**:
> "v0.1 permission declarations express intended authorization policy. SubprocessBackend does not provide hardened OS-level enforcement of all declared permissions. Future ExecutionBackends may provide enforcement."

### 7. Human Approval Required

**v0.1 Governance**: ALL newly generated capabilities require explicit human approval before registration.

```
EVALUATED
  ↓
AWAITING_APPROVAL  ← Explicit state
  ↓
Human reviews: capability DNA, evaluation results, permissions
  ↓
APPROVED or REJECTED  ← Explicit decision
  ↓
REGISTERED (only if approved)
```

**No automated approval in v0.1.** Policy-based risk assessment is future work.

### 8. Model/Provider Agnostic

**No vendor lock-in.**

```python
# Protocol-based design
class ModelProvider(Protocol):
    def generate(self, prompt: str) -> str: ...
    def get_capabilities(self) -> ModelCapabilities: ...

# v0.1 mock implementation
class MockModelProvider(ModelProvider):
    """Deterministic responses for testing."""
```

**Future**: Real LLM integrations (Anthropic, OpenAI, Ollama, etc.) will implement the protocol without changing core architecture.

---

## System Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        USER                                  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │   IntentRequest      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ CapabilityPlanner    │
              │  (Deterministic)     │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  CapabilityPlan      │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │  Capability DNA      │
              │  (YAML + Provenance) │
              └──────────┬───────────┘
                         │
         ┌───────────────┴───────────────┐
         │                               │
         ▼                               ▼
┌────────────────┐              ┌────────────────┐
│   Validator    │              │  Capability    │
└────────┬───────┘              │  Artifact      │
         │                      └────────┬───────┘
         │                               │
         └───────────┬───────────────────┘
                     │
                     ▼
          ┌────────────────────┐
          │ ExecutionBackend   │
          │  (Subprocess)      │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │   Evaluator        │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │  Security Gate     │
          │  (Human Approval)  │
          └─────────┬──────────┘
                    │
                    ▼
          ┌────────────────────┐
          │ Capability Registry│
          │  (File-based)      │
          └────────────────────┘
```

### Module Structure

```
genesis/
├── planning/                  # Intent → Plan transformation
│   ├── intent.py             # IntentRequest model
│   ├── planner.py            # CapabilityPlanner protocol
│   └── plan.py               # CapabilityPlan model
│
├── capabilities/              # Capability domain
│   ├── manifest.py           # Capability DNA model
│   ├── artifact.py           # Capability Artifact model
│   ├── registry.py           # Artifact storage & retrieval
│   └── validator.py          # Schema validation
│
├── execution/                 # Execution abstraction
│   └── backend.py            # ExecutionBackend protocol + implementations
│
├── core/                      # Core engine
│   └── lifecycle.py          # State machine
│
├── security/                  # Security controls
│   ├── permissions.py        # Permission model
│   └── gates.py              # Approval gates
│
├── models/                    # Model abstraction
│   ├── interface.py          # ModelProvider protocol
│   └── registry.py           # Model selection
│
├── evaluation/                # Capability evaluation
│   └── evaluator.py          # Evaluation engine
│
└── observability/             # System observability
    └── events.py             # Unified event model (SINGLE LOCATION)
```

---

## Component Design

### Planning Layer

**Purpose**: Transform user intent into capability specifications.

```python
@dataclass
class IntentRequest:
    """User's high-level goal."""
    description: str
    requirements: dict[str, Any]
    constraints: dict[str, Any]

class CapabilityPlanner(Protocol):
    """Transforms intent into capability plan."""
    def plan(self, intent: IntentRequest) -> CapabilityPlan: ...

@dataclass
class CapabilityPlan:
    """Planned capability before manifestation."""
    name: str
    version: str
    capability_type: CapabilityType
    runtime: RuntimeSpec
    permissions: PermissionSet
    dependencies: list[Dependency]
```

**v0.1 Implementation**: `DeterministicPlanner`
- Rule-based logic
- No LLM dependency
- Proves architecture without external services

**Future Evolution**:
```
DeterministicPlanner (v0.1)
  ↓
LLMPlanner (v0.4) - Uses language models for planning
  ↓
MultiAgentPlanner (v0.6) - Collaborative planning
  ↓
RecursivePlanner (v0.8) - Capabilities plan capabilities
```

### Capability DNA

**Purpose**: Declarative specification of a capability's requirements and constraints.

```yaml
apiVersion: genesis.cognitiveos.dev/v1alpha1
kind: Capability
metadata:
  name: hello-world
  version: 0.1.0
  description: "Simple greeting capability"
  
  provenance:
    createdBy: GENESIS  # Enum value
    createdAt: "2026-09-23T10:30:00Z"
    parentCapabilities: []

spec:
  type: simple
  
  runtime:
    type: python
    entrypoint: hello_capability.main:greet
  
  requirements:
    python: ">=3.11"
  
  dependencies:
    capabilities: []
    models: []
  
  permissions:
    filesystem:
      read: false
      write: false
    network:
      outbound: false
    process:
      spawn: false
  
  evaluation:
    tests:
      - type: unit
        path: tests/unit
    approval_gates:
      - type: human
        required: true
```

**Validation**: JSON Schema ensures structural correctness.

### Capability Artifact

**Purpose**: Distributable package containing DNA + implementation + metadata.

```
Registry Structure:
capabilities/registry/hello-world@0.1.0/
├── artifact.yaml       # Artifact metadata
├── capability.yaml     # Capability DNA
├── implementation/     # Code files
├── evaluation.json     # Test results
├── provenance.json     # Detailed provenance
└── integrity.sha256    # Integrity checksums
```

**Artifact vs DNA**:
- **DNA**: Portable specification (what it is)
- **Artifact**: Complete distributable package (everything needed)

### Execution Backend

**Purpose**: Abstract execution boundary with pluggable implementations.

```python
class ExecutionBackend(Protocol):
    """Execution boundary abstraction."""
    def execute(
        self, 
        artifact: CapabilityArtifact, 
        **kwargs: Any
    ) -> ExecutionResult: ...

class InProcessBackend(ExecutionBackend):
    """Execute in current process (testing only)."""

class SubprocessBackend(ExecutionBackend):
    """Execute in isolated subprocess (v0.1)."""

class ContainerBackend(ExecutionBackend):
    """Execute in container (future - hardened sandbox)."""
```

**Process Permission Semantics**:

When a capability declares:
```yaml
permissions:
  process:
    spawn: false
```

This means: **The capability code itself cannot spawn child processes.**

It does NOT mean: **Genesis cannot launch the capability in a subprocess.**

**Critical Distinction**:
- **Genesis execution authority**: Can use SubprocessBackend to create execution boundary
- **Capability process permissions**: Capability code cannot spawn children

### Lifecycle State Machine

```
DRAFT
  ↓
PLANNING  ← Intent being transformed
  ↓
PLANNED
  ↓
VALIDATING
  ↓
VALIDATED
  ↓
BUILDING
  ↓
BUILT
  ↓
TESTING
  ↓
TESTED
  ↓
EVALUATING
  ↓
EVALUATED
  ↓
AWAITING_APPROVAL  ← Explicit human decision point
  ↓
[APPROVED] → REGISTERED
  ↓
[REJECTED] → Terminal state
```

**Operational States** (future, conceptual):
- REGISTERED: Exists in registry
- ENABLED: Available for execution
- DISABLED: Registered but inactive
- DEPRECATED: Marked for removal

**v0.1**: Focus on registration path only.

### Security Gates

**Purpose**: Human approval checkpoint before registration.

```python
class ApprovalGate:
    def request_approval(
        self, 
        artifact: CapabilityArtifact,
        evaluation: EvaluationResult
    ) -> ApprovalDecision: ...
```

**v0.1 Behavior**:
- ALL capabilities require approval
- No automated approval
- Interface displays: DNA, permissions, evaluation results
- Human makes explicit APPROVE/REJECT decision

**Future**: `PolicyEngine` for risk-based automated approval.

### Event System

**Purpose**: Observable system with structured event emission.

```python
@dataclass
class Event:
    event_type: EventType
    timestamp: datetime
    capability_id: str
    actor: str
    payload: dict[str, Any]

class EventEmitter:
    def emit(self, event: Event) -> None: ...
```

**Single Canonical Location**: `genesis/observability/events.py`

**Event Types**:
- CAPABILITY_PLANNING_STARTED
- CAPABILITY_PLANNED
- CAPABILITY_VALIDATED
- CAPABILITY_BUILT
- CAPABILITY_TESTED
- CAPABILITY_EVALUATED
- CAPABILITY_AWAITING_APPROVAL
- CAPABILITY_APPROVED
- CAPABILITY_REJECTED
- CAPABILITY_REGISTERED

**v0.1 Implementation**: JSON-lines log file  
**Future**: Event streaming infrastructure

---

## Data Flow

### Complete Lifecycle Flow

```
1. USER submits IntentRequest
     ↓
2. DeterministicPlanner.plan(intent) → CapabilityPlan
     ↓
3. generate_manifest_from_plan(plan) → Capability DNA (YAML)
     ↓
4. CapabilityValidator.validate(dna) → ValidationResult
     ↓
5. CapabilityArtifact.build(dna, implementation) → Artifact
     ↓
6. SubprocessBackend.execute(artifact, mode="test") → ExecutionResult
     ↓
7. Evaluator.evaluate(artifact, test_result) → EvaluationResult
     ↓
8. SecurityGate.request_approval(artifact, eval) → ApprovalDecision
     ↓
9. IF approved:
     CapabilityRegistry.register(artifact)
     → Stored in capabilities/registry/name@version/
     ↓
10. Capability available for retrieval and execution
```

### Event Flow

Every lifecycle transition emits an event:

```
[Event] CAPABILITY_PLANNING_STARTED
[Event] CAPABILITY_PLANNED
[Event] CAPABILITY_VALIDATED
[Event] CAPABILITY_BUILT
[Event] CAPABILITY_TESTED
[Event] CAPABILITY_EVALUATED
[Event] CAPABILITY_AWAITING_APPROVAL
[Event] CAPABILITY_APPROVED  (or REJECTED)
[Event] CAPABILITY_REGISTERED
```

Events logged to: `logs/events.jsonl`

---

## Security Architecture

### Defense in Depth

**Layer 1: Permission Declaration**
```yaml
permissions:
  filesystem:
    read: false
    write: false
  network:
    outbound: false
  process:
    spawn: false
```

**Default**: Deny all

**Layer 2: Approval Gates**
- Human approval required for ALL capabilities (v0.1)
- Explicit AWAITING_APPROVAL state
- No automatic bypass

**Layer 3: Execution Boundary**
- SubprocessBackend provides process isolation
- NOT OS-level permission enforcement
- Container-based enforcement is future work

### Security Invariants

1. **No shell commands in DNA**: Prevents RCE vulnerabilities
2. **Deny-by-default permissions**: Explicit opt-in required
3. **Human approval**: No capability activates without explicit approval
4. **Provenance tracking**: Every capability has origin metadata
5. **Immutable lifecycle**: State transitions are unidirectional
6. **Observable**: All security-relevant events are logged
7. **Honest posture**: Documentation accurate about what v0.1 provides

### What v0.1 Does NOT Provide

❌ **Hardened OS-level permission enforcement**  
❌ **Container-based sandboxing**  
❌ **Filesystem access control**  
❌ **Network traffic filtering**  
❌ **Process spawning prevention**  
❌ **Capability signing/verification**  
❌ **Cryptographic integrity guarantees**  

These are future work with hardened ExecutionBackends.

### What v0.1 DOES Provide

✅ **Permission declaration model**  
✅ **Permission validation**  
✅ **Deny-by-default policy**  
✅ **Human approval gates**  
✅ **Process-level isolation**  
✅ **Audit logging**  
✅ **Provenance tracking**  
✅ **Honest documentation**  

---

## Future Evolution

### Roadmap

**v0.1** (Current): Governed lifecycle with deterministic planner
- Intent → Plan → DNA → Registry
- SubprocessBackend
- Human approval for all
- Local file registry

**v0.2**: Capability Composition
- Capability + Capability → New Capability
- Dependency resolution
- Composite capability types

**v0.3**: Resource Intelligence
- Smart model selection
- Tool recommendation
- Service discovery

**v0.4**: Model-Driven Planning
- LLMPlanner implementation
- Natural language intent → specification
- Real LLM integrations (Anthropic, OpenAI, Ollama)

**v0.5**: Evolution Candidates
- Capability optimization suggestions
- Performance-based refinement
- A/B testing framework

**v0.6**: Multi-Agent Planning
- Collaborative capability design
- Specialized planner agents
- Consensus mechanisms

**v0.7**: Hardened Execution
- ContainerBackend implementation
- OS-level permission enforcement
- Filesystem/network isolation

**v0.8**: Recursive Capability Creation
- Capabilities that create capabilities
- Governance for recursive systems
- Lineage tracking

**v1.0**: CognitiveOS Integration
- Full integration with CognitiveOS
- Distributed execution
- Cloud registry
- Production hardening

### Extensibility Points

**Model Providers**: Implement `ModelProvider` protocol  
**Execution Backends**: Implement `ExecutionBackend` protocol  
**Planners**: Implement `CapabilityPlanner` protocol  
**Evaluators**: Extend `Evaluator` base class  
**Security Policies**: Implement `PolicyEngine` (future)  

### Architectural North Star

**Genesis enables capabilities to be built from other capabilities.**

The v0.1 architecture is designed to support this vision:
- Provenance tracking for lineage
- Artifact model for composition
- Permission model for security
- Approval gates for governance
- Event system for observability

Recursive capability creation will be introduced incrementally only after the lifecycle, governance, registry, and evaluation foundations are proven.

---

## References

- [Capability DNA Specification](capability-dna.md)
- [Security Model](security-model.md)
- [Roadmap](roadmap.md)
- [Architecture Decision Records](adr/)

---

**Document Version**: 1.0  
**Last Updated**: 2026-09-23  
**Status**: Implementation Baseline
