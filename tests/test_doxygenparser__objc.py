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
"""
Tests for parsing Objective C from Doxygen XML files.
"""

import pytest

import xml.etree.ElementTree as ET

from asciidoxy.doxygenparser.objc import ObjectiveCLanguage
from asciidoxy.doxygenparser.parser import DoxygenXmlParser
from .shared import assert_equal_or_none_if_empty


def test_parse_objc_interface(parser_factory):
    parser = parser_factory("objc/default")

    objc_class = parser.api_reference.find("ADCoordinate", kind="class", lang="objc")
    assert objc_class is not None
    assert objc_class.id == "objc-interface_a_d_coordinate"
    assert objc_class.name == "ADCoordinate"
    assert objc_class.full_name == "ADCoordinate"
    assert objc_class.language == "objc"
    assert objc_class.kind == "class"
    assert objc_class.brief == "Class to hold information about a coordinate."
    assert objc_class.description == "A coordinate has a latitude, longitude, and an altitude."
    assert objc_class.include == "ADCoordinate.h"
    assert objc_class.namespace is None

    assert len(objc_class.members) == 5
    assert len(objc_class.enumvalues) == 0

    member_names = sorted(m.name for m in objc_class.members)
    assert member_names == sorted([
        "latitude",
        "longitude",
        "altitude",
        "isValid",
        "init",
    ])


def test_parse_objc_protocol(parser_factory):
    parser = parser_factory("objc/default")

    objc_class = parser.api_reference.find("ADTrafficEvent", kind="protocol", lang="objc")
    assert objc_class is not None
    assert objc_class.id == "objc-protocol_a_d_traffic_event-p"
    assert objc_class.name == "ADTrafficEvent"
    assert objc_class.full_name == "ADTrafficEvent"
    assert objc_class.language == "objc"
    assert objc_class.kind == "protocol"
    assert objc_class.brief == "Information about a traffic event."
    assert objc_class.description == ""
    assert objc_class.namespace is None

    assert len(objc_class.members) == 2
    assert len(objc_class.enumvalues) == 0

    member_names = sorted(m.name for m in objc_class.members)
    assert member_names == sorted([
        "data",
        "updateWithCause:andDelay:",
    ])


def test_parse_objc_member_function(parser_factory):
    parser = parser_factory("objc/default")

    member = parser.api_reference.find("ADTrafficEvent.updateWithCause:andDelay:",
                                       kind="function",
                                       lang="objc")
    assert member is not None
    assert member.id == "objc-protocol_a_d_traffic_event-p_1aaa32145fd9b5ebec01740ac078738262"
    assert member.name == "updateWithCause:andDelay:"
    assert member.full_name == "ADTrafficEvent.updateWithCause:andDelay:"
    assert member.language == "objc"
    assert member.kind == "function"
    assert member.definition == "id ADTrafficEvent-p::updateWithCause:andDelay:"
    assert member.args == "(NSInteger cause,[andDelay] NSInteger delay)"
    assert member.brief == "Update the traffic event data."
    assert member.description == "Verifies the new information before updating."
    assert member.prot == "public"
    assert member.static is False
    assert member.namespace == "ADTrafficEvent"

    assert len(member.enumvalues) == 0

    assert len(member.params) == 2

    param = member.params[0]
    assert param.type is not None
    assert not param.type.id
    assert not param.type.kind
    assert param.type.language == "objc"
    assert param.type.name == "NSInteger"
    assert param.type.namespace == "ADTrafficEvent"
    assert not param.type.prefix
    assert not param.type.suffix
    assert len(param.type.nested) == 0
    assert param.name == "cause"
    assert param.description == "New TPEG cause code."

    param = member.params[1]
    assert param.type is not None
    assert not param.type.id
    assert not param.type.kind
    assert param.type.language == "objc"
    assert param.type.name == "NSInteger"
    assert param.type.namespace == "ADTrafficEvent"
    assert not param.type.prefix
    assert not param.type.suffix
    assert len(param.type.nested) == 0
    assert param.name == "delay"
    assert param.description == "New delay in seconds."


def test_parse_objc_block(parser_factory):
    parser = parser_factory("objc/default")

    element = parser.api_reference.find("OnTrafficEventCallback", kind="block", lang="objc")
    assert element is not None
    assert element.kind == "block"
    assert element.language == "objc"
    assert element.name == "OnTrafficEventCallback"
    assert element.full_name == "OnTrafficEventCallback"
    assert element.namespace is None

    assert element.returns is not None
    assert element.returns.type is not None
    assert element.returns.type.name == "void"
    assert element.returns.type.language == "objc"
    assert element.returns.type.namespace is None

    assert len(element.params) == 1

    param = element.params[0]
    assert param.type is not None
    assert param.type.name == "id"
    assert not param.type.prefix
    assert not param.type.suffix
    assert len(param.type.nested) == 1

    nested = param.type.nested[0]
    assert nested.name == "ADTrafficEvent"


@pytest.fixture(params=[
    "",
    "nullable ",
    "const ",
    "__weak ",
    "__strong ",
    "nullable __weak ",
    "nullable __strong ",
])
def objc_type_prefix(request):
    return request.param


@pytest.fixture(params=["", " *", " **", " * *"])
def objc_type_suffix(request):
    return request.param


def test_parse_objc_type_from_text_simple(objc_type_prefix, objc_type_suffix):
    parser = DoxygenXmlParser()
    objc = ObjectiveCLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = f"{objc_type_prefix}NSInteger{objc_type_suffix}"

    type_ref = objc.parse_type(type_element)
    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "objc"
    assert type_ref.name == "NSInteger"
    assert_equal_or_none_if_empty(type_ref.prefix, objc_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, objc_type_suffix)
    assert len(type_ref.nested) == 0


@pytest.mark.parametrize("type_with_space", [
    "short int", "signed short", "signed short int", "unsigned short", "unsigned short int",
    "signed int", "signed", "unsigned", "unsigned int", "long int", "signed long",
    "signed long int", "unsigned long", "unsigned long int", "long long", "long long int",
    "signed long long", "signed long long int", "unsigned long long", "unsigned long long int",
    "signed char", "long double"
])
def test_parse_objc_type_with_space(type_with_space):
    parser = DoxygenXmlParser()
    objc = ObjectiveCLanguage(parser)

    type_element = ET.Element("type")
    type_element.text = type_with_space

    type_ref = objc.parse_type(type_element)
    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "objc"
    assert type_ref.name == type_with_space
    assert type_ref.prefix is None
    assert type_ref.suffix is None
