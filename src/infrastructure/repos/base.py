from abc import ABC, abstractmethod
from typing import Any, Optional, AsyncIterable
from uuid import UUID

from src.domain import GeoPoint, Organization
from src.infrastructure.models import OrganizationORM


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


class BaseOrganizationRepository(BaseRepository[Organization, UUID], ABC):
    """
    Extended repository interface for OrganizationORM
    with support for location-based filtering and activity-based queries.
    """

    @abstractmethod
    async def get_all_in_radius(
        self,
        center: GeoPoint,
        radius_meters: float,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        activity_id: Optional[UUID] = None,
        **filters: Any
    ) -> AsyncIterable["OrganizationORM"]:
        """
        Retrieve organizations within a given radius of a point.

        Args:
            center (GeoPoint): Center point of the search.
            radius_meters (float): Search radius in meters.
            offset (int, optional): Pagination offset.
            limit (int, optional): Maximum number of results.
            activity_id (UUID, optional): Filter by activity.
            **filters: Additional filters for the query.

        Returns:
            AsyncIterable[OrganizationORM]: Asynchronous iterator of organizations.
        """

    @abstractmethod
    async def get_all_in_bbox(
        self,
        sw: GeoPoint,
        ne: GeoPoint,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        activity_id: Optional[UUID] = None,
        **filters: Any
    ) -> AsyncIterable["OrganizationORM"]:
        """
        Retrieve organizations inside a bounding box defined by two coordinates.

        Args:
            sw (GeoPoint): South-west corner of the bounding box.
            ne (GeoPoint): North-east corner of the bounding box.
            offset (int, optional): Pagination offset.
            limit (int, optional): Maximum number of results.
            activity_id (UUID, optional): Filter by activity.
            **filters: Additional filters for the query.

        Returns:
            AsyncIterable[OrganizationORM]: Asynchronous iterator of organizations.
        """

    @abstractmethod
    async def get_all_by_activity_tree(
        self,
        root_activity_id: UUID,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> AsyncIterable["Organization"]:
        """
        Retrieve all organizations related to a given activity
        and any of its descendant activities in the activity hierarchy.

        Args:
            root_activity_id (UUID): ID of the root activity to search from.
            offset (int, optional): Pagination offset.
            limit (int, optional): Maximum number of results.
            **filters: Additional filters for the query.

        Returns:
            AsyncIterable[Organization]: Asynchronous iterator of organizations.
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
