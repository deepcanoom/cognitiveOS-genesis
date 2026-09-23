# Contributing to CognitiveOS Genesis

Thank you for your interest in contributing to CognitiveOS Genesis!

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How to Contribute

### Reporting Issues

- Use GitHub Issues for bug reports and feature requests
- Check existing issues before creating duplicates
- Provide clear reproduction steps for bugs
- Use the issue templates when available

### Development Process

1. **Fork the repository**
2. **Create a feature branch**
   \\\ash
   git checkout -b feature/your-feature-name
   \\\
3. **Make your changes**
   - Follow the coding standards below
   - Write tests for new functionality
   - Update documentation as needed
4. **Run tests and linting**
   \\\ash
   pytest
   ruff check .
   mypy genesis
   \\\
5. **Commit with clear messages**
   \\\ash
   git commit -m "feat: add capability composition validator"
   \\\
6. **Push and create a Pull Request**

### Commit Message Convention

Follow [Conventional Commits](https://www.conventionalcommits.org/):

- \eat:\ New feature
- \ix:\ Bug fix
- \docs:\ Documentation changes
- \	est:\ Test additions or modifications
- \efactor:\ Code refactoring
- \chore:\ Maintenance tasks

### Coding Standards

#### Python Style
- Follow PEP 8
- Use type hints for all function signatures
- Maximum line length: 100 characters
- Use \uff\ for linting
- Use \lack\ for formatting

#### Architecture Principles
- Maintain model-agnostic abstractions
- Respect security boundaries
- Keep modules cohesive and loosely coupled
- Prefer composition over inheritance
- Write testable code

#### Testing
- Write unit tests for all new functionality
- Maintain or improve code coverage
- Add integration tests for cross-module features
- Include security tests for sensitive operations

#### Documentation
- Update relevant documentation for user-facing changes
- Add docstrings to all public functions and classes
- Create Architecture Decision Records (ADRs) for significant decisions
- Keep examples up to date

### Security Contributions

Security is architectural in Genesis. When contributing:

- Never bypass security gates
- Maintain least privilege principles
- Document permission requirements
- Add security tests for sensitive operations
- Report security vulnerabilities privately (see [SECURITY.md](SECURITY.md))

### What to Contribute

#### High Priority
- Core capability lifecycle implementation
- Model registry and routing
- Evaluation framework
- Security policy enforcement
- Documentation improvements
- Test coverage

#### Welcome Contributions
- Example capabilities
- Provider integrations (model, tool, MCP)
- Evaluation metrics
- Documentation
- Bug fixes

#### Avoid
- Breaking changes without discussion
- Hardcoded vendor dependencies
- Ungoverned autonomous behavior
- Security bypasses
- Untested code

### Pull Request Process

1. **PR must pass all checks**
   - Tests pass
   - Linting passes
   - Type checking passes
   - No security violations

2. **PR must include**
   - Clear description of changes
   - Tests for new functionality
   - Updated documentation
   - Link to related issue (if applicable)

3. **Review process**
   - Maintainers will review within 7 days
   - Address feedback constructively
   - Be patient and respectful

4. **Merge criteria**
   - 1+ maintainer approval
   - All checks pass
   - Conflicts resolved
   - Documentation updated

### Development Setup

\\\ash
# Clone your fork
git clone https://github.com/YOUR-USERNAME/CognitiveOS-Genesis.git
cd CognitiveOS-Genesis

# Add upstream remote
git remote add upstream https://github.com/deepcanoom/CognitiveOS-Genesis.git

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check .

# Run type checking
mypy genesis
\\\

### Questions?

- Open a GitHub Discussion
- Comment on related issues
- Reach out to maintainers

Thank you for contributing to the future of cognitive systems!
