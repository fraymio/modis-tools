# MODIS Tools

MODIS Tools is a Python library to easily (and quickly) download MODIS imagery from the NASA Earthdata platform.

NASA’s Earthdata portal organizes MODIS data into collections, products, and granules. MODIS Tools provides a series of classes to search MODIS collection metadata for products, select the tiles you want, and download granules from the results of those queries. All you need are Earthdata account credentials and the desired MODIS product’s short name and version. 

## Example

After adding your username and password, the snippet below will download MOD13A1 granules for Nigeria for 2016, 2017, and 2018 to the current directory.

```python
from modis_tools.auth import ModisSession
from modis_tools.resources import CollectionApi, GranuleApi
from modis_tools.granule_handler import GranuleHandler

username = ""  # Update this line
password = ""  # Update this line

# Authenticate a session
session = ModisSession(username=username, password=password)

# Query the MODIS catalog for collections
collection_client = CollectionApi(session=session)
collections = collection_client.query(short_name="MOD13A1", version="061")

# Query the selected collection for granules
granule_client = GranuleApi.from_collection(collections[0], session=session)

# Filter the selected granules via spatial and temporal parameters
nigeria_bbox = [2.1448863675, 4.002583177, 15.289420717, 14.275061098]
nigeria_granules = granule_client.query(start_date="2016-01-01", end_date="2018-12-31", bounding_box=nigeria_bbox)

# Download the granules
GranuleHandler.download_from_granules(nigeria_granules, session)
```

## Further Details and Options

### Authentication

With username and password:

```python
from modis_tools.auth import ModisSession
from modis_tools.resources import CollectionApi

username = ""
password = ""

# Reusable session
session = ModisSession(username=username, password=password)
collection_client = CollectionApi(session=session)
# - or -
collection_client = CollectionApi(username=username, password=password)
```

With session as context manager

```python
...
with ModisSession(username=username, password=password) as session:
    collection_client = CollectionApi(session=session)
    ...
```

Using a netrc file, you can create clients without authentication:

```python
from modis_tools.auth import add_earthdata_netrc, remove_earthdata_netrc

username = ""
password = ""
# Create an entry for Earthdata in the ~/.netrc file, only needs to be run once
add_earthdata_netrc(username, password)

...
# Now sessions can be created without passing username and password explicitly
session = ModisSession()
granule_client = GranuleApi()

# You can remove the credentials if necessary. It will only remove
# the Earthdata entry
remove_earthdata_netrc()
...
```

### Query Parameters

You can interact with the Earthdata Search API to browse collections and granules via the `CollectionApi` and `GranuleApi` classes respectively. Most query parameters for collections and granules listed in the [Earthdata documentation](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html) can be passed directly to either class's `query()` method. 

*Note: To specify a modifier for a parameter (eg. `parameter[option]`), you'll need to unpack it from a dictionary: `**{"parameter[option]": "value"}` rather than passing it directly as a keyword argument.*

*Note: Response models for both classes' `query()` methods can be found in `modis_tools/models.py`.*

```python
# Collections query returns a list of matching collections
collections = collection_client.query(short_name="MOD13A1", version="061")

# Create a GranuleApi from a Collection, the `concept_id` search parameter is set
# to the collection
granule_client = GranuleApi.from_collection(collections[0])
# Granules collection returns a generator with matching granules
granules = granule_client.query(start_date="2019-02-02", limit=50)
```

Some parameters will be preprocessed and formatted. You can also use the raw parameters shown in the Earthdata documentation, but you'll have to make sure the format is correct.

#### Time parameters

Time ranges can be defined by at least one of `start_date` and `end_date` that can be passed as `datetime.datetime` objects, or strings/dicts/tuples that can be parsed to `datetime` objects. `time_delta` can be a `datetime.timedelta` object or something that can be parsed to one.

```python
from datetime import datetime, timedelta

# Any of the following definitions work for both `start_date` and `end_date`
start_date = datetime(2017, 12, 31)
start_date = {"year": 2017, "month": 12, "day": 31}
start_date = "2017-12-31"
start_date = (2017, 12, 31)

# Any of the following definitions for time_delta will create a one year time range.
# Sign of time delta doesn't matter, it will be determined by whether start or end
# is provided
time_delta = timedelta(365)
time_delta = 365 # Days is the default unit for time_delta
time_delta = {"weeks": 52, "days": 1}

end_date = datetime(2018, 12, 31)

# With the above parameters, the following three will query the same time range
granules = granule_client.query(start_date=start_end, end_date=end_date)
granules = granule_client.query(time_delta=time_delta, start_date=start_date)
granules = granule_client.query(time_delta=time_delta, end_date=end_date)

# If only one of start or end is provided, the date query is open ended
granules = granule_client.query(start_date=start_end)
```

#### Spatial parameters

The `spatial` and `bounding_box` parameters for collections and granules will parse ogr `Geometry`s, shapely `geometry`s (used by geopandas), or
GeoJSONs features/geometries. Multipolygons and geometry collections are converted to convex hulls for simpler queries. All spatial queries should
be in `(longitude, latitude)` order.

If bounding box is a geometry object, the envelope will be calculated. As a list or tuple, bounding box should be in the order `(xmin, ymin, xmax, ymax)`.

```python
import geopandas as gpd

df = gpd.read_file("/Users/leith/Desktop/dhs_mwi.geojson")
geom = df.geometry[0]

malawi_granules = granule_client.query(start_date="2017-01-01", end_date="2018-12-31", spatial=geom)

...
from osgeo import ogr

ds = ogr.GetDriverByName("GeoJSON").Open("drc.geojson")
l = ds.GetLayer()
feat = l.GetNextFeature()

drc_granules = granule_client.query(start_date="2015-09-01", bounding_box=feat.geometry)
```

### Downloading

The return value of a query with the GranuleAPI is a generator. This avoids calling the MODIS API more than is immediately needed if more than one page of results is found. 

Iterating through a generator consumes it. If you need to reuse the values, convert it to a list with `list(granules)`.

```python
GranuleHandler.download_from_granules(granules, session=session)

# Files paths can be traced from the granule return values
file_paths = GranuleHandler.download_from_granules(granules, session=session)

# Saves to current directory, use `path` to save somewhere else
GranuleHandler.download_from_granules(granules, session=session, path="../Desktop")

# Retrieve first approved types
# Priority is given in order of returned links, not file types
file_paths = GranuleHandler.download_from_granules(granules, session, ext = ("hdf", "h5", "nc", "xml"))

```

#### Multithreaded Downloads

The `threads` parameter in `GranuleHandler.download_from_granules()` specifies how many concurrent processes or threads should be used while downloading. 

`threads` is an integer, specifying the maximum number of concurrently running workers. 

* If 1 is given, no parallelism is used at all, which is useful for debugging. 
* If set to -1, all CPUs are used. 
* For `threads` below -1, (n_cpus + 1 + n_jobs) are used. For example with `threads=-2`, all CPUs but one are used.

```python
GranuleHandler.download_from_granules(nigeria_granules, modis_session=session, threads=-1)
```

#### MODIS Data Types

Currently modis_tools only supports downloading of hdf file type.

## Development and Testing

### Setting up a development environment

- To install all production dependencies, run:

  ```python
  pip install -r requirements.txt
  ```

- To install dev-dependencies to run tests, run:

  ```python
  pip install -e .[test]
  ```

- Note that `gdal` is optionally supported as an extra dependency. This is for users who wish to use `ogr.Geometry` objects to spatially query the modis data to be retrieved. Assuming you have all the libraries installed to run gdal, you can install this dependency with:

  ```python
  pip install -e .[gdal]
  ```

- To install more than one extra dependency-set, separate them with a comma as seen in the below example. The full list of supported dependency-sets are listed under `extras_require` in setup.py:

  ```python
  pip install -e .[test,gdal]
  ```

### Testing

1. All tests can be found in `./tests` with a directory structure mirroring the directory structure of the files being tested
2. To run tests, navigate terminal to the root of this repo, and
   1. To run only unit tests (faster) run the following:
      `pytest -m "not integration_test"`
   2. To run only integration tests (slower) run the following:
      `pytest -m integration_test`
   3. To run the whole test suit, run:
      `pytest`

### Release Instructions

For project maintainers:

* Once all changes have been merged to main for a release, make a branch called
  to upgrade the version, eg. `upgrade-1.13`
* `pip install build twine`
* Update version `in setup.py`
* Create the source archive and wheel with `python -m build`
* `twine check dist/*` to check the files you've just build

*The final steps assumes you've set up your PyPi and TestPyPi accounts*
* Test upload to TestPyPi with `twine upload -r testpypi dist/*`
* If you haven't set up MFA for PyPi/TestPyPi, use your normal login username
  and password
* If you have, use `__token__` as the username and an [API
  token](https://pypi.org/help/#apitoken) as your password
* Assuming the test upload goes smoothly, upload to PyPi with `twine upload dist`
* Merge the version update branch to main


## Issues and Contributing

We welcome any feedback and contributions from the community!
- To report an issue or to request support, please use the [github issues](https://github.com/fraymio/modis-tools/issues).
- To contribute, please check out our [contribution guidline](./CONTRIBUTING.md).