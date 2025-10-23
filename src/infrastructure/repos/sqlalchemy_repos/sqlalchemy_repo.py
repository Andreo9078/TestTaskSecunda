from typing import Any, Optional, AsyncIterable, Type

from sqlalchemy import select, Select
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.repos.base import BaseRepository, BaseORMToDomainMapper
from src.infrastructure.repos.exceptions import ObjectAlreadyExists, ObjectDoesNotExists


class SQLAlchemyRepository[ORMObj, DomainObj, ID](BaseRepository[ORMObj, ID]):
    def __init__(
        self,
        table: Type[ORMObj],
        session: AsyncSession,
        domain_mapper: BaseORMToDomainMapper[ORMObj, DomainObj]
    ) -> None:
        self.table = table
        self.session = session
        self.domain_mapper = domain_mapper

    async def get(self, obj_id: ID) -> Optional[DomainObj]:
        res = await self._get(obj_id)

        if res is None:
            return None

        return self.domain_mapper.to_domain(
            res
        )

    async def get_all(self, **filters: Any) -> AsyncIterable[DomainObj]:
        stmt = self._create_get_all_stmt(**filters)
        res = await self.session.stream(stmt)

        async for row in res.scalars():
            yield self.domain_mapper.to_domain(row)

    async def create(self, obj: DomainObj) -> None:
        if await self._get(obj.id):
            raise ObjectAlreadyExists(
                f"Object with id {obj.id} already exists."
            )

        await self._save(obj)

    async def update(self, obj: DomainObj) -> None:
        if not await self._get(obj.id):
            raise ObjectDoesNotExists(
                f"Object with id {obj.id} does not exists."
            )

        await self._save(obj)

    async def delete(self, obj_id: ID) -> None:
        orm_obj = await self._get(obj_id)
        if orm_obj:
            await self.session.delete(orm_obj)
        else:
            raise ObjectDoesNotExists(
                f"Object with id {obj_id} does not exists."
            )

    async def _save(self, obj: DomainObj):
        record = self.domain_mapper.from_domain(obj)
        await self.session.merge(record)

    async def _get(self, obj_id: ID) -> Optional[ORMObj]:
        statement = select(self.table).where(self.table.id == obj_id)
        res = await self.session.execute(statement)

        return res.scalar_one_or_none()

    def _create_get_all_stmt(
        self, offset: int = None, limit: int = None, **filters: Any
    ) -> Select:
        stmt = select(self.table).filter_by(**filters)
        if offset is not None:
            stmt = stmt.offset(offset)
        if limit is not None:
            stmt = stmt.limit(limit)

        return stmt
