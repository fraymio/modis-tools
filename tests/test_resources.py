from modis_tools.resources import CollectionApi
from modis_tools.api import ModisApi


class TestCollectionApi:
    def test_foo_bar(self):
        assert issubclass(CollectionApi, ModisApi)
