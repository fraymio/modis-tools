from typing import Any, Iterable, List, Optional, Literal, Type, TypeVar, Union
from pathlib import Path
from multiprocessing import Pool, cpu_count

from pydantic.networks import HttpUrl
from urllib.parse import urlsplit
from requests.models import Response
from requests.sessions import Session

from modis_tools.auth import ModisSession, has_download_cookies
from modis_tools.models import Granule
from modis_tools.constants.urls import URLs

ParamType = Literal["xml", "hdf"]
T = TypeVar("T")


class GranuleHandler:
    @classmethod
    def download_from_granules(
        cls,
        one_or_many_granules: Union[Iterable[Granule], Granule],
        modis_session: ModisSession,
        threads: int = 1,
        path: Optional[str] = None,
        force: bool = False,
    ) -> List[Path]:
        """Download the corresponding raster file for each item in `granules`

        Args:
            one_or_many_granules (Iterator[Granule]): Either a single `Granule`
                object, or Several `Granule` objects as an `Iterable` that have
                a `.link` property
            modis_session (ModisSession): A logged in `ModisSession` object
            threads (int, optional): Specify how many concurrent processes or
                threads should be used while downloading. s an integer,
                specifying the maximum number of concurrently running workers.
                If 1 is given, no joblib parallelism is used at all, which is
                useful for debugging. If set to -1, all CPUs are used. For
                `threads` below -1, (n_cpus + 1 + n_jobs) are used. For example
                with `threads=-2`, all CPUs but one are used.
            path (Optional[str], optional): The directory to save the file. If set
                None, defaults to current directory.
            force (bool, optional): download file regardless if it exists and
                matches remote content size. Defaults to False.

        Returns:
            List[str]: Path to the newly downloaded file(s)
        """
        granules = cls._coerce_to_list(one_or_many_granules, Granule)
        urls = [cls.get_url_from_granule(x, "hdf") for x in granules]
        if threads in (None, 0, 1):
            return cls.download_from_urls(
                urls, modis_session=modis_session, path=path, force=force
            )
        n_threads = threads if threads > 1 else cpu_count() + 1 + threads
        with Pool(processes=n_threads) as p:
            result = p.starmap(
                cls.download_from_urls, ((u, modis_session, path, force) for u in urls)
            )
        # Flatten return value since `result` is a list of lists
        return [item for sublist in result for item in sublist]

    @staticmethod
    def _coerce_to_list(
        possible_list: Union[Iterable[Any], Any], obj_type: Type[T]
    ) -> Iterable[T]:
        """Cast possible single object into list

        Args:
            possible_list (Union[Iterable[Any], Any]): Variable to be converted to a list
            obj_type (Type): The type of the item within the returned list.
                Even though `obj_type` isn't used in implementation, it's key in
                determining return type
        """
        if isinstance(possible_list, obj_type):
            possible_list = [possible_list]
        return possible_list

    @staticmethod
    def get_url_from_granule(granule: Granule, ext: ParamType = "hdf") -> HttpUrl:
        """Return link for file extension from Earthdata resource."""
        for link in granule.links:
            if link.href.host == URLs.RESOURCE.value and link.href.path.endswith(ext):
                return link.href
        raise Exception("No matching link found")

    @classmethod
    def download_from_urls(
        cls,
        one_or_many_urls: Union[Iterable[HttpUrl], HttpUrl],
        modis_session: ModisSession,
        path: Optional[str] = None,
        force: bool = False,
    ) -> List[Path]:
        """Save file locally using remote name.

        :param path directory to save file, defaults to current directory
        :type str or Path

        :param force download file regardless if it exists and matches remote
            content size
        :type bool, default False

        :returns Path to the newly downloaded file
        :rtype List[Path]
        """
        urls = cls._coerce_to_list(one_or_many_urls, HttpUrl)
        file_paths = []
        for url in urls:
            req = cls._get(url, modis_session.session)
            file_path = Path(path or "") / Path(url).name
            content_size = int(req.headers.get("Content-Length", -1))
            if (
                force
                or not file_path.exists()
                or file_path.stat().st_size != content_size
            ):
                with open(file_path, "wb") as handle:
                    for chunk in req.iter_content(chunk_size=2 ** 20):
                        handle.write(chunk)
            file_paths.append(file_path)
        return file_paths

    @classmethod
    def _get(
        cls, url: HttpUrl, session: Session, stream: Optional[bool] = True
    ) -> Response:
        """
        Get request for MODIS file url. Raise an error if no file content.

        :param stream return content as chunked stream of data
        :type bool

        :rtype request
        """
        if not has_download_cookies(session):
            location = cls._get_location(url, session)
        else:
            location = url
        req = session.get(location, stream=stream)
        content_size = int(req.headers.get("Content-Length", -1))
        if content_size <= 1:
            raise FileNotFoundError("No file content found")
        return req

    @staticmethod
    def _get_location(url: HttpUrl, session: Session) -> str:
        """Make initial request to fetch file location from header."""
        split_result = urlsplit(url)
        https_url = split_result._replace(scheme="https").geturl()
        location_resp = session.get(https_url, allow_redirects=False)
        location = location_resp.headers.get("Location")
        if not location:
            raise FileNotFoundError("No file location found")
        return location
