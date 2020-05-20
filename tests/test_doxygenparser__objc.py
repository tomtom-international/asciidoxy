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


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_interface(api_reference):
    objc_class = api_reference.find("ADCoordinate", kind="class", lang="objc")
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


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_protocol(api_reference):
    objc_class = api_reference.find("ADTrafficEvent", kind="protocol", lang="objc")
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


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_member_function(api_reference):
    member = api_reference.find("ADTrafficEvent.updateWithCause:andDelay:",
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


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_block(api_reference):
    element = api_reference.find("OnTrafficEventCallback", kind="block", lang="objc")
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
