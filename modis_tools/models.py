"""Return classes from API requests."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import field_validator, AnyUrl, BaseModel, HttpUrl


# Shared structure
class ApiLink(BaseModel):
    rel: HttpUrl
    hreflang: str
    href: AnyUrl
    type: Optional[str] = None

    @property
    def rel(self, val: str) -> str:
        """Remove trailing hashes before validating."""
        return val.rstrip("#")

    @field_validator("href", mode="before")
    @classmethod
    def convert_spaces(cls, v: AnyUrl) -> str:
        """Spaces in links are problematic; this validator encodes them."""
        return v.replace(" ", "%20")


class ApiEntry(BaseModel):
    """Shared core fields for API entries."""

    id: str
    title: str
    dataset_id: str
    coordinate_system: str
    time_start: str
    updated: Optional[datetime] = None
    links: List[Any]


class ApiEntryExtended(ApiEntry):
    """
    Extends base ApiEntry to include all information returned for entries from
    the MODIS API
    """

    browse_flag: bool
    data_center: str
    online_access_flag: bool
    original_format: str


class ApiFeed(BaseModel):
    # id: HttpUrl - probably not useful and raises error for very long queries
    updated: datetime
    title: str
    entry: List[Any]


# Resource links
class CollectionLink(ApiLink):
    pass


class GranuleLink(ApiLink):
    inherited: Optional[bool] = None
    type: Optional[str] = None


# Resource entries
class Collection(ApiEntry):
    """Core fields for collections."""

    processing_level_id: str
    short_name: str
    summary: str
    version_id: str
    links: List[CollectionLink]


class CollectionExtended(ApiEntryExtended, Collection):
    """
    Extends base Collection to include all information returned for collections from
    the MODIS API.
    """

    archive_center: str
    boxes: List[str]
    has_formats: bool
    has_spatial_subsetting: bool
    has_temporal_subsetting: bool
    has_transforms: bool
    has_variables: bool
    orbit_parameters: Dict[Any, Any]
    organizations: List[str]


class Granule(ApiEntry):
    """Core fields for granules."""

    cloud_cover: Optional[str] = None
    collection_concept_id: str
    day_night_flag: Optional[str] = None
    granule_size: Optional[float] = None
    polygons: Optional[List[Any]] = None
    producer_granule_id: Optional[str] = None
    time_end: datetime
    links: List[GranuleLink]


class GranuleExtended(ApiEntryExtended, Granule):
    """
    Extends base Collection to include all information returned for granules from
    the MODIS API.
    """

    pass


# Resource feeds
class CollectionFeed(ApiFeed):
    entry: List[Collection]


class GranuleFeed(ApiFeed):
    entry: List[Granule]
