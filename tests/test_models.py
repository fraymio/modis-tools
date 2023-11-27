import pytest

from modis_tools.models import CollectionFeed, ApiLink


class TestApiLink:
    @pytest.fixture
    def link_with_space(self) -> dict:
        return {
            "inherited": True,
            "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
            "hreflang": "en-US",
            "href": "https://oceandata.sci.gsfc.nasa.gov/directdataaccess/Level-3 Binned/Aqua-MODIS/",
        }

    def test_space_is_removed_from_link(self, link_with_space: dict):
        validated = ApiLink(**link_with_space)
        assert isinstance(validated.href.path, str)
        assert " " not in validated.href.path
        assert "%20" in validated.href.path


class TestCollectionFeed:

    @pytest.fixture
    def example_json_response(self) -> dict:
        """
        This is a response from a query with the CollectionApi class. See the
        `NOTE` below indicating a problematic link. In this test class, we
        use this example response to ensure that we can handle spaces in links.
        """
        return (
            {
                "feed": {
                    "entry": [
                        {
                            "archive_center": "NASA/GSFC/SED/ESD/GCDC/OB.DAAC",
                            "boxes": ["-90 -180 90 180"],
                            "browse_flag": False,
                            "cloud_hosted": False,
                            "collection_data_type": "SCIENCE_QUALITY",
                            "consortiums": ["GEOSS", "EOSDIS"],
                            "coordinate_system": "CARTESIAN",
                            "data_center": "OB_DAAC",
                            "dataset_id": "Aqua MODIS Global Binned Chlorophyll (CHL) "
                            "Data, version R2022.0",
                            "has_formats": False,
                            "has_spatial_subsetting": False,
                            "has_temporal_subsetting": False,
                            "has_transforms": False,
                            "has_variables": False,
                            "id": "C2330511478-OB_DAAC",
                            "links": [
                                {
                                    # NOTE the space in the href is problematic
                                    "href": "https://oceandata.sci.gsfc.nasa.gov/directdataaccess/Level-3 "
                                    "Binned/Aqua-MODIS/",
                                    "hreflang": "en-US",
                                    "rel": "http://esipfed.org/ns/fedsearch/1.1/data#",
                                },
                                {
                                    "href": "https://oceancolor.gsfc.nasa.gov/atbd/",
                                    "hreflang": "en-US",
                                    "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                                },
                                {
                                    "href": "https://oceancolor.gsfc.nasa.gov/reprocessing/",
                                    "hreflang": "en-US",
                                    "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                                },
                                {
                                    "href": "https://oceancolor.gsfc.nasa.gov/citations/",
                                    "hreflang": "en-US",
                                    "rel": "http://esipfed.org/ns/fedsearch/1.1/documentation#",
                                },
                                {
                                    "href": "https://oceancolor.gsfc.nasa.gov/data/10.5067/AQUA/MODIS/L3B/CHL/2022",
                                    "hreflang": "en-US",
                                    "rel": "http://esipfed.org/ns/fedsearch/1.1/metadata#",
                                },
                            ],
                            "online_access_flag": True,
                            "orbit_parameters": {},
                            "organizations": ["NASA/GSFC/SED/ESD/GCDC/OB.DAAC", "OBPG"],
                            "original_format": "UMM_JSON",
                            "platforms": ["Aqua"],
                            "processing_level_id": "3",
                            "service_features": {
                                "esi": {
                                    "has_formats": False,
                                    "has_spatial_subsetting": False,
                                    "has_temporal_subsetting": False,
                                    "has_transforms": False,
                                    "has_variables": False,
                                },
                                "harmony": {
                                    "has_formats": False,
                                    "has_spatial_subsetting": False,
                                    "has_temporal_subsetting": False,
                                    "has_transforms": False,
                                    "has_variables": False,
                                },
                                "opendap": {
                                    "has_formats": False,
                                    "has_spatial_subsetting": False,
                                    "has_temporal_subsetting": False,
                                    "has_transforms": False,
                                    "has_variables": False,
                                },
                            },
                            "short_name": "MODISA_L3b_CHL",
                            "summary": "MODIS (or Moderate-Resolution Imaging "
                            "Spectroradiometer) is a key instrument aboard "
                            "the Terra (EOS AM) and Aqua (EOS PM) "
                            "satellites. Terra's orbit around the Earth is "
                            "timed so that it passes from north to south "
                            "across the equator in the morning, while Aqua "
                            "passes south to north over the equator in the "
                            "afternoon. Terra MODIS and Aqua MODIS are "
                            "viewing the entire Earth's surface every 1 to "
                            "2 days, acquiring data in 36 spectral bands, "
                            "or groups of wavelengths (see MODIS Technical "
                            "Specifications). These data will improve our "
                            "understanding of global dynamics and "
                            "processes occurring on the land, in the "
                            "oceans, and in the lower atmosphere. MODIS is "
                            "playing a vital role in the development of "
                            "validated, global, interactive Earth system "
                            "models able to predict global change "
                            "accurately enough to assist policy makers in "
                            "making sound decisions concerning the "
                            "protection of our environment.",
                            "time_start": "2002-07-04T00:00:00.000Z",
                            "title": "Aqua MODIS Global Binned Chlorophyll (CHL) "
                            "Data, version R2022.0",
                            "updated": "2019-10-01T00:00:00.000Z",
                            "version_id": "R2022.0",
                        }
                    ],
                    "id": "https://cmr.earthdata.nasa.gov:443/search/collections.json?short_name=MODISA_L3b_CHL&version=R2022.0",
                    "title": "ECHO dataset metadata",
                    "updated": "2023-11-27T17:15:07.456Z",
                }
            }
        )

    def test_collection_feed_can_handle_links_with_spaces(
            self, example_json_response
    ):
        feed = example_json_response["feed"]
        CollectionFeed(**feed)
