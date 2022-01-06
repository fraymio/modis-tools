""" Classes and wrapper for grouped or preprocessed parameters. """

from typing import Any, Optional

import re

from datetime import datetime, timedelta
from dateutil import parser

try:
    from osgeo.ogr import Geometry
except ImportError:
    Geometry = type(None)

try:
    _HAS_SHAPELY = True
    import shapely.geometry
    from shapely import wkt

    SHAPELY_TYPES = shapely.geometry.base.BaseGeometry
except ImportError:
    _HAS_SHAPELY = False
    SHAPELY_TYPES = (type(None),)


class RequestsArg:
    """Base for processing arguments to requests. Require args to implement
    a `to_dict` method.
    """

    def to_dict(self):
        """Convert args to dictionary."""
        raise NotImplementedError


class CollectionDoiParams(RequestsArg):
    """Formated product short name and version."""

    modis_doi: str = "10.5067/MODIS"

    def __init__(self, short_name: Optional[Any] = None, version: Optional[Any] = None):
        self.short_name = short_name
        self.version = version

    def to_dict(self):
        return {"doi": f"{self.modis_doi}/{self.short_name}.{self.version}"}


class DateParams(RequestsArg):
    """Parsed date range with start, end, and difference."""

    stftime_format = "%Y-%m-%dT%H:%M:%SZ"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

    def __init__(
        self,
        start_date: Optional[Any] = None,
        end_date: Optional[Any] = None,
        time_delta: Optional[Any] = None,
    ):
        if all([start_date, end_date, time_delta]):
            self.start_date = self._parse_datetime(start_date)
            self.end_date = self._parse_datetime(end_date)
            delta = self._parse_timedelta(time_delta)
            if self.start_date + abs(delta) != self.end_date:
                raise Exception(
                    "If all start, end, and time delta are used they must "
                    "add up (start + delta = end)."
                )
        elif not any([start_date, end_date]):
            raise Exception("One end of date range needed")
        else:
            if start_date is not None:
                self.start_date = self._parse_datetime(start_date)
                if time_delta is not None:
                    delta = self._parse_timedelta(time_delta)
                    self.end_date = self.start_date + abs(delta)
            if end_date is not None:
                self.end_date = self._parse_datetime(end_date)
                if time_delta is not None:
                    delta = self._parse_timedelta(time_delta)
                    self.start_date = self.end_date - abs(delta)

    @property
    def time_delta(self):
        """Difference between start and end dates. None if open ended."""
        if all([self.end_date, self.start_date]):
            return self.end_date - self.start_date

    def _parse_datetime(self, obj: Any) -> datetime:
        """Try to parse data to datetime."""
        try:
            if issubclass(type(obj), datetime):
                parsed = obj
            elif isinstance(obj, str):
                parsed = parser.parse(obj)
            elif isinstance(obj, (tuple, list)):
                parsed = datetime(*obj)
            elif isinstance(obj, dict):
                parsed = datetime(**obj)
            return parsed
        except (ValueError, TypeError, parser.ParserError) as err:
            raise Exception("Could not convert date(s) to datetime") from err

    def _parse_timedelta(self, obj: Any) -> timedelta:
        """Try to parse data to timedelta."""
        if issubclass(type(obj), timedelta):
            parsed = obj
        elif isinstance(obj, int):
            parsed = timedelta(obj)
        elif isinstance(obj, dict):
            try:
                parsed = timedelta(**obj)
            except TypeError as err:
                raise Exception("Could not convert time_delta") from err
        return parsed

    def to_dict(self):
        """Return data range as `temporal` argument."""
        start = (
            ""
            if self.start_date is None
            else self.start_date.strftime(self.stftime_format)
        )
        end = (
            "" if self.end_date is None else self.end_date.strftime(self.stftime_format)
        )

        temporal = re.sub(r"^,|,$", "/", start + "," + end)

        return {"temporal": temporal}


class FileQuery(RequestsArg):
    """Format file post query."""

    def to_dict(self):
        pass


class SpatialQuery(RequestsArg):
    """Format spatial search query."""

    geom_type: str
    coordinates: str

    def __init__(
        self,
        spatial: Any = None,
        bounding_box: Any = None
    ):
        """Parse geometry type and coordinates from spatial query.

        Args:
            spatial (Any, optional): spatial intersection query with 
                granules. Will parse ogr.Geometry's, shapely objects, GeoJSON 
                features/geometries. Geometries must be in longitude, latitude.
                Defaults to None.
            bounding_box (Any, optional): spatial query using bounding
                box. Will parse ogr.Geometry's, shapely objects, GeoJSON 
                features/geometries, or list of coordinates in the format 
                (xmin, ymin, xmax, ymax). Geometries must be in longitude,
                latitude. Defaults to None.
        """
        if spatial:
            self._parse_spatial(spatial)
        else:
            self._parse_bounding_box(bounding_box)

    def _parse_spatial(self, spatial):
        # Convert everything to shapely
        if isinstance(spatial, dict) and _HAS_SHAPELY:
            if "geometry" in spatial:
                geom = shapely.geometry.shape(spatial["geometry"])
            else:
                geom = shapely.geometry.shape(spatial)
        elif isinstance(spatial, Geometry):
            geom = wkt.loads(spatial.ExportToWkt())
        elif isinstance(spatial, SHAPELY_TYPES):
            geom = spatial
        else:
            raise ValueError(
                f"Can't create spatial query based on provided spatial input of type {type(spatial)}; it should be a dict, ogr.Geometry or shapely.geometry type"
            )
        if geom.geom_type in ("MultiPolygon", "GeometryCollection"):
            # For complex polygons/geometries use convex hull
            geom = geom.convex_hull
        if geom.geom_type.startswith("Line"):
            self.geom_type = "line"
        else:
            self.geom_type = geom.geom_type.lower()

        self.coordinates = self._coordinate_string(geom)

    def _coordinate_string(self, geom):
        """Format coordinates to string. Regex to find pieces of coordinate sequences.
        For polygons with inner rings, we use only the outer boundary by using the first
        sequence.
        """
        if geom.geom_type == "Polygon":
            # Ensure coordinates are counter clockwise
            geom = shapely.geometry.polygon.orient(geom)
        wkt_string = wkt.dumps(geom, rounding_precision=4)
        pieces = re.findall(r"\(([\d\.\-, ]+)\)", wkt_string)
        return pieces[0].replace(", ", ",").replace(" ", ",")

    def _parse_bounding_box(self, bounding_box):
        """
        Parse coorindates from bounding box argument.
        """
        self.geom_type = "bounding_box"
        if isinstance(bounding_box, (list, tuple)):
            assertion = "Bounding box should be (xmin, ymin, xmax, ymax)"
            assert (
                bounding_box[0] <= bounding_box[2] or bounding_box[1] <= bounding_box[3]
            ), assertion
            coordinates = bounding_box
        elif isinstance(bounding_box, dict) and _HAS_SHAPELY:
            if "geometry" in bounding_box:
                coordinates = shapely.geometry.shape(bounding_box["geometry"]).bounds
            else:
                coordinates = shapely.geometry.shape(bounding_box).bounds
        elif isinstance(bounding_box, Geometry):
            xmin, xmax, ymin, ymax = bounding_box.GetEnvelope()
            coordinates = [xmin, ymin, xmax, ymax]
        elif isinstance(bounding_box, SHAPELY_TYPES):
            coordinates = bounding_box.bounds
        else:
            raise ValueError(
                f"Can't create bounding box query based on spatial input of type {type(bounding_box)}; it should be a list, tuple, dict, ogr.Geometry or shapely.geometry type"
            )
        self.coordinates = ",".join([str(c) for c in coordinates])

    def to_dict(self):
        return {self.geom_type: self.coordinates}
