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
"""Tests for parsing C++ from Doxygen XML files."""

import pytest

import xml.etree.ElementTree as ET

from asciidoxy.doxygenparser.cpp import CppLanguage
from asciidoxy.doxygenparser.parser import DoxygenXmlParser
from tests.shared import assert_equal_or_none_if_empty, sub_element


def test_parse_cpp_class(parser_factory):
    parser = parser_factory("cpp/default")

    cpp_class = parser.api_reference.find("asciidoxy::geometry::Coordinate",
                                          kind="class",
                                          lang="cpp")
    assert cpp_class is not None
    assert cpp_class.id == "cpp-classasciidoxy_1_1geometry_1_1_coordinate"
    assert cpp_class.name == "Coordinate"
    assert cpp_class.full_name == "asciidoxy::geometry::Coordinate"
    assert cpp_class.language == "cpp"
    assert cpp_class.kind == "class"
    assert cpp_class.brief == "Class to hold information about a coordinate."
    assert cpp_class.description == "A coordinate has a latitude, longitude, and an altitude."
    assert cpp_class.include == "coordinate.hpp"
    assert cpp_class.namespace == "asciidoxy::geometry"

    assert len(cpp_class.members) == 13
    assert len(cpp_class.enumvalues) == 0

    member_names = sorted(m.name for m in cpp_class.members)
    assert member_names == sorted([
        "Coordinate",
        "Latitude",
        "Longitude",
        "Altitude",
        "IsValid",
        "latitude_",
        "longitude_",
        "altitude_",
        "Update",
        "Update",
        "Update",
        "Update",
        "Update",
    ])


def test_parse_cpp_class_with_nested_class(parser_factory):
    parser = parser_factory("cpp/default")

    cpp_class = parser.api_reference.find("asciidoxy::traffic::TrafficEvent",
                                          kind="class",
                                          lang="cpp")
    assert cpp_class is not None
    assert cpp_class.id == "cpp-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert cpp_class.namespace == "asciidoxy::traffic"
    assert len(cpp_class.inner_classes) == 1

    nested_class = cpp_class.inner_classes[0]
    assert nested_class.name == "asciidoxy::traffic::TrafficEvent::TrafficEventData"
    assert nested_class.namespace == "asciidoxy::traffic::TrafficEvent"
    assert nested_class.id == ("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1_traffic_"
                               "event_data")
    assert nested_class.language == "cpp"
    # referred object will be set after parsing all classes, during phase of resolving references
    assert nested_class.referred_object is None


def test_parse_cpp_class__ignore_friend_declarations(parser_factory):
    parser = parser_factory("cpp/default")

    cpp_class = parser.api_reference.find("asciidoxy::system::ServiceStarter",
                                          kind="class",
                                          lang="cpp")
    assert cpp_class is not None
    assert len([member for member in cpp_class.members if member.kind == "friend"]) == 0


def test_parse_cpp_member_function_no_return_value(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::geometry::Coordinate::Coordinate",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a69ac21cad618c0c033815f2cbdc86318")
    assert member.name == "Coordinate"
    assert member.full_name == "asciidoxy::geometry::Coordinate::Coordinate"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "asciidoxy::geometry::Coordinate::Coordinate"
    assert member.args == "()"
    assert member.brief == "Default constructor."
    assert member.description == ""
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "asciidoxy::geometry::Coordinate"

    assert len(member.params) == 0
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0
    assert member.returns is None


def test_parse_cpp_member_function_only_return_value(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::geometry::Coordinate::IsValid",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a8d7e0eac29549fa4666093e36914deac")
    assert member.name == "IsValid"
    assert member.full_name == "asciidoxy::geometry::Coordinate::IsValid"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "bool asciidoxy::geometry::Coordinate::IsValid"
    assert member.args == "() const"
    assert member.brief == "Check if the coordinate is valid."
    assert member.description == "A coordinate is valid if its values are within WGS84 bounds."
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "asciidoxy::geometry::Coordinate"

    assert len(member.params) == 0
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.description == "True if valid, false if not."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "bool"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert len(member.returns.type.nested) == 0
    assert member.returns.type.namespace == "asciidoxy::geometry::Coordinate"


def test_parse_cpp_member_function_params_and_return_value(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::traffic::TrafficEvent::Update",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.id == ("cpp-classasciidoxy_1_1traffic_1_1_traffic_event_"
                         "1a829eda83200a17d2d2f8a5fced5f000b")
    assert member.name == "Update"
    assert member.full_name == "asciidoxy::traffic::TrafficEvent::Update"
    assert member.language == "cpp"
    assert member.kind == "function"
    assert member.definition == "bool asciidoxy::traffic::TrafficEvent::Update"
    assert member.args == "(int cause, int delay)"
    assert member.brief == "Update the traffic event data."
    assert member.description == "Verifies the new information before updating."
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert len(member.params) == 2
    param1, param2 = member.params

    assert param1.name == "cause"
    assert param1.description == "New TPEG cause code."

    assert param1.type is not None
    assert param1.type.id is None
    assert param1.type.kind is None
    assert param1.type.language == "cpp"
    assert param1.type.name == "int"
    assert param1.type.namespace == "asciidoxy::traffic::TrafficEvent"

    assert not param1.type.prefix
    assert not param1.type.suffix
    assert len(param1.type.nested) == 0

    assert param2.name == "delay"
    assert param2.description == "New delay in seconds."

    assert param2.type is not None
    assert param2.type.id is None
    assert param2.type.kind is None
    assert param2.type.language == "cpp"
    assert param2.type.name == "int"
    assert param2.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not param2.type.prefix
    assert not param2.type.suffix
    assert len(param2.type.nested) == 0

    assert member.returns is not None
    assert member.returns.description == "True if the update is valid."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "bool"
    assert member.returns.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert len(member.returns.type.nested) == 0


def test_parse_cpp_member_function_with_nested_return_type(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::traffic::TrafficEvent::SharedData",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.name == "SharedData"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"

    assert member.returns is not None
    assert member.returns.description == "The shared pointer."
    assert member.returns.type is not None
    assert member.returns.type.id is None
    assert member.returns.type.kind is None
    assert member.returns.type.language == "cpp"
    assert member.returns.type.name == "std::shared_ptr"
    assert member.returns.type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix

    assert len(member.returns.type.nested) == 1
    nested_type = member.returns.type.nested[0]
    assert nested_type.id == ("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1"
                              "_traffic_event_data")
    assert nested_type.kind == "compound"
    assert nested_type.language == "cpp"
    assert nested_type.name == "TrafficEventData"
    assert nested_type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert not nested_type.prefix
    assert not nested_type.suffix
    assert len(nested_type.nested) == 0


def test_parse_cpp_member_enum(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::traffic::TrafficEvent::Severity",
                                       kind="enum",
                                       lang="cpp")
    assert member is not None
    assert member.name == "Severity"
    assert member.brief == "Severity scale for traffic events."
    assert (member.description ==
            "The more severe the traffic event, the more likely it is to have a large delay.")

    assert len(member.enumvalues) == 4
    enum_value = [e for e in member.enumvalues if e.name == "High"][0]
    assert enum_value.id == ("cpp-classasciidoxy_1_1traffic_1_1_traffic_event_"
                             "1a47c51b1f1f014cb943377fb67ad903b9a655d20c1ca69519ca647684edbb2db35")
    assert enum_value.name == "High"
    assert enum_value.full_name == "asciidoxy::traffic::TrafficEvent::Severity::High"
    assert enum_value.language == "cpp"
    assert enum_value.initializer == "= 3"
    assert enum_value.brief == "High severity."
    assert enum_value.description == "Better stay away here."
    assert enum_value.kind == "enumvalue"


def test_parse_cpp_member_function_with_exception(parser_factory):
    parser = parser_factory("cpp/default")

    member = parser.api_reference.find("asciidoxy::traffic::TrafficEvent::CalculateDelay()",
                                       kind="function",
                                       lang="cpp")
    assert member is not None
    assert member.name == "CalculateDelay"
    assert member.namespace == "asciidoxy::traffic::TrafficEvent"

    assert len(member.exceptions) == 1
    assert member.exceptions[0].type
    assert member.exceptions[0].type.name == "std::runtime_exception"
    assert member.exceptions[0].type.namespace == "asciidoxy::traffic::TrafficEvent"
    assert member.exceptions[0].description == "Thrown when the update encounters a critical error."


@pytest.fixture(params=[
    "", "const ", "volatile ", "constexpr ", "mutable ", "enum ", "class ", "const class ",
    "mutable volatile enum ", "constexpr class "
])
def cpp_type_prefix(request):
    return request.param


@pytest.fixture(params=["", " *", " &", " **", " * *", " const *", " * const *"])
def cpp_type_suffix(request):
    return request.param


def test_parse_cpp_type_from_text_simple(cpp_type_prefix, cpp_type_suffix):
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}double{cpp_type_suffix}"

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "cpp"
    assert type_ref.name == "double"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)
    assert len(type_ref.nested) == 0


def test_parse_cpp_type_from_text_nested_with_prefix_and_suffix(cpp_type_prefix, cpp_type_suffix):
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = (f"{cpp_type_prefix}Coordinate< {cpp_type_prefix}Unit{cpp_type_suffix} "
                         f">{cpp_type_suffix}")

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id is None
    assert nested_ref.kind is None
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Unit"
    assert_equal_or_none_if_empty(nested_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(nested_ref.suffix, cpp_type_suffix)


def test_parse_cpp_type_from_ref_with_prefix_and_suffix(cpp_type_prefix, cpp_type_suffix):
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = cpp_type_prefix
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=cpp_type_suffix)

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)
    assert len(type_ref.nested) == 0


def test_parse_cpp_type_from_ref_with_nested_text_type():
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = "const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail="< const Unit > &")

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert type_ref.prefix == "const "
    assert type_ref.suffix == " &"

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id is None
    assert nested_ref.kind is None
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Unit"
    assert nested_ref.prefix == "const "
    assert not nested_ref.suffix


def test_parse_cpp_type_from_text_with_nested_ref_type():
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = "const std::unique_ptr< const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=" & > *")

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == "std::unique_ptr"
    assert type_ref.prefix == "const "
    assert type_ref.suffix == " *"

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id == "cpp-tomtom_coordinate"
    assert nested_ref.kind == "compound"
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Coordinate"
    assert nested_ref.prefix == "const "
    assert nested_ref.suffix == " &"


def test_parse_cpp_type_from_multiple_nested_text_and_ref():
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = "const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=" < std::unique_ptr< ")
    sub_element(type_element,
                "ref",
                refid="tomtom_box",
                kindref="compound",
                text="Box",
                tail=" >, ")
    sub_element(type_element,
                "ref",
                refid="tomtom_point",
                kindref="compound",
                text="Point",
                tail=" < const std::string & > >")

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert type_ref.prefix == "const "
    assert not type_ref.suffix

    assert len(type_ref.nested) == 2
    nested_1 = type_ref.nested[0]
    assert nested_1 is not None
    assert not nested_1.id
    assert not nested_1.kind
    assert nested_1.language == "cpp"
    assert nested_1.name == "std::unique_ptr"
    assert not nested_1.prefix
    assert not nested_1.suffix

    assert len(nested_1.nested) == 1
    nested_1_1 = nested_1.nested[0]
    assert nested_1_1 is not None
    assert nested_1_1.id == "cpp-tomtom_box"
    assert nested_1_1.kind == "compound"
    assert nested_1_1.language == "cpp"
    assert nested_1_1.name == "Box"
    assert not nested_1_1.prefix
    assert not nested_1_1.suffix

    nested_2 = type_ref.nested[1]
    assert nested_2 is not None
    assert nested_2.id == "cpp-tomtom_point"
    assert nested_2.kind == "compound"
    assert nested_2.language == "cpp"
    assert nested_2.name == "Point"
    assert not nested_2.prefix
    assert not nested_2.suffix

    assert len(nested_2.nested) == 1
    nested_2_1 = nested_2.nested[0]
    assert nested_2_1 is not None
    assert not nested_2_1.id
    assert not nested_2_1.kind
    assert nested_2_1.language == "cpp"
    assert nested_2_1.name == "std::string"
    assert nested_2_1.prefix == "const "
    assert nested_2_1.suffix == " &"


def test_parse_cpp_type_multiple_prefix_and_suffix():
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = "mutable volatile std::string * const *"

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == "std::string"
    assert type_ref.prefix == "mutable volatile "
    assert type_ref.suffix == " * const *"


@pytest.mark.parametrize("type_with_space", [
    "short int", "signed short", "signed short int", "unsigned short", "unsigned short int",
    "signed int", "signed", "unsigned", "unsigned int", "long int", "signed long",
    "signed long int", "unsigned long", "unsigned long int", "long long", "long long int",
    "signed long long", "signed long long int", "unsigned long long", "unsigned long long int",
    "signed char", "long double"
])
def test_parse_cpp_type_with_space(cpp_type_prefix, type_with_space, cpp_type_suffix):
    parser = DoxygenXmlParser()
    cpp = CppLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}{type_with_space}{cpp_type_suffix}"

    type_ref = cpp.parse_type(type_element)
    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == type_with_space
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)
