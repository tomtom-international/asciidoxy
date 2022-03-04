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
"""Utilities for loading API reference test data."""
from __future__ import annotations

from pathlib import Path

from asciidoxy.api_reference import ApiReference
from asciidoxy.parser import parser_factory

test_data_dir = Path(__file__).parent.parent / "data"
generated_test_data_dir = test_data_dir / "generated"
doxygen_test_data_dir = generated_test_data_dir / "doxygen"


def doxygen_versions():
    return [str(version.name) for version in doxygen_test_data_dir.glob("*")]


def generated_test_data_factory(reference_type: str, name: str, version: str = None):
    if reference_type == "doxygen":
        assert version is not None
        return generated_test_data_dir / reference_type / version / name
    elif reference_type == "dokka":
        return generated_test_data_dir / reference_type / name
    else:
        assert False


class ApiReferenceLoader:
    api_reference_set = [
        ("doxygen", "cpp/default"),
        ("doxygen", "java/default"),
        ("doxygen", "objc/default"),
        ("doxygen", "python/default"),
    ]

    def __init__(self):
        self._version = None
        self._api_reference = ApiReference()

    def version(self, version: str) -> ApiReferenceLoader:
        self._version = version
        return self

    def load_all(self) -> ApiReference:
        for reference_type, reference_set_name in self.api_reference_set:
            self.add(reference_type, reference_set_name)
        return self.load()

    def add(self, reference_type: str, reference_set_name: str) -> ApiReferenceLoader:
        parser = parser_factory(reference_type, self._api_reference)
        parser.parse(generated_test_data_factory(reference_type, reference_set_name, self._version))
        return self

    def load(self, resolve_references: bool = True) -> ApiReference:
        if resolve_references:
            self._api_reference.resolve_references()
        return self._api_reference
