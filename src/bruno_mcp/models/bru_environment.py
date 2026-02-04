"""BruEnvironment data model for Bruno environment files."""

from pydantic import BaseModel


class BruEnvironment(BaseModel):
    """Model representing a Bruno environment configuration.

    Attributes:
        name: Environment name (filename without .bru extension).
        variables: Dictionary of all variables (merged vars and secrets).
    """

    name: str
    variables: dict[str, str]
