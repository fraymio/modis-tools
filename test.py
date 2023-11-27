from modis_tools.auth import ModisSession
from modis_tools.granule_handler import GranuleHandler
from modis_tools.resources import CollectionApi, GranuleApi

username = ""  # Update this line
password = ""  # Update this line

# Authenticate a session
session = ModisSession(username=username, password=password)

collection_client = CollectionApi(session=session)
# This one is broken
collections = collection_client.query(short_name="MODISA_L3b_CHL", version="R2022.0")
# This one should work
# collections = collection_client.query(short_name="MOD11A1", version="061")

granule_client = GranuleApi.from_collection(collections[0], session=session)

india_bbox = [55.00, 5.00, 105.00, 45.00]
india_granules = granule_client.query(
    start_date="2020-01-01", end_date="2020-02-01", bounding_box=india_bbox
)

GranuleHandler.download_from_granules(
    india_granules, session, ext=("hdf", "h5", "nc", "xml")
)
