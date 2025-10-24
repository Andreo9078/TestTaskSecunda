from src.exc_registry import ExceptionRegistry
from src.utils import create_handler

registry = ExceptionRegistry()


@registry.exception(create_handler(422))
class MaxDepthExceeded(Exception):
    """Raised when trying to add an activity deeper than level 3."""
