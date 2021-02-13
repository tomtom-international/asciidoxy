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

from .shared import ProgressMock


def test_resolve_references_for_return_types(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_partial_references_for_return_types(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_references_for_parameters(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_partial_references_for_parameters(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_references_for_typedefs(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_references_for_inner_type_reference(parser_driver_factory):
    parser = parser_driver_factory("cpp/default")

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


def test_resolve_references_for_exceptions(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_partial_references_for_exceptions(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

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


def test_resolve_references_prefer_same_namespace(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

    member_a_t = parser.api_reference.find("asciidoxy::traffic::CreateConvertor",
                                           kind="function",
                                           lang="cpp")
    assert member_a_t is not None
    assert member_a_t.returns
    assert member_a_t.returns.type
    assert not member_a_t.returns.type.id
    assert not member_a_t.returns.type.kind

    member_a = parser.api_reference.find("asciidoxy::CreateConvertor", kind="function", lang="cpp")
    assert member_a is not None
    assert member_a.returns
    assert member_a.returns.type
    assert not member_a.returns.type.id
    assert not member_a.returns.type.kind

    member_a_g = parser.api_reference.find("asciidoxy::geometry::CreateConvertor",
                                           kind="function",
                                           lang="cpp")
    assert member_a_g is not None
    assert member_a_g.returns
    assert member_a_g.returns.type
    assert not member_a_g.returns.type.id
    assert not member_a_g.returns.type.kind

    parser.resolve_references()

    assert member_a_t.returns
    assert member_a_t.returns.type
    assert member_a_t.returns.type.id == "cpp-classasciidoxy_1_1traffic_1_1_convertor"
    assert member_a_t.returns.type.kind == "class"
    assert member_a_t.returns.type.namespace == "asciidoxy::traffic"

    assert member_a.returns
    assert member_a.returns.type
    assert member_a.returns.type.id == "cpp-classasciidoxy_1_1_convertor"
    assert member_a.returns.type.kind == "class"
    assert member_a.returns.type.namespace == "asciidoxy"

    assert member_a_g.returns
    assert member_a_g.returns.type
    assert member_a_g.returns.type.id == "cpp-classasciidoxy_1_1geometry_1_1_convertor"
    assert member_a_g.returns.type.kind == "class"
    assert member_a_g.returns.type.namespace == "asciidoxy::geometry"


def test_resolve_references_fails_when_ambiguous(parser_driver_factory):
    # When internal resolving fails, the type will not be resolved to the exact type, and will be
    # shown in the documentation as plain text. It should not raise an error.
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

    member = parser.api_reference.find("asciidoxy::traffic::geometry::CreateConvertor",
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


def test_resolve_references__report_progress(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", "cpp/consumer")

    progress_mock = ProgressMock()
    parser.resolve_references(progress=progress_mock)

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 49


def test_force_language_java(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="java")

    element = parser.api_reference.find("asciidoxy.traffic.TrafficEvent", kind="class", lang="java")
    assert element is not None
    assert element.language == "java"


def test_force_language_objc(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="objc")

    element = parser.api_reference.find("Logger", kind="class", lang="objc")
    assert element is not None
    assert element.language == "objc"


def test_force_language_unknown(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="unknown")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"


def test_force_language_empty(parser_driver_factory):
    parser = parser_driver_factory("cpp/default", force_language="")

    element = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                        kind="class",
                                        lang="cpp")
    assert element is not None
    assert element.language == "cpp"
