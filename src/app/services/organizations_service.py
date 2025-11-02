from typing import AsyncIterable
from uuid import UUID

from src.app.entities import GeoPoint, Organization
from src.infrastructure.repos.base import BaseOrganizationRepository


class OrganizationService:
    def __init__(self, org_repo: BaseOrganizationRepository):
        self._org_repo = org_repo

    async def get(self, _id: UUID) -> Organization:
        return await self._org_repo.get(_id)

    async def get_all(self, **filters) -> list[Organization]:
        res = []

        orgs = self._org_repo.get_all(**filters)

        async for org in orgs:
            print(org.building.location)
            res.append(org)

        return res

    async def get_all_in_radius(
        self, latitude: float, longitude: float, radius: float, **filters
    ) -> list[Organization]:
        center = GeoPoint(
            latitude=latitude,
            longitude=longitude,
        )
        orgs = self._org_repo.get_all_in_radius(center, radius, **filters)

        return await self._async_iter_to_list(orgs)

    async def get_all_in_bbox(
        self,
        sw_latitude: float,
        sw_longitude: float,
        ne_latitude: float,
        ne_longitude: float,
        **filters
    ):
        sw = GeoPoint(
            latitude=sw_latitude,
            longitude=sw_longitude,
        )
        ne = GeoPoint(
            latitude=ne_latitude,
            longitude=ne_longitude,
        )
        orgs = self._org_repo.get_all_in_bbox(sw, ne, **filters)

        return await self._async_iter_to_list(orgs)

    async def get_all_in_actively_tree(self, actively_root_id: UUID, **filters):
        orgs = self._org_repo.get_all_by_activity_tree(actively_root_id, **filters)

        return await self._async_iter_to_list(orgs)

    @staticmethod
    async def _async_iter_to_list(iter_: AsyncIterable) -> list:
        res = []

        async for item in iter_:
            res.append(item)

        return res
