import uuid
from typing import Optional

from geoalchemy2 import Geography, WKBElement
from sqlalchemy import String, UUID, ForeignKey, Index, Integer, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base

organization_activities = Table(
    "organization_activity",
    Base.metadata,
    Column(
        "organization_id",
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="CASCADE"),
        primary_key=True
    ),
    Column(
        "activity_id",
        UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        primary_key=True
    )
)


class BuildingORM(Base):
    __tablename__ = "building"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    location: Mapped[WKBElement] = mapped_column(
        Geography(geometry_type="POINT", srid=4326),
        nullable=False,
    )

    organizations: Mapped[list["OrganizationORM"]] = relationship(
        back_populates="building",
        passive_deletes=True,
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_building_location", "location", postgresql_using="gist"),
    )


class OrganizationORM(Base):
    __tablename__ = "organization"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

    building_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("building.id", ondelete="CASCADE"),
        nullable=False
    )

    building: Mapped["BuildingORM"] = relationship(
        back_populates="organizations",
        lazy="selectin",
    )

    phones: Mapped[list["PhoneORM"]] = relationship(
        back_populates="organization",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    activities: Mapped[list["ActivityORM"]] = relationship(
        "ActivityORM",
        secondary=organization_activities,
        back_populates="organizations",
        lazy="selectin",
    )


class PhoneORM(Base):
    __tablename__ = "phone"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    number: Mapped[str] = mapped_column(String, nullable=False)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("organization.id", ondelete="CASCADE"),
        nullable=False
    )

    organization: Mapped["OrganizationORM"] = relationship(
        back_populates="phones"
    )


class ActivityORM(Base):
    __tablename__ = "activity"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    depth: Mapped[int] = mapped_column(Integer, nullable=False)

    parent_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("activity.id", ondelete="CASCADE"),
        nullable=True
    )

    parent: Mapped["ActivityORM"] = relationship(
        "ActivityORM",
        remote_side=[id],
        foreign_keys=[parent_id],
        back_populates="children",
        lazy="selectin",
    )

    children: Mapped[list["ActivityORM"]] = relationship(
        "ActivityORM",
        back_populates="parent",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    organizations: Mapped[list["OrganizationORM"]] = relationship(
        "OrganizationORM",
        secondary=organization_activities,
        back_populates="activities",
        lazy="selectin",
    )
