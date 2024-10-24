import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    install_requires = fh.read().split()

setuptools.setup(
    name="modis_tools",
    version="1.1.5",
    author="fraym",
    author_email="datascience@fraym.io",
    description="Tools for working with the MODIS API and MODIS data.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/fraymio/modis-tools.git",
    packages=setuptools.find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Programming Language :: Python :: 3.7",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require={
        "test": ["pytest"],
        "gdal": ["gdal"],
    },
)
