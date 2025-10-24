from geoalchemy2 import WKBElement
from geoalchemy2.shape import from_shape
from shapely import Point

from src.domain import GeoPoint


def geopoint_to_wkb(point: GeoPoint) -> WKBElement:
    """Преобразует GeoPoint в WKBElement для GeoAlchemy2"""
    shapely_point = Point(point.longitude, point.latitude)
    return from_shape(shapely_point, srid=4326)
