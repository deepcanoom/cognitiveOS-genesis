"""
Tests for Hello World Capability

These tests demonstrate the Genesis testing contract:
- Capabilities ship with their own tests
- Tests are executed via SubprocessBackend in test mode
- pytest is the standard test framework
"""

import pytest
from hello_world import greet, main


def test_greet_default():
    """Test default greeting."""
    result = greet()
    assert result == "Hello, World!"


def test_greet_custom_name():
    """Test custom name greeting."""
    result = greet("Genesis")
    assert result == "Hello, Genesis!"


def test_greet_empty_string():
    """Test empty string handling."""
    result = greet("")
    assert result == "Hello, !"


def test_main_executes(capsys):
    """Test main function executes without error."""
    main()
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
