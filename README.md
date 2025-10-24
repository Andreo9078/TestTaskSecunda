## Описание проекта

Это FastAPI-приложение для работы с организациями.
Позволяет:

- Получать организации по различным фильтрам (здание, вид деятельности, геопозиция)
- Получать организацию по ID
- Искать организации по виду деятельности, включая вложенные уровни
- Поиск по названию организации

Стек:

- `FastAPI`
- `PostgreSQL` + `PostGIS`
- `Alembic` для миграций
- `Poetry` для управления зависимостями

### 🚀 Запуск проекта

1. Подготовка `.env`

Создайте файл `.env`:
```dotenv
DB_USER=postgres
DB_PASS=postgres
DB_NAME=app_db
DB_PORT=5432

API_KEY=supersecretkey
```

2. Запуск через Docker Compose

```commandline
docker compose up -d
```

FastAPI доступен: http://localhost:8000

Swagger UI: http://localhost:8000/docs

PgAdmin: http://localhost:5050

### 📑 Эндпоинты

1. Получить список организаций

```http request
GET /organizations
```

Параметры Query (опционально):

- `building_id` — фильтр по зданию
- `name` — поиск по названию
- `activity_id` — фильтр по виду деятельности


2. Получить организацию по ID

```http request
GET /organizations/{id}
```

3. Организации в радиусе от точки

```http request
GET /organizations/in_radius
```
Параметры Query:

- `latitude` — широта центра
- `longitude` — долгота центра
- `radius` — радиус в метрах

Опционально: фильтры `building_id`, `activity_root_id`

4. Организации в bounding box

```http request
GET /organizations/in_bbox
```

Параметры Query:

- `sw_lat`, `sw_lon` — юго-западные координаты
- `ne_lat`, `ne_lon` — северо-восточные координаты

Опционально: фильтры `building_id`, `activity_root_id`

5. Поиск организаций по виду деятельности

```http request
GET /organizations/search_by_activity/{activity_root_id}
```

Возвращает организации по указанному виду деятельности и всех его дочерних.

### ER - диаграмма БД

![ТЗSecunda](https://github.com/user-attachments/assets/2981e1be-b6c7-48ef-9262-2b201824397b)

