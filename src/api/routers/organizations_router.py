from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.api.depends import OrganizationServiceDepends
from src.api.schemes.get_organization import OrganizationFilters, GetOrganization, GeoPoint

router = APIRouter(prefix="/organizations")


@router.get("")
async def get_organizations(
    org_service: OrganizationServiceDepends,
    filters: OrganizationFilters = Depends(),
) -> list[GetOrganization]:
    orgs = await org_service.get_all(
        **filters.model_dump(exclude_none=True)
    )

    return [GetOrganization.model_validate(org) for org in orgs]


@router.get("/{id}")
async def get_organization(
    id: UUID,
    org_service: OrganizationServiceDepends,
) -> GetOrganization:
    org = await org_service.get(id)

    return GetOrganization.model_validate(org)


@router.get("/in_radius")
async def get_organizations_in_radius(
    org_service: OrganizationServiceDepends,
    radius: float,
    filters: OrganizationFilters = Depends(),
    geo_point: GeoPoint = Depends(),

) -> list[GetOrganization]:
    orgs = await org_service.get_all_in_radius(
        latitude=geo_point.latitude,
        longitude=geo_point.longitude,
        radius=radius,
        **filters.model_dump(exclude_none=True),
    )

    return [GetOrganization.model_validate(org) for org in orgs]


@router.get("/in_bbox")
async def get_organizations_in_bbox(
    org_service: OrganizationServiceDepends,
    filters: OrganizationFilters = Depends(),
    sw_lat: float = Query(..., alias="sw_lat"),
    sw_lon: float = Query(..., alias="sw_lon"),
    ne_lat: float = Query(..., alias="ne_lat"),
    ne_lon: float = Query(..., alias="ne_lon"),
) -> list[GetOrganization]:
    orgs = await org_service.get_all_in_bbox(
        sw_lat, sw_lon,
        ne_lat, ne_lon,
        **filters.model_dump(exclude_none=True))

    return [GetOrganization.model_validate(org) for org in orgs]


@router.get("/search_by_activity/{activity_root_id}")
async def search_by_activity(
    org_service: OrganizationServiceDepends,
    activity_root_id: UUID,
) -> list[GetOrganization]:
    orgs = await org_service.get_all_in_actively_tree(
        activity_root_id,
    )
    return [GetOrganization.model_validate(org) for org in orgs]
