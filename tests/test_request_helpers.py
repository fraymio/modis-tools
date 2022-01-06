from datetime import timedelta
import sys

import pytest

try:
    import shapely
    import shapely.geometry

    SHAPELY_TYPES = (
        shapely.geometry.GeometryCollection,
        shapely.geometry.LineString,
        shapely.geometry.LinearRing,
        shapely.geometry.MultiPolygon,
        shapely.geometry.Point,
        shapely.geometry.Polygon,
    )
except ImportError:
    ...

try:
    from osgeo import ogr
except ImportError:
    ...

from modis_tools.request_helpers import DateParams, SpatialQuery

NEED_OSGEO = "Requires installation of osgeo"
NEED_SHAPELY = "Requires installation of shapely"

class TestDateParams:
    def test_with_one_date_raises_error(self):
        with pytest.raises(Exception):
            DateParams()

    def test_time_delta_is_correct(self):
        DateParams("2005-01-01", "2005-01-02", timedelta(days=1))

    def test_start_after_end_raises_error(self):
        with pytest.raises(Exception):
            DateParams("2005-01-01", "2005-01-02", timedelta(days=2))

    def test_can_infer_time_delta(self):
        d = DateParams("2005-01-01", "2005-01-02")
        assert d.time_delta == timedelta(days=1)


class TestSpatialQuery:
    @pytest.mark.skipif("shapely" not in sys.modules, reason=NEED_SHAPELY)
    def test_can_update_shapely_types(self):
        for t in SHAPELY_TYPES:
            assert issubclass(
                t, shapely.geometry.base.BaseGeometry
            ), f"Shapely no longer considers {t} as a `BaseGeometry`. `SpatialQuery()` must be updated accordingly"

    def test_can_parse_nga_list_bbox(self):
        bbox = [2.1448863675, 4.002583177, 15.289420717, 14.275061098]
        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "2.1448863675,4.002583177,15.289420717,14.275061098"
        assert query.geom_type == "bounding_box"

    def test_parse_mock_list_bbox(self):
        bbox = [1.2, 3.4, 5.6, 7.8]
        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "1.2,3.4,5.6,7.8"
        assert query.geom_type == "bounding_box"

    def test_parse_mock_tuple_bbox(self):
        bbox = (1.2, 3.4, 5.6, 7.8)
        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "1.2,3.4,5.6,7.8"
        assert query.geom_type == "bounding_box"

    def test_parse_inverted_mock_list_bbox_fails(self):
        bbox = [10, 10, 0, 0]
        with pytest.raises(AssertionError):
            query = SpatialQuery(spatial=None, bounding_box=bbox)

    @pytest.mark.skipif("osgeo" not in sys.modules, reason=NEED_OSGEO)
    def test_can_parse_bbox_from_gdal_bbox(self):
        bbox = ogr.Geometry(ogr.wkbLinearRing)
        bbox.AddPoint(1, 1)
        bbox.AddPoint(1, 2)
        bbox.AddPoint(2, 2)
        bbox.AddPoint(2, 1)
        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "1.0,1.0,2.0,2.0"
        assert query.geom_type == "bounding_box"

    @pytest.mark.skipif("osgeo" not in sys.modules, reason=NEED_OSGEO)
    def test_can_parse_spatial_from_gdal_bbox(self):
        wkt = "POLYGON ((5 30, 5 33, 2 33, 2 30, 5 30))"
        spatial = ogr.CreateGeometryFromWkt(wkt)
        query = SpatialQuery(spatial=spatial, bounding_box=None)
        assert (
            query.coordinates
            == "5.0000,30.0000,5.0000,33.0000,2.0000,33.0000,2.0000,30.0000,5.0000,30.0000"
        )
        assert query.geom_type == "polygon"

    @pytest.mark.skipif("osgeo" not in sys.modules, reason=NEED_OSGEO)
    def test_can_parse_bbox_from_gdal_diamond_polygon(self):
        # Create a pentagon
        bbox = ogr.Geometry(ogr.wkbLinearRing)
        bbox.AddPoint(1, 2)
        bbox.AddPoint(2, 3)
        bbox.AddPoint(3, 2)
        bbox.AddPoint(2, 1)
        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "1.0,1.0,3.0,3.0"
        assert query.geom_type == "bounding_box"

    @pytest.mark.skipif("osgeo" not in sys.modules, reason=NEED_OSGEO)
    def test_can_parse_spatial_from_gdal_multipoligon(self):
        multipolygon = ogr.Geometry(ogr.wkbMultiPolygon)

        # Create ring #1
        ring1 = ogr.Geometry(ogr.wkbLinearRing)
        ring1.AddPoint(12.0, 63.0)
        ring1.AddPoint(12.0, 62.0)
        ring1.AddPoint(13.0, 62.0)
        ring1.AddPoint(13.0, 63.0)
        ring1.AddPoint(12.0, 63.0)

        # Create polygon #1
        poly1 = ogr.Geometry(ogr.wkbPolygon)
        poly1.AddGeometry(ring1)
        multipolygon.AddGeometry(poly1)

        # Create ring #2
        ring2 = ogr.Geometry(ogr.wkbLinearRing)
        ring2.AddPoint(11.0, 64.0)
        ring2.AddPoint(11.0, 62.0)
        ring2.AddPoint(12.5, 62.0)
        ring2.AddPoint(12.5, 64.0)
        ring2.AddPoint(11.0, 64.0)

        # Create polygon #2
        poly2 = ogr.Geometry(ogr.wkbPolygon)
        poly2.AddGeometry(ring2)
        multipolygon.AddGeometry(poly2)

        query = SpatialQuery(spatial=multipolygon, bounding_box=None)
        assert (
            query.coordinates
            == "11.0000,62.0000,0.0000,13.0000,62.0000,0.0000,13.0000,63.0000,0.0000,12.5000,64.0000,0.0000,11.0000,64.0000,0.0000,11.0000,62.0000,0.0000"
        )
        assert query.geom_type == "polygon"

    @pytest.mark.skipif("shapely" not in sys.modules, reason=NEED_SHAPELY)
    def test_can_parse_bbox_from_shapely_box(self):
        bbox = shapely.geometry.box(2, 30, 5, 33)
        assert isinstance(bbox, shapely.geometry.base.BaseGeometry)

        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "2.0,30.0,5.0,33.0"
        assert query.geom_type == "bounding_box"

    @pytest.mark.skipif("shapely" not in sys.modules, reason=NEED_SHAPELY)
    def test_can_parse_bbox_from_shapely_wkt(self):
        bbox = shapely.wkt.loads("POLYGON ((5 30, 5 33, 2 33, 2 30, 5 30))")
        assert isinstance(bbox, shapely.geometry.base.BaseGeometry)

        query = SpatialQuery(spatial=None, bounding_box=bbox)
        assert query.coordinates == "2.0,30.0,5.0,33.0"
        assert query.geom_type == "bounding_box"

    @pytest.mark.skipif("shapely" not in sys.modules, reason=NEED_SHAPELY)
    def test_can_parse_spatial_from_shapely_wkt(self):
        spatial = shapely.wkt.loads("POLYGON ((5 30, 5 33, 2 33, 2 30, 5 30))")
        assert isinstance(spatial, shapely.geometry.base.BaseGeometry)

        query = SpatialQuery(spatial=spatial, bounding_box=None)
        assert (
            query.coordinates
            == "5.0000,30.0000,5.0000,33.0000,2.0000,33.0000,2.0000,30.0000,5.0000,30.0000"
        )
        assert query.geom_type == "polygon"
