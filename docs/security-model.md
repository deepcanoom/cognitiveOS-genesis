# Security Model

**Version**: 0.1.0  
**Status**: Implementation Baseline  
**Date**: 2026-09-23

---

## Table of Contents

1. [Security Philosophy](#security-philosophy)
2. [Threat Model](#threat-model)
3. [Defense in Depth](#defense-in-depth)
4. [v0.1 Security Posture](#v01-security-posture)
5. [Security Controls](#security-controls)
6. [Limitations](#limitations)
7. [Future Hardening](#future-hardening)
8. [Security Best Practices](#security-best-practices)

---

## Security Philosophy

### Core Principles

1. **Honest Security Posture**
   - We document what we **actually provide**, not what we aspire to
   - No false claims about sandboxing or enforcement
   - Clear communication of limitations

2. **Deny by Default**
   - All permissions default to most restrictive
   - Explicit opt-in required for capabilities
   - No implicit permission grants

3. **Defense in Depth**
   - Multiple security layers
   - No single point of failure
   - Graceful degradation

4. **Human in the Loop**
   - No automatic approval of new capabilities
   - Explicit review and decision points
   - Observable lifecycle

5. **Security Through Transparency**
   - All capabilities tracked with provenance
   - All lifecycle transitions logged
   - Auditability built-in

### What Security Means in Genesis

**Security in Genesis is about governance and observability, not containment.**

v0.1 provides:
- ✅ **Permission declaration model**
- ✅ **Human approval gates**
- ✅ **Audit logging**
- ✅ **Provenance tracking**
- ✅ **Process-level isolation**

v0.1 does NOT provide:
- ❌ **Hardened OS-level permission enforcement**
- ❌ **Container-based sandboxing**
- ❌ **Filesystem access control**
- ❌ **Network traffic filtering**

**This is by design** - v0.1 proves governance architecture. Hardened execution comes later.

---

## Threat Model

### In-Scope Threats (v0.1)

**1. Accidental Overpermissioned Capabilities**
- **Threat**: Developer requests more permissions than needed
- **Mitigation**: Deny-by-default + human approval review

**2. Capability DNA with Shell Commands**
- **Threat**: Manifests containing arbitrary executable commands
- **Mitigation**: Declarative-only DNA schema + validation

**3. Untracked Capability Origin**
- **Threat**: Cannot determine who/what created a capability
- **Mitigation**: Mandatory provenance tracking

**4. Approval Bypass**
- **Threat**: Capability reaches registry without approval
- **Mitigation**: Immutable lifecycle state machine

**5. Self-Referential Dependencies**
- **Threat**: Capability depends on itself (infinite loop)
- **Mitigation**: Dependency validation

**6. Undocumented Security Claims**
- **Threat**: Users believe v0.1 provides hardened sandboxing
- **Mitigation**: Explicit documentation of limitations

### Out-of-Scope Threats (v0.1)

**Explicitly NOT Protected Against in v0.1:**

**1. Malicious Capability Code**
- A capability approved by human can execute arbitrary Python
- SubprocessBackend provides process isolation only
- No filesystem/network enforcement

**2. Resource Exhaustion**
- No memory limits
- No CPU limits
- No timeout enforcement

**3. Data Exfiltration**
- Capability with network permission can send data anywhere
- No traffic inspection or filtering

**4. Privilege Escalation**
- If host OS is vulnerable, subprocess can escalate
- No hardened kernel namespace isolation

**5. Side-Channel Attacks**
- Timing attacks
- Cache-based attacks
- No mitigations

**Why Out of Scope?**

v0.1 is a **governance and lifecycle demonstration**. The architecture supports future hardening, but v0.1 deliberately scopes to:
1. Prove the governance model works
2. Establish provenance and auditability
3. Create extension points for hardened execution

**Hardened execution backends (containers, VMs) are future work.**

---

## Defense in Depth

### Layer 1: Permission Declaration

**What It Is**: Capability DNA explicitly declares required permissions.

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

**Default**: All permissions = false

**What It Prevents**:
- ✅ Undocumented permission requirements
- ✅ Accidental overpermissioning (requires explicit declaration)

**What It Does NOT Prevent**:
- ❌ Capability from accessing resources if approved
- ❌ OS-level permission enforcement (v0.1)

**Status**: ✅ Implemented

### Layer 2: Schema Validation

**What It Is**: JSON Schema validation of Capability DNA.

**Validations**:
- Required fields present
- Correct data types
- Valid enums (createdBy, permission values)
- Name/version format compliance
- Structured entrypoint (no shell commands)

**What It Prevents**:
- ✅ Malformed manifests
- ✅ Shell commands in DNA
- ✅ Invalid permission declarations
- ✅ Arbitrary provenance values

**Status**: ✅ Implemented

### Layer 3: Dependency Validation

**What It Is**: Validation of capability dependencies.

**v0.1 Validations**:
- No self-references
- No simple circular dependencies
- Well-formed dependency declarations

**What It Prevents**:
- ✅ Obvious dependency cycles
- ✅ Self-referential capabilities

**What It Does NOT Prevent**:
- ❌ Complex transitive cycles (deferred to v0.2)
- ❌ Malicious dependencies (no signature verification)

**Status**: ✅ Implemented (minimal)

### Layer 4: Human Approval Gate

**What It Is**: Explicit human review before capability registration.

**Process**:
```
EVALUATED
  ↓
AWAITING_APPROVAL
  ↓
Human Reviews:
  - Capability DNA
  - Permissions requested
  - Evaluation results
  - Provenance
  ↓
APPROVE or REJECT
  ↓
REGISTERED (only if approved)
```

**What It Prevents**:
- ✅ Automated capability deployment without review
- ✅ Capabilities with suspicious permissions
- ✅ Unevaluated capabilities

**Status**: ✅ Implemented

### Layer 5: Execution Boundary

**What It Is**: Subprocess-based execution isolation.

**Implementation**: `SubprocessBackend`

**What It Provides**:
- ✅ Process-level isolation
- ✅ Capability runs in separate process
- ✅ Can be monitored/killed by parent

**What It Does NOT Provide**:
- ❌ Filesystem access control
- ❌ Network access control
- ❌ Memory limits
- ❌ CPU limits
- ❌ Hardened namespace isolation

**Critical Understanding**:

**SubprocessBackend is NOT a security sandbox.**

It is an **execution boundary** that:
- Isolates capability execution from Genesis runtime
- Provides a seam for future hardened backends
- Allows basic process management

**Status**: ✅ Implemented (with honest documentation)

### Layer 6: Audit Logging

**What It Is**: All lifecycle transitions logged as structured events.

**Events Logged**:
- CAPABILITY_PLANNING_STARTED
- CAPABILITY_PLANNED
- CAPABILITY_VALIDATED
- CAPABILITY_TESTED
- CAPABILITY_EVALUATED
- CAPABILITY_AWAITING_APPROVAL
- CAPABILITY_APPROVED / REJECTED
- CAPABILITY_REGISTERED

**Log Format**: JSON-lines (`logs/events.jsonl`)

**What It Provides**:
- ✅ Complete audit trail
- ✅ Forensic analysis capability
- ✅ Compliance evidence

**Status**: ✅ Implemented

### Layer 7: Provenance Tracking

**What It Is**: Every capability records origin metadata.

```yaml
provenance:
  createdBy: GENESIS  # Enum: HUMAN | GENESIS | IMPORTED
  createdAt: "2026-09-23T10:30:00Z"
  parentCapabilities:
    - parent-cap@1.0.0
```

**What It Provides**:
- ✅ Origin tracking
- ✅ Lineage for composed capabilities
- ✅ Accountability

**Status**: ✅ Implemented

---

## v0.1 Security Posture

### What v0.1 Security Actually Means

**Genesis v0.1 is a governed capability lifecycle system, not a hardened execution sandbox.**

**Security Guarantees**:

1. **✅ Permission Policy Enforcement**
   - Capabilities cannot be registered without declared permissions
   - Human reviews permissions before approval

2. **✅ Governance Enforcement**
   - No capability bypasses approval gate
   - Immutable lifecycle state machine

3. **✅ Audit Trail**
   - All security-relevant events logged
   - Provenance tracked

4. **✅ Declarative DNA**
   - No arbitrary shell commands
   - Structured, validatable manifest format

5. **✅ Process Isolation**
   - Capability runs in separate process
   - Crash isolation from Genesis runtime

**Security NON-Guarantees**:

1. **❌ OS-Level Permission Enforcement**
   - Permission declarations are policy, not enforcement
   - SubprocessBackend cannot restrict filesystem/network access

2. **❌ Malicious Code Prevention**
   - Approved capability can execute arbitrary Python
   - No code analysis or sandboxing

3. **❌ Resource Limits**
   - No memory limits
   - No CPU limits
   - No timeout enforcement

4. **❌ Data Exfiltration Prevention**
   - Capability with network permission can send data anywhere
   - No traffic inspection

**Threat Model Summary**:

v0.1 protects against:
- ✅ Accidental overpermissioning
- ✅ Governance bypasses
- ✅ Undocumented capabilities
- ✅ Shell command injection in DNA

v0.1 does NOT protect against:
- ❌ Malicious approved capabilities
- ❌ Resource exhaustion
- ❌ Side-channel attacks
- ❌ Privilege escalation

**Appropriate Use Cases**:

✅ **Safe for v0.1**:
- Trusted development environments
- Demonstration purposes
- Governance proof-of-concept
- Capability lifecycle validation
- Internal tooling with trusted code

❌ **NOT Safe for v0.1**:
- Production environments
- Untrusted capability code
- Multi-tenant systems
- Sensitive data processing (without additional controls)
- Public-facing services

---

## Security Controls

### Permission Model

**Structure**:
```yaml
permissions:
  filesystem:
    read: boolean    # Default: false
    write: boolean   # Default: false
  network:
    outbound: boolean  # Default: false
  process:
    spawn: boolean  # Default: false
```

**Semantics**:

**filesystem.read = false**
- **Intent**: Capability should not read files
- **v0.1 Enforcement**: None (SubprocessBackend cannot enforce)
- **Governance**: Human reviewer sees this declaration

**filesystem.write = false**
- **Intent**: Capability should not write files
- **v0.1 Enforcement**: None
- **Governance**: Approval required if true

**network.outbound = false**
- **Intent**: Capability should not make network requests
- **v0.1 Enforcement**: None
- **Governance**: Approval required if true

**process.spawn = false**
- **Intent**: Capability code should not spawn child processes
- **v0.1 Enforcement**: None
- **Governance**: Prevents capabilities from acting as process launchers

**Critical Distinction**:

```
Genesis Runtime Authority:
  ↓
  CAN use SubprocessBackend to execute capability
  (this is runtime infrastructure, not capability permission)

Capability Permission:
  ↓
  process.spawn = false means:
  Capability CODE cannot call subprocess.Popen() etc.
```

### Approval Gate

**v0.1 Behavior**: All capabilities require human approval.

**No Automatic Approval** - even for capabilities with zero permissions.

**Approval Interface** (conceptual):
```
Capability: hello-world@0.1.0
Created By: GENESIS
Permissions:
  - filesystem.read: false
  - filesystem.write: false
  - network.outbound: false
  - process.spawn: false
Evaluation: PASSED (100/100)
Tests: 5/5 passed

Approve? [y/n]:
```

**Decision Recorded**:
```json
{
  "event_type": "CAPABILITY_APPROVED",
  "timestamp": "2026-09-23T10:30:00Z",
  "capability_id": "hello-world@0.1.0",
  "actor": "human",
  "decision": "approved"
}
```

### Provenance

**Format**:
```yaml
provenance:
  createdBy: GENESIS  # Typed enum, not free string
  createdAt: "2026-09-23T10:30:00Z"
  parentCapabilities: []
```

**Validation**:
- `createdBy` must be `HUMAN | GENESIS | IMPORTED`
- `createdAt` must be valid ISO 8601 timestamp
- `parentCapabilities` must be well-formed references

**Future Extensions**:
```yaml
provenance:
  createdBy: GENESIS
  generatorVersion: 0.7.2
  models:
    - provider: anthropic
      model: claude-sonnet-4.5
  source:
    repository: https://github.com/org/genesis
    commit: abc123
```

---

## Limitations

### Known Security Limitations

#### 1. No OS-Level Permission Enforcement

**Limitation**: SubprocessBackend cannot enforce filesystem, network, or process restrictions.

**Impact**: An approved capability can:
- Read any file the Genesis process can read
- Write any file the Genesis process can write
- Make network requests
- Spawn child processes

**Mitigation**: Human approval reviews permissions. Future: ContainerBackend with hardened enforcement.

**Affected Permissions**:
- `filesystem.read`
- `filesystem.write`
- `network.outbound`
- `process.spawn`

#### 2. No Resource Limits

**Limitation**: Capabilities can consume arbitrary memory, CPU, disk.

**Impact**: Resource exhaustion attacks possible.

**Mitigation**: None in v0.1. Future: Resource limit enforcement in ExecutionBackend.

#### 3. No Code Analysis

**Limitation**: Genesis does not analyze capability code for malicious behavior.

**Impact**: Approved capability can execute arbitrary Python.

**Mitigation**: Human approval + trust. Future: Static analysis, behavioral monitoring.

#### 4. No Signature Verification

**Limitation**: Capability artifacts not cryptographically signed.

**Impact**: Cannot verify artifact integrity or origin beyond checksums.

**Mitigation**: SHA256 checksums. Future: GPG/digital signatures.

#### 5. No Network Traffic Inspection

**Limitation**: Capabilities with network permission have unrestricted access.

**Impact**: Data exfiltration, command-and-control possible.

**Mitigation**: Human approval reviews network permission. Future: Traffic filtering, allowlists.

### Documentation Requirements

**Every security-related document must explicitly state**:

> "v0.1 permission declarations express intended authorization policy. SubprocessBackend does not provide hardened OS-level enforcement of all declared permissions. Future ExecutionBackends may provide enforcement."

**Test naming must reflect validation, not enforcement**:

✅ Correct:
- `test_permission_validation.py`
- `test_permission_defaults.py`
- `test_permission_policy_checks.py`

❌ Incorrect:
- `test_permission_enforcement.py` (implies OS-level enforcement)
- `test_filesystem_restriction_enforced.py`

---

## Future Hardening

### Roadmap

**v0.7**: Hardened Execution Backend

**Features**:
- Container-based isolation (Docker/Podman)
- Linux namespace isolation
- Filesystem mount restrictions
- Network namespace isolation
- Resource limits (cgroups)
- Seccomp filters
- AppArmor/SELinux profiles

**Example**:
```python
class ContainerBackend(ExecutionBackend):
    """Hardened container-based execution."""
    
    def execute(self, artifact: CapabilityArtifact) -> ExecutionResult:
        # Create isolated container
        # Mount only allowed paths
        # Restrict network based on permissions
        # Apply resource limits
        # Execute with seccomp/AppArmor
        # Monitor and enforce
```

**v0.8**: Signature Verification

**Features**:
- GPG signing of artifacts
- Public key infrastructure
- Trust chains
- Signature validation before execution

**v0.9**: Static Analysis

**Features**:
- AST analysis for suspicious patterns
- Dependency vulnerability scanning
- Behavioral heuristics

**v1.0**: Behavioral Monitoring

**Features**:
- Runtime behavior monitoring
- Anomaly detection
- Kill switches for policy violations

---

## Security Best Practices

### For Capability Developers

1. **Request Minimal Permissions**
   ```yaml
   # ✅ Good
   permissions:
     filesystem:
       read: false
       write: false
   
   # ❌ Bad
   permissions:
     filesystem:
       read: true
       write: true  # Do you really need write?
   ```

2. **Document Provenance Accurately**
   ```yaml
   provenance:
     createdBy: HUMAN  # Be honest
     parentCapabilities: []  # If truly original
   ```

3. **Include Comprehensive Tests**
   ```yaml
   evaluation:
     tests:
       - type: unit
       - type: integration
       - type: security  # Don't skip
   ```

4. **Never Include Credentials in DNA**
   - Use environment variables
   - Use secret management systems
   - Never hardcode API keys

### For Genesis Operators

1. **Review All Permissions**
   - Understand what capability is requesting
   - Approve only if justified

2. **Monitor Audit Logs**
   ```bash
   tail -f logs/events.jsonl | grep APPROVAL
   ```

3. **Track Provenance**
   - Know origin of all capabilities
   - Investigate unknown `createdBy` values

4. **Test in Isolated Environment**
   - Don't run untrusted capabilities in production
   - Use dedicated test environments

5. **Keep Genesis Updated**
   - Security improvements in newer versions
   - Hardened execution backends coming

### For Reviewers

**Approval Checklist**:
- [ ] Capability DNA validated successfully
- [ ] Permissions requested are minimal and justified
- [ ] Provenance is complete and accurate
- [ ] All tests passed
- [ ] No suspicious code patterns (manual review)
- [ ] Understand what the capability does
- [ ] Dependencies (if any) are trusted

**Red Flags**:
- ⚠️ Requests all permissions
- ⚠️ No tests provided
- ⚠️ Provenance incomplete/suspicious
- ⚠️ Name doesn't match description
- ⚠️ Unclear purpose

---

## Incident Response

### If Malicious Capability Detected

1. **DO NOT APPROVE**
2. **Reject immediately**
3. **Document findings**
4. **Review audit log** for similar patterns
5. **Investigate origin** (createdBy, parentCapabilities)

### If Approved Capability Misbehaves

1. **Kill process** (Genesis has process handle)
2. **Review audit logs**
3. **Check permissions granted**
4. **Disable/remove from registry**
5. **Investigate**:
   - Was approval justified?
   - Did capability violate declared permissions?
   - Code review for malicious behavior

---

## References

- [Architecture Documentation](architecture.md)
- [Capability DNA Specification](capability-dna.md)
- [SECURITY.md](../SECURITY.md) - Vulnerability reporting

---

**Document Version**: 1.0  
**Last Updated**: 2026-09-23  
**Status**: Implementation Baseline

**Security Contact**: security@cognitiveos.dev  
**Vulnerability Reports**: See SECURITY.md
