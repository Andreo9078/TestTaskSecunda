from typing import TYPE_CHECKING

from fastapi.encoders import jsonable_encoder
from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point
from starlette.requests import Request
from starlette.responses import JSONResponse

if TYPE_CHECKING:
    from src.domain import GeoPoint


def geopoint_to_wkb(point: "GeoPoint") -> WKBElement:
    """Преобразует GeoPoint в WKBElement для GeoAlchemy2"""
    shapely_point = Point(point.longitude, point.latitude)
    return from_shape(shapely_point, srid=4326)


def create_handler(code: int):
    async def json_resp_handler(request: Request, exc: Exception) -> JSONResponse:
        return JSONResponse(
            status_code=code,
            content=jsonable_encoder(
                {
                    "detail": [
                        {
                            "loc": ["body"],
                            "msg": str(exc),
                            "type": exc.__class__.__name__,
                        }
                    ]
                }
            ),
        )

    return json_resp_handler
