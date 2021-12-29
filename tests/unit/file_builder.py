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
"""Builder to create a directory structure with required input files for tests."""

from pathlib import Path
from typing import Optional

from asciidoxy.api_reference import ApiReference
from asciidoxy.config import Configuration
from asciidoxy.document import Document
from asciidoxy.generator.asciidoc import GeneratingApi, PreprocessingApi
from asciidoxy.generator.context import Context
from asciidoxy.packaging import Package, PackageManager


class FileBuilder:
    def __init__(self, base_dir: Path, build_dir: Path):
        self.package_manager = PackageManager(build_dir)

        self.packages_dir = base_dir / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)

        self.input_dir = self.packages_dir / "INPUT"
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self.work_dir = self.package_manager.work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.input_doc = None

        self.adoc_files_to_register = []
        self.multipage = False
        self.warnings_are_errors = False

    def add_input_file(self, name: str, register: bool = True):
        self.package_manager.set_input_files(self.input_dir / name, self.input_dir)
        self.input_doc = self.add_include_file(name, register)
        self.input_doc.is_root = True
        return self.input_doc

    def add_include_file(self, name: str, register: bool = True):
        pkg = self._add_package(Package.INPUT_PACKAGE_NAME)
        return self._add_file(pkg, name, register)

    def add_package_file(self, package: str, name: str, register: bool = True):
        pkg = self._add_package(package)
        return self._add_file(pkg, name, register)

    def add_package_default_file(self, package: str, name: str, register: bool = True):
        pkg = self._add_package(package, name)
        return self._add_file(pkg, name, register)

    def _add_file(self, package: Package, name: str, register: bool = True):
        doc = Document(Path(name), package, self.work_dir)

        input_file = doc.original_file
        input_file.parent.mkdir(parents=True, exist_ok=True)
        input_file.touch()

        work_file = doc.work_file
        work_file.parent.mkdir(parents=True, exist_ok=True)
        work_file.touch()

        if register:
            self.adoc_files_to_register.append(doc)

        return doc

    def _add_package(self, package_name: str, default_file: Optional[str] = None):
        pkg = self.package_manager.packages.get(package_name)
        if pkg is None:
            pkg = Package(package_name)
            pkg.adoc_src_dir = self.packages_dir / package_name
            if default_file:
                pkg.adoc_root_doc = pkg.adoc_src_dir / default_file
            pkg.scoped = True
            self.package_manager.packages[package_name] = pkg
        return pkg

    def context(self):
        config = Configuration()
        config.input_file = self.input_doc.original_file
        config.build_dir = self.package_manager.build_dir
        config.destination_dir = self.package_manager.build_dir / "output"
        config.cache_dir = self.package_manager.build_dir / "cache"
        config.backend = "html5"
        config.warnings_are_errors = self.warnings_are_errors
        config.debug = False
        config.log_level = "INFO"
        config.multipage = self.multipage
        config.extra = []

        c = Context(reference=ApiReference(),
                    package_manager=self.package_manager,
                    document=self.input_doc,
                    config=config)

        for file in self.adoc_files_to_register:
            c.documents[file.relative_path] = file
            if file is not self.input_doc:
                file.included_in = self.input_doc

        c.multipage = self.multipage
        c.warnings_are_errors = self.warnings_are_errors

        return c

    def apis(self):
        context = self.context()
        yield PreprocessingApi(context)
        yield GeneratingApi(context)
