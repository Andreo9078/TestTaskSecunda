from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

class _GeoPoint(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    latitude: float
    longitude: float

class _Phone(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    number: str


class _Activity(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str

class _Building(BaseModel):
    name: str
    location: _GeoPoint
    id: UUID


class OrganizationFilters(BaseModel):
    building_id: Optional[UUID] = None
    activity_id: Optional[UUID] = None
    name: Optional[str] = None
    offset: int = 0
    limit: int = Field(10, le=50, ge=1)


class GetOrganization(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str

    phones: list[_Phone] = []
    activities: list[_Activity]

class GetDetailedOrganization(GetOrganization):
    building: _Building




class GeoPoint(BaseModel):
    latitude: float
    longitude: float
