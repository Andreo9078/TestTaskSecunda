import uuid
from dataclasses import dataclass, field
from typing import Optional
from uuid import UUID

from src.exceptions import MaxDepthExceeded

# ---------- Value Objects ----------


@dataclass(frozen=True)
class GeoPoint:
    latitude: float
    longitude: float


@dataclass(frozen=True)
class Phone:
    number: str


# ---------- Entities ----------


@dataclass
class Building:
    name: str
    location: GeoPoint
    id: UUID = field(default_factory=uuid.uuid4)
    organizations: list["Organization"] = field(default_factory=list)

    def add_organization(self, org: "Organization") -> None:
        self.organizations.append(org)
        org.building = self


@dataclass
class Organization:
    name: str
    id: UUID = field(default_factory=uuid.uuid4)
    phones: list[Phone] = field(default_factory=list)
    building: Optional[Building] = None
    activities: list["Activity"] = field(default_factory=list)

    def add_phone(self, phone: Phone) -> None:
        self.phones.append(phone)

    def add_activity(self, activity: "Activity") -> None:
        if activity not in self.activities:
            self.activities.append(activity)


@dataclass
class Activity:
    name: str
    depth: int
    id: UUID = field(default_factory=uuid.uuid4)
    parent: Optional["Activity"] = None
    children: list["Activity"] = field(default_factory=list)

    def add_child(self, child: "Activity") -> None:
        child.parent = self
        child.depth = self.depth + 1

        if child.depth > 3:
            raise MaxDepthExceeded("Depth can't be gather then 3")

        self.children.append(child)
