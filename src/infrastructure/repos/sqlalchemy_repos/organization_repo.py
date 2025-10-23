from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .sqlalchemy_repo import SQLAlchemyRepository
from ..base import BaseORMToDomainMapper
from ...models import OrganizationORM
from ....domain import Organization


class OrganizationRepo(SQLAlchemyRepository[OrganizationORM, Organization, UUID]):
    def __init__(
        self,
        session: AsyncSession,
        mapper: BaseORMToDomainMapper[OrganizationORM, Organization]
    ):
        super().__init__(OrganizationORM, session, mapper)
