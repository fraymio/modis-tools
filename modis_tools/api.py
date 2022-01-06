""" Base API to use with MODIS. """

import copy
from functools import partial
from typing import Callable, Optional, Union
from requests.models import Response

from requests.sessions import Session

from .auth import ModisSession
from .constants.mimetypes import MimeTypes
from .constants.urls import URLs

Sessions = Union[ModisSession, Session]


class ModisApi:
    """General class for MODIS CMR API

    Parameters set on the object are included in all requests, and
    overridden by those specificed in function call
    """

    resource: str
    params: Optional[dict] = None
    _mime_type: str = "json"

    def __init__(
        self,
        session: Optional[Sessions] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
    ):
        if isinstance(session, ModisSession):
            self.session = session.session
        elif isinstance(session, Session):
            if session.auth is not None:
                self.session = session
        else:
            modis_session = ModisSession(username=username, password=password)
            self.session = modis_session.session
        self.session.headers["Accept"] = MimeTypes[self._mime_type].value

    @property
    def resource_url(self) -> str:
        """Resource URL."""
        return "/".join(["https:/", URLs.API.value, "search", self.resource])

    @property
    def get(self) -> Callable[..., Response]:
        """Handle get requests."""
        return partial(self.session.get, url=self.resource_url)

    @property
    def post(self) -> Callable[..., Response]:
        """Handle post requests."""
        return partial(self.session.post, url=self.resource_url)

    @property
    def mime_type(self) -> str:
        """Mime type for data returned from API."""
        return self._mime_type

    @mime_type.setter
    def mime_type(self, mime_type):
        """Validate the availaility of mime type before setting"""
        try:
            self.session.headers["Accept"] = MimeTypes[mime_type].value
            self._mime_type = mime_type
        except KeyError:
            raise Exception("Invalid mimetype")

    @property
    def no_auth(self):
        """Create a copy of the current ModisAPI without auth. Needed for some CMR
        resources.
        """
        no_auth_session = copy.deepcopy(self)
        no_auth_session.session.auth = None
        return no_auth_session
