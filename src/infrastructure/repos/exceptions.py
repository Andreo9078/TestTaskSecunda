class ObjectAlreadyExists(Exception):
    """Raised when trying to create an object that already exists in the repository."""


class ObjectDoesNotExists(Exception):
    """Raised when trying to update or delete an object that does not exist in the repository."""
