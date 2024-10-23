""" Classes to use MODIS API to download satellite data. """
import json
from typing import Any, Iterator, List, Optional

from .api import ModisApi, Sessions
from .decorators import params_args
from .models import Collection, CollectionFeed, Granule, GranuleFeed
from .request_helpers import DateParams, SpatialQuery

class CollectionApi(ModisApi):
    """API for MODIS's 'collections' resource"""

    resource: str = "collections"

    def __init__(
        self,
        session: Optional[Sessions] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__(session=session, username=username, password=password)

    def query(self, **kwargs) -> List[Collection]:
        resp = self.no_auth.get(params=kwargs)
        try:
            collection_feed = CollectionFeed(**resp.json()["feed"])
        except (json.JSONDecodeError, KeyError, IndexError) as err:
            raise Exception("Error in querying collections") from err
        return collection_feed.entry


DEFAULT_GRANULE_PARAMS = {
    "downloadable": "true",
    "page_size": 2000,
    "sort_key": "-start_date",
}


class GranuleApi(ModisApi):
    """API for MODIS's 'granules' resource"""

    resource: str = "granules"
    params: dict = DEFAULT_GRANULE_PARAMS.copy()

    def __init__(
        self,
        session: Optional[Sessions] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        super().__init__(session=session, username=username, password=password)

    @classmethod
    def from_collection(
        cls, collection: Collection, session: Optional[Sessions] = None
    ) -> "GranuleApi":
        """Create granule client from Collection using concept_id."""
        granule = cls(session=session)
        granule.params["concept_id"] = collection.id
        return granule

    @params_args(DateParams, SpatialQuery)
    def query(
        self,
        start_date: Any = None,
        end_date: Any = None,
        time_delta: Any = None,
        spatial: Any = None,
        bounding_box: Any = None,
        limit: Optional[int] = None,
        **kwargs,
    ) -> Iterator[Granule]:
        """Query granules. Yields a generator of matching granules
        Default parameters can be overridden:
            downloadable: true
            page_size: 2000

        :param start_date start od date query
        :type Any will attempt to parse to datetime

        :param end_date end of date query
        :type Any will attempt to parse to datetime

        :param time_delta time difference, if one of start or end are defined
        :type Any will attempt to parse to timedelta

        :param spatial spatial intersection query with granules. Will parse
            ogr.Geometry's, shapely objects, GeoJSON features/geometries.
            Geometries must be in longitude, latitude
        :type Any will attempt to parse to coordinate string

        :param bbox spatial query using bounding box. Will parse ogr.Geometry's,
            shapely objects, GeoJSON features/geometries, or list of coordinates
            in the format (xmin, ymin, xmax, ymax). Geometries must be in longitude,
            latitude
        :type Any

        :param limit maximum number of results to return. If None, all results are
            returned
        :type int

        :param kwargs any additional arguments will be passed as query params. For
            additional options see:
                https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html

        :rtype generator of granules
        """
        params = kwargs.pop("params", {})
        params = {**(self.params or {}), **kwargs, **params}
        yielded = 0
        while not limit or yielded < limit:
            try:
                resp = self.no_auth.get(params=params, auth=None)
                feed = resp.json()["feed"]
                granule_feed = GranuleFeed(**feed)
            except (json.JSONDecodeError, KeyError, IndexError) as err:
                raise Exception(f"{resp},{resp.json()}") from err
            granules = granule_feed.entry
            if limit:
                granules = granules[: limit - yielded]
            for granule in granules:
                yield granule
            yielded += len(granules)

            # Empty "CMR-Search-After" means the end of the query
            # https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#search-after
            if "CMR-Search-After" not in resp.headers:
                break
            self.session.headers["CMR-Search-After"] = resp.headers["CMR-Search-After"]
        self.session.headers.pop("CMR-Search-After", None)
