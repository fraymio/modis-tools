import pytest

from datetime import datetime, timedelta

from modis_tools.auth import ModisSession, has_download_cookies


class TestModisSession:
    def test_creates_session(self):

        modis = ModisSession("test user", "test password")
        assert modis.session

    def test_no_credentials_raises_exception(self):

        expected = Exception

        with pytest.raises(expected):
            modis = ModisSession()


class TestDownloadCookies:
    @pytest.fixture()
    def session_with_cookies(self):

        modis = ModisSession("test user", "test password")

        time = datetime.now() + timedelta(hours=9)

        modis.session.cookies.set(
            "urs_user_already_logged",
            value="yes",
            domain=".earthdata.nasa.gov",
            expires=datetime.timestamp(time),
        )
        modis.session.cookies.set(
            "DATA", value="fake value,", domain="e4ftl01.cr.usgs.gov"
        )
        modis.session.cookies.set(
            "_urs-gui_session",
            value="fake value",
            domain="urs.earthdata.nasa.gov",
            expires=datetime.timestamp(time),
        )

        return modis.session

    def test_no_cookies_returns_false(self):

        modis = ModisSession("test user", "test password")

        expected = False

        assert has_download_cookies(modis.session) == expected

    def test_correct_cookies_return_true(self, session_with_cookies):

        expected = True

        assert has_download_cookies(session_with_cookies) == expected

    def test_expired_first_cookie_return_false(self, session_with_cookies):

        time = datetime.now() + timedelta(hours=-9)

        session_with_cookies.cookies.set(
            "urs_user_already_logged",
            value="yes",
            domain=".earthdata.nasa.gov",
            expires=datetime.timestamp(time),
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected

    def test_expired_gui_cookie_return_false(self, session_with_cookies):

        time = datetime.now() + timedelta(hours=-9)

        session_with_cookies.cookies.set(
            "_urs-gui_session",
            value="fake value",
            domain="urs.earthdata.nasa.gov",
            expires=datetime.timestamp(time),
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected

    def test_incorrect_earthdata_domain_return_false(self, session_with_cookies):

        time = datetime.now() + timedelta(hours=9)

        session_with_cookies.cookies.set(
            "urs_user_already_logged",
            value="yes",
            domain="wrong.url",
            expires=datetime.timestamp(time),
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected

    def test_logged_in_value_no_returns_false(self, session_with_cookies):

        time = datetime.now() + timedelta(hours=9)

        session_with_cookies.cookies.set(
            "urs_user_already_logged",
            value="no",
            domain=".earthdata.nasa.gov",
            expires=datetime.timestamp(time),
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected

    def test_incorrect_data_domain_returns_false(self, session_with_cookies):

        session_with_cookies.cookies.set(
            "DATA", value="fake value,", domain="wrong.url"
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected

    def test_incorrect_gui_domain_returns_false(self, session_with_cookies):

        time = datetime.now() + timedelta(hours=9)

        session_with_cookies.cookies.set(
            "_urs-gui_session",
            value="fake value",
            domain="wrong.url",
            expires=datetime.timestamp(time),
        )

        expected = False

        assert has_download_cookies(session_with_cookies) == expected
