from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache
from redis import asyncio as aioredis
from starlette import status

from src.api import api_router
from src.config import API_KEY, REDIS_HOST, REDIS_PORT
from src.exceptions import registry as main_exc_registry
from src.infrastructure.repos.exceptions import registry as repos_exc_registry

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    redis = aioredis.from_url(
        f"redis://{REDIS_HOST}:{REDIS_PORT}", encoding="utf-8", decode_responses=True
    )
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")
    yield


@cache()
async def get_cache():
    return 1


app = FastAPI(
    dependencies=[Depends(get_api_key)],
    lifespan=lifespan,
)

app.include_router(api_router)

main_exc_registry(app.add_exception_handler)
repos_exc_registry(app.add_exception_handler)
