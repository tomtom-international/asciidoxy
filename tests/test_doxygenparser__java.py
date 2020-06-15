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


@pytest.mark.parametrize("api_reference_set", [["java/default"]])
def test_parse_java_class(api_reference):
    java_class = api_reference.find("com.asciidoxy.geometry.Coordinate", kind="class", lang="java")
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


@pytest.mark.parametrize("api_reference_set", [["java/default"]])
def test_parse_java_class_with_nested_class(api_reference):
    java_class = api_reference.find("com.asciidoxy.traffic.TrafficEvent", kind="class", lang="java")
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

    assert nested_class.referred_object is not None
    assert nested_class.referred_object.id == nested_class.id
    assert nested_class.referred_object.name == "Severity"
    assert nested_class.referred_object.kind == "enum"

    nested_class = java_class.inner_classes[1]
    assert nested_class.name == "com.asciidoxy.traffic.TrafficEvent.TrafficEventData"
    assert nested_class.namespace == "com.asciidoxy.traffic.TrafficEvent"
    assert nested_class.id == ("java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_1_1_"
                               "traffic_event_data")
    assert nested_class.language == "java"

    assert nested_class.referred_object is not None
    assert nested_class.referred_object.id == nested_class.id
    assert nested_class.referred_object.name == "TrafficEventData"
    assert nested_class.referred_object.kind == "class"


@pytest.mark.parametrize("api_reference_set", [["java/default"]])
def test_parse_java_method(api_reference):
    member = api_reference.find("com.asciidoxy.traffic.TrafficEvent.Update",
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
    assert not member.returns.type.nested
    assert member.returns.description == "True if the update is valid."
