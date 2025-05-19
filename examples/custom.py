# Example: adding a custom converter

from dataclasses import dataclass
import castfit


@dataclass
class LatLon:
    lat: float
    lon: float


@castfit.casts
def str_to_latlon(s: str) -> LatLon:
    lat, lon = map(float, s.split(","))
    return LatLon(lat, lon)


assert castfit.to_type("40.7,-74.0", LatLon) == LatLon(40.7, -74.0)
