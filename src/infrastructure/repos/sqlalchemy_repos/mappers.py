from typing import Optional

from geoalchemy2.shape import to_shape, from_shape
from shapely import Point

from src.domain import Building, Organization, Activity, Phone, GeoPoint
from src.infrastructure.models import (
    BuildingORM, OrganizationORM, ActivityORM, PhoneORM
)
from src.infrastructure.repos.base import BaseORMToDomainMapper


class PhoneORMMapper(BaseORMToDomainMapper[PhoneORM, Phone]):
    """Mapper for Phone (simple value object, no cycles)"""

    def to_domain(
        self, data_obj: PhoneORM, visited: Optional[dict] = None
    ) -> Phone:
        return Phone(number=data_obj.number)

    def from_domain(
        self, domain_obj: Phone, visited: Optional[dict] = None
    ) -> PhoneORM:
        return PhoneORM(number=domain_obj.number)


class ActivityORMMapper(BaseORMToDomainMapper[ActivityORM, Activity]):
    """Mapper for Activity with self-referential relationship"""

    def to_domain(
        self, data_obj: ActivityORM, visited: Optional[dict] = None
    ) -> Activity:
        if visited is None:
            visited = {}

        if data_obj.id in visited:
            return visited[data_obj.id]

        activity = Activity(
            id=data_obj.id,
            name=data_obj.name,
            depth=data_obj.depth,
            parent=None,
            children=[]
        )
        visited[activity.id] = activity

        if data_obj.parent:
            activity.parent = self.to_domain(data_obj.parent, visited)

        for child_orm in data_obj.children:
            child_domain = self.to_domain(child_orm, visited)
            activity.children.append(child_domain)

        return activity

    def from_domain(
        self, domain_obj: Activity, visited: Optional[dict] = None
    ) -> ActivityORM:
        if visited is None:
            visited = {}

        if domain_obj.id in visited:
            return visited[domain_obj.id]

        orm_obj = ActivityORM(
            id=domain_obj.id,
            name=domain_obj.name,
            depth=domain_obj.depth,
        )

        visited[orm_obj.id] = orm_obj

        if domain_obj.parent:
            orm_obj.parent = self.from_domain(domain_obj.parent, visited)
            orm_obj.parent_id = domain_obj.parent.id

        for child_domain in domain_obj.children:
            child_orm = self.from_domain(child_domain, visited)
            orm_obj.children.append(child_orm)

        return orm_obj


class OrganizationORMMapper(
    BaseORMToDomainMapper[OrganizationORM, Organization]
):
    """Mapper for Organization"""

    def __init__(
        self,
        phone_mapper: BaseORMToDomainMapper[PhoneORM, Phone] | None,
        activity_mapper: BaseORMToDomainMapper[ActivityORM, Activity] | None,
        building_mapper: BaseORMToDomainMapper[BuildingORM, Building] | None,
    ):
        self.phone_mapper = phone_mapper
        self.activity_mapper = activity_mapper
        self.building_mapper = building_mapper

    def to_domain(
        self, data_obj: OrganizationORM, visited: Optional[dict] = None
    ) -> Organization:
        if visited is None:
            visited = {}

        if data_obj.id in visited:
            return visited[data_obj.id]

        org = Organization(
            id=data_obj.id,
            name=data_obj.name,
            phones=[],
            building=None,
            activities=[]
        )

        visited[org.id] = org

        for phone_orm in data_obj.phones:
            phone_domain = self.phone_mapper.to_domain(phone_orm, visited)
            org.phones.append(phone_domain)

        if self.building_mapper and data_obj.building:
            org.building = self.building_mapper.to_domain(
                data_obj.building, visited
            )

        for activity_orm in data_obj.activities:
            activity_domain = self.activity_mapper.to_domain(
                activity_orm, visited
            )
            org.activities.append(activity_domain)

        return org

    def from_domain(
        self, domain_obj: Organization, visited: Optional[dict] = None
    ) -> OrganizationORM:
        if visited is None:
            visited = {}

        if domain_obj.id in visited:
            return visited[domain_obj.id]

        orm_obj = OrganizationORM(
            id=domain_obj.id,
            name=domain_obj.name,
        )

        if domain_obj.building:
            orm_obj.building_id = domain_obj.building.id

        visited[orm_obj.id] = orm_obj

        for phone_domain in domain_obj.phones:
            phone_orm = self.phone_mapper.from_domain(phone_domain, visited)
            phone_orm.organization_id = domain_obj.id
            orm_obj.phones.append(phone_orm)

        if self.building_mapper and domain_obj.building:
            orm_obj.building = self.building_mapper.from_domain(
                domain_obj.building, visited
            )

        for activity_domain in domain_obj.activities:
            activity_orm = self.activity_mapper.from_domain(
                activity_domain, visited
            )
            orm_obj.activities.append(activity_orm)

        return orm_obj


class BuildingORMMapper(BaseORMToDomainMapper[BuildingORM, Building]):
    """Mapper for Building"""

    def __init__(
        self,
        org_mapper: BaseORMToDomainMapper[OrganizationORM, Organization] | None,
    ):
        self.org_mapper = org_mapper

    def to_domain(
        self, data_obj: BuildingORM, visited: Optional[dict] = None
    ) -> Building:
        if visited is None:
            visited = {}

        if data_obj.id in visited:
            return visited[data_obj.id]

        point = to_shape(data_obj.location)
        geo_point = GeoPoint(latitude=point.y, longitude=point.x)

        building = Building(
            id=data_obj.id,
            name=data_obj.name,
            location=geo_point,
            organizations=[]
        )

        visited[building.id] = building

        for org_orm in data_obj.organizations:
            org_domain = self.org_mapper.to_domain(org_orm, visited)
            building.organizations.append(org_domain)

        return building

    def from_domain(
        self, domain_obj: Building, visited: Optional[dict] = None
    ) -> BuildingORM:
        if visited is None:
            visited = {}

        if domain_obj.id in visited:
            return visited[domain_obj.id]

        geo_point = from_shape(
            Point(domain_obj.location.longitude, domain_obj.location.latitude),
            srid=4326
        )

        orm_obj = BuildingORM(
            id=domain_obj.id,
            name=domain_obj.name,
            location=geo_point,
        )

        visited[orm_obj.id] = orm_obj

        for org_domain in domain_obj.organizations:
            org_orm = self.org_mapper.from_domain(org_domain, visited)
            orm_obj.organizations.append(org_orm)

        return orm_obj
