"""Compiler-specific exceptions."""


class SkillCompilerError(ValueError):
    """Raised when compilation cannot preserve source semantics."""
