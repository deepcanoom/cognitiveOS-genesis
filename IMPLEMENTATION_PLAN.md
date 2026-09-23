# CognitiveOS Genesis v0.1 - Implementation Plan (REVISED)

**Status**: Corrected Architecture (Awaiting Final Approval)  
**Date**: 2026-09-23  
**Version**: 2.0

---

## Document Purpose

This is the detailed implementation plan for CognitiveOS Genesis v0.1, incorporating all architectural corrections from the review process.

**Key Changes from V1**:
- ✅ Intent → Plan → DNA flow added
- ✅ Shell commands removed from Capability DNA
- ✅ Execution boundary clarified (not hardened sandbox)
- ✅ Provenance tracking added
- ✅ Artifact concept introduced
- ✅ Human approval semantics clarified
- ✅ Event model unified
- ✅ Dependency resolution simplified

---

## Revised Module Structure

```
genesis/
  __init__.py
  
  # PLANNING LAYER (New)
  planning/
    __init__.py
    intent.py              # IntentRequest model
    planner.py             # Planner protocol + DeterministicPlanner impl
    plan.py                # CapabilityPlan model
  
  # CAPABILITY CORE (Enhanced with provenance + artifact)
  capabilities/
    __init__.py
    manifest.py            # Capability DNA model (with provenance)
    artifact.py            # CapabilityArtifact concept
    validator.py           # JSON Schema validation
    registry.py            # File-based artifact registry
    resolver.py            # Minimal dependency validation (no complex resolution)
  
  # LIFECYCLE
  core/
    __init__.py
    lifecycle.py           # State machine
    states.py              # State enum
  
  # EXECUTION (ExecutionBackend abstraction)
  execution/
    __init__.py
    backend.py             # ExecutionBackend protocol
    subprocess_backend.py  # SubprocessBackend implementation
  
  # MODELS (abstraction only, mock impl)
  models/
    __init__.py
    interface.py           # ModelProvider protocol
    registry.py            # Model registry
    mock_provider.py       # Mock implementation for v0.1
  
  # SECURITY
  security/
    __init__.py
    permissions.py         # Permission model (deny-by-default)
    gates.py               # Approval gates (human required)
    policies.py            # Future: PolicyEngine interface (stub)
  
  # EVALUATION
  evaluation/
    __init__.py
    runner.py              # Test execution
    results.py             # EvaluationResult model
  
  # OBSERVABILITY (unified, no duplication)
  observability/
    __init__.py
    events.py              # Event model + EventEmitter (canonical)
    logger.py              # Structured logging

schemas/
  capability.schema.json   # JSON Schema for Capability DNA

examples/
  hello_capability/
    run.py                 # Full Intent → Registry demonstration
    implementation/
      __init__.py
      main.py              # Greeting logic
    tests/
      test_greet.py

tests/
  __init__.py
  
  unit/
    test_intent.py
    test_planner.py
    test_manifest.py
    test_artifact.py
    test_validator.py
    test_registry.py
    test_lifecycle.py
    test_permissions.py
    test_execution_backend.py
  
  integration/
    test_full_lifecycle.py
  
  security/
    test_permission_enforcement.py
```

**Total Core Modules**: ~25 Python files  
**Total Test Files**: ~10 test files  
**Documentation**: 7 files

---

## Implementation Phases (Revised)

### PHASE 0: Foundation (COMPLETE REMAINING)

**Goal**: Establish Python project infrastructure and version control

**Tasks**:
1. ✅ Repository structure exists
2. Create `pyproject.toml`
3. Create `.gitignore`
4. Create `.env.example`
5. Initialize git repository
6. Create initial commit

**Exit Criteria**: `pip install -e .` works, git initialized

---

### PHASE 1: Documentation

**Goal**: Document the corrected architecture before implementing

**Files**:
1. `docs/vision.md` - What Genesis is and why
2. `docs/architecture.md` - Complete system design
3. `docs/capability-dna.md` - Manifest specification (declarative, no shell commands)
4. `docs/security-model.md` - Execution boundaries, permissions, approval gates
5. `docs/roadmap.md` - v0.1 → v0.2 → ... → CognitiveOS integration
6. `docs/adr/001-manifest-format.md` - ADR: YAML with runtime specs
7. `docs/adr/002-execution-backend.md` - ADR: ExecutionBackend abstraction

**Exit Criteria**: Architecture fully documented, reviewable

---

### PHASE 2: Planning Layer

**Goal**: Implement Intent → Plan transformation

**Files**:
1. `genesis/planning/__init__.py`
2. `genesis/planning/intent.py`
   ```python
   @dataclass
   class IntentRequest:
       description: str
       requirements: dict
       constraints: dict
   ```

3. `genesis/planning/plan.py`
   ```python
   @dataclass
   class CapabilityPlan:
       name: str
       version: str
       type: CapabilityType
       runtime: RuntimeSpec
       permissions: PermissionSet
       dependencies: List[Dependency]
   ```

4. `genesis/planning/planner.py`
   ```python
   class CapabilityPlanner(Protocol):
       def plan(self, intent: IntentRequest) -> CapabilityPlan: ...
   
   class DeterministicPlanner:
       """Rule-based planner (no LLM)."""
       def plan(self, intent: IntentRequest) -> CapabilityPlan:
           # Simple transformation logic
           ...
   ```

5. `tests/unit/test_intent.py`
6. `tests/unit/test_planner.py`

**Exit Criteria**: 
- `IntentRequest` → `DeterministicPlanner` → `CapabilityPlan` works
- Tests pass

---

### PHASE 3: Capability Layer

**Goal**: Implement Capability DNA with provenance and artifact concept

**Files**:
1. `genesis/capabilities/__init__.py`

2. `genesis/capabilities/manifest.py`
   ```python
   @dataclass
   class Provenance:
       created_by: str  # "human" or "genesis"
       created_at: datetime
       parent_capabilities: List[str]
   
   @dataclass
   class CapabilityDNA:
       api_version: str
       kind: str
       metadata: Metadata  # includes provenance
       spec: CapabilitySpec  # runtime, permissions (NO shell commands)
   ```

3. `genesis/capabilities/artifact.py`
   ```python
   @dataclass
   class CapabilityArtifact:
       dna: CapabilityDNA
       implementation: Path
       provenance: Provenance
       evaluation: Optional[EvaluationResult]
       integrity: IntegrityMetadata
   ```

4. `genesis/capabilities/validator.py`
   ```python
   class CapabilityValidator:
       def validate(self, dna: CapabilityDNA) -> ValidationResult:
           # JSON Schema validation
           ...
   ```

5. `genesis/capabilities/registry.py`
   ```python
   class CapabilityRegistry:
       def register(self, artifact: CapabilityArtifact) -> None: ...
       def get(self, name: str, version: str) -> CapabilityArtifact: ...
       def list(self) -> List[CapabilityMetadata]: ...
   ```

6. `genesis/capabilities/resolver.py`
   ```python
   class DependencyResolver:
       def validate_dependencies(self, dna: CapabilityDNA) -> ValidationResult:
           # Minimal: self-reference check, obvious cycles
           # NOT full semantic version resolution (deferred to v0.2)
           ...
   ```

7. `schemas/capability.schema.json` - JSON Schema

8. Tests:
   - `test_manifest.py`
   - `test_artifact.py`
   - `test_validator.py`
   - `test_registry.py`

**Exit Criteria**:
- CapabilityPlan → CapabilityDNA works
- DNA validates against schema
- Artifacts can be constructed
- Registry can store and retrieve artifacts
- Tests pass

---

### PHASE 4: Execution + Lifecycle

**Goal**: Implement execution boundary and state machine

**Files**:
1. `genesis/execution/__init__.py`

2. `genesis/execution/backend.py`
   ```python
   class ExecutionBackend(Protocol):
       """Abstract execution boundary (NOT hardened sandbox)."""
       def execute(self, artifact: CapabilityArtifact, mode: str, **kwargs) -> ExecutionResult: ...
   ```

3. `genesis/execution/subprocess_backend.py`
   ```python
   class SubprocessBackend:
       """Subprocess execution (v0.1 execution boundary)."""
       def execute(self, artifact: CapabilityArtifact, mode: str, **kwargs) -> ExecutionResult:
           # Execute using subprocess, capture output
           ...
   ```

4. `genesis/core/__init__.py`

5. `genesis/core/states.py`
   ```python
   class LifecycleState(Enum):
       DRAFT = "draft"
       PLANNING = "planning"
       PLANNED = "planned"
       VALIDATING = "validating"
       VALIDATED = "validated"
       BUILDING = "building"
       BUILT = "built"
       TESTING = "testing"
       TESTED = "tested"
       EVALUATING = "evaluating"
       EVALUATED = "evaluated"
       AWAITING_APPROVAL = "awaiting_approval"
       APPROVED = "approved"
       REJECTED = "rejected"
       REGISTERED = "registered"
   ```

6. `genesis/core/lifecycle.py`
   ```python
   class CapabilityLifecycle:
       def transition(self, from_state: LifecycleState, to_state: LifecycleState) -> None:
           # Validate transition, emit event
           ...
   ```

7. Tests:
   - `test_execution_backend.py`
   - `test_lifecycle.py`

**Exit Criteria**:
- ExecutionBackend abstraction works
- SubprocessBackend can execute Python code
- Lifecycle state transitions work
- Tests pass

---

### PHASE 5: Security + Approval

**Goal**: Implement permissions and human approval gates

**Files**:
1. `genesis/security/__init__.py`

2. `genesis/security/permissions.py`
   ```python
   @dataclass
   class PermissionSet:
       filesystem_read: bool = False
       filesystem_write: bool = False
       network_outbound: bool = False
       process_spawn: bool = False
       
       @staticmethod
       def none() -> PermissionSet:
           """Deny-by-default."""
           return PermissionSet()
   ```

3. `genesis/security/gates.py`
   ```python
   @dataclass
   class ApprovalDecision:
       approved: bool
       reason: str
       timestamp: datetime
   
   class ApprovalGate:
       def request_approval(self, artifact: CapabilityArtifact, eval_result: EvaluationResult) -> ApprovalDecision:
           # v0.1: Always require human input
           # Future: Policy-based
           ...
   ```

4. `genesis/security/policies.py` (stub for future)
   ```python
   # Future: PolicyEngine for risk-based approval
   # v0.1: Just interface definition
   ```

5. Tests:
   - `test_permissions.py`
   - `tests/security/test_permission_enforcement.py`

**Exit Criteria**:
- Permission model works
- Approval gate requires human decision
- Security tests pass

---

### PHASE 6: Models + Evaluation

**Goal**: Implement model abstraction and evaluation

**Files**:
1. `genesis/models/__init__.py`

2. `genesis/models/interface.py`
   ```python
   class ModelProvider(Protocol):
       def generate(self, prompt: str, **kwargs) -> str: ...
       def get_capabilities(self) -> ModelCapabilities: ...
   ```

3. `genesis/models/registry.py`
   ```python
   class ModelRegistry:
       def register(self, name: str, provider: ModelProvider) -> None: ...
       def get(self, name: str) -> ModelProvider: ...
   ```

4. `genesis/models/mock_provider.py`
   ```python
   class MockModelProvider:
       """Mock provider for v0.1 testing."""
       def generate(self, prompt: str, **kwargs) -> str:
           return "Mock response"
   ```

5. `genesis/evaluation/__init__.py`

6. `genesis/evaluation/runner.py`
   ```python
   class TestRunner:
       def run_tests(self, artifact: CapabilityArtifact) -> TestResult: ...
   ```

7. `genesis/evaluation/results.py`
   ```python
   @dataclass
   class EvaluationResult:
       test_results: TestResult
       score: float
       passed: bool
   ```

8. `genesis/observability/__init__.py`

9. `genesis/observability/events.py` (canonical event model)
   ```python
   class EventType(Enum):
       CAPABILITY_PLANNING_STARTED = "capability.planning.started"
       CAPABILITY_PLANNED = "capability.planned"
       CAPABILITY_VALIDATED = "capability.validated"
       CAPABILITY_TESTED = "capability.tested"
       CAPABILITY_AWAITING_APPROVAL = "capability.awaiting_approval"
       CAPABILITY_APPROVED = "capability.approved"
       CAPABILITY_REJECTED = "capability.rejected"
       CAPABILITY_REGISTERED = "capability.registered"
   
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

10. `genesis/observability/logger.py`

11. Tests

**Exit Criteria**:
- Model abstraction exists
- Evaluation can score capabilities
- Events emit correctly
- Tests pass

---

### PHASE 7: Hello Capability (Full Flow)

**Goal**: Demonstrate complete Intent → Registry lifecycle

**Files**:
1. `examples/hello_capability/run.py`
   ```python
   """
   Complete demonstration:
   1. Submit IntentRequest
   2. DeterministicPlanner generates plan
   3. Convert plan to DNA (with provenance)
   4. Validate DNA
   5. Construct artifact
   6. Execute tests via SubprocessBackend
   7. Evaluate results
   8. Request human approval
   9. Register in local registry
   10. Retrieve and execute
   """
   ```

2. `examples/hello_capability/implementation/__init__.py`

3. `examples/hello_capability/implementation/main.py`
   ```python
   def greet(name: str) -> str:
       return f"Hello, {name}!"
   ```

4. `examples/hello_capability/tests/test_greet.py`

5. `examples/hello_capability/README.md`

6. `tests/integration/test_full_lifecycle.py`
   ```python
   def test_hello_capability_intent_to_registry():
       # Full end-to-end integration test
       ...
   ```

**Exit Criteria**:
- `python examples/hello_capability/run.py` works
- Demonstrates every phase of lifecycle
- Produces expected output
- Integration test passes

---

### PHASE 8: Testing + Quality

**Goal**: Ensure quality standards

**Tasks**:
1. Run `pytest` - all tests pass
2. Run `pytest --cov` - coverage >70%
3. Run `ruff check` - 0 errors
4. Run `mypy genesis` - 0 errors
5. Fix all discovered issues
6. Add missing tests if coverage insufficient

**Exit Criteria**:
- All tests pass
- Coverage >70%
- No lint errors
- No type errors

---

### PHASE 9: Final Documentation

**Goal**: Ensure documentation matches implementation

**Tasks**:
1. Update README.md with actual status
2. Create CLAUDE.md for future sessions
3. Verify all docs/ files are accurate
4. Create development report
5. Update PROGRESS.md

**Exit Criteria**:
- README reflects reality
- Documentation is accurate
- Future developers can onboard

---

## Technology Stack (Confirmed)

### Core Dependencies
```toml
[project]
dependencies = [
    "pydantic>=2.0",       # Data validation
    "pyyaml>=6.0",         # YAML parsing
    "jsonschema>=4.0",     # Schema validation
]
```

### Development Dependencies
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-cov>=4.0",
    "pytest-asyncio>=0.23",
    "ruff>=0.3",
    "mypy>=1.8",
    "types-pyyaml",
]
```

**Rationale**: Minimal, standard, no vendor lock-in

---

## Definition of Done (Complete)

v0.1 is complete when all 32 criteria from ARCHITECTURE_PROPOSAL.md are met:

### Architecture (7 criteria)
- Intent → Plan → DNA flow
- No shell commands in DNA
- ExecutionBackend abstraction
- Honest execution boundary documentation
- Provenance in manifests
- Artifact concept demonstrated
- Unified event model

### Functionality (8 criteria)
- IntentRequest → DeterministicPlanner → CapabilityPlan
- Plan → DNA conversion
- DNA validation
- Artifact construction
- SubprocessBackend execution
- Human approval requirement
- Registration
- Retrieval

### Testing (4 criteria)
- Unit tests pass
- Integration test (full flow)
- Security tests
- >70% coverage

### Quality (3 criteria)
- ruff check passes
- mypy passes
- Type hints present

### Documentation (5 criteria)
- Architecture documented
- Capability DNA spec
- Security model documented
- ADRs written
- README accurate

### Demonstration (1 criterion)
- Hello capability demonstrates full Intent → Registry flow

### Repository (4 criteria)
- Git initialized
- pip install works
- No secrets
- .gitignore configured

---

## Estimated Timeline

**PHASE 0**: 0.5 hours  
**PHASE 1**: 1.5 hours  
**PHASE 2**: 1.5 hours  
**PHASE 3**: 2 hours  
**PHASE 4**: 2 hours  
**PHASE 5**: 1.5 hours  
**PHASE 6**: 1 hour  
**PHASE 7**: 2 hours  
**PHASE 8**: 2 hours  
**PHASE 9**: 1 hour  

**Total**: 10-14 hours

---

## Risk Register (Updated)

| Risk | Probability | Impact | Mitigation | Status |
|------|------------|--------|------------|--------|
| Planning layer complexity | Low | Medium | Keep DeterministicPlanner simple | Mitigated |
| Shell command removal | None | None | Corrected in design | Resolved |
| Execution boundary confusion | None | Low | Clear documentation | Mitigated |
| Artifact overhead | Low | Low | Minimal v0.1 implementation | Accepted |
| Approval gate UX | Low | Low | Interface-based design | Mitigated |
| Scope creep | Medium | Medium | Strict phase gates | Monitored |

**Overall Risk**: LOW

---

## Key Architectural Invariants (Enforced)

1. ✅ No shell commands in Capability DNA
2. ✅ Intent → Plan → DNA flow
3. ✅ Deny-by-default permissions
4. ✅ Human approval required
5. ✅ Provenance tracking
6. ✅ ExecutionBackend abstraction
7. ✅ Honest security documentation
8. ✅ Model-agnostic design
9. ✅ Observable lifecycle (events)
10. ✅ Minimal dependencies

---

## Version Roadmap Context

### v0.1 (This Plan)
**Theme**: Governed Capability Lifecycle  
**Deliverables**: Intent → Plan → DNA → Artifact → Registry

### v0.2 - Composition
**Theme**: Capabilities from capabilities  
**Deliverables**: Dependency resolution, recursive composition

### v0.3 - Resource Intelligence
**Theme**: Smart resource selection  
**Future enhancement to DeterministicPlanner**

### v0.4 - LLM Planning
**Theme**: AI-powered capability generation  
**Replaces DeterministicPlanner with LLMPlanner**

### v0.5 - Evolution
**Theme**: Capability improvement  
**Evolutionary capabilities**

### v0.x - CognitiveOS Integration
**Theme**: Genesis as subsystem  
**Full integration**

---

## Next Action

**Upon final approval of this plan**:

Begin PHASE 0 task execution:
1. Create pyproject.toml
2. Create .gitignore
3. Create .env.example
4. Initialize git
5. Create initial commit

Then proceed through phases 1-9 sequentially.

---

**Document Status**: READY FOR FINAL APPROVAL  
**Architecture Status**: CORRECTED  
**Implementation Status**: AWAITING AUTHORIZATION

**Prepared by**: Kiro (AI Engineering Agent)  
**Date**: 2026-09-23  
**Version**: 2.0 (Revised)
