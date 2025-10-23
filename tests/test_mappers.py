import uuid
from unittest.mock import Mock

import pytest

try:
    from shapely.geometry import Point
    from geoalchemy2.shape import from_shape

    HAS_SHAPELY = True
except ImportError:
    HAS_SHAPELY = False
    Point = None
    from_shape = None

from src.domain import Building, Organization, Activity, Phone, GeoPoint
from src.infrastructure.repos.sqlalchemy_repos.mappers import (
    PhoneORMMapper,
    ActivityORMMapper,
    OrganizationORMMapper,
    BuildingORMMapper
)


# ========== Helper Functions ==========

def create_mock_phone_orm(phone_id, number, org_id):
    """Create mock PhoneORM"""
    mock = Mock()
    mock.id = phone_id
    mock.number = number
    mock.organization_id = org_id
    return mock


def create_mock_activity_orm(activity_id, name, depth, parent=None, children=None):
    """Create mock ActivityORM"""
    mock = Mock()
    mock.id = activity_id
    mock.name = name
    mock.depth = depth
    mock.parent = parent
    mock.parent_id = parent.id if parent else None
    mock.children = children or []
    return mock


def create_mock_organization_orm(org_id, name, building_id, building=None, phones=None,
                                 activities=None):
    """Create mock OrganizationORM"""
    mock = Mock()
    mock.id = org_id
    mock.name = name
    mock.building_id = building_id
    mock.building = building
    mock.phones = phones or []
    mock.activities = activities or []
    return mock


def create_mock_building_orm(building_id, name, location, organizations=None):
    """Create mock BuildingORM"""
    mock = Mock()
    mock.id = building_id
    mock.name = name
    mock.location = location
    mock.organizations = organizations or []
    return mock


# ========== Fixtures ==========

@pytest.fixture
def phone_mapper():
    """Fixture for PhoneORMMapper"""
    return PhoneORMMapper()


@pytest.fixture
def activity_mapper():
    """Fixture for ActivityORMMapper"""
    return ActivityORMMapper()


@pytest.fixture
def organization_mapper(phone_mapper, activity_mapper):
    """Fixture for OrganizationORMMapper"""
    return OrganizationORMMapper(
        phone_mapper=phone_mapper,
        activity_mapper=activity_mapper,
        building_mapper=None
    )


@pytest.fixture
def building_mapper(organization_mapper):
    """Fixture for BuildingORMMapper"""
    mapper = BuildingORMMapper(org_mapper=organization_mapper)
    organization_mapper.building_mapper = mapper
    return mapper


# ========== Phone Mapper Tests ==========

class TestPhoneORMMapper:

    def test_phone_to_domain(self, phone_mapper):
        """Test Phone ORM to Domain conversion"""
        phone_orm = create_mock_phone_orm(
            phone_id=uuid.uuid4(),
            number="+1234567890",
            org_id=uuid.uuid4()
        )

        phone_domain = phone_mapper.to_domain(phone_orm)

        assert phone_domain.number == "+1234567890"

    def test_phone_from_domain(self, phone_mapper, monkeypatch):
        """Test Phone Domain to ORM conversion"""
        phone_domain = Phone(number="+0987654321")

        mock_phone_orm = Mock()
        mock_phone_orm.number = "+0987654321"

        mock_phone_class = Mock(return_value=mock_phone_orm)
        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.PhoneORM',
            mock_phone_class
        )

        phone_orm = phone_mapper.from_domain(phone_domain)

        assert phone_orm.number == "+0987654321"
        mock_phone_class.assert_called_once_with(number="+0987654321")


# ========== Activity Mapper Tests ==========

class TestActivityORMMapper:

    def test_activity_to_domain_simple(self, activity_mapper):
        """Test simple Activity conversion without children"""
        activity_orm = create_mock_activity_orm(
            activity_id=uuid.uuid4(),
            name="Retail",
            depth=0
        )

        activity_domain = activity_mapper.to_domain(activity_orm)

        assert activity_domain.name == "Retail"
        assert activity_domain.depth == 0
        assert activity_domain.parent is None
        assert len(activity_domain.children) == 0

    def test_activity_to_domain_with_children(self, activity_mapper):
        """Test Activity conversion with children"""
        parent_id = uuid.uuid4()

        parent_orm = create_mock_activity_orm(
            activity_id=parent_id,
            name="Retail",
            depth=0
        )

        child1_orm = create_mock_activity_orm(
            activity_id=uuid.uuid4(),
            name="Food",
            depth=1,
            parent=parent_orm
        )

        child2_orm = create_mock_activity_orm(
            activity_id=uuid.uuid4(),
            name="Electronics",
            depth=1,
            parent=parent_orm
        )

        parent_orm.children = [child1_orm, child2_orm]

        parent_domain = activity_mapper.to_domain(parent_orm)

        assert parent_domain.name == "Retail"
        assert len(parent_domain.children) == 2
        assert parent_domain.children[0].name == "Food"
        assert parent_domain.children[1].name == "Electronics"
        assert parent_domain.children[0].parent is parent_domain

    def test_activity_from_domain_simple(self, activity_mapper, monkeypatch):
        """Test Activity Domain to ORM conversion"""
        activity_domain = Activity(
            id=uuid.uuid4(),
            name="Services",
            depth=0
        )

        mock_activity_orm = Mock()
        mock_activity_orm.id = activity_domain.id
        mock_activity_orm.name = "Services"
        mock_activity_orm.depth = 0
        mock_activity_orm.children = []

        mock_activity_class = Mock(return_value=mock_activity_orm)
        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.ActivityORM',
            mock_activity_class
        )

        activity_orm = activity_mapper.from_domain(activity_domain)

        assert activity_orm.name == "Services"
        assert activity_orm.depth == 0

    def test_activity_cycle_prevention(self, activity_mapper):
        """Test cycle prevention during Activity conversion"""
        parent_id = uuid.uuid4()

        parent_orm = create_mock_activity_orm(
            activity_id=parent_id,
            name="Parent",
            depth=0
        )

        child_orm = create_mock_activity_orm(
            activity_id=uuid.uuid4(),
            name="Child",
            depth=1,
            parent=parent_orm
        )

        parent_orm.children = [child_orm]

        parent_domain = activity_mapper.to_domain(parent_orm)

        assert parent_domain.children[0].parent is parent_domain


# ========== Building Mapper Tests ==========

@pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
class TestBuildingORMMapper:

    def test_building_to_domain_simple(self, building_mapper):
        """Test Building conversion without organizations"""
        building_id = uuid.uuid4()
        geo_point = from_shape(Point(30.5, 50.4), srid=4326)

        building_orm = create_mock_building_orm(
            building_id=building_id,
            name="Tower A",
            location=geo_point
        )

        building_domain = building_mapper.to_domain(building_orm)

        assert building_domain.id == building_id
        assert building_domain.name == "Tower A"
        assert building_domain.location.longitude == pytest.approx(30.5)
        assert building_domain.location.latitude == pytest.approx(50.4)
        assert len(building_domain.organizations) == 0

    def test_building_from_domain_simple(self, building_mapper, monkeypatch):
        """Test Building Domain to ORM conversion"""
        building_domain = Building(
            id=uuid.uuid4(),
            name="Office Complex",
            location=GeoPoint(latitude=51.5, longitude=-0.1),
            organizations=[]
        )

        mock_building_orm = Mock()
        mock_building_orm.name = "Office Complex"
        mock_building_orm.location = Mock()
        mock_building_orm.organizations = []

        mock_building_class = Mock(return_value=mock_building_orm)
        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.BuildingORM',
            mock_building_class
        )

        building_orm = building_mapper.from_domain(building_domain)

        assert building_orm.name == "Office Complex"
        assert building_orm.location is not None


# ========== Organization Mapper Tests ==========

class TestOrganizationORMMapper:

    def test_organization_to_domain_simple(self, organization_mapper):
        """Test Organization conversion without relationships"""
        org_id = uuid.uuid4()
        building_id = uuid.uuid4()

        org_orm = create_mock_organization_orm(
            org_id=org_id,
            name="Tech Corp",
            building_id=building_id
        )

        org_domain = organization_mapper.to_domain(org_orm)

        assert org_domain.id == org_id
        assert org_domain.name == "Tech Corp"
        assert len(org_domain.phones) == 0
        assert len(org_domain.activities) == 0

    def test_organization_with_phones(self, organization_mapper):
        """Test Organization conversion with phones"""
        org_id = uuid.uuid4()

        phone1_orm = create_mock_phone_orm(
            phone_id=uuid.uuid4(),
            number="+1111111111",
            org_id=org_id
        )

        phone2_orm = create_mock_phone_orm(
            phone_id=uuid.uuid4(),
            number="+2222222222",
            org_id=org_id
        )

        org_orm = create_mock_organization_orm(
            org_id=org_id,
            name="Restaurant",
            building_id=uuid.uuid4(),
            phones=[phone1_orm, phone2_orm]
        )

        org_domain = organization_mapper.to_domain(org_orm)

        assert len(org_domain.phones) == 2
        assert org_domain.phones[0].number == "+1111111111"
        assert org_domain.phones[1].number == "+2222222222"

    def test_organization_from_domain_with_phones(self, organization_mapper, monkeypatch):
        """Test Organization Domain to ORM conversion with phones"""
        org_domain = Organization(
            id=uuid.uuid4(),
            name="Cafe",
            phones=[
                Phone(number="+3333333333"),
                Phone(number="+4444444444")
            ]
        )

        # Mock phones
        mock_phone1 = Mock()
        mock_phone1.number = "+3333333333"
        mock_phone1.organization_id = None

        mock_phone2 = Mock()
        mock_phone2.number = "+4444444444"
        mock_phone2.organization_id = None

        mock_phone_class = Mock(side_effect=[mock_phone1, mock_phone2])

        # Mock organization
        mock_org = Mock()
        mock_org.name = "Cafe"
        mock_org.phones = []

        mock_org_class = Mock(return_value=mock_org)

        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.OrganizationORM',
            mock_org_class
        )
        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.PhoneORM',
            mock_phone_class
        )

        org_orm = organization_mapper.from_domain(org_domain)

        assert org_orm.name == "Cafe"
        assert len(org_orm.phones) == 2


# ========== Integration Tests ==========

@pytest.mark.skipif(not HAS_SHAPELY, reason="Shapely not installed")
class TestIntegrationMappers:

    def test_building_with_organizations_to_domain(self, building_mapper):
        """Integration test: Building with Organizations"""
        building_id = uuid.uuid4()
        org1_id = uuid.uuid4()
        org2_id = uuid.uuid4()

        geo_point = from_shape(Point(20.0, 40.0), srid=4326)

        building_orm = create_mock_building_orm(
            building_id=building_id,
            name="Business Center",
            location=geo_point
        )

        org1_orm = create_mock_organization_orm(
            org_id=org1_id,
            name="Company A",
            building_id=building_id,
            building=building_orm
        )

        org2_orm = create_mock_organization_orm(
            org_id=org2_id,
            name="Company B",
            building_id=building_id,
            building=building_orm
        )

        building_orm.organizations = [org1_orm, org2_orm]

        building_domain = building_mapper.to_domain(building_orm)

        assert building_domain.name == "Business Center"
        assert len(building_domain.organizations) == 2
        assert building_domain.organizations[0].name == "Company A"
        assert building_domain.organizations[1].name == "Company B"
        assert building_domain.organizations[0].building is building_domain
        assert building_domain.organizations[1].building is building_domain

    def test_building_organization_cycle_prevention(self, building_mapper):
        """Test Building <-> Organization cycle prevention"""
        building_id = uuid.uuid4()
        org_id = uuid.uuid4()

        geo_point = from_shape(Point(15.0, 35.0), srid=4326)

        building_orm = create_mock_building_orm(
            building_id=building_id,
            name="Cycle Test Building",
            location=geo_point
        )

        org_orm = create_mock_organization_orm(
            org_id=org_id,
            name="Cycle Test Org",
            building_id=building_id,
            building=building_orm
        )

        building_orm.organizations = [org_orm]

        building_domain = building_mapper.to_domain(building_orm)

        assert building_domain.organizations[0].building is building_domain

    def test_organization_with_activities(self, organization_mapper):
        """Test Organization with Activities"""
        org_id = uuid.uuid4()
        activity_id = uuid.uuid4()

        activity_orm = create_mock_activity_orm(
            activity_id=activity_id,
            name="Retail",
            depth=0
        )

        org_orm = create_mock_organization_orm(
            org_id=org_id,
            name="Shop",
            building_id=uuid.uuid4(),
            activities=[activity_orm]
        )

        org_domain = organization_mapper.to_domain(org_orm)

        assert len(org_domain.activities) == 1
        assert org_domain.activities[0].name == "Retail"

    def test_round_trip_building(self, building_mapper, monkeypatch):
        """Test round-trip: Domain -> ORM -> Domain"""
        original_building = Building(
            id=uuid.uuid4(),
            name="Test Building",
            location=GeoPoint(latitude=55.75, longitude=37.62),
            organizations=[]
        )

        mock_building_orm = Mock()
        mock_building_orm.id = original_building.id
        mock_building_orm.name = "Test Building"
        mock_building_orm.location = from_shape(
            Point(37.62, 55.75),
            srid=4326
        )
        mock_building_orm.organizations = []

        mock_building_class = Mock(return_value=mock_building_orm)
        monkeypatch.setattr(
            'src.infrastructure.repos.sqlalchemy_repos.mappers.BuildingORM',
            mock_building_class
        )

        # Domain -> ORM
        building_orm = building_mapper.from_domain(original_building)

        # ORM -> Domain
        result_building = building_mapper.to_domain(building_orm)

        assert result_building.id == original_building.id
        assert result_building.name == original_building.name
        assert result_building.location.latitude == pytest.approx(
            original_building.location.latitude)
        assert result_building.location.longitude == pytest.approx(
            original_building.location.longitude)

    def test_complex_structure_with_all_relations(self, building_mapper):
        """Complex test with all relationships"""
        building_id = uuid.uuid4()
        org_id = uuid.uuid4()
        activity_id = uuid.uuid4()

        geo_point = from_shape(Point(10.0, 20.0), srid=4326)

        activity_orm = create_mock_activity_orm(
            activity_id=activity_id,
            name="Restaurant",
            depth=0
        )

        phone_orm = create_mock_phone_orm(
            phone_id=uuid.uuid4(),
            number="+5555555555",
            org_id=org_id
        )

        building_orm = create_mock_building_orm(
            building_id=building_id,
            name="Food Court",
            location=geo_point
        )

        org_orm = create_mock_organization_orm(
            org_id=org_id,
            name="Pizza Place",
            building_id=building_id,
            building=building_orm,
            phones=[phone_orm],
            activities=[activity_orm]
        )

        building_orm.organizations = [org_orm]

        building_domain = building_mapper.to_domain(building_orm)

        assert building_domain.name == "Food Court"
        assert len(building_domain.organizations) == 1

        org = building_domain.organizations[0]
        assert org.name == "Pizza Place"
        assert len(org.phones) == 1
        assert org.phones[0].number == "+5555555555"
        assert len(org.activities) == 1
        assert org.activities[0].name == "Restaurant"
        assert org.building is building_domain