"""
Script to populate the database with test data.

Usage:
    python seed_database.py

Or with custom parameters:
    python seed_database.py --buildings-per-city 10 --clear

Configuration is taken from src.infrastructure.config (DB_HOST, DB_NAME, etc.)
"""

import asyncio
import random
import sys
import uuid
from pathlib import Path
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import selectinload

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from geoalchemy2.shape import from_shape
from shapely.geometry import Point

from src.infrastructure.db import async_session_maker
from src.infrastructure.models import (ActivityORM, BuildingORM,
                                       OrganizationORM, PhoneORM,
                                       organization_activities)

# Test data constants
CITIES = [
    {
        "name": "Москва",
        "lat": 55.7558,
        "lon": 37.6173,
        "streets": ["Тверская", "Арбат", "Ленинский проспект", "Кутузовский проспект"],
    },
    {
        "name": "Санкт-Петербург",
        "lat": 59.9343,
        "lon": 30.3351,
        "streets": [
            "Невский проспект",
            "Лиговский проспект",
            "Московский проспект",
            "Садовая",
        ],
    },
    {
        "name": "Новосибирск",
        "lat": 55.0084,
        "lon": 82.9357,
        "streets": [
            "Красный проспект",
            "Вокзальная магистраль",
            "Большевистская",
            "Ленина",
        ],
    },
    {
        "name": "Екатеринбург",
        "lat": 56.8389,
        "lon": 60.6057,
        "streets": ["Ленина", "Малышева", "8 Марта", "Куйбышева"],
    },
    {
        "name": "Казань",
        "lat": 55.8304,
        "lon": 49.0661,
        "streets": ["Баумана", "Пушкина", "Кремлёвская", "Петербургская"],
    },
]

BUILDING_TYPES = [
    "Бизнес-центр",
    "Торговый центр",
    "Офисное здание",
    "Торгово-деловой комплекс",
    "Башня",
    "Плаза",
    "Комплекс",
    "Деловой квартал",
]

COMPANY_TYPES = [
    "ООО",
    "АО",
    "ПАО",
    "ИП",
    "Компания",
    "Группа компаний",
    "Холдинг",
    "Корпорация",
]

COMPANY_NAMES = [
    "Технологии",
    "Решения",
    "Консалтинг",
    "Сервис",
    "Инновации",
    "Цифровые решения",
    "Системы",
    "Партнёры",
    "Эксперт",
    "Профи",
    "Мастер",
    "Альянс",
]

PHONE_PREFIXES = [
    "+7495",
    "+7812",
    "+7383",
    "+7343",
    "+7843",
]  # Moscow, SPb, Novosibirsk, Ekaterinburg, Kazan

# Activity hierarchy
ACTIVITY_TREE = {
    "Розничная торговля": {
        "depth": 1,
        "children": ["Продукты питания", "Электроника", "Одежда", "Товары для дома"],
    },
    "Услуги": {
        "depth": 1,
        "children": [
            "Финансовые услуги",
            "Юридические услуги",
            "Консалтинг",
            "IT-услуги",
        ],
    },
    "Здравоохранение": {
        "depth": 1,
        "children": ["Больницы", "Поликлиники", "Аптеки", "Стоматология"],
    },
    "Образование": {
        "depth": 1,
        "children": ["Школы", "Университеты", "Учебные центры", "Библиотеки"],
    },
    "Развлечения": {
        "depth": 1,
        "children": ["Кинотеатры", "Рестораны", "Кафе", "Бары"],
    },
}


def generate_phone_number(city_prefix: str = None) -> str:
    """Generate a random Russian phone number"""
    if city_prefix is None:
        prefix = random.choice(PHONE_PREFIXES)
    else:
        prefix = city_prefix
    number = "".join([str(random.randint(0, 9)) for _ in range(7)])
    return f"{prefix}{number}"


def generate_building_address(city: dict) -> str:
    """Generate a Russian building address"""
    street = random.choice(city["streets"])
    house_num = random.randint(1, 150)
    building_type = random.choice(BUILDING_TYPES)

    # Sometimes add строение/корпус
    additional = ""
    if random.random() > 0.7:
        additional = f", стр. {random.randint(1, 5)}"
    elif random.random() > 0.5:
        additional = f", корп. {random.randint(1, 3)}"

    return f"{building_type} '{street}', ул. {street}, д. {house_num}{additional}"


def generate_geo_point(base_lat: float, base_lon: float) -> Point:
    """Generate a random geo point near the base coordinates"""
    # Add random offset (approximately ±5km)
    lat_offset = random.uniform(-0.05, 0.05)
    lon_offset = random.uniform(-0.05, 0.05)
    return Point(base_lon + lon_offset, base_lat + lat_offset)


async def create_activities(session) -> dict[str, ActivityORM]:
    """Create activity hierarchy"""
    print("Создание активностей...")

    activities_map = {}

    # Create root activities
    for activity_name, activity_data in ACTIVITY_TREE.items():
        activity = ActivityORM(
            id=uuid.uuid4(),
            name=activity_name,
            depth=activity_data["depth"],
            parent_id=None,
        )
        session.add(activity)
        activities_map[activity_name] = activity

    await session.flush()

    # Create child activities
    for parent_name, activity_data in ACTIVITY_TREE.items():
        parent = activities_map[parent_name]

        for child_name in activity_data["children"]:
            child = ActivityORM(
                id=uuid.uuid4(), name=child_name, depth=2, parent_id=parent.id
            )
            session.add(child)
            activities_map[child_name] = child

    await session.flush()
    print(f"Создано {len(activities_map)} активностей")

    return activities_map


async def create_building(
    session,
    city: dict,
) -> BuildingORM:
    """Create a single building"""
    name = generate_building_address(city)

    point = generate_geo_point(city["lat"], city["lon"])
    location = from_shape(point, srid=4326)

    building = BuildingORM(id=uuid.uuid4(), name=name, location=location)

    session.add(building)
    return building


async def create_organization(
    session,
    building: BuildingORM,
    org_number: int,
    activities: List[ActivityORM],
    city_phone_prefix: str,
) -> OrganizationORM:
    """Create a single organization with phones and activities"""
    company_type = random.choice(COMPANY_TYPES)
    company_name = random.choice(COMPANY_NAMES)
    name = f'{company_type} "{company_name}-{org_number}"'

    org_id = uuid.uuid4()
    organization = OrganizationORM(id=org_id, name=name, building_id=building.id)

    session.add(organization)

    result = await session.execute(
        select(OrganizationORM)
        .options(selectinload(OrganizationORM.activities))
        .where(OrganizationORM.id == org_id)
    )
    organization = result.scalar_one()

    await session.flush()

    # Add 1-3 phones
    num_phones = random.randint(1, 3)
    for i in range(num_phones):
        phone = PhoneORM(
            id=uuid.uuid4(),
            number=generate_phone_number(city_phone_prefix),
            organization_id=organization.id,
        )
        session.add(phone)

    # Add 1-3 random activities
    num_activities = random.randint(1, 3)
    selected_activities = random.sample(
        activities, min(num_activities, len(activities))
    )
    organization.activities.extend(selected_activities)

    return organization


async def seed_database(num_buildings_per_city: int = 5):
    """Main function to seed the database"""
    print(f"Подключение к базе данных...")

    async with async_session_maker() as session:
        try:
            # Create activities first
            activities_map = await create_activities(session)
            all_activities = list(activities_map.values())

            # Create buildings and organizations for each city
            total_buildings = 0
            total_organizations = 0
            total_phones = 0

            for city in CITIES:
                print(f"\nProcessing city: {city['name']}")

                # Get phone prefix for this city
                city_idx = CITIES.index(city)
                city_phone_prefix = (
                    PHONE_PREFIXES[city_idx]
                    if city_idx < len(PHONE_PREFIXES)
                    else PHONE_PREFIXES[0]
                )

                for building_num in range(1, num_buildings_per_city + 1):
                    # Create building
                    building = await create_building(session, city)
                    total_buildings += 1

                    # Create 2-5 organizations per building
                    num_orgs = random.randint(2, 5)

                    for org_num in range(1, num_orgs + 1):
                        # Select random activities for this organization
                        num_org_activities = random.randint(1, 3)
                        org_activities = random.sample(
                            all_activities, min(num_org_activities, len(all_activities))
                        )

                        await create_organization(
                            session,
                            building,
                            org_num,
                            org_activities,
                            city_phone_prefix,
                        )
                        total_organizations += 1

                        # Count phones (1-3 per org)
                        total_phones += random.randint(1, 3)

                    if building_num % 2 == 0:
                        print(
                            f"  Created {building_num}/{num_buildings_per_city} buildings..."
                        )

            # Commit all changes
            await session.commit()

            print("\n" + "=" * 60)
            print("Заполнение базы данных завершено успешно!")
            print("=" * 60)
            print(f"Городов: {len(CITIES)}")
            print(f"Зданий: {total_buildings}")
            print(f"Организаций: {total_organizations}")
            print(f"Телефонов: {total_phones}")
            print(f"Активностей: {len(activities_map)} (включая дочерние)")
            print("=" * 60)

        except Exception as e:
            await session.rollback()
            print(f"\nОшибка при заполнении: {e}")
            raise


async def clear_database():
    """Clear all data from the database"""
    print("Очистка базы данных...")

    async with async_session_maker() as session:
        try:
            # Delete in correct order due to foreign keys
            await session.execute(organization_activities.delete())

            # Delete phones (cascade will handle)
            from sqlalchemy import delete

            await session.execute(delete(PhoneORM))

            # Delete organizations
            await session.execute(delete(OrganizationORM))

            # Delete buildings
            await session.execute(delete(BuildingORM))

            # Delete activities
            await session.execute(delete(ActivityORM))

            await session.commit()
            print("База данных успешно очищена!")

        except Exception as e:
            await session.rollback()
            print(f"Ошибка при очистке базы данных: {e}")
            raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Заполнение базы данных тестовыми данными"
    )
    parser.add_argument(
        "--buildings-per-city",
        type=int,
        default=5,
        help="Количество зданий на город (по умолчанию: 5)",
    )
    parser.add_argument(
        "--clear", action="store_true", help="Очистить базу данных перед заполнением"
    )

    args = parser.parse_args()

    async def main():
        if args.clear:
            await clear_database()

        await seed_database(args.buildings_per_city)

    asyncio.run(main())
