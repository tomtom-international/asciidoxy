# Copyright (C) 2019, TomTom (http://tomtom.com).
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
from typing import Dict, Optional, Tuple, Union

from tqdm import tqdm

from ..document import Document, Package
from ..parser.doxygen import Driver
from .collect import CollectError, collect, specs_from_file

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
    file_name: Optional[Union[str, Path]]

    def __init__(self, package_name: str, file_name: Optional[Union[str, Path]]):
        self.package_name = package_name
        self.file_name = file_name

    def __str(self) -> str:
        return f"File not found in package {self.package_name}: {self.file_name or 'default file'}."


class PackageManager:
    build_dir: Path
    work_dir: Path
    packages: Dict[str, Package]
    warnings_are_errors: bool
    copied_files: Dict[Path, Package]
    copied_dirs: Dict[Path, Package]

    def __init__(self, build_dir: Path, warnings_are_errors: bool = True):
        self.build_dir = build_dir
        self.warnings_are_errors = warnings_are_errors

        self.work_dir = build_dir / "intermediate"
        self.packages = {}
        self.copied_files = {}
        self.copied_dirs = {}

    @property
    def image_work_dir(self) -> Path:
        return self.work_dir / "images"

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
        pkg = Package(Package.INPUT_PACKAGE_NAME)
        pkg.adoc_src_dir = include_dir
        pkg.adoc_root_doc = in_file
        pkg.scoped = True

        if image_dir is not None:
            pkg.adoc_image_dir = image_dir
        elif (in_file.parent / "images").is_dir():
            pkg.adoc_image_dir = in_file.parent / "images"

        if include_dir is None:
            pkg.copy_adoc_src_dir = False
            pkg.adoc_src_dir = in_file.parent

        self.packages[Package.INPUT_PACKAGE_NAME] = pkg

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
        loop = asyncio.get_event_loop_policy().new_event_loop()
        packages = loop.run_until_complete(collect(specs, download_dir, progress))
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

    def prepare_work_directory(self,
                               in_file: Path,
                               clear: bool = True,
                               progress: Optional[tqdm] = None) -> Document:
        """Create a work directory in which the files to be processed by AsciiDoctor can be created.

        Args:
            in_file:  Input file that will be processed.
            clear:    Clear the work directory if it already exists.
            progress: Optional progress reporting.

        Returns:
            Document to start processing.

        Raises:
            FileCollisionError: The same file is present in multiple packages.
        """
        if Package.INPUT_PACKAGE_NAME not in self.packages:
            self.set_input_files(in_file)

        if progress is not None:
            progress.total = len(self.packages)
            progress.update(0)

        if clear and self.work_dir.exists():
            shutil.rmtree(self.work_dir)

        self.image_work_dir.mkdir(parents=True, exist_ok=True)

        for pkg in self.packages.values():
            if pkg.copy_adoc_src_dir and pkg.adoc_src_dir is not None:
                self._copy_dir_contents(pkg.adoc_src_dir, self.work_dir, pkg)
            elif pkg.adoc_root_doc is not None:
                shutil.copy2(pkg.adoc_root_doc, self.work_dir)
            if pkg.adoc_image_dir is not None:
                self._copy_dir_contents(pkg.adoc_image_dir, self.image_work_dir, pkg)
            if progress is not None:
                progress.update()

        return self.make_document(Package.INPUT_PACKAGE_NAME, in_file.name)

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

    def input_package(self) -> Package:
        """Get the meta-package representing the input and include files."""
        assert Package.INPUT_PACKAGE_NAME in self.packages
        return self.packages[Package.INPUT_PACKAGE_NAME]

    def find_original_file(self,
                           work_file: Path,
                           package_hint: Optional[str] = None) -> Tuple[str, Path]:
        """Find the original relative file name for a file in the working directory."""
        rel_path = work_file.relative_to(self.work_dir)

        if package_hint and package_hint in self.packages:
            pkg = self.packages[package_hint]
            if pkg.adoc_src_dir is not None and (pkg.adoc_src_dir / rel_path).is_file():
                return pkg.name, rel_path

        input_pkg = self.input_package()
        assert input_pkg.adoc_root_doc is not None
        if input_pkg.adoc_src_dir is None and work_file.name == input_pkg.adoc_root_doc.name:
            return Package.INPUT_PACKAGE_NAME, Path(work_file.name)

        for pkg in self.packages.values():
            if pkg.adoc_src_dir is not None and (pkg.adoc_src_dir / rel_path).is_file():
                return pkg.name, rel_path

        assert False, "Cannot locate original file"

    def make_document(self,
                      package_name: Optional[str] = None,
                      file_name: Optional[Union[str, Path]] = None) -> Document:
        """Get a document from a package.

        Args:
            package_name: Name of the containing package. Empty to look in input files.
            file_name:    File name of the document. Empty to use the package default file.

        Returns:
            A valid document.

        Raises:
            UnknownPackageError
            UnknownFileError
        """
        if not package_name:
            package_name = Package.INPUT_PACKAGE_NAME

        pkg = self.packages.get(package_name, None)
        if pkg is None:
            raise UnknownPackageError(package_name)

        if file_name:
            file_path = Path(file_name)
        else:
            if pkg.adoc_root_doc is None or pkg.adoc_src_dir is None:
                # TODO: More specific error about missing default document
                raise UnknownFileError(package_name, file_name)
            file_path = pkg.adoc_root_doc.relative_to(pkg.adoc_src_dir)

        doc = Document(file_path, pkg, self.work_dir)

        if not doc.original_file.is_file():
            raise UnknownFileError(package_name, file_name)

        return doc

    def _warning_or_error(self, error: Exception):
        if self.warnings_are_errors:
            raise error
        else:
            logger.warning(str(error))

    def _copy_dir_contents(self, src: Path, dst: Path, pkg: Package) -> None:
        if dst in self.copied_files:
            raise FileCollisionError(
                pkg.name, f"Package {self.copied_files[dst].name} contains file {dst.name}, which"
                f" is also a directory in package {pkg.name}.")
        elif dst.is_file():
            raise FileCollisionError(
                pkg.name, f"Unexpected file {dst.name}, blocking creation of a directory"
                f" from package {pkg.name}. You may need to clear your build or output directory.")

        dst.mkdir(parents=True, exist_ok=True)
        self.copied_dirs[dst] = pkg

        for src_entry in src.iterdir():
            if src_entry.is_symlink():
                continue

            dst_entry = dst / src_entry.relative_to(src)
            if src_entry.is_file():
                if dst_entry in self.copied_files:
                    file_collision_error = FileCollisionError(
                        pkg.name, f"File {dst_entry.name} from package {pkg.name} already exists "
                        f"in package {self.copied_files[dst_entry].name}.")
                    self._warning_or_error(file_collision_error)
                elif dst_entry in self.copied_dirs:
                    raise FileCollisionError(
                        pkg.name, f"File {dst_entry.name} from package {pkg.name} is also a "
                        f"directory in package {self.copied_dirs[dst_entry].name}.")
                elif dst_entry.is_dir():
                    raise FileCollisionError(
                        pkg.name, f"Unexpected directory {dst_entry.name}, blocking creation of a "
                        f"file from package {pkg.name}. You may need to clear your build or output"
                        "directory.")
                shutil.copy2(src_entry, dst_entry)
                self.copied_files[dst_entry] = pkg
            elif src_entry.is_dir():
                self._copy_dir_contents(src_entry, dst_entry, pkg)
