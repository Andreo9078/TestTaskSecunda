from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ....domain import Building
from ...models import BuildingORM
from ..base import BaseORMToDomainMapper
from .sqlalchemy_repo import SQLAlchemyRepository


class BuildingRepo(SQLAlchemyRepository[BuildingORM, Building, UUID]):
    def __init__(
        self,
        session: AsyncSession,
        mapper: BaseORMToDomainMapper[BuildingORM, Building],
    ):
        super().__init__(BuildingORM, session, mapper)
