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
import shutil

from pathlib import Path
from tqdm import tqdm
from typing import List, Optional

from ..doxygenparser import Driver
from .collect import CollectError, Package, collect, specs_from_file


class FileCollisionError(CollectError):
    """Raised when files from different packages collide."""
    def __str__(self) -> str:
        return (f"File is present in multiple packages. Detected in package {self.name}:"
                f"\n{self.message}")


class PackageManager:
    build_dir: Path
    work_dir: Path
    image_work_dir: Path
    packages: List[Package]

    def __init__(self, build_dir: Path):
        self.build_dir = build_dir
        self.work_dir = build_dir / "intermediate"
        self.image_work_dir = self.work_dir / "images"
        self.packages = []

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
        self.packages = asyncio.get_event_loop().run_until_complete(
            collect(specs, download_dir, progress))

    def load_reference(self, parser: Driver, progress: Optional[tqdm] = None) -> None:
        """Load API reference from available packages.

        Args:
            parser:   Parser to feed the API reference.
            progress: Optional progress reporting.
        """
        if progress is not None:
            progress.total = len(self.packages)
            progress.update(0)

        for pkg in self.packages:
            if pkg.reference_dir is not None:
                for xml_file in pkg.reference_dir.glob("**/*.xml"):
                    parser.parse(xml_file)
            if progress is not None:
                progress.update()

    def prepare_work_directory(self, in_file: Path, progress: Optional[tqdm] = None) -> Path:
        """Create a work directory in which the files to be processed by AsciiDoctor can be created.

        Args:
            in_file: Input file that will be processed.
            progress: Optional progress reporting.

        Returns:
            Location of the input file in the working directory.

        Raises:
            FileCollisionError: The same file is present in multiple packages.
        """
        if progress is not None:
            progress.total = len(self.packages) + 1
            progress.update(0)

        if self.work_dir.exists():
            shutil.rmtree(self.work_dir)

        shutil.copytree(in_file.parent, self.work_dir)
        self.image_work_dir.mkdir(parents=True, exist_ok=True)
        if progress is not None:
            progress.update()

        for pkg in self.packages:
            if pkg.adoc_src_dir is not None:
                _copy_dir_contents(pkg.adoc_src_dir, self.work_dir, pkg)
            if pkg.adoc_image_dir is not None:
                _copy_dir_contents(pkg.adoc_image_dir, self.image_work_dir, pkg)
            if progress is not None:
                progress.update()

        return self.work_dir / in_file.name


def _copy_dir_contents(src: Path, dst: Path, pkg: Package) -> None:
    # In Python 3.8 we can use:
    # `shutil.copytree(src, dst, dirs_exist_ok=True)`

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
            if dst_entry.exists():
                raise FileCollisionError(
                    pkg.name, f"File {dst_entry.name} from {pkg.name} already exists in"
                    "another package.")
            shutil.copy2(src_entry, dst_entry)
        elif src_entry.is_dir():
            _copy_dir_contents(src_entry, dst_entry, pkg)
