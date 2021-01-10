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
"""Tests for the Swift parser based on SourceKitten."""

import pytest

from pathlib import Path

from asciidoxy.api_reference import ApiReference
from asciidoxy.model import Compound, Parameter, ReturnValue, TypeRef
from asciidoxy.parser.sourcekitten.driver import Driver, structure_and_doc_files


@pytest.fixture
def generated_data():
    def _func(file_name: str):
        return Path(__file__).parent / "generated" / file_name

    return _func


@pytest.fixture
def json_data(generated_data):
    def _func(swift_file):
        return generated_data(f"source_kitten/swift/default/{swift_file}.structure.json")

    return _func


@pytest.fixture
def api_reference():
    return ApiReference()


@pytest.fixture
def driver(api_reference):
    return Driver(api_reference)


def test_structure_and_doc_files__one_file__no_tag(tmp_path):
    structure_file = tmp_path / "Class.swift.json"
    structure_file.touch()
    assert structure_and_doc_files(structure_file) == (structure_file, structure_file)


def test_structure_and_doc_files__one_file__structure_tag(tmp_path):
    structure_file = tmp_path / "Class.swift.structure.json"
    structure_file.touch()
    assert structure_and_doc_files(structure_file) == (structure_file, structure_file)


def test_structure_and_doc_files__one_file__doc_tag(tmp_path):
    doc_file = tmp_path / "Class.swift.doc.json"
    doc_file.touch()
    assert structure_and_doc_files(doc_file) == (doc_file, doc_file)


def test_structure_and_doc_files__both_files__both_tagged(tmp_path):
    structure_file = tmp_path / "Class.swift.structure.json"
    structure_file.touch()
    doc_file = tmp_path / "Class.swift.doc.json"
    doc_file.touch()
    assert structure_and_doc_files(structure_file) == (structure_file, doc_file)


def test_structure_and_doc_files__both_files__only_structure_tagged(tmp_path):
    structure_file = tmp_path / "Class.swift.structure.json"
    structure_file.touch()
    doc_file = tmp_path / "Class.swift.json"
    doc_file.touch()
    assert structure_and_doc_files(doc_file) == (structure_file, doc_file)


def test_structure_and_doc_files__both_files__only_doc_tagged(tmp_path):
    structure_file = tmp_path / "Class.swift.json"
    structure_file.touch()
    doc_file = tmp_path / "Class.swift.doc.json"
    doc_file.touch()
    assert structure_and_doc_files(structure_file) == (structure_file, doc_file)


def test_parse__struct(driver, json_data, api_reference):
    assert driver.parse(json_data("Coordinate.swift")) is True

    struct = api_reference.find("Coordinate", kind="struct", lang="swift")
    assert struct is not None

    # TODO
    assert struct.id
    struct.id = None
    for member in struct.members:
        assert member.id
        member.id = None

    assert struct == Compound(
        language="swift",
        name="Coordinate",
        full_name="Coordinate",
        kind="struct",
        prot="public",
        brief="Class to hold information about a coordinate.",
        description="A coordinate has a latitude, longitude, and an altitude.",
        members=[
            Compound(language="swift",
                     name="latitude",
                     full_name="Coordinate.latitude",
                     namespace="Coordinate",
                     kind="variable",
                     prot="public",
                     brief="Latitude in degrees.",
                     returns=ReturnValue(
                         type=TypeRef(name="Double", language="swift", namespace="Coordinate"))),
            Compound(language="swift",
                     name="longitude",
                     full_name="Coordinate.longitude",
                     namespace="Coordinate",
                     kind="variable",
                     prot="public",
                     brief="Longitude in degrees.",
                     returns=ReturnValue(
                         type=TypeRef(name="Double", language="swift", namespace="Coordinate"))),
            Compound(language="swift",
                     name="altitude",
                     full_name="Coordinate.altitude",
                     namespace="Coordinate",
                     kind="variable",
                     prot="public",
                     brief="Altitude in degrees.",
                     returns=ReturnValue(
                         type=TypeRef(name="Double", language="swift", namespace="Coordinate"))),
            Compound(language="swift",
                     name="init()",
                     full_name="Coordinate.init()",
                     namespace="Coordinate",
                     kind="function",
                     prot="public",
                     brief="Default constructor."),
            Compound(language="swift",
                     name="update(_:)",
                     full_name="Coordinate.update(_:)",
                     namespace="Coordinate",
                     kind="function",
                     prot="public",
                     brief="Update from another coordinate.",
                     description="- Parameters:\n    - other: The coordinate to update from.",
                     params=[
                         Parameter(name="other",
                                   type=TypeRef(name="Coordinate",
                                                language="swift",
                                                namespace="Coordinate"))
                     ]),
        ])
