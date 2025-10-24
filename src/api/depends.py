from typing import Annotated, AsyncGenerator, TypeAlias

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.services.organizations_service import OrganizationService
from src.infrastructure.db import async_session_maker
from src.infrastructure.repos import OrganizationRepo
from src.infrastructure.repos.sqlalchemy_repos.mappers import (
    ActivityORMMapper, BuildingORMMapper, OrganizationORMMapper,
    PhoneORMMapper)


async def _get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def _get_org_repo(
    session: Annotated[AsyncSession, Depends(_get_async_session)],
) -> OrganizationRepo:
    building_mapper = BuildingORMMapper(None)

    mapper = OrganizationORMMapper(
        PhoneORMMapper(), ActivityORMMapper(), building_mapper
    )

    building_mapper.org_mapper = mapper

    return OrganizationRepo(session, mapper)


def get_org_service(org_repo: Annotated[OrganizationRepo, Depends(_get_org_repo)]):
    return OrganizationService(org_repo=org_repo)


OrganizationServiceDepends: TypeAlias = Annotated[
    OrganizationService, Depends(get_org_service)
]
