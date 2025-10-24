from fastapi import FastAPI, Security, HTTPException, Depends
from fastapi.security import APIKeyHeader
from starlette import status

from src.api import api_router
from src.config import API_KEY

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_api_key(api_key: str = Security(api_key_header)):
    if api_key != API_KEY:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing API Key",
        )
    return api_key


app = FastAPI(dependencies=[Depends(get_api_key)])

app.include_router(api_router)
