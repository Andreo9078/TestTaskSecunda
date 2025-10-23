from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain import Activity
from src.infrastructure.models import ActivityORM
from src.infrastructure.repos.base import BaseORMToDomainMapper
from .sqlalchemy_repo import SQLAlchemyRepository


class ActivityRepo(SQLAlchemyRepository[ActivityORM, Activity, UUID]):
    def __init__(
        self,
        session: AsyncSession,
        mapper: BaseORMToDomainMapper[ActivityORM, Activity]
    ):
        super().__init__(ActivityORM, session, mapper)
