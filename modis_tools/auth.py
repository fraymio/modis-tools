""" Modis authentication functions. """

from typing import Optional, Union

from datetime import datetime
from netrc import netrc
from pathlib import Path
import stat

from requests import sessions
from requests.auth import HTTPBasicAuth

from .constants.urls import URLs


class ModisSession:
    """Auth session for querying and downloading MODIS data."""

    session: sessions.Session

    def __init__(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth: Optional[HTTPBasicAuth] = None,
    ):
        self.username = username
        self.password = password
        self.session = sessions.Session()
        if auth:
            self.session.auth = auth
        elif username is not None and password is not None:
            self.session.auth = HTTPBasicAuth(username, password)
        else:
            try:
                username, _, password = netrc().authenticators(URLs.URS.value)
            except FileNotFoundError:
                raise Exception(
                    "Unable to create authenticated session. Likely that username and password not found"
                )

            self.session.auth = HTTPBasicAuth(username, password)

    def __enter__(self):
        return self.session

    def __exit__(self, exc_type, exc_value, exc_traceback):
        self.session.close()


def has_download_cookies(session):
    """Check if session has valid cookies for CMR API using assertions."""
    cookies = {cookie.name: cookie for cookie in session.cookies}
    try:
        logged_in = cookies["urs_user_already_logged"]
        assert logged_in.domain == URLs.EARTHDATA.value
        assert datetime.fromtimestamp(logged_in.expires) > datetime.now()
        assert logged_in.value == "yes"
        if "DATA" in cookies:
            # specific to the cookies for LP DAAC source
            data = cookies["DATA"]
            assert data.domain == URLs.RESOURCE.value
        elif "CIsForCookie_OPS" in cookies:
            data = cookies["CIsForCookie_OPS"]
            # specific to the cookies for NSIDC DAAC source
            assert data.domain == URLs.NSIDC_RESOURCE.value
        else:
            raise KeyError("Data source not recognized. Please open an issue informing us of the desired data source.")

        gui = cookies["_urs-gui_session"]
        assert gui.domain == URLs.URS.value
        assert datetime.fromtimestamp(gui.expires) > datetime.now()

        return True
    except (KeyError, AssertionError) as err:
        return False


def _write_netrc(file: Union[str, Path], permissions: dict):
    with open(file, "w") as handle:
        for host, (un, _, pw) in permissions.items():
            domain = "default" if host == "default" else f"machine {host}"
            handle.write(f"{domain}\nlogin {un}\npassword {pw}\n")


def add_earthdata_netrc(username: str, password: str, update: bool = True):
    """Write Modis permissions to netrc file.

    :param username Earthdata account username
    :type str

    :param password Earthdata account password
    :type str

    :param update whether to update if Earthdata entry already exists in netrc
    :type bool, default True
    """
    netrc_file = Path.home() / ".netrc"
    permissions = {}
    if netrc_file.exists():
        existing = netrc().hosts
        if URLs.URS.value in existing and not update:
            return
        permissions = existing
    permissions[URLs.URS.value] = (username, None, password)
    _write_netrc(netrc_file, permissions)

    owner_read_write = stat.S_IFREG | stat.S_IRUSR | stat.S_IWUSR
    netrc_file.chmod(owner_read_write)  # Limit permissions to owner


def remove_earthdata_netrc():
    """
    Remove the netrc entry for Earthdata, if it exists.
    """
    netrc_file = Path.home() / ".netrc"
    if not netrc_file.exists():
        return
    existing = netrc().hosts
    existing.pop(URLs.URS.value, None)
    if not existing:
        netrc_file.unlink()
    else:
        _write_netrc(netrc_file, existing)
