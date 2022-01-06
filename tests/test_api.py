from functools import partial

from requests.sessions import Session
import pytest

from modis_tools.api import ModisApi
from modis_tools.auth import ModisSession
from modis_tools.constants.urls import URLs

URL = URLs.API.value


class TestModisApi:
    def test_can_init_with_username_and_password(self):
        api = ModisApi(username="", password="")
        assert isinstance(api.session, Session)

    def test_can_init_with_session(self):
        api = ModisApi(session=ModisSession("", ""))
        assert isinstance(api.session, Session)

    def test_mime_type_defaults_to_json(self):
        api = ModisApi(session=ModisSession("", ""))
        assert api.mime_type == "json"

    def test_url_derives_from_resource(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        assert api.resource_url == f"https://{URL}/search/test"

    def test_changes_in_resource_also_update_url(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        assert api.resource_url == f"https://{URL}/search/test"
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "new_test"
        assert api.resource_url == f"https://{URL}/search/new_test"

    def test_bad_mime_type_raises_exception(self):
        api = ModisApi(session=ModisSession("", ""))
        with pytest.raises(Exception):
            api.mime_type = "bad_type"

    def test_get_is_a_partial_method(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        get = api.get

        assert callable(get)
        assert isinstance(get, partial)
        assert get.keywords["url"] == f"https://{URL}/search/test"

    def test_post_is_a_partial_method(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        post = api.post

        assert callable(post)
        assert isinstance(post, partial)
        assert post.keywords["url"] == f"https://{URL}/search/test"

    def test_get_is_a_delegate_of_session_dot_get(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        get = api.get
        assert get.func == api.session.get

    def test_post_is_a_delegate_of_session_dot_post(self):
        api = ModisApi(session=ModisSession("", ""))
        api.resource = "test"
        post = api.post
        assert post.func == api.session.post
