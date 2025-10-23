from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterable


class BaseRepository[Obj, ID](ABC):
    """
    Abstract base class for repositories defining a common CRUD interface.

    Type Parameters:
        Obj: Type of the domain object.
        ID: Type of the object identifier (e.g., int or UUID).

    """

    @abstractmethod
    async def get_all(
        self, offset: int = None, limit: int = None, **filters: Any
    ) -> AsyncIterable[Obj]:
        """
        Retrieve a list of objects with optional pagination and filtering.

        Args:
            offset (int, optional): The starting offset for the query.
            limit (int, optional): The maximum number of objects to return.
            **filters (Any): Arbitrary filters for the query.

        Returns:
            AsyncIterable[Obj]: An asynchronous iterable of found objects.

        """

    @abstractmethod
    async def get(self, id_obj: ID) -> Optional[Obj]:
        """
        Retrieve an object by its identifier.

        Args:
            id_obj (ID): The identifier of the object.

        Returns:
            Optional[Obj]: The object if found, otherwise None.

        """

    @abstractmethod
    async def create(self, obj: Obj) -> None:
        """
        Create a new object in the repository.

        Args:
            obj (Obj): The object to be created.

        Raises:
            ObjectAlreadyExists: If an object with the same identifier already exists.

        """

    @abstractmethod
    async def delete(self, id_obj: ID) -> None:
        """
        Delete an object from the repository by its identifier.

        Args:
            id_obj (ID): The identifier of the object to be deleted.

        Raises:
            ObjectDoesNotExists: If the object with the given identifier does not exist.

        """

    @abstractmethod
    async def update(self, obj: Obj) -> None:
        """
        Update an existing object in the repository.

        Args:
            obj (Obj): The object with updated data.

        Raises:
            ObjectDoesNotExists: If the object does not exist in the repository.
            ObjectAlreadyExists: If the update violates a uniqueness constraint.

        """


class BaseORMToDomainMapper[ORMModel, DomainObj](ABC):
    """
    Abstract base class for mappers that convert between ORM models and domain objects.

    Type Parameters:
        ORMModel: The ORM model class (e.g., SQLAlchemy model).
        DomainObj: The domain object class (e.g., Pydantic model).

    """

    @abstractmethod
    def to_domain(self, obj: ORMModel, visited: Optional[dict] = None) -> DomainObj:
        """
        Convert an ORM model instance to a domain object.

        Args:
            obj (ORMModel): The ORM model instance to convert.
            visited (dict, optional): A cache of already processed objects to avoid recursion in cyclic relationships.

        Returns:
            DomainObj: The resulting domain object.

        """

    @abstractmethod
    def from_domain(self, obj: DomainObj, visited: Optional[dict] = None) -> ORMModel:
        """
        Convert a domain object to an ORM model instance.

        Args:
            obj (DomainObj): The domain object to convert.
            visited (dict, optional): A cache of already processed objects to avoid recursion in cyclic relationships.

        Returns:
            ORMModel: The resulting ORM model instance.

        """
