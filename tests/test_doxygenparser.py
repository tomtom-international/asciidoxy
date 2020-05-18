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
"""Generic tests for parsing Doxygen XML files."""

import pytest

from asciidoxy.api_reference import AmbiguousLookupError
from asciidoxy.doxygenparser.parser import DoxygenXmlParser

from .shared import ProgressMock


def test_find_complete_match(parser_factory):
    parser = parser_factory("cpp/default")

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate", kind="function",
                                     lang="cpp") is None
    assert parser.api_reference.find("asciidoxy::geometry::Coordinate", kind="class",
                                     lang="java") is None
    assert parser.api_reference.find(
        "asciidoxy::geometry::Coordinate::Coordinate", kind="class", lang="cpp") is None
    assert parser.api_reference.find("asciidoxy::geometry::Coordinate", kind="class",
                                     lang="cpp") is not None


def test_find_only_by_id(parser_factory):
    parser = parser_factory("cpp/default")

    assert parser.api_reference.find(
        target_id="cpp-classasciidoxy_1_1geometry_1_1_coordinate") is not None


def test_find_only_by_name(parser_factory):
    parser = parser_factory("cpp/default")

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate") is not None


def test_find_by_name_and_kind(test_data):
    parser = DoxygenXmlParser()
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("Coordinate", kind="class")
    assert element is not None
    assert element.kind == "class"

    element = parser.api_reference.find("Coordinate", kind="interface")
    assert element is not None
    assert element.kind == "interface"

    assert parser.api_reference.find("Coordinate", kind="function") is None


def test_find_by_name_and_lang(test_data):
    parser = DoxygenXmlParser()
    parser.parse(test_data / "ambiguous_names.xml")

    element = parser.api_reference.find("BoundingBox", lang="java")
    assert element is not None
    assert element.language == "java"

    element = parser.api_reference.find("BoundingBox", lang="objc")
    assert element is not None
    assert element.language == "objc"

    assert parser.api_reference.find("BoundingBox", lang="cpp") is None


def test_find_by_name_and_namespace(parser_factory):
    parser = parser_factory("cpp/default")

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate",
                                     namespace="asciidoxy") is not None
    assert parser.api_reference.find("geometry::Coordinate", namespace="asciidoxy") is not None

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate",
                                     namespace="asciidoxy::geometry") is not None
    assert parser.api_reference.find("geometry::Coordinate",
                                     namespace="asciidoxy::geometry") is not None
    assert parser.api_reference.find("Coordinate", namespace="asciidoxy::geometry") is not None

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate",
                                     namespace="asciidoxy::traffic") is not None
    assert parser.api_reference.find("geometry::Coordinate",
                                     namespace="asciidoxy::traffic") is not None


def test_find_by_name__prefer_exact_match(parser_factory):
    parser = parser_factory("cpp/default")

    assert parser.api_reference.find(
        "asciidoxy::geometry::Coordinate::Coordinate",
        namespace="asciidoxy").namespace == "asciidoxy::geometry::Coordinate"

    with pytest.raises(AmbiguousLookupError):
        # TODO: Unsupported case for now
        assert parser.api_reference.find("Coordinate",
                                         namespace="asciidoxy::geometry::Coordinate") is None

    assert parser.api_reference.find("asciidoxy::geometry::Coordinate",
                                     namespace="asciidoxy").namespace == "asciidoxy::geometry"
    assert parser.api_reference.find(
        "Coordinate", namespace="asciidoxy::geometry").namespace == "asciidoxy::geometry"


def test_find_by_name_ambiguous(test_data):
    parser = DoxygenXmlParser()
    parser.parse(test_data / "ambiguous_names.xml")

    with pytest.raises(AmbiguousLookupError) as exception1:
        parser.api_reference.find("BoundingBox")
    assert len(exception1.value.candidates) == 2

    with pytest.raises(AmbiguousLookupError) as exception2:
        parser.api_reference.find("Coordinate", lang="cpp")
    assert len(exception2.value.candidates) == 2


def test_find_method__explicit_no_arguments(parser_factory):
    reference = parser_factory("cpp/default").api_reference

    element = reference.find("asciidoxy::geometry::Coordinate::Coordinate()")
    assert element is not None


def test_find_method__explicit_no_arguments__requires_no_args(parser_factory):
    reference = parser_factory("cpp/default").api_reference

    element = reference.find("asciidoxy::traffic::TrafficEvent::Update()")
    assert element is None


def test_find_method__select_based_on_args(parser_factory):
    reference = parser_factory("cpp/default").api_reference

    with pytest.raises(AmbiguousLookupError):
        reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent")

    element = reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent()")
    assert element is not None

    element = reference.find("asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)")
    assert element is not None


def test_find_method__select_based_on_args_2(parser_factory):
    reference = parser_factory("cpp/default").api_reference

    with pytest.raises(AmbiguousLookupError):
        reference.find("asciidoxy::geometry::Coordinate::Update")

    element = reference.find("asciidoxy::geometry::Coordinate::Update()")
    assert element is None

    element = reference.find("asciidoxy::geometry::Coordinate::Update(const Coordinate&)")
    assert element is not None

    element = reference.find(
        "asciidoxy::geometry::Coordinate::Update(std::tuple< double, double, double >)")
    assert element is not None

    element = reference.find(
        "asciidoxy::geometry::Coordinate::Update(std::tuple< double, double >)")
    assert element is not None

    element = reference.find("asciidoxy::geometry::Coordinate::Update(double, double)")
    assert element is not None

    element = reference.find("asciidoxy::geometry::Coordinate::Update(double, double, double)")
    assert element is not None


def test_resolve_references_for_return_types(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::CurrentPosition",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id

    parser.resolve_references()

    assert member.returns
    assert member.returns.type
    assert member.returns.type.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert member.returns.type.kind == "class"


def test_resolve_partial_references_for_return_types(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::TrafficNearby",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert len(member.returns.type.nested) == 1
    assert not member.returns.type.nested[0].id

    parser.resolve_references()

    assert member.returns
    assert member.returns.type
    assert len(member.returns.type.nested) == 1
    assert member.returns.type.nested[0].id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.returns.type.nested[0].kind == "class"


def test_resolve_references_for_parameters(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::IsNearby",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert len(member.params) == 1
    assert member.params[0].type
    assert not member.params[0].type.id

    parser.resolve_references()

    assert len(member.params) == 1
    assert member.params[0].type
    assert member.params[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert member.params[0].type.kind == "class"


def test_resolve_partial_references_for_parameters(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::InTraffic",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert len(member.params) == 1
    assert member.params[0].type
    assert not member.params[0].type.id

    parser.resolve_references()

    assert len(member.params) == 1
    assert member.params[0].type
    assert member.params[0].type.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.params[0].type.kind == "class"


def test_resolve_references_for_typedefs(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Traffic", kind="typedef")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id

    parser.resolve_references()

    assert member.returns
    assert member.returns.type
    assert member.returns.type.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert member.returns.type.kind == "class"


def test_resolve_references_for_inner_type_reference(parser_factory):
    parser = parser_factory("cpp/default")

    parent_class = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                             kind="class",
                                             lang="cpp")
    assert parent_class is not None
    assert len(parent_class.inner_classes) > 0

    nested_class = parent_class.inner_classes[0]
    assert nested_class.name == "asciidoxy::traffic::TrafficEvent::TrafficEventData"
    assert nested_class.referred_object is None

    parser.resolve_references()

    assert nested_class.referred_object is not None
    assert nested_class.referred_object.full_name == nested_class.name


def test_resolve_references_for_exceptions(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::Override",
                                       kind="function")
    assert member is not None
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert not member.exceptions[0].type.id

    parser.resolve_references()

    assert member.returns
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate"
    assert member.exceptions[0].type.kind == "class"


def test_resolve_partial_references_for_exceptions(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::positioning::Positioning::TrafficNearby",
                                       kind="function")
    assert member is not None
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert not member.exceptions[0].type.id

    parser.resolve_references()

    assert member.returns
    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.id == "cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate"
    assert member.exceptions[0].type.kind == "class"


def test_resolve_references_fails_when_ambiguous(parser_factory):
    # When internal resolving fails, the type will not be resolved to the exact type, and will be
    # shown in the documentation as plain text. It should not raise an error.
    parser = parser_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::traffic::CreateConvertor",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id
    assert not member.returns.type.kind

    parser.resolve_references()

    assert member.returns
    assert member.returns.type
    assert not member.returns.type.id
    assert not member.returns.type.kind


def test_resolve_references__report_progress(parser_factory):
    parser = parser_factory("cpp/default", "cpp/consumer")

    progress_mock = ProgressMock()
    parser.resolve_references(progress=progress_mock)

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 37


def test_force_language_java(parser_factory):
    parser = parser_factory("cpp/default", force_language="java")

    element = parser.api_reference.find("asciidoxy.traffic.TrafficEvent", kind="class", lang="java")
    assert element is not None
    assert element.language == "java"


def test_force_language_objc(parser_factory):
    parser = parser_factory("cpp/default", force_language="objc")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="objc")
    assert element is not None
    assert element.language == "objc"


def test_force_language_unknown(parser_factory):
    parser = parser_factory("cpp/default", force_language="unknown")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"


def test_force_language_empty(parser_factory):
    parser = parser_factory("cpp/default", force_language="")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"
