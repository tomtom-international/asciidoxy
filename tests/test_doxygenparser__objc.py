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

from asciidoxy.model import Compound, EnumValue
from asciidoxy.parser.doxygen.objc import ObjectiveCTraits


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
    assert not param.type.nested
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
    assert not param.type.nested
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

    block_type = element.returns.type
    assert not block_type.name
    assert block_type.language == "objc"
    assert block_type.namespace is None
    assert len(block_type.args) == 2

    assert block_type.returns is not None
    assert block_type.returns.name == "void"
    assert block_type.returns.language == "objc"
    assert block_type.returns.namespace is None
    assert not block_type.returns.args

    arg = block_type.args[0]
    assert not arg.name
    assert arg.type is not None
    assert arg.type.name == "id"
    assert not arg.type.prefix
    assert not arg.type.suffix
    assert len(arg.type.nested) == 1

    nested = arg.type.nested[0]
    assert nested.name == "ADTrafficEvent"

    arg = block_type.args[1]
    assert arg.name == "delay"
    assert arg.type is not None
    assert arg.type.name == "NSInteger"
    assert not arg.type.prefix
    assert not arg.type.suffix
    assert not arg.type.nested


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_enum__ignore_nesting(api_reference):
    element = api_reference.find("ADSeverity", kind="enum", lang="objc")
    assert element == Compound(
        id="objc-interface_traffic_event_data_1a2b685c89f864a1bc00a329d00ce0b273",
        name="ADSeverity",
        full_name="ADSeverity",
        language="objc",
        kind="enum",
        include="ADTrafficEvent.h",
        namespace=None,
        prot="protected",
        brief="Severity scale for traffic events.",
        description=  # noqa: E251
        "The more severe the traffic event, the more likely it is to have a large delay.",
        enumvalues=[
            EnumValue(
                id="objc-interface_traffic_event_data_"
                "1a2b685c89f864a1bc00a329d00ce0b273a2e99d30bdeb60d88efab9c1f1b0f941d",
                name="ADSeverityLow",
                full_name="ADSeverityLow",
                language="objc",
                kind="enumvalue",
                brief="Low severity.",
                description="",
                initializer="= 1",
            ),
            EnumValue(
                id="objc-interface_traffic_event_data_"
                "1a2b685c89f864a1bc00a329d00ce0b273a30638ab30516654ec0bc609510e92f38",
                name="ADSeverityMedium",
                full_name="ADSeverityMedium",
                language="objc",
                kind="enumvalue",
                brief="Medium severity.",
                description="",
                initializer="= 2",
            ),
            EnumValue(
                id="objc-interface_traffic_event_data_"
                "1a2b685c89f864a1bc00a329d00ce0b273ae0df39be1faf7f462fac153063744958",
                name="ADSeverityHigh",
                full_name="ADSeverityHigh",
                language="objc",
                kind="enumvalue",
                brief="High severity.",
                description="Better stay away here.",
                initializer="= 3",
            ),
            EnumValue(
                id="objc-interface_traffic_event_data_"
                "1a2b685c89f864a1bc00a329d00ce0b273a505a6b31acd5b18078487c3ddad40701",
                name="ADSeverityUnknown",
                full_name="ADSeverityUnknown",
                language="objc",
                kind="enumvalue",
                brief="Severity unknown.",
                description="",
                initializer="= 4",
            ),
        ],
    )


@pytest.mark.parametrize("api_reference_set", [["objc/default"]])
def test_parse_objc_enum_value__ignore_nesting(api_reference):
    element = api_reference.find("ADSeverityLow", kind="enumvalue", lang="objc")
    assert element == EnumValue(
        id="objc-interface_traffic_event_data_"
        "1a2b685c89f864a1bc00a329d00ce0b273a2e99d30bdeb60d88efab9c1f1b0f941d",
        name="ADSeverityLow",
        full_name="ADSeverityLow",
        language="objc",
        kind="enumvalue",
        brief="Low severity.",
        description="",
        initializer="= 1",
    )


@pytest.mark.parametrize("kind", [None, "", "function", "variable"])
def test_traits__full_name__add_parent_as_namespace(kind):
    assert ObjectiveCTraits.full_name("name", "parent", kind) == "parent.name"


@pytest.mark.parametrize("kind", ["enum", "enumvalue", "interface", "protocol"])
def test_traits__full_name__do_not_add_parent_as_namespace(kind):
    assert ObjectiveCTraits.full_name("name", "parent", kind) == "name"


def test_traits__full_name__no_parent():
    assert ObjectiveCTraits.full_name("name") == "name"
    assert ObjectiveCTraits.full_name("name", "") == "name"


def test_traits__full_name__parent_already_in_namespace():
    assert ObjectiveCTraits.full_name("parent.name", "parent") == "parent.name"


@pytest.mark.parametrize("kind", [None, "", "function", "variable"])
def test_traits__namespace(kind):
    assert ObjectiveCTraits.namespace("name", kind) is None
    assert ObjectiveCTraits.namespace("parent.name", kind) == "parent"
    assert ObjectiveCTraits.namespace("root.parent.name", kind) == "root.parent"


@pytest.mark.parametrize("kind", ["enum", "enumvalue", "interface", "protocol"])
def test_traits__namespace__ignored(kind):
    assert ObjectiveCTraits.namespace("name", kind) is None
    assert ObjectiveCTraits.namespace("parent.name", kind) is None
    assert ObjectiveCTraits.namespace("root.parent.name", kind) is None
