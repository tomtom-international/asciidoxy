# Copyright (C) 2019-2020, TomTom (http://tomtom.com).
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Collecting source files from different locations.

Sources are collected as packages. These can be local directories, or are downloaded from a remote
server. Each package can contain XML files containing the API reference documentation and/or
other files that can be directly included in the documentation.
"""

import aiohttp
import asyncio
import csv
import io
import logging
import os
import tarfile
import toml

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Type, TypeVar, Union

from tqdm import tqdm

logger = logging.getLogger(__name__)


class CollectError(Exception):
    """Base class for errors while collecting packages.

    Attributes:
        name: Name of the package for which an error was encountered.
        message: Details of the error.
    """
    name: str
    message: str

    def __init__(self, name: str, message: str):
        self.name = name
        self.message = message


class DownloadError(CollectError):
    """Raised when downloading a package failed."""
    def __str__(self) -> str:
        return f"Failed to download package: {self.name}:\n{self.message}"


class InvalidPackageError(CollectError):
    """Raised when package contents are not valid."""
    def __str__(self) -> str:
        return f"Invalid package: {self.name}:\n{self.message}"


class SpecificationError(Exception):
    """Raised when the specification in the configuration files is not valid.

    Attributes:
        message: Details of the error.
    """
    message: str

    def __init__(self, message: str):
        self.message = message

    def __str__(self) -> str:
        return f"Invalid specification: {self.message}"


class Package:
    """A package that is ready to be used by AsciiDoxy.

    Attributes:
        name: Name of the package.
        xml_dirs: List of directories containing XML descriptions of the API.
        include_dirs: List of directories containing files for inclusion in the documentation.
    """
    name: str
    xml_dirs: List[Path]
    include_dirs: List[Path]

    def __init__(self, name: str):
        self.name = name
        self.xml_dirs = []
        self.include_dirs = []


PackageSpecT = TypeVar("PackageSpecT", bound="PackageSpec")


class PackageSpec(ABC):
    """Base class for package specifications.

    Attributes:
        name: Name of the package.
        xml_subdir: Subdirectory in the package containing XML descriptions of the API.
        include_subdir: Subdirectory in the package containing files for inclusion.
    """
    name: str

    xml_subdir: Optional[str] = None
    include_subdir: Optional[str] = None

    def __init__(self, name: str, **kwargs):
        self.name = name

    @abstractmethod
    async def collect(self, download_dir: Path, session: aiohttp.ClientSession) -> Package:
        """Collect the package.

        Args:
            download_dir: Directory to store downloaded packages.
            session: HTTP session to use for content that needs to be downloaded.

        Returns:
            Information about the package.
        """
        pass

    @classmethod
    def from_toml(cls: Type[PackageSpecT], name: str, raw_spec: Mapping[str, Any],
                  **init_args) -> PackageSpecT:
        """Create a package specification from TOML file contents.

        Args:
            name: Name of the specification entry in TOML.
            raw_spec: Specification entry from TOML.
            init_args: Internal.

        Returns:
            A package specification based on the TOML contents.

        Raises:
            SpecificationError: The specification in TOML is invalid.
        """
        get = cls._make_getter(name, raw_spec)

        spec = cls(name, **init_args)
        spec.xml_subdir = get("xml_subdir")
        spec.include_subdir = get("include_subdir")
        return spec

    @staticmethod
    def _make_getter(name, raw_spec):
        def get(attr_name):
            value = raw_spec.get(attr_name, None)
            if value is None:
                raise SpecificationError(f"Package {name}, or its source, has no `{attr_name}`.")
            return value

        return get

    def _make_package(self, package_dir: Path) -> Package:
        pkg = Package(self.name)
        if self.xml_subdir:
            xml_dir = package_dir / self.xml_subdir
            if xml_dir.is_dir():
                logger.debug(f"{self.name} has XML subdirectory")
                pkg.xml_dirs.append(xml_dir)
        if self.include_subdir:
            include_dir = package_dir / self.include_subdir
            if include_dir.is_dir():
                logger.debug(f"{self.name} has include subdirectory")
                pkg.include_dirs.append(include_dir)

        if not pkg.xml_dirs and not pkg.include_dirs:
            raise InvalidPackageError(self.name, "Package does not contain XML or include files.")
        return pkg


class LocalPackageSpec(PackageSpec):
    """Specification of a package using a local directory.

    Attributes:
        package_dir: Directory containing the package.
    """
    package_dir: Path

    def __init__(self, name: str, package_dir: Union[os.PathLike, str]):
        super().__init__(name)
        self.package_dir = Path(package_dir)

    async def collect(self, download_dir: Path, session: aiohttp.ClientSession) -> Package:
        """See PackageSpec.collect"""
        return self._make_package(self.package_dir)

    @classmethod
    def from_toml(cls, name: str, raw_spec: Mapping[str, Any], **init_args) -> "LocalPackageSpec":
        """See PackageSpec.from_toml"""
        get = cls._make_getter(name, raw_spec)

        return super().from_toml(name, raw_spec, package_dir=Path(get("package_dir")), **init_args)


class HttpPackageSpec(PackageSpec):
    """Specification of a package downloaded from a remote server.

    Expects to download (compressed) tar files. All tar files will be extracted to the same output
    directory.

    The `url_template` is used to create download URLs for all files from a generic template. You
    can use the following placeholders in the template:
    * `{name}`: Replaced with the name of the package.
    * `{version}`: Replaced with the version of the package.
    * `{file_name}`: Replaced with the file name.

    Attributes:
        version: Version number of the package.
        url_template: Template for creating the URL to download the tar files from.
        file_names: List of files to download.
    """
    version: str
    url_template: str
    file_names: List[str]

    def __init__(self, name: str, version: str, url_template: str):
        super().__init__(name)
        self.version = version
        self.url_template = url_template
        self.file_names = []

    async def collect(self, download_dir: Path, session: aiohttp.ClientSession) -> Package:
        """See PackageSpec.collect"""
        package_dir = download_dir / self.name / self.version
        if not package_dir.is_dir():
            await self._download_files(package_dir, session)
        else:
            logger.debug(f"Using cached version of {self.name}:{self.version}")

        return self._make_package(package_dir)

    async def _download_files(self, package_dir: Path, session: aiohttp.ClientSession):
        package_dir.mkdir(parents=True, exist_ok=True)

        jobs = []
        for file_name in self.file_names:
            url = self.url_template.format(name=self.name,
                                           version=self.version,
                                           file_name=file_name)

            jobs.append(self._download(session, url, package_dir))
        await asyncio.gather(*jobs)

    async def _download(self, session: aiohttp.ClientSession, url: str, target_dir: Path):
        try:
            async with session.get(url) as response:
                data = await response.read()
                target_dir.mkdir(parents=True, exist_ok=True)
                tar_file = tarfile.open(fileobj=io.BytesIO(data))
                tar_file.extractall(target_dir)
        except tarfile.ReadError as tar_error:
            raise DownloadError(self.name, f"Cannot read tar file from {url}.") from tar_error
        except aiohttp.client_exceptions.ClientResponseError as http_error:
            raise DownloadError(self.name, f"Failed to download: {http_error}.") from http_error

    @classmethod
    def from_toml(cls, name: str, raw_spec: Mapping[str, Any], **init_args) -> "HttpPackageSpec":
        """See PackageSpec.from_toml"""
        get = cls._make_getter(name, raw_spec)

        spec = super().from_toml(name,
                                 raw_spec,
                                 version=get("version"),
                                 url_template=get("url_template"),
                                 **init_args)
        spec.file_names = get("file_names")

        if not isinstance(spec.file_names, list):
            raise SpecificationError(f"Package {name} `file_names` must be a list.")
        return spec


async def collect(specs: Sequence[PackageSpec],
                  download_dir: Path,
                  progress: Optional[tqdm] = None) -> List[Package]:
    """Collect the packages based on the list of specifications.

    Args:
        specs: A list of package specifications to collect.
        download_dir: Directory to store downloaded packages.

    Returns:
        A list of packages matching the package specifications.

    Raises:
        InvalidPackageError: One of the collected packages is not valid. It does not contain the
            required directories.
        DownloadError: An error occurred while downloading a remote package.
    """
    if progress is not None:

        async def _progress_report(coro):
            ret = await coro
            progress.update()
            return ret
    else:

        async def _progress_report(coro):
            return await coro

    conn = aiohttp.TCPConnector(limit=4)
    async with aiohttp.ClientSession(connector=conn, raise_for_status=True) as session:
        jobs = []
        for spec in specs:
            jobs.append(_progress_report(spec.collect(download_dir, session)))
        return await asyncio.gather(*jobs)


def versions_from_file(version_file: Union[os.PathLike, str]) -> Mapping[str, str]:
    """Load package versions from a CSV file.

    The package versions can be used if no version is specified in the package specification.

    Args:
        version_file: Path to the file containing the versions.

    Returns:
        A dictionairy where the key is the package name, and the value the version.
    """
    version_file = Path(version_file)

    with version_file.open(mode="r", encoding="utf-8") as version_file_handle:
        reader = csv.DictReader(version_file_handle)
        return {row['Component name']: row['Version'] for row in reader}


def _combine_dict(a: Dict[Any, Any], b: Dict[Any, Any]):
    a = a.copy()
    a.update(b)
    return a


def specs_from_file(
        spec_file: Union[os.PathLike, str],
        version_file: Optional[Union[os.PathLike, str]] = None) -> Sequence[PackageSpec]:
    """Load package specifications from a file.

    Optionally a version CSV file is used to provide package versions.

    Args:
        spec_file: Path to a TOML file containing package specifications.
        version_file: Optional. Path to a CSV file containing package versions.

    Returns:
        A list of package specifications as present in the TOML file.

    Raises:
        SpecificationError: The specifications in the file are not valid.
    """
    if version_file:
        versions = versions_from_file(version_file)
    else:
        versions = {}

    raw_specs = toml.load(spec_file)

    raw_sources = raw_specs.get("sources", {})
    raw_packages = raw_specs.get("packages", None)
    if not raw_packages:
        raise SpecificationError("No packages defined in specification file.")

    specs = []
    for name, raw_package_spec in raw_packages.items():

        if "source" in raw_package_spec:
            source_spec = raw_sources.get(raw_package_spec["source"], None)
            if source_spec is None:
                raise SpecificationError(
                    f"Undefined source `{raw_package_spec['source']}` in package {name}")
            raw_package_spec = _combine_dict(source_spec, raw_package_spec)

        if "version" not in raw_package_spec:
            version = versions.get(name, None)
            if version is not None:
                raw_package_spec["version"] = version

        def _get(attr_name):
            value = raw_package_spec.get(attr_name, None)
            if value is None:
                raise SpecificationError(f"Package {name}, or its source, has no `{attr_name}`.")
            return value

        spec_type = {"http": HttpPackageSpec, "local": LocalPackageSpec}.get(_get("type"), None)
        if spec_type is None:
            raise SpecificationError(f"Unknown type `{_get('type')}`")

        # mypy cannot correctly deduce the type of spec_type
        specs.append(spec_type.from_toml(name, raw_package_spec))  # type: ignore

    return specs
