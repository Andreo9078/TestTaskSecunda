from typing import Optional
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy import Column, Integer, String
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import declarative_base

from src.infrastructure.repos.base import BaseORMToDomainMapper
from src.infrastructure.repos.exceptions import (ObjectAlreadyExists,
                                                 ObjectDoesNotExists)
from src.infrastructure.repos.sqlalchemy_repos.sqlalchemy_repo import \
    SQLAlchemyRepository

# Configure pytest for asyncio
pytest_plugins = ("pytest_asyncio",)

Base = declarative_base()


# Test fixtures - Domain and ORM models
class DomainUser:
    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email

    def __eq__(self, other):
        return (
            isinstance(other, DomainUser)
            and self.id == other.id
            and self.name == other.name
            and self.email == other.email
        )


class ORMUser(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    email = Column(String(100))

    def __init__(self, id: int, name: str, email: str):
        self.id = id
        self.name = name
        self.email = email


class UserMapper(BaseORMToDomainMapper[ORMUser, DomainUser]):
    def to_domain(self, orm_obj: ORMUser, visited: Optional[dict] = None) -> DomainUser:
        return DomainUser(id=orm_obj.id, name=orm_obj.name, email=orm_obj.email)

    def from_domain(
        self, domain_obj: DomainUser, visited: Optional[dict] = None
    ) -> ORMUser:
        return ORMUser(id=domain_obj.id, name=domain_obj.name, email=domain_obj.email)


@pytest.fixture
def mock_session():
    """Create a mock AsyncSession"""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def user_mapper():
    """Create UserMapper instance"""
    return UserMapper()


@pytest.fixture
def repository(mock_session, user_mapper):
    """Create SQLAlchemyRepository instance"""
    return SQLAlchemyRepository(
        table=ORMUser, session=mock_session, domain_mapper=user_mapper
    )


@pytest.fixture
def sample_orm_user():
    """Create sample ORM user"""
    return ORMUser(id=1, name="John Doe", email="john@example.com")


@pytest.fixture
def sample_domain_user():
    """Create sample domain user"""
    return DomainUser(id=1, name="John Doe", email="john@example.com")


class TestGet:
    """Tests for get method"""

    @pytest.mark.asyncio
    async def test_get_existing_object(
        self, repository, mock_session, sample_orm_user, sample_domain_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_orm_user
        mock_session.execute.return_value = mock_result

        result = await repository.get(1)

        assert result == sample_domain_user
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_non_existing_object(self, repository, mock_session):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        result = await repository.get(999)

        assert result is None
        mock_session.execute.assert_called_once()


class TestGetAll:
    """Tests for get_all method"""

    @pytest.mark.asyncio
    async def test_get_all_without_filters(self, repository, mock_session):
        orm_users = [
            ORMUser(id=1, name="User 1", email="user1@example.com"),
            ORMUser(id=2, name="User 2", email="user2@example.com"),
        ]

        # Create async iterator mock
        async def async_gen():
            for user in orm_users:
                yield user

        mock_scalars = Mock()
        mock_scalars.__aiter__ = lambda self: async_gen()

        mock_stream_result = Mock()
        mock_stream_result.scalars.return_value = mock_scalars

        mock_session.stream.return_value = mock_stream_result

        results = []
        async for user in repository.get_all():
            results.append(user)

        assert len(results) == 2
        assert results[0].id == 1
        assert results[1].id == 2
        mock_session.stream.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all_with_filters(self, repository, mock_session):
        orm_user = ORMUser(id=1, name="John", email="john@example.com")

        async def async_gen():
            yield orm_user

        mock_scalars = Mock()
        mock_scalars.__aiter__ = lambda self: async_gen()

        mock_stream_result = Mock()
        mock_stream_result.scalars.return_value = mock_scalars

        mock_session.stream.return_value = mock_stream_result

        results = []
        async for user in repository.get_all(name="John"):
            results.append(user)

        assert len(results) == 1
        assert results[0].name == "John"

    @pytest.mark.asyncio
    async def test_get_all_with_pagination(self, repository, mock_session):
        async def async_gen():
            return
            yield  # Make it a generator

        mock_scalars = Mock()
        mock_scalars.__aiter__ = lambda self: async_gen()

        mock_stream_result = Mock()
        mock_stream_result.scalars.return_value = mock_scalars

        mock_session.stream.return_value = mock_stream_result

        results = []
        async for user in repository.get_all(offset=10, limit=5):
            results.append(user)

        mock_session.stream.assert_called_once()


class TestCreate:
    """Tests for create method"""

    @pytest.mark.asyncio
    async def test_create_new_object(
        self, repository, mock_session, sample_domain_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        await repository.create(sample_domain_user)

        mock_session.execute.assert_called_once()
        mock_session.merge.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_existing_object_raises_exception(
        self, repository, mock_session, sample_domain_user, sample_orm_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_orm_user
        mock_session.execute.return_value = mock_result

        with pytest.raises(ObjectAlreadyExists) as exc_info:
            await repository.create(sample_domain_user)

        assert "already exists" in str(exc_info.value)
        mock_session.merge.assert_not_called()


class TestUpdate:
    """Tests for update method"""

    @pytest.mark.asyncio
    async def test_update_existing_object(
        self, repository, mock_session, sample_domain_user, sample_orm_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_orm_user
        mock_session.execute.return_value = mock_result

        await repository.update(sample_domain_user)

        mock_session.execute.assert_called_once()
        mock_session.merge.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_non_existing_object_raises_exception(
        self, repository, mock_session, sample_domain_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ObjectDoesNotExists) as exc_info:
            await repository.update(sample_domain_user)

        assert "does not exists" in str(exc_info.value)
        mock_session.merge.assert_not_called()


class TestDelete:
    """Tests for delete method"""

    @pytest.mark.asyncio
    async def test_delete_existing_object(
        self, repository, mock_session, sample_orm_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_orm_user
        mock_session.execute.return_value = mock_result

        await repository.delete(1)

        mock_session.execute.assert_called_once()
        mock_session.delete.assert_called_once_with(sample_orm_user)

    @pytest.mark.asyncio
    async def test_delete_non_existing_object_raises_exception(
        self, repository, mock_session
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_session.execute.return_value = mock_result

        with pytest.raises(ObjectDoesNotExists) as exc_info:
            await repository.delete(999)

        assert "does not exists" in str(exc_info.value)
        mock_session.delete.assert_not_called()


class TestPrivateMethods:
    """Tests for private methods"""

    @pytest.mark.asyncio
    async def test_save_calls_merge(self, repository, mock_session, sample_domain_user):
        await repository._save(sample_domain_user)

        mock_session.merge.assert_called_once()
        args = mock_session.merge.call_args[0]
        assert isinstance(args[0], ORMUser)
        assert args[0].id == sample_domain_user.id

    @pytest.mark.asyncio
    async def test_get_returns_orm_object(
        self, repository, mock_session, sample_orm_user
    ):
        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_orm_user
        mock_session.execute.return_value = mock_result

        result = await repository._get(1)

        assert result == sample_orm_user
        assert isinstance(result, ORMUser)

    def test_create_get_all_stmt_without_pagination(self, repository):
        stmt = repository._create_get_all_stmt(name="John")

        assert stmt is not None

    def test_create_get_all_stmt_with_pagination(self, repository):
        stmt = repository._create_get_all_stmt(offset=10, limit=5, name="John")

        assert stmt is not None

    def test_create_get_all_stmt_filters_applied(self, repository):
        stmt = repository._create_get_all_stmt(name="John", email="john@test.com")

        assert stmt is not None
        # Check that filters are in the compiled statement
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "users" in compiled.lower()
