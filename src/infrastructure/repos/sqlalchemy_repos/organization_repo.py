from typing import Any, Optional
from uuid import UUID

from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_DWithin
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from src.domain import GeoPoint, Organization
from src.infrastructure.models import (ActivityORM, BuildingORM,
                                       OrganizationORM,
                                       organization_activities)
from src.infrastructure.repos.base import (BaseOrganizationRepository,
                                           BaseORMToDomainMapper)
from src.infrastructure.repos.sqlalchemy_repos.sqlalchemy_repo import \
    SQLAlchemyRepository
from src.utils import geopoint_to_wkb


class OrganizationRepo(
    SQLAlchemyRepository[OrganizationORM, Organization, UUID],
    BaseOrganizationRepository,
):
    def __init__(
        self,
        session: AsyncSession,
        mapper: BaseORMToDomainMapper[OrganizationORM, Organization],
    ):
        super().__init__(OrganizationORM, session, mapper)

    async def get_all_in_bbox(
        self,
        sw: GeoPoint,
        ne: GeoPoint,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        activity_id: Optional[UUID] = None,
        **filters,
    ):
        stmt = self._create_get_all_stmt(offset, limit, activity_id)

        stmt = stmt.options(
            selectinload(self.table.building),
        ).join(self.table.building)

        envelope = func.ST_MakeEnvelope(
            sw.longitude, sw.latitude, ne.longitude, ne.latitude, 4326
        )
        stmt = stmt.where(func.ST_Within(BuildingORM.location.cast(Geometry), envelope))

        res = await self.session.stream(stmt)

        async for row in res.scalars():
            yield self.domain_mapper.to_domain(row)

    async def get_all_in_radius(
        self,
        center: GeoPoint,
        radius_meters: float,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        activity_id: Optional[UUID] = None,
        **filters,
    ):
        stmt = self._create_get_all_stmt(offset, limit, activity_id)

        wkb_center = geopoint_to_wkb(center)

        stmt = stmt.options(
            selectinload(self.table.building),
        ).join(BuildingORM)

        stmt = stmt.where(ST_DWithin(BuildingORM.location, wkb_center, radius_meters))

        res = await self.session.stream(stmt)

        async for row in res.scalars():
            yield self.domain_mapper.to_domain(row)

    async def get_all_by_activity_tree(
        self,
        root_activity_id: UUID,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
    ):
        activity_alias = aliased(ActivityORM)
        base_cte = (
            select(ActivityORM.id)
            .where(ActivityORM.id == root_activity_id)
            .cte(name="activity_tree", recursive=True)
        )

        recursive = select(activity_alias.id).join(
            base_cte, activity_alias.parent_id == base_cte.c.id
        )
        activity_tree = base_cte.union_all(recursive)

        stmt = (
            select(OrganizationORM)
            .join(
                organization_activities,
                OrganizationORM.id == organization_activities.c.organization_id,
            )
            .join(
                activity_tree,
                organization_activities.c.activity_id == activity_tree.c.id,
            )
        )

        stmt = stmt.options(
            selectinload(OrganizationORM.building),
            selectinload(OrganizationORM.activities),
        )

        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        res = await self.session.stream(stmt)
        async for org in res.scalars():
            yield self.domain_mapper.to_domain(org)

    def _create_get_all_stmt(
        self,
        offset: Optional[int] = None,
        limit: Optional[int] = None,
        activity_id: Optional[UUID] = None,
        name: Optional[str] = None,
        **filters: Any,
    ) -> Select:
        stmt = super()._create_get_all_stmt(offset, limit, **filters)

        stmt = stmt.options(
            selectinload(self.table.building), selectinload(self.table.activities)
        )

        if activity_id is not None:
            stmt = stmt.join(self.table.activities).where(ActivityORM.id == activity_id)
        if name is not None:
            stmt = stmt.where(self.table.name.ilike(f"%{name}%"))

        return stmt
