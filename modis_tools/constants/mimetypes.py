from enum import Enum


class MimeTypes(Enum):
    html = "text/html"
    json = "application/json"
    xml = "application/xml"
    echo10 = "application/echo10+xml"
    iso = "application/iso19115+xml"
    iso19115 = "application/iso19115+xml"
    dif = "application/dif+xml"
    dif10 = "application/dif10+xml"
    csv = "text/csv"
    atom = "application/atom+xml"
    opendata = "application/opendata+json"
    kml = "application/vnd.google-earth.kml+xml"
    native = "application/metadata+xml"
    umm_json = "application/vnd.nasa.cmr.umm_results+json"
