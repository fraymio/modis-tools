import os
from urllib.parse import urlsplit

from pydantic import AnyUrl as AnyUrlv2
from pydantic import version
from pydantic.v1 import AnyUrl as AnyUrlv1

version.version_info()

any_url_v1 = AnyUrlv1("http://www.example.com", scheme="http", host="www.example.com")
any_url_v2 = AnyUrlv2("http://www.example.com")

type(any_url_v1)
type(any_url_v2)

any_url_v1.host
any_url_v2.host

print(urlsplit("https://google.com/"))
print(os.fspath("https://google.com/"))

urlsplit(any_url_v1)
urlsplit(any_url_v2)

os.fspath(any_url_v1)
os.fspath(any_url_v2)
