# CognitiveOS Genesis v0.1 - Architecture Proposal

**Status**: REVISED (Post-Review)  
**Date**: 2026-09-23  
**Version**: 2.0 (Corrected)

---

## Executive Summary

This document proposes the complete architecture for CognitiveOS Genesis v0.1 — a minimal but complete vertical slice demonstrating the governed capability lifecycle **from intent to registry**.

**Current State**: Foundation exists (directories, basic docs, no code)  
**Goal**: Working end-to-end demo demonstrating **Intent → Plan → DNA → Artifact → Registry**  
**Timeline**: 10-14 focused development hours across 8 phases  
**Risk Level**: Low (minimal dependencies, well-scoped, architecturally sound)

---

## Key Architectural Decisions

### 1. Capability DNA Format: Declarative YAML (No Shell Commands)

**Choice**: YAML manifests describe WHAT a capability needs, not HOW to execute it

**Example**:
```yaml
apiVersion: genesis.cognitiveos.dev/v1alpha1
kind: Capability
metadata:
  name: hello-world
  version: 0.1.0
  
  provenance:
    createdBy: genesis  # or: human
    createdAt: "2026-09-23T10:30:00Z"
    parentCapabilities: []

spec:
  type: simple
  
  runtime:
    type: python
    entrypoint: hello_capability.main:greet
  
  requirements:
    python: ">=3.11"
  
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

**Why**:
- **Security**: No arbitrary shell commands (prevents RCE vulnerabilities)
- **Declarative**: Describes resources, not execution instructions
- **Controlled**: Execution happens through trusted `ExecutionBackend`
- **Provenance**: Tracks capability origin for recursive systems
- **Future-proof**: Supports AI-generated capabilities safely

---

### 2. Intent → Plan → DNA Flow

**The Genesis Heart**: Transform user intent into capability specifications

**Domain Contracts**:
```python
@dataclass
class IntentRequest:
    """User's high-level goal."""
    description: str
    requirements: dict
    constraints: dict

@dataclass
class CapabilityPlan:
    """Planned capability before manifestation."""
    name: str
    version: str
    type: CapabilityType
    runtime: RuntimeSpec
    permissions: PermissionSet
    dependencies: List[Dependency]

class CapabilityPlanner(Protocol):
    """Transforms intent into plan."""
    def plan(self, intent: IntentRequest) -> CapabilityPlan: ...
```

**v0.1 Implementation**: `DeterministicPlanner` (rule-based, no LLM)  
**Future**: LLMPlanner, AgenticPlanner

**Flow**:
```
IntentRequest("Create a greeting capability")
  ↓
DeterministicPlanner
  ↓
CapabilityPlan(name="hello-world", runtime=...)
  ↓
Capability DNA (YAML manifest)
```

**Why**: This demonstrates the core Genesis value proposition — automated capability specification from intent.

---

### 3. Lifecycle State Machine

```
DRAFT → PLANNING → PLANNED → VALIDATING → VALIDATED → 
BUILDING → BUILT → TESTING → TESTED → EVALUATING → 
EVALUATED → AWAITING_APPROVAL → APPROVED → REGISTERED
                                    ↓
                                REJECTED
```

**Key States**:
- **PLANNING**: Intent being transformed into plan
- **AWAITING_APPROVAL**: Explicit human decision required
- **REGISTERED**: Stored in registry (not automatically active)

**Principles**:
- Immutable states (no backwards transitions)
- Event emission on all transitions
- Human approval as explicit gate
- Registration ≠ Activation (capabilities can be registered but disabled)

---

### 4. Execution Boundary (Not Security Sandbox)

**Honest Security Posture**: v0.1 provides execution isolation, NOT hardened sandboxing

**Abstraction**:
```python
class ExecutionBackend(Protocol):
    """Abstract execution boundary."""
    def execute(self, artifact: CapabilityArtifact, **kwargs) -> ExecutionResult: ...

# Implementations:
class InProcessBackend(ExecutionBackend):
    """Execute in current process (testing only)"""
    
class SubprocessBackend(ExecutionBackend):
    """Execute in isolated subprocess (v0.1)"""
    
class ContainerBackend(ExecutionBackend):
    """Execute in container (future - hardened sandbox)"""
```

**v0.1 Reality**:
- Uses `SubprocessBackend`
- Provides process isolation
- **NOT considered a security sandbox**
- Suitable for demonstration and trusted capabilities
- Container-based hardening is future work

**Why**: Technical honesty. We don't claim security guarantees we don't provide.

---

### 5. Capability Artifact Concept

**Separation of Concerns**:
```
Capability DNA (what it is)
  +
Implementation (code)
  +
Evaluation Result (test outcomes)
  +
Provenance (origin)
  +
Integrity Metadata (checksums)
  =
Capability Artifact (distributable package)
```

**Registry Structure**:
```
capabilities/registry/
  hello-world@0.1.0/
    artifact.yaml         # Artifact metadata
    capability.yaml       # Capability DNA
    implementation/       # Code
    evaluation.json       # Test results
    provenance.json       # Provenance tracking
    integrity.sha256      # Integrity checksums
```

**Why**: Prepares for future distribution, signing, and verification.

---

### 6. Security Model: Defense in Depth

**Layer 1 - Permission Declaration** (manifest-level)
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
Default: Deny all

**Layer 2 - Approval Gates** (lifecycle-level)
```
ALL newly generated capabilities require explicit human approval.
```
No automatic approval in v0.1. Future: Policy-based risk assessment.

**Layer 3 - Execution Boundary** (runtime-level)
```
SubprocessBackend provides process isolation.
ContainerBackend (future) provides hardened sandbox.
```

**Principles**:
- Deny by default
- Least privilege
- Explicit approval
- Auditability

---

### 7. Registry: File-Based Artifact Storage

```
capabilities/
  registry/
    hello-world@0.1.0/
      artifact.yaml
      capability.yaml
      implementation/
      evaluation.json
      provenance.json
      integrity.sha256
  index.json
```

**Operations**:
- register(artifact), get(name, version), list()
- Minimal dependency validation (no complex resolution)
- Simple, testable, no external infrastructure

**Why**: Sufficient for v0.1, interface designed for future database/distributed registry.

---

### 8. Model Abstraction: Provider-Agnostic

```python
class ModelProvider(Protocol):
    def generate(self, prompt: str, **kwargs) -> str: ...
    def get_capabilities(self) -> ModelCapabilities: ...

class ModelRegistry:
    def register(name: str, provider: ModelProvider): ...
    def select(requirements: ModelRequirements) -> ModelProvider: ...
```

**v0.1**: Interface + mock provider only  
**Future**: Real LLM integrations, intelligent routing

---

### 9. Event System: Unified Observability

```python
# genesis/observability/events.py (single canonical location)

@dataclass
class Event:
    event_type: EventType
    timestamp: datetime
    capability_id: str
    actor: str
    payload: dict

class EventEmitter:
    def emit(self, event: Event) -> None: ...
```

**EventTypes**:
- CAPABILITY_PLANNING_STARTED
- CAPABILITY_PLANNED
- CAPABILITY_VALIDATED
- CAPABILITY_TESTED
- CAPABILITY_AWAITING_APPROVAL
- CAPABILITY_APPROVED
- CAPABILITY_REJECTED
- CAPABILITY_REGISTERED

**v0.1**: JSON-lines log file  
**Future**: Event streaming infrastructure

---

## Complete Vertical Slice

### The "Hello Capability" Demonstration

**What**: Simple greeting capability demonstrating **Intent → Specification → Registry**

**Why This Example**:
- ✅ Proves the complete Genesis lifecycle
- ✅ No external dependencies
- ✅ No security risks
- ✅ Demonstrates AI capability generation pattern (even though planner is deterministic)
- ✅ Easy to understand and verify

### Full Lifecycle Flow

**1. Intent Submission**
```python
intent = IntentRequest(
    description="Create a greeting capability that says hello to a given name",
    requirements={
        "input": "name (string)",
        "output": "greeting message (string)"
    },
    constraints={
        "no_network": True,
        "no_filesystem": True
    }
)
```

**2. Planning (DeterministicPlanner)**
```python
planner = DeterministicPlanner()
plan = planner.plan(intent)
# Result: CapabilityPlan with runtime spec, permissions, etc.
```

**3. DNA Generation**
```python
dna = generate_manifest_from_plan(plan)
# Produces capability.yaml with:
# - provenance: createdBy=genesis
# - runtime: type=python, entrypoint=...
# - permissions: deny-by-default
# - NO shell commands
```

**4. Validation**
```python
validator = CapabilityValidator()
result = validator.validate(dna)
assert result.valid
```

**5. Artifact Construction**
```python
artifact = CapabilityArtifact.build(
    dna=dna,
    implementation=load_implementation(),
    provenance=extract_provenance(dna)
)
```

**6. Testing via ExecutionBackend**
```python
backend = SubprocessBackend()
test_result = backend.execute(artifact, mode="test")
assert test_result.success
```

**7. Evaluation**
```python
evaluator = Evaluator()
eval_result = evaluator.evaluate(artifact, test_result)
```

**8. Human Approval Gate**
```python
gate = ApprovalGate()
decision = gate.request_approval(artifact, eval_result)
# Output: "Capability hello-world@0.1.0 requires approval. Approve? (y/n)"
```

**9. Registration**
```python
if decision.approved:
    registry = CapabilityRegistry()
    registry.register(artifact)
    # Stored in: capabilities/registry/hello-world@0.1.0/
```

**Success Metric**: 
```bash
python examples/hello_capability/run.py
```

**Expected Output**:
```
[INTENT] Processing: Create a greeting capability...
[PLANNING] Generating capability plan...
[PLANNING] ✓ Plan created: hello-world@0.1.0
[MANIFEST] Generating Capability DNA...
[VALIDATION] Validating manifest...
[VALIDATION] ✓ Valid
[ARTIFACT] Constructing artifact...
[EXECUTION] Running tests...
[EXECUTION] ✓ All tests passed
[EVALUATION] Score: 100/100
[SECURITY] Human approval required
[APPROVAL] Approve hello-world@0.1.0? (y/n): y
[REGISTRY] Registering artifact...
[REGISTRY] ✓ Registered: hello-world@0.1.0
[DEMO] Executing capability...
Hello, World!
```

---

## Implementation Scope

### What v0.1 WILL Have

✅ **Intent → Specification Flow**: IntentRequest → DeterministicPlanner → CapabilityPlan → DNA  
✅ **Declarative Capability DNA**: No shell commands, runtime specs only  
✅ **Provenance Tracking**: createdBy, parentCapabilities  
✅ **Artifact Concept**: DNA + implementation + provenance + integrity  
✅ **Manifest Validation**: YAML + JSON Schema  
✅ **Local Artifact Registry**: File-based storage  
✅ **Permission Model**: Deny-by-default, declarative permissions  
✅ **Approval Gates**: Human approval required for all new capabilities  
✅ **Execution Boundary**: SubprocessBackend with honest security documentation  
✅ **Lifecycle State Machine**: Complete state transitions with events  
✅ **Unified Event System**: Single canonical event model  
✅ **Model Abstraction**: Provider-agnostic interface (mock implementation)  
✅ **Hello Capability Example**: Full Intent → Registry demonstration  
✅ **Comprehensive Tests**: Unit + integration + security (>70% coverage)  
✅ **Complete Documentation**: Architecture, security, capability DNA specs  
✅ **Professional Setup**: pyproject.toml, ruff, mypy, pytest  

### What v0.1 Will NOT Have

❌ Real LLM integration (DeterministicPlanner only)  
❌ LLMPlanner or AgenticPlanner  
❌ Recursive capability composition  
❌ Advanced dependency resolution (v0.2)  
❌ Container-based hardened sandbox  
❌ Policy-based approval automation  
❌ Web UI or API  
❌ External registry support  
❌ Capability evolution engine  
❌ Distributed execution  
❌ Cloud deployment  
❌ Artifact signing (beyond checksums)  

---

## Technology Stack

**Core**:
- Python 3.11+ (we have 3.14.4)
- pydantic (data validation)
- pyyaml (YAML parsing)
- jsonschema (schema validation)

**Development**:
- pytest (testing)
- ruff (linting + formatting)
- mypy (type checking)
- pytest-cov (coverage)

**Rationale**: Minimal, industry-standard dependencies. No vendor lock-in.

---

## Files to Create (~25 total)

**Planning Layer**: 3 files  
**Capability Core**: 5 files  
**Execution**: 2 files  
**Lifecycle**: 2 files  
**Security**: 3 files  
**Models**: 3 files  
**Evaluation**: 2 files  
**Observability**: 2 files  
**Example**: 4 files  
**Schema**: 1 file  
**Tests**: 8 files  
**Config**: 3 files  
**Docs**: 7 files  

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for complete module structure.

---

## Implementation Phases

**PHASE 0**: Foundation (git init, pyproject.toml) — 0.5 hours  
**PHASE 1**: Documentation (architecture, capability DNA, security) — 1.5 hours  
**PHASE 2**: Planning layer (intent, planner, plan models) — 1.5 hours  
**PHASE 3**: Capability layer (manifest, artifact, validator) — 2 hours  
**PHASE 4**: Execution + lifecycle — 2 hours  
**PHASE 5**: Security + approval gates — 1.5 hours  
**PHASE 6**: Models + evaluation — 1 hour  
**PHASE 7**: Hello capability with full flow — 2 hours  
**PHASE 8**: Testing + quality assurance — 2 hours  
**PHASE 9**: Final documentation — 1 hour  

**Total**: 10-14 hours of focused development

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Planning layer complexity | Low | Medium | Keep DeterministicPlanner rule-based and minimal |
| Shell command removal impact | None | None | Corrected before implementation |
| Artifact concept overhead | Low | Low | Minimal v0.1 implementation, justified by future needs |
| Approval gate UX | Low | Low | Interface allows multiple implementations |
| Scope creep | Medium | Medium | Strict phase gates, deferred v0.2 features explicitly |
| Provider lock-in | None | None | Protocol-based design prevents this |

**Overall Risk**: LOW  
**Reason**: Well-scoped, architecturally sound, security-conscious

---

## Definition of Done

v0.1 is complete when:

### Architecture
1. ✅ Intent → Plan → DNA flow works end-to-end
2. ✅ No shell commands in Capability DNA (runtime specs only)
3. ✅ ExecutionBackend abstraction with SubprocessBackend implementation
4. ✅ Documentation clarifies execution boundary (not hardened sandbox)
5. ✅ Provenance in all capability manifests
6. ✅ Capability Artifact concept demonstrated
7. ✅ Single unified event model

### Functionality
8. ✅ `IntentRequest` → `DeterministicPlanner` → `CapabilityPlan` works
9. ✅ CapabilityPlan converts to Capability DNA (YAML)
10. ✅ DNA validates against JSON Schema
11. ✅ Artifact construction succeeds
12. ✅ SubprocessBackend executes capabilities
13. ✅ All new capabilities require human approval
14. ✅ Approved artifacts register in local registry
15. ✅ Registered artifacts can be retrieved

### Testing
16. ✅ All unit tests pass
17. ✅ Integration test demonstrates full Intent → Registry flow
18. ✅ Security tests verify permission enforcement
19. ✅ Test coverage >70%

### Quality
20. ✅ `ruff check` passes (0 errors)
21. ✅ `mypy` passes (0 errors)
22. ✅ All Python files have type hints

### Documentation
23. ✅ docs/architecture.md reflects actual implementation
24. ✅ docs/capability-dna.md shows declarative runtime specs
25. ✅ docs/security-model.md clarifies execution boundaries
26. ✅ ADR for manifest format decision
27. ✅ README accurate and complete

### Demonstration
28. ✅ `python examples/hello_capability/run.py` demonstrates:
    - Intent submission
    - Deterministic planning
    - DNA generation (with provenance)
    - Validation
    - Artifact construction
    - Execution via SubprocessBackend
    - Testing
    - Human approval request
    - Registration
    - Final execution

### Repository
29. ✅ Git initialized with clean commit history
30. ✅ `pip install -e .` works
31. ✅ No secrets committed
32. ✅ .gitignore properly configured

---

## Critical Architectural Invariants

These principles MUST be maintained:

1. **No Shell Commands in DNA**: Capability manifests describe resources, not execution instructions
2. **Intent-Driven**: Architecture must support Intent → Plan → DNA flow
3. **Model Agnostic**: Never hardcode to specific LLM provider
4. **Security First**: Deny-by-default permissions, explicit approval gates
5. **Honest Security Posture**: No false claims about sandboxing
6. **Provenance Tracking**: All capabilities track origin (createdBy, parents)
7. **Observable**: All lifecycle transitions emit events
8. **Testable**: No feature without tests
9. **Reversible**: No uncontrolled self-modification
10. **Documented**: Architecture decisions recorded (ADRs)
11. **Minimal**: No dependencies without justification
12. **Extensible**: Interfaces designed for future needs (LLMPlanner, ContainerBackend, etc.)

---

## Questions for Approval

Before implementation begins, please confirm:

### Core Architecture
- ✅/❌ YAML manifests with JSON Schema validation
- ✅/❌ File-based local registry (no database)
- ✅/❌ Three-layer security model
- ✅/❌ Protocol-based model abstraction

### Scope
- ✅/❌ Hello capability as demonstration example
- ✅/❌ No real LLM integration in v0.1
- ✅/❌ Mock providers for testing only
- ✅/❌ Process-level sandboxing (not container-based)

### Implementation
- ✅/❌ 8-phase sequential implementation
- ✅/❌ Minimal dependencies (pydantic, pyyaml, jsonschema)
- ✅/❌ >70% test coverage target
- ✅/❌ Complete documentation before coding

### Timeline
- ✅/❌ 8-12 hour estimated timeline acceptable
- ✅/❌ Phase-by-phase approach (not big-bang)

---

## Alternative Approaches Considered

### Capability DNA: Declarative vs Imperative
**Chosen**: Declarative (runtime specs, no shell commands)  
**Rationale**: Security, future AI generation safety  
**Rejected**: Imperative shell commands (RCE vulnerability)

### Planning: LLM vs Deterministic
**Chosen**: Deterministic for v0.1  
**Rationale**: Proves architecture without LLM dependency/cost  
**Deferred**: LLMPlanner to v0.4

### Execution: Container vs Subprocess
**Chosen**: Subprocess (v0.1)  
**Rationale**: Simpler, adequate for demonstration  
**Deferred**: Container-based hardened sandbox to future version

### Registry: Database vs File-Based
**Chosen**: File-based  
**Rationale**: No infrastructure, easier testing  
**Rejected**: Database (premature optimization)

### Manifest: YAML vs JSON vs TOML
**Chosen**: YAML  
**Rationale**: Human-readable, comments, git-friendly  
**Rejected**: JSON (less readable), TOML (less common for manifests)

### Approval: Automated Risk-Based vs Always Human
**Chosen**: Always human (v0.1)  
**Rationale**: Simpler, safer default  
**Deferred**: Policy-based risk assessment to v0.2+

### Events: Separate core/observability vs Unified
**Chosen**: Unified (genesis/observability/events.py)  
**Rationale**: Avoids duplication  
**Rejected**: Duplicate event concepts

---

## Success Criteria

**Technical Success**:
- Intent → Plan → DNA → Registry works end-to-end
- No shell commands in manifests
- All tests pass (>70% coverage)
- Type checking passes (mypy)
- Linting passes (ruff)
- Hello capability demonstrates full lifecycle

**Architectural Success**:
- Clean abstractions with clear responsibilities
- No vendor lock-in (provider-agnostic)
- Extensible interfaces (DeterministicPlanner → LLMPlanner path clear)
- Security principles demonstrable
- Honest documentation about capabilities/limitations

**Documentation Success**:
- README accurate and compelling
- Architecture fully documented
- Security model clearly explained
- Capability DNA spec complete
- ADRs for key decisions
- Future developer can onboard and extend

**Project Success**:
- Under git control with clean history
- Professional Python project (pyproject.toml, ruff, mypy)
- Open source ready (LICENSE, CONTRIBUTING, SECURITY)
- Foundation proven for v0.2+ (composition, LLM planning, evolution)

---

## Next Steps

**Current Status**: Architecture revised and corrected per review feedback.

**Upon final approval**:

1. **Complete PHASE 0**: Git init, pyproject.toml, .gitignore
2. **Begin PHASE 1**: Write architectural documentation
3. **PHASE 2**: Implement planning layer (IntentRequest, DeterministicPlanner, CapabilityPlan)
4. **PHASE 3**: Implement capability layer (manifest with provenance, artifact, validator)
5. **PHASE 4**: Implement execution + lifecycle (SubprocessBackend, state machine)
6. **PHASE 5**: Implement security (permissions, approval gates)
7. **PHASE 6**: Implement models + evaluation
8. **PHASE 7**: Build hello capability with complete Intent → Registry flow
9. **PHASE 8**: Testing + quality assurance (pytest, ruff, mypy)
10. **PHASE 9**: Final documentation + CLAUDE.md
11. **Update PROGRESS.md** after each completed phase
12. **Final review** and development report

---

## Architectural Review

**Original Status**: AWAITING APPROVAL  
**Review Status**: CORRECTIONS APPLIED  
**Current Status**: AWAITING FINAL APPROVAL

**Key Corrections Applied**:
1. ✅ Removed shell commands from Capability DNA
2. ✅ Restored Intent → Specification flow (the Genesis heart)
3. ✅ Clarified execution boundary (not hardened sandbox)
4. ✅ Added provenance tracking
5. ✅ Introduced Capability Artifact concept
6. ✅ Clarified human approval semantics
7. ✅ Separated registration from activation
8. ✅ Limited dependency resolution scope
9. ✅ Unified event model
10. ✅ Preserved all sound original decisions

**All corrections accepted** - see [ARCHITECTURE_REVIEW_RESPONSE.md](ARCHITECTURE_REVIEW_RESPONSE.md) for details.

---

## Request for Final Approval

**This revised architecture is ready for implementation.**

Please confirm:
- ✅ Intent → Plan → DNA flow (DeterministicPlanner, no LLM)
- ✅ Declarative Capability DNA (no shell commands)
- ✅ Execution boundary abstraction (SubprocessBackend, honest docs)
- ✅ Provenance tracking in manifests
- ✅ Human approval required for all capabilities
- ✅ File-based artifact registry
- ✅ Minimal scope (no v0.2 features)

**If approved, implementation will begin immediately with PHASE 0.**

---

**Document Version**: 2.0 (Corrected)  
**Prepared by**: Kiro (AI Engineering Agent)  
**Review Date**: 2026-09-23  
**Session**: CognitiveOS Genesis Bootstrap
