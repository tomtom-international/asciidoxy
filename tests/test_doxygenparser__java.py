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
"""Tests for parsing Java from Doxygen XML files."""

import pytest

import xml.etree.ElementTree as ET

from asciidoxy.doxygenparser.java import JavaLanguage
from asciidoxy.doxygenparser.parser import DoxygenXmlParser
from tests.shared import assert_equal_or_none_if_empty


def test_parse_java_class(parser_factory):
    parser = parser_factory("java/default")

    java_class = parser.api_reference.find("com.asciidoxy.geometry.Coordinate",
                                           kind="class",
                                           lang="java")
    assert java_class is not None
    assert java_class.id == "java-classcom_1_1asciidoxy_1_1geometry_1_1_coordinate"
    assert java_class.name == "Coordinate"
    assert java_class.full_name == "com.asciidoxy.geometry.Coordinate"
    assert java_class.language == "java"
    assert java_class.kind == "class"
    assert java_class.brief == "Class to hold information about a coordinate."
    assert java_class.description == "A coordinate has a latitude, longitude, and an altitude."
    assert java_class.namespace == "com.asciidoxy.geometry"

    assert len(java_class.members) == 8
    assert len(java_class.enumvalues) == 0

    member_names = sorted(m.name for m in java_class.members)
    assert member_names == sorted([
        "Coordinate",
        "Latitude",
        "Longitude",
        "Altitude",
        "IsValid",
        "latitude_",
        "longitude_",
        "altitude_",
    ])


def test_parse_java_class_with_nested_class(parser_factory):
    parser = parser_factory("java/default")

    java_class = parser.api_reference.find("com.asciidoxy.traffic.TrafficEvent",
                                           kind="class",
                                           lang="java")
    assert java_class is not None
    assert java_class.id == "java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event"
    assert java_class.namespace == "com.asciidoxy.traffic"
    # one for nested class and one for enum
    assert len(java_class.inner_classes) == 2

    nested_class = java_class.inner_classes[0]
    assert nested_class.name == "com.asciidoxy.traffic.TrafficEvent.Severity"
    assert nested_class.namespace == "com.asciidoxy.traffic.TrafficEvent"
    assert nested_class.language == "java"
    assert nested_class.id == "java-enumcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_1_1_severity"
    # referred object will be set after parsing all classes, during phase of resolving references
    assert nested_class.referred_object is None

    nested_class = java_class.inner_classes[1]
    assert nested_class.name == "com.asciidoxy.traffic.TrafficEvent.TrafficEventData"
    assert nested_class.namespace == "com.asciidoxy.traffic.TrafficEvent"
    assert nested_class.id == ("java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_1_1_"
                               "traffic_event_data")
    assert nested_class.language == "java"
    # referred object will be set after parsing all classes, during phase of resolving references
    assert nested_class.referred_object is None

    parser.resolve_references()

    nested_class = java_class.inner_classes[0]
    assert nested_class.referred_object
    assert nested_class.referred_object.name == "Severity"
    assert nested_class.referred_object.kind == "enum"

    nested_class = java_class.inner_classes[1]
    assert nested_class.referred_object
    assert nested_class.referred_object.name == "TrafficEventData"
    assert nested_class.referred_object.kind == "class"


def test_parse_java_method(parser_factory):
    parser = parser_factory("java/default")

    member = parser.api_reference.find("com.asciidoxy.traffic.TrafficEvent.Update",
                                       kind="function",
                                       lang="java")

    assert member is not None
    assert member.id == ("java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_"
                         "1a72847da5fa4e03763f089c5d044085d4")
    assert member.name == "Update"
    assert member.full_name == "com.asciidoxy.traffic.TrafficEvent.Update"
    assert member.language == "java"
    assert member.kind == "function"
    assert member.definition == "boolean com.asciidoxy.traffic.TrafficEvent.Update"
    assert member.args == "(int cause, int delay)"
    assert member.brief == "Update the traffic event data."
    assert member.description == "Verifies the new information before updating."
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "com.asciidoxy.traffic.TrafficEvent"

    assert len(member.params) == 2
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.type is not None
    assert not member.returns.type.id
    assert not member.returns.type.kind
    assert member.returns.type.language == "java"
    assert member.returns.type.name == "boolean"
    assert member.returns.type.namespace == "com.asciidoxy.traffic.TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert len(member.returns.type.nested) == 0
    assert member.returns.description == "True if the update is valid."


@pytest.fixture(params=["", "final ", "synchronized ", "synchronized final "])
def java_type_prefix(request):
    return request.param


def test_parse_java_type_from_text_simple(java_type_prefix):
    parser = DoxygenXmlParser()
    java = JavaLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}double"

    type_ref = java.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "java"
    assert type_ref.name == "double"
    assert_equal_or_none_if_empty(type_ref.prefix, java_type_prefix)
    assert not type_ref.suffix
    assert len(type_ref.nested) == 0


@pytest.mark.parametrize("generic_prefix, generic_name", [("? extends ", "Unit"),
                                                          ("T extends ", "Unit"),
                                                          ("T extends ", "Unit "), (None, "T "),
                                                          (None, "T")])
def test_parse_java_type_with_generic(java_type_prefix, generic_prefix, generic_name):
    parser = DoxygenXmlParser()
    java = JavaLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}Position<{generic_prefix or ''}{generic_name}>"

    type_ref = java.parse_type(type_element)
    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "java"
    assert type_ref.name == "Position"
    assert_equal_or_none_if_empty(type_ref.prefix, java_type_prefix)
    assert not type_ref.suffix
    assert len(type_ref.nested) == 1
    assert type_ref.nested[0].prefix == generic_prefix
    assert type_ref.nested[0].name == generic_name.strip()
    assert not type_ref.nested[0].suffix
