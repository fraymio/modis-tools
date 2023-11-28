""" URLs for the API """
from enum import Enum


class URLs(Enum):
    """URLs"""

    API: str = "cmr.earthdata.nasa.gov"
    URS: str = "urs.earthdata.nasa.gov"
    RESOURCE: str = "e4ftl01.cr.usgs.gov"
    MOD11A2_V061_RESOURCE: str = "data.lpdaac.earthdatacloud.nasa.gov"
    NSIDC_RESOURCE: str = "n5eil01u.ecs.nsidc.org"
    EARTHDATA: str = ".earthdata.nasa.gov"
    LAADS_RESOURCE: str = "ladsweb.modaps.eosdis.nasa.gov"
    MODISA_L3b_CHL_V061_RESOURCE: str = "oceancolor.gsfc.nasa.gov"
    MODISA_L3b_CHL_V061_RESOURCE_SCI: str = "oceandata.sci.gsfc.nasa.gov"
