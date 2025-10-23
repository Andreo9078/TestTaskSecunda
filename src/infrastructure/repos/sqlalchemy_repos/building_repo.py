from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from .sqlalchemy_repo import SQLAlchemyRepository
from ..base import BaseORMToDomainMapper
from ...models import BuildingORM
from ....domain import Building


class BuildingRepo(
    SQLAlchemyRepository[BuildingORM, Building, UUID]
):
    def __init__(
        self,
        session: AsyncSession,
        mapper: BaseORMToDomainMapper[BuildingORM, Building]
    ):
        super().__init__(BuildingORM, session, mapper)
