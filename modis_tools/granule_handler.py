from multiprocessing import cpu_count
from pathlib import Path
from typing import Any, Iterable, List, Literal, Optional, Tuple, Type, TypeVar, Union
from urllib.parse import urlsplit

from pydantic.networks import AnyUrl, HttpUrl
from requests.auth import HTTPProxyAuth
from requests.models import Response
from requests.sessions import Session
from tqdm import tqdm
from tqdm.contrib.concurrent import process_map

from modis_tools.auth import ModisSession, has_download_cookies
from modis_tools.constants.urls import URLs
from modis_tools.models import Granule

T = TypeVar("T")


class GranuleHandler:
    @classmethod
    def download_from_granules(
        cls,
        one_or_many_granules: Union[Iterable[Granule], Granule],
        modis_session: ModisSession,
        ext: Union[str, Tuple] = ("hdf", "h5", "nc", "xml"),
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
            ext (Union[str, Tuple]): Specify the permitted file extensions. If nothing is passed
                defaults to all of ("hdf", "h5", "nc", "xml").
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
        urls = [cls.get_url_from_granule(x, ext) for x in granules]
        if threads in (None, 0, 1):
            return cls.download_from_urls(
                urls, modis_session=modis_session, path=path, force=force, disable=False
            )
        n_threads = threads if threads > 1 else cpu_count() + 1 + threads
        result = process_map(
            cls.wrapper_download_from_urls,
            ((u, modis_session, path, force) for u in urls),
            max_workers=n_threads,
            total=len(urls),
            desc="Downloading",
            position=0,
            unit="file",
        )
        if isinstance(result[0], list):
            result = [item for sublist in result for item in sublist]
        return result

    @classmethod
    def wrapper_download_from_urls(cls, args: Iterable[Any]) -> List[Path]:
        """wrapper to unpack arguments for `download_from_urls`

        Args:
            args (Iterable[Any]): Iterator to unpack
        """
        return cls.download_from_urls(*args)

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
    def get_url_from_granule(granule: Granule, ext: Union[str, Tuple]) -> HttpUrl:
        """Return link for file extension from Earthdata resource."""
        for link in granule.links:
            if link.href.host in [
                URLs.RESOURCE.value,
                URLs.NSIDC_RESOURCE.value,
                URLs.MOD11A2_V061_RESOURCE.value,
                URLs.LAADS_RESOURCE.value,
                URLs.MODISA_L3b_CHL_V061_RESOURCE.value,
                URLs.MODISA_L3b_CHL_V061_RESOURCE_SCI.value,
            ] and link.href.path.endswith(ext):
                return link.href
        raise Exception("No matching link found")

    @classmethod
    def download_from_urls(
        cls,
        one_or_many_urls: Union[Iterable[HttpUrl], HttpUrl],
        modis_session: ModisSession,
        path: Optional[str] = None,
        force: bool = False,
        disable: bool = True,
    ) -> List[Path]:
        """Save file locally using remote name.

        :param path directory to save file, defaults to current directory
        :type str or Path

        :param force download file regardless if it exists and matches remote
            content size
        :type bool, default False

        :param disable tqdm progress bar. Disable if using multiprocessing
        :type bool, default True

        :returns Path to the newly downloaded file
        :rtype List[Path]
        """
        urls = cls._coerce_to_list(one_or_many_urls, AnyUrl)
        file_paths = []
        for url in tqdm(urls, disable=disable, desc="Downloading", unit="file"):
            req = cls._get(url, modis_session)
            file_path = Path(path or "") / Path(url).name
            content_size = int(req.headers.get("Content-Length", -1))
            if (
                force
                or not file_path.exists()
                or file_path.stat().st_size != content_size
            ):
                with open(file_path, "wb") as handle:
                    for chunk in req.iter_content(chunk_size=2**20):
                        handle.write(chunk)
            file_paths.append(file_path)
        return file_paths

    @classmethod
    def _get(
        cls,
        url: HttpUrl,
        modis_session: ModisSession,
        stream: Optional[bool] = True,
    ) -> Response:
        """
        Get request for MODIS file url. Raise an error if no file content.

        :param stream return content as chunked stream of data
        :type bool

        :rtype request
        """
        session = modis_session.session
        if not has_download_cookies(session):
            location = cls._get_location(url, modis_session)
        else:
            location = url
        req = session.get(location, stream=stream)
        content_size = int(req.headers.get("Content-Length", -1))
        if content_size <= 1:
            raise FileNotFoundError("No file content found")
        return req

    @staticmethod
    def _get_location(url: HttpUrl, modis_session: ModisSession) -> str:
        """Make initial request to fetch file location from header."""
        session = modis_session.session
        split_result = urlsplit(url)
        https_url = split_result._replace(scheme="https").geturl()
        if url.host == URLs.LAADS_RESOURCE.value:
            location_resp = session.get(https_url, allow_redirects=True)
            location = location_resp.url  # ends up being the same as https_url
        elif url.host == URLs.MODISA_L3b_CHL_V061_RESOURCE_SCI.value:
            location_resp = session.get(https_url, allow_redirects=True)
            # go to last re-direct location
            location = location_resp.history[-1].headers.get("Location")
        else:
            location_resp = session.get(https_url, allow_redirects=False)
            if location_resp.status_code == 401:
                # try using ProxyAuth if BasicAuth returns 401 (unauthorized)
                location_resp = session.get(
                    https_url,
                    allow_redirects=False,
                    auth=HTTPProxyAuth(modis_session.username, modis_session.password),
                )
            location = location_resp.headers.get("Location")
        if not location:
            raise FileNotFoundError("No file location found")
        return location
