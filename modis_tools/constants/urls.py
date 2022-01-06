""" URLs for the API """
from enum import Enum


class URLs(Enum):
    """ URLs """

    API: str = "cmr.earthdata.nasa.gov"
    URS: str = "urs.earthdata.nasa.gov"
    RESOURCE: str = "e4ftl01.cr.usgs.gov"
    EARTHDATA: str = ".earthdata.nasa.gov"
