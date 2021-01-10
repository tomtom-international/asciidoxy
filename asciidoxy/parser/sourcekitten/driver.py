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
"""Read API reference information from SourceKitten JSON output."""

import json

from pathlib import Path
from typing import Tuple

from .parser import DocParser, StructureParser
from ..driver_base import DriverBase
from ...api_reference import ApiReference
from ...model import Compound, ReferableElement, TypeRef


class Driver(DriverBase):
    def __init__(self, api_reference: ApiReference):
        super().__init__(api_reference)

    def register(self, element: ReferableElement) -> None:
        """Register a new element."""
        self.api_reference.append(element)

    def unresolved_ref(self, ref: TypeRef) -> None:
        """Register an unresolved reference."""

    def inner_type_ref(self, parent: Compound, ref: TypeRef) -> None:
        """Register an inner type reference."""

    def parse(self, file_or_path) -> bool:
        """Parse all objects in a file and make them available for API reference generation.

        Params:
            file_or_path: File object or path for the file to parse.

        Returns:
            True if file is parsed. False if the file is invalid.
        """
        structure_file, doc_file = structure_and_doc_files(file_or_path)

        with open(structure_file) as file_handle:
            structure_data = json.load(file_handle)
        if not structure_data:
            return False

        with open(doc_file) as file_handle:
            doc_data = json.load(file_handle)
        if not doc_data:
            return False

        doc_parser = DocParser()
        for data in doc_data.values():
            doc_parser.parse(data)

        structure_parser = StructureParser(self, doc_parser.documentation)
        structure_parser.parse(structure_data)
        return True


def structure_and_doc_files(file_or_path: str) -> Tuple[Path, Path]:
    input_file = Path(file_or_path)

    if input_file.stem.endswith(".structure"):
        structure_file = input_file
        doc_file = input_file.with_name(f"{input_file.stem[:-10]}.doc.json")
        if doc_file.is_file():
            return structure_file, doc_file
        else:
            return input_file, input_file

    else:
        structure_file = input_file
        doc_file = input_file.with_name(f"{input_file.stem}.doc.json")
        if doc_file.is_file():
            return structure_file, doc_file

        structure_file = input_file.with_name(f"{input_file.stem}.structure.json")
        doc_file = input_file
        if structure_file.is_file():
            return structure_file, doc_file

    return input_file, input_file
