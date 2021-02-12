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
"""Documentation package manager."""

import asyncio
import logging
import shutil

from pathlib import Path
from tqdm import tqdm
from typing import Dict, Optional

from ..parser.doxygen import Driver
from .collect import CollectError, Package, collect, specs_from_file

logger = logging.getLogger(__name__)


class FileCollisionError(CollectError):
    """Raised when files from different packages collide."""
    def __str__(self) -> str:
        return (f"File is present in multiple packages. Detected in package {self.name}:"
                f"\n{self.message}")


class UnknownPackageError(Exception):
    package_name: str

    def __init__(self, package_name: str):
        self.package_name = package_name

    def __str(self) -> str:
        return f"Unknown package name: {self.package_name}."


class UnknownFileError(Exception):
    package_name: str
    file_name: Optional[str]

    def __init__(self, package_name: str, file_name: Optional[str]):
        self.package_name = package_name
        self.file_name = file_name

    def __str(self) -> str:
        return f"File not found in package {self.package_name}: {self.file_name or 'default file'}."


class PackageManager:
    build_dir: Path
    work_dir: Path
    image_work_dir: Path
    packages: Dict[str, Package]
    warnings_are_errors: bool

    INPUT_FILES: str = "INPUT"

    def __init__(self, build_dir: Path, warnings_are_errors: bool = True):
        self.build_dir = build_dir
        self.warnings_are_errors = warnings_are_errors

        self.work_dir = build_dir / "intermediate"
        self.image_work_dir = self.work_dir / "images"
        self.packages = {}

    def set_input_files(self,
                        in_file: Path,
                        include_dir: Optional[Path] = None,
                        image_dir: Optional[Path] = None) -> None:
        """Set the input files to collect.

        Args:
            in_file:     AsciiDoc file used as input.
            include_dir: Directory containing files to include from AsciiDoc files. `None` to not
                             include additional files.
            image_dir:   Directory containing iamges to include from AsciiDoc files. If `None` and
                            directory named `images` is present next to the `in_file`, that
                            directory is used for images. Otherwise, no images are copied.
        """
        pkg = Package(self.INPUT_FILES)
        pkg.adoc_src_dir = include_dir
        pkg.adoc_root_doc = in_file
        pkg.scoped = True

        if image_dir is not None:
            pkg.adoc_image_dir = image_dir
        elif (in_file.parent / "images").is_dir():
            pkg.adoc_image_dir = in_file.parent / "images"
        self.packages[self.INPUT_FILES] = pkg

    def collect(self,
                spec_file: Path,
                version_file: Optional[Path] = None,
                progress: Optional[tqdm] = None) -> None:
        """Collect specified packages.

        Args:
            spec_file:    TOML file containing specifications.
            version_file: CSV file with versions to apply to the spec file.
            progress:     Optional progress reporting.

        Raises:
            SpecificationError: The specification file is invalid.
            CollectError:       A failure occurred while collecting the packages.
        """
        specs = specs_from_file(spec_file, version_file)
        if progress is not None:
            progress.total = len(specs)
            progress.update(0)

        download_dir = self.build_dir / "download"
        packages = asyncio.get_event_loop().run_until_complete(
            collect(specs, download_dir, progress))
        self.packages.update({pkg.name: pkg for pkg in packages})

    def load_reference(self, parser: Driver, progress: Optional[tqdm] = None) -> None:
        """Load API reference from available packages.

        Args:
            parser:   Parser to feed the API reference.
            progress: Optional progress reporting.
        """
        if progress is not None:
            progress.total = len(self.packages)
            progress.update(0)

        for pkg in self.packages.values():
            if pkg.reference_dir is not None:
                for xml_file in pkg.reference_dir.glob("**/*.xml"):
                    parser.parse(xml_file)
            if progress is not None:
                progress.update()

    def prepare_work_directory(self, in_file: Path, progress: Optional[tqdm] = None) -> Path:
        """Create a work directory in which the files to be processed by AsciiDoctor can be created.

        Args:
            in_file:  Input file that will be processed.
            progress: Optional progress reporting.

        Returns:
            Location of the input file in the working directory.

        Raises:
            FileCollisionError: The same file is present in multiple packages.
        """
        if progress is not None:
            progress.total = len(self.packages)
            progress.update(0)

        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

        self.image_work_dir.mkdir(parents=True, exist_ok=True)

        for pkg in self.packages.values():
            if pkg.adoc_src_dir is not None:
                self._copy_dir_contents(pkg.adoc_src_dir, self.work_dir, pkg)
            elif pkg.adoc_root_doc is not None:
                shutil.copy2(pkg.adoc_root_doc, self.work_dir)
            if pkg.adoc_image_dir is not None:
                self._copy_dir_contents(pkg.adoc_image_dir, self.image_work_dir, pkg)
            if progress is not None:
                progress.update()

        return self.work_dir / in_file.name

    def make_image_directory(self, parent: Path, progress: Optional[tqdm] = None) -> None:
        """Create an `images` directory in the specified path.

        Useful for output formats that require you to copy the images yourself.

        Args:
            parent:   Directory under which the images directory needs to be created.
            progress: Optional progress reporting.

        Raises:
            FileCollisionError: The same file is present in multiple packages.
        """
        if progress is not None:
            progress.total = len(self.packages)
            progress.update(0)

        image_dir = parent / "images"
        image_dir.mkdir(parents=True, exist_ok=True)
        for pkg in self.packages.values():
            if pkg.adoc_image_dir is not None:
                self._copy_dir_contents(pkg.adoc_image_dir, image_dir, pkg)
            if progress is not None:
                progress.update()

    def file_in_work_directory(self, package_name: str, file_name: Optional[str]) -> Path:
        """Get the absolute path to a file in the work directory.

        Args:
            package_name: Package the file is in.
            file_name:    Name of the file in the package. None or empty to use the default file for
                              the package.

        Returns:
            Absolute path to the file.

        Raises:
            UnknownPackageError: There is no package with that name.
            UnknownFileError:    The package does not contain a file with that name, or does not
                                     have a default file.
        """
        pkg = self.packages.get(package_name, None)
        if pkg is None:
            raise UnknownPackageError(package_name)

        if pkg.adoc_src_dir is None:
            raise UnknownFileError(package_name, file_name)

        if file_name:
            src_file = pkg.adoc_src_dir / file_name
            work_file = self.work_dir / file_name
        else:
            if pkg.adoc_root_doc is None:
                raise UnknownFileError(package_name, file_name)
            src_file = pkg.adoc_root_doc
            work_file = self.work_dir / src_file.relative_to(pkg.adoc_src_dir)

        if not src_file.is_file():
            raise UnknownFileError(package_name, file_name)

        assert work_file.is_file()
        return work_file

    def input_package(self) -> Package:
        """Get the meta-package representing the input and include files."""
        assert self.INPUT_FILES in self.packages
        return self.packages[self.INPUT_FILES]

    def _warning_or_error(self, error: Exception):
        if self.warnings_are_errors:
            raise error
        else:
            logger.warning(str(error))

    def _copy_dir_contents(self, src: Path, dst: Path, pkg: Package) -> None:
        if dst.is_file():
            raise FileCollisionError(
                pkg.name, f"Another package contains file {dst.name}, which is a directory"
                f" in {pkg.name}.")
        dst.mkdir(parents=True, exist_ok=True)

        for src_entry in src.iterdir():
            if src_entry.is_symlink():
                continue

            dst_entry = dst / src_entry.relative_to(src)
            if src_entry.is_file():
                if dst_entry.is_file():
                    file_collision_error = FileCollisionError(
                        pkg.name, f"File {dst_entry.name} from {pkg.name} already exists in"
                        " another package.")
                    self._warning_or_error(file_collision_error)
                elif dst_entry.is_dir():
                    raise FileCollisionError(
                        pkg.name, f"Another package contains file {dst_entry.name}, which is a"
                        f"directory in {pkg.name}.")
                shutil.copy2(src_entry, dst_entry)
            elif src_entry.is_dir():
                self._copy_dir_contents(src_entry, dst_entry, pkg)
