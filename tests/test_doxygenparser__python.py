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
"""Tests for parsing python from Doxygen XML files."""

import pytest


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_class(api_reference):
    python_class = api_reference.find("asciidoxy.geometry.Coordinate", kind="class", lang="python")
    assert python_class is not None
    assert python_class.id == "python-classasciidoxy_1_1geometry_1_1_coordinate"
    assert python_class.name == "Coordinate"
    assert python_class.full_name == "asciidoxy.geometry.Coordinate"
    assert python_class.language == "python"
    assert python_class.kind == "class"
    assert python_class.brief == "Class to hold information about a coordinate."
    assert python_class.description == "A coordinate has a latitude, longitude, and an altitude."
    assert python_class.namespace == "asciidoxy.geometry"

    assert len(python_class.members) == 8
    assert len(python_class.enumvalues) == 0

    member_names = sorted(m.name for m in python_class.members)
    assert member_names == sorted([
        "altitude", "latitude", "longitude", "is_valid", "__init__", "from_string", "combine",
        "from_string_safe"
    ])


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_class_with_nested_class(api_reference):
    python_class = api_reference.find("asciidoxy.traffic.TrafficEvent", kind="class", lang="python")
    assert python_class is not None
    assert python_class.id == "python-classasciidoxy_1_1traffic_1_1_traffic_event"
    assert python_class.namespace == "asciidoxy.traffic"
    # one for nested class and one for enum
    assert len(python_class.inner_classes) == 2

    nested_class = python_class.inner_classes[0]
    assert nested_class.name == "asciidoxy.traffic.TrafficEvent.Severity"
    assert nested_class.namespace == "asciidoxy.traffic.TrafficEvent"
    assert nested_class.language == "python"
    assert nested_class.id == "python-classasciidoxy_1_1traffic_1_1_traffic_event_1_1_severity"
    assert nested_class.prot == "public"

    assert nested_class.referred_object
    assert nested_class.referred_object.id == nested_class.id
    assert nested_class.referred_object.name == "Severity"
    assert nested_class.referred_object.kind == "class"

    nested_class = python_class.inner_classes[1]
    assert nested_class.name == "asciidoxy.traffic.TrafficEvent.TrafficEventData"
    assert nested_class.namespace == "asciidoxy.traffic.TrafficEvent"
    assert nested_class.id == ("python-classasciidoxy_1_1traffic_1_1_traffic_event_1_1_"
                               "traffic_event_data")
    assert nested_class.language == "python"
    assert nested_class.prot == "public"

    assert nested_class.referred_object
    assert nested_class.referred_object.id == nested_class.id
    assert nested_class.referred_object.name == "TrafficEventData"
    assert nested_class.referred_object.kind == "class"


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_method(api_reference):
    member = api_reference.find("asciidoxy.traffic.TrafficEvent.update",
                                kind="function",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1traffic_1_1_traffic_event_"
                         "1a3eb310fb6cb4929eabe8eea356e59f2e")
    assert member.name == "update"
    assert member.full_name == "asciidoxy.traffic.TrafficEvent.update"
    assert member.language == "python"
    assert member.kind == "function"
    assert member.definition == " bool asciidoxy.traffic.TrafficEvent.update"
    assert member.args == "(self, int cause, int delay)"
    assert member.brief == "Update the traffic event data."
    assert member.description == "Verifies the new information before updating."
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "asciidoxy.traffic.TrafficEvent"

    assert len(member.params) == 3

    assert member.params[0].type
    assert member.params[0].type.name == "self"
    assert not member.params[0].name
    assert not member.params[0].description
    assert not member.params[0].default_value

    assert member.params[1].type
    assert member.params[1].type.name == "int"
    assert member.params[1].name == "cause"
    assert member.params[1].description == "New TPEG cause code."
    assert not member.params[2].default_value

    assert member.params[2].type
    assert member.params[2].type.name == "int"
    assert member.params[2].name == "delay"
    assert member.params[2].description == "New delay in seconds."
    assert not member.params[2].default_value

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.type is not None
    assert not member.returns.type.id
    assert not member.returns.type.kind
    assert member.returns.type.language == "python"
    assert member.returns.type.name == "bool"
    assert member.returns.type.namespace == "asciidoxy.traffic.TrafficEvent"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert not member.returns.type.nested
    assert member.returns.description == "True if the update is valid."


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_classmethod(api_reference):
    member = api_reference.find("asciidoxy.geometry.Coordinate.from_string",
                                kind="function",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a993b41d0a7518e83d751aa90e0d15fbe")
    assert member.name == "from_string"
    assert member.prot == "public"
    assert member.static is False

    assert len(member.params) == 2

    assert member.params[0].type
    assert member.params[0].type.name == "cls"
    assert not member.params[0].name
    assert not member.params[0].description

    assert member.params[1].type
    assert member.params[1].type.name == "str"
    assert member.params[1].name == "value"
    assert not member.params[1].description

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.type is not None
    assert member.returns.type.id == "python-classasciidoxy_1_1geometry_1_1_coordinate"
    assert member.returns.type.kind == "class"
    assert member.returns.type.language == "python"
    assert member.returns.type.name == "Coordinate"
    assert member.returns.type.namespace == "asciidoxy.geometry.Coordinate"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert not member.returns.type.nested
    assert not member.returns.description


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_staticmethod(api_reference):
    member = api_reference.find("asciidoxy.geometry.Coordinate.combine",
                                kind="function",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a4b820d9d0bdf81ddd7e22c243a41421d")
    assert member.name == "combine"
    assert member.prot == "public"
    assert member.static is True

    assert len(member.params) == 2

    assert member.params[0].type
    assert member.params[0].type.name == "Coordinate"
    assert member.params[0].name == "left"
    assert not member.params[0].description

    assert member.params[1].type
    assert member.params[1].type.name == "Coordinate"
    assert member.params[1].name == "right"
    assert not member.params[1].description


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_variable(api_reference):
    member = api_reference.find("asciidoxy.geometry.Coordinate.longitude",
                                kind="variable",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a0eb652e91c894dc2e49d9fbf3f224aa5")
    assert member.name == "longitude"
    assert member.prot == "public"
    assert member.static is False

    assert len(member.params) == 0
    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    # Not supported by Doxygen yet
    # assert member.returns is not None
    # assert member.returns.type is not None
    # assert not member.returns.type.id
    # assert not member.returns.type.kind
    # assert member.returns.type.language == "python"
    # assert member.returns.type.name == "float"
    # assert member.returns.type.namespace == "asciidoxy.geometry.Coordinate"
    # assert not member.returns.type.prefix
    # assert not member.returns.type.suffix
    # assert not member.returns.type.nested
    # assert not member.returns.description


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_constructor(api_reference):
    member = api_reference.find("asciidoxy.geometry.Coordinate.__init__",
                                kind="function",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1ae2c5561a335e7d226ae84bd561abb95f")
    assert member.name == "__init__"
    assert member.full_name == "asciidoxy.geometry.Coordinate.__init__"
    assert member.language == "python"
    assert member.kind == "function"
    assert member.definition == "def asciidoxy.geometry.Coordinate.__init__"
    assert member.args == "(self)"
    assert not member.brief
    assert not member.description
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "asciidoxy.geometry.Coordinate"

    assert len(member.params) == 1

    assert member.params[0].type
    assert member.params[0].type.name == "self"
    assert not member.params[0].name
    assert not member.params[0].description

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is None


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python_nested_argument_and_return_type(api_reference):
    member = api_reference.find("asciidoxy.geometry.Coordinate.from_string_safe",
                                kind="function",
                                lang="python")

    assert member is not None
    assert member.id == ("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                         "1a6711de457ebaf61c48358c2d2a37dbfa")
    assert member.name == "from_string_safe"
    assert member.prot == "public"
    assert member.static is False

    assert len(member.params) == 2

    assert member.params[0].type
    assert member.params[0].type.name == "cls"
    assert not member.params[0].name
    assert not member.params[0].description

    assert member.params[1].type
    assert member.params[1].type.name == "Optional"
    assert len(member.params[1].type.nested) == 1
    assert member.params[1].type.nested[0].name == "str"
    assert member.params[1].name == "value"
    assert not member.params[1].description

    assert len(member.exceptions) == 0
    assert len(member.enumvalues) == 0

    assert member.returns is not None
    assert member.returns.type is not None
    assert not member.returns.type.id
    assert not member.returns.type.kind
    assert member.returns.type.language == "python"
    assert member.returns.type.name == "Optional"
    assert member.returns.type.namespace == "asciidoxy.geometry.Coordinate"
    assert not member.returns.type.prefix
    assert not member.returns.type.suffix
    assert not member.returns.description
    assert len(member.returns.type.nested) == 1
    assert member.returns.type.nested[0].name == "Coordinate"
    assert member.returns.type.nested[0].namespace == "asciidoxy.geometry.Coordinate"


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python__default_parameter_value__init(api_reference):
    member = api_reference.find("asciidoxy.default_values.Point.__init__")
    assert member is not None
    assert len(member.params) == 3

    assert not member.params[0].name
    assert not member.params[0].default_value

    assert member.params[1].name == "x"
    assert member.params[1].default_value == "0"

    assert member.params[2].name == "y"
    assert member.params[2].default_value == "1"


@pytest.mark.parametrize("api_reference_set", [["python/default"]])
def test_parse_python__default_parameter_value__method(api_reference):
    member = api_reference.find("asciidoxy.default_values.Point.increment")
    assert member is not None
    assert len(member.params) == 3

    assert not member.params[0].name
    assert not member.params[0].default_value

    assert member.params[1].name == "x"
    assert member.params[1].default_value == "2"

    assert member.params[2].name == "y"
    assert member.params[2].default_value == "3"
