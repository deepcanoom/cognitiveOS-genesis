"""
Hello World Capability - Minimal Reference Implementation

This is a real, executable capability used for:
1. Genesis bootstrap testing
2. Architecture demonstration
3. Integration testing reference
"""


def greet(name: str = "World") -> str:
    """
    Generate a greeting message.
    
    This is the entrypoint referenced in the capability DNA as:
    runtime_entrypoint: "hello_world:greet"
    
    Args:
        name: Name to greet (default: "World")
        
    Returns:
        Greeting message string
    """
    return f"Hello, {name}!"


def main() -> None:
    """
    Main entrypoint for command-line execution.
    
    Capability DNA can reference this as:
    runtime_entrypoint: "hello_world:main"
    """
    print(greet())


if __name__ == "__main__":
    main()
