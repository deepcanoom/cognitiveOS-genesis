# Security Policy

## Supported Versions

CognitiveOS Genesis is currently in experimental development (v0.x).

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |

## Security Principles

Genesis is built on security-first principles:

1. **Least Privilege**: Capabilities receive only necessary permissions
2. **Deny by Default**: All sensitive operations require explicit authorization
3. **Sandbox Before Trust**: New capabilities execute in isolated environments
4. **Human Approval**: Critical operations require human confirmation
5. **Auditability**: All capability actions are logged and traceable
6. **Reversibility**: Operations can be rolled back when possible

## Reporting a Vulnerability

**DO NOT** report security vulnerabilities through public GitHub issues.

### Preferred Method

Email security reports to: **security@[project-domain]** (to be configured)

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested mitigation (if available)

### What to Expect

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Status Updates**: Every 14 days
- **Fix Timeline**: Depends on severity

### Severity Classification

| Severity | Description | Response Time |
|----------|-------------|---------------|
| **Critical** | Remote code execution, privilege escalation, credential exposure | 24-48 hours |
| **High** | Unauthorized access, data exposure, security gate bypass | 7 days |
| **Medium** | Information disclosure, DoS potential | 14 days |
| **Low** | Minor security improvements | 30 days |

## Security Scope

### In Scope
- Authentication and authorization bypasses
- Sandbox escapes
- Capability permission violations
- Security gate circumvention
- Credential or secret exposure
- Privilege escalation
- Malicious capability injection

### Out of Scope
- Social engineering attacks
- Physical security
- Third-party service vulnerabilities
- Denial of Service (unless critical)
- Issues in example/demo code

## Responsible Disclosure

We kindly request:
- **Private Reporting**: Do not publicly disclose until we've addressed the issue
- **Reasonable Timeline**: Give us time to fix before disclosure (typically 90 days)
- **Good Faith**: Do not exploit the vulnerability beyond proof-of-concept
- **Collaboration**: Work with us to understand and resolve the issue

## Recognition

We maintain a security acknowledgments file for researchers who responsibly disclose vulnerabilities.

## Security Features

### Current (v0.1)
- Capability permission manifest
- Security gate validation
- Sandbox runtime isolation
- Human approval gates
- Structured audit logging

### Planned
- Capability signature verification
- Runtime anomaly detection
- Resource usage limits
- Network policy enforcement
- Secrets management integration
- Automated security scanning

## Secure Development Practices

We follow:
- Code review for all changes
- Static analysis (ruff, mypy, bandit)
- Dependency vulnerability scanning
- Security-focused testing
- Regular security audits

## Known Limitations (v0.1)

Genesis is experimental software. Known security limitations:

1. **Local-only security**: v0.1 implements local security gates only
2. **Limited sandbox**: Full process isolation not yet implemented
3. **No signature verification**: Capability manifests are not cryptographically signed
4. **Basic permission model**: Granular RBAC not fully implemented

**Do not deploy Genesis in production or with sensitive data without thorough security review.**

## Security Checklist for Contributors

Before submitting security-sensitive code:

- [ ] Follows least privilege principle
- [ ] Validates all inputs
- [ ] Does not expose credentials
- [ ] Requires appropriate permissions
- [ ] Includes security tests
- [ ] Updates security documentation
- [ ] Logs security-relevant events
- [ ] No hardcoded secrets
- [ ] Handles errors securely

## Contact

Security concerns: security@[project-domain] (to be configured)  
General questions: GitHub Discussions

Thank you for helping keep CognitiveOS Genesis secure!
