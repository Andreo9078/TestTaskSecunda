from src.exc_registry import ExceptionRegistry
from src.utils import create_handler

registry = ExceptionRegistry()


@registry.exception(create_handler(422))
class ObjectAlreadyExists(Exception):
    """Raised when trying to create an object that already exists in the repository."""


@registry.exception(create_handler(422))
class ObjectDoesNotExists(Exception):
    """Raised when trying to update or delete an object that does not exist in the repository."""
