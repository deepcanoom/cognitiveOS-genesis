# CognitiveOS Genesis - Implementation Plan

## Overall Objective

Bootstrap CognitiveOS Genesis v0.1: A governed capability creation engine demonstrating the complete capability lifecycle from intent to registry.

## Architecture Overview

```
CognitiveOS Genesis v0.1
│
├── Core Engine (genesis/core/)
│   ├── Lifecycle management
│   ├── Event system
│   └── Planning engine
│
├── Capability System (genesis/capabilities/)
│   ├── DNA specification
│   ├── Registry
│   ├── Resolver
│   └── Factory
│
├── Model Layer (genesis/models/)
│   ├── Provider abstraction
│   ├── Registry
│   └── Router
│
├── Agents (genesis/agents/)
│   ├── Runtime
│   └── Factory
│
├── Security (genesis/security/)
│   ├── Policy engine
│   ├── Permission model
│   └── Approval gates
│
├── Evaluation (genesis/evaluation/)
│   ├── Test runner
│   └── Scoring
│
└── Observability (genesis/observability/)
    ├── Event logging
    └── Metrics
```

## Implementation Phases

### PHASE 0: Foundation ✓ (PARTIALLY COMPLETE)
- [x] Repository structure
- [x] README.md
- [x] LICENSE
- [x] CONTRIBUTING.md
- [x] SECURITY.md
- [ ] CODE_OF_CONDUCT.md
- [ ] pyproject.toml
- [ ] .gitignore
- [ ] .env.example
- [ ] docker-compose.yml
- [ ] Git initialization

### PHASE 1: Documentation
- [ ] docs/vision.md
- [ ] docs/architecture.md
- [ ] docs/principles.md
- [ ] docs/roadmap.md
- [ ] docs/capability-dna.md
- [ ] docs/security-model.md
- [ ] docs/adr/001-capability-manifest-format.md

### PHASE 2: Core Data Models
- [ ] genesis/models/article.py (domain model example)
- [ ] genesis/capabilities/manifest.py (Capability DNA)
- [ ] genesis/core/events.py (event system)
- [ ] genesis/security/permissions.py (permission model)
- [ ] schemas/capability.schema.json

### PHASE 3: Core Infrastructure
- [ ] genesis/capabilities/registry.py
- [ ] genesis/models/registry.py
- [ ] genesis/models/router.py
- [ ] genesis/security/policy.py
- [ ] genesis/security/gates.py
- [ ] genesis/observability/events.py

### PHASE 4: Capability Lifecycle
- [ ] genesis/core/lifecycle.py
- [ ] genesis/core/planner.py
- [ ] genesis/capabilities/resolver.py
- [ ] genesis/capabilities/factory.py
- [ ] genesis/evaluation/runner.py

### PHASE 5: Example Implementation
- [ ] examples/hello_capability/manifest.yaml
- [ ] examples/hello_capability/implementation.py
- [ ] examples/hello_capability/run.py
- [ ] examples/hello_capability/README.md

### PHASE 6: Testing
- [ ] tests/unit/test_manifest.py
- [ ] tests/unit/test_registry.py
- [ ] tests/unit/test_lifecycle.py
- [ ] tests/unit/test_security.py
- [ ] tests/integration/test_hello_capability.py
- [ ] tests/security/test_permission_model.py

### PHASE 7: Validation & Quality
- [ ] Run pytest
- [ ] Run ruff
- [ ] Run mypy
- [ ] Fix all errors
- [ ] Verify hello_capability works end-to-end

### PHASE 8: Final Documentation
- [ ] Update README with actual implementation status
- [ ] Create CLAUDE.md for future sessions
- [ ] Create development report
- [ ] Verify all documentation is accurate

## Dependencies

```
Phase 0 → Phase 1 (docs need foundation)
Phase 1 → Phase 2 (models need spec)
Phase 2 → Phase 3 (infra needs models)
Phase 3 → Phase 4 (lifecycle needs infra)
Phase 4 → Phase 5 (examples need lifecycle)
Phase 5 → Phase 6 (tests need examples)
Phase 6 → Phase 7 (validation needs tests)
Phase 7 → Phase 8 (final docs need validation)
```

## Validation Criteria

Each phase is complete only when:

1. All files in phase exist
2. All files are syntactically valid
3. Relevant tests pass (phases 6+)
4. PROGRESS.md is updated
5. Git commit is created (when appropriate)

## Technical Stack

- **Language**: Python 3.11+
- **Package Management**: pip/pyproject.toml
- **Testing**: pytest
- **Linting**: ruff
- **Type Checking**: mypy
- **Formatting**: black (via ruff)
- **Schema**: JSON Schema
- **Documentation**: Markdown

## Security Invariants

Every implementation must respect:

1. Least privilege
2. Deny by default
3. No hardcoded credentials
4. Human approval for sensitive ops
5. All actions logged
6. Sandbox isolation
7. Permission validation

## Definition of Done (v0.1)

The bootstrap is complete when:

1. ✅ Repository structure exists
2. ✅ All documentation files exist and are accurate
3. ✅ Capability DNA specification is documented
4. ✅ One capability can be represented (hello_capability)
5. ✅ Capability validation works
6. ✅ Local registry works
7. ✅ Model registry/selection abstraction exists
8. ✅ Lifecycle states exist
9. ✅ Approval gate exists
10. ✅ Automated tests exist and pass
11. ✅ Security principles are implemented
12. ✅ CLAUDE.md exists
13. ✅ Project can be installed locally
14. ✅ `python examples/hello_capability/run.py` works
15. ✅ All lint/type checks pass

## Current Phase

**PHASE 0: Foundation** (in progress)

Next task: Complete remaining Phase 0 files
