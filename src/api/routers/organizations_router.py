from uuid import UUID

from fastapi import APIRouter, Depends, Query
from fastapi_cache.decorator import cache

from src.api.depends import OrganizationServiceDepends
from src.api.schemes.get_organization import (GeoPoint, GetOrganization,
                                              OrganizationFilters)

router = APIRouter(prefix="/organizations")


@router.get(
    "",
    summary="Get list of organizations",
    description="Returns a list of organizations with optional filtering.",
    response_model=list[GetOrganization],
)
@cache(expire=30)
async def get_organizations(
    org_service: OrganizationServiceDepends,
    filters: OrganizationFilters = Depends(),
) -> list[GetOrganization]:
    orgs = await org_service.get_all(**filters.model_dump(exclude_none=True))

    return [GetOrganization.model_validate(org) for org in orgs]


@router.get(
    "/{id}",
    summary="Get organization by ID",
    description="Retrieve a single organization by its UUID.",
    response_model=GetOrganization,
)
async def get_organization(
    id: UUID,
    org_service: OrganizationServiceDepends,
) -> GetOrganization:
    org = await org_service.get(id)
    return GetOrganization.model_validate(org)


@router.get(
    "/in_radius",
    summary="Get organizations within a radius",
    description="Returns organizations within a given radius (meters) from a geo point.",
    response_model=list[GetOrganization],
)
@cache(expire=30)
async def get_organizations_in_radius(
    org_service: OrganizationServiceDepends,
    radius: float = Query(..., gt=0, description="Radius in meters"),
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


@router.get(
    "/in_bbox",
    summary="Get organizations within a bounding box",
    description="Returns organizations located inside the specified bounding box.",
    response_model=list[GetOrganization],
)
@cache(expire=30)
async def get_organizations_in_bbox(
    org_service: OrganizationServiceDepends,
    filters: OrganizationFilters = Depends(),
    sw_lat: float = Query(
        ..., alias="sw_lat", description="South-west latitude of bounding box"
    ),
    sw_lon: float = Query(
        ..., alias="sw_lon", description="South-west longitude of bounding box"
    ),
    ne_lat: float = Query(
        ..., alias="ne_lat", description="North-east latitude of bounding box"
    ),
    ne_lon: float = Query(
        ..., alias="ne_lon", description="North-east longitude of bounding box"
    ),
):
    orgs = await org_service.get_all_in_bbox(
        sw_lat, sw_lon, ne_lat, ne_lon, **filters.model_dump(exclude_none=True)
    )

    return [GetOrganization.model_validate(org) for org in orgs]


@router.get(
    "/search_by_activity/{activity_root_id}",
    summary="Search organizations by activity root",
    description="Returns organizations linked to a given activity root ID.",
    response_model=list[GetOrganization],
)
@cache(expire=30)
async def search_by_activity(
    org_service: OrganizationServiceDepends,
    activity_root_id: UUID,
) -> list[GetOrganization]:
    orgs = await org_service.get_all_in_actively_tree(
        activity_root_id,
    )
    return [GetOrganization.model_validate(org) for org in orgs]
