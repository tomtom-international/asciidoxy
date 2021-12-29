# Copyright (C) 2019, TomTom (http://tomtom.com).
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
from pytest import param

from asciidoxy.parser.doxygen.objc import ObjectiveCTraits
from tests.unit.matchers import (
    IsEmpty,
    IsFalse,
    IsNone,
    Unordered,
    m_compound,
    m_parameter,
    m_returnvalue,
    m_typeref,
)


@pytest.mark.parametrize("api_reference_set", [["objc/default"]], ids=[""])
@pytest.mark.parametrize("search_params,matcher", [
    param(dict(name="ADCoordinate", kind="class", lang="objc"),
          m_compound(
              id="objc-interface_a_d_coordinate",
              name="ADCoordinate",
              full_name="ADCoordinate",
              language="objc",
              kind="class",
              brief="Class to hold information about a coordinate.",
              description="A coordinate has a latitude, longitude, and an altitude.",
              include="ADCoordinate.h",
              namespace=IsNone(),
              members=Unordered(
                  m_compound(name="latitude"),
                  m_compound(name="longitude"),
                  m_compound(name="altitude"),
                  m_compound(name="isValid"),
                  m_compound(name="init"),
              ),
          ),
          id="Interface"),
    param(dict(name="ADTrafficEvent", kind="protocol", lang="objc"),
          m_compound(
              id="objc-protocol_a_d_traffic_event-p",
              name="ADTrafficEvent",
              full_name="ADTrafficEvent",
              language="objc",
              kind="protocol",
              brief="Information about a traffic event.",
              description=IsEmpty(),
              namespace=IsNone(),
              members=Unordered(
                  m_compound(name="data"),
                  m_compound(name="updateWithCause:andDelay:"),
              ),
          ),
          id="Protocol"),
    param(dict(name="ADTrafficEvent.updateWithCause:andDelay:", kind="function", lang="objc"),
          m_compound(
              id="objc-protocol_a_d_traffic_event-p_1aaa32145fd9b5ebec01740ac078738262",
              name="updateWithCause:andDelay:",
              full_name="ADTrafficEvent.updateWithCause:andDelay:",
              language="objc",
              kind="function",
              definition="id ADTrafficEvent-p::updateWithCause:andDelay:",
              args="(NSInteger cause,[andDelay] NSInteger delay)",
              brief="Update the traffic event data.",
              description="Verifies the new information before updating.",
              prot="public",
              static=IsFalse(),
              namespace="ADTrafficEvent",
              params=[
                  m_parameter(
                      name="cause",
                      description="New TPEG cause code.",
                      type=m_typeref(
                          id=IsEmpty(),
                          kind=IsEmpty(),
                          language="objc",
                          name="NSInteger",
                          namespace="ADTrafficEvent",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                          nested=IsEmpty(),
                      ),
                  ),
                  m_parameter(
                      name="delay",
                      description="New delay in seconds.",
                      type=m_typeref(
                          id=IsEmpty(),
                          kind=IsEmpty(),
                          language="objc",
                          name="NSInteger",
                          namespace="ADTrafficEvent",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                          nested=IsEmpty(),
                      ),
                  ),
              ],
          ),
          id="Method"),
    param(dict(name="OnTrafficEventCallback", kind="block", lang="objc"),
          m_compound(
              kind="block",
              language="objc",
              name="OnTrafficEventCallback",
              full_name="OnTrafficEventCallback",
              namespace=IsNone(),
              returns=m_returnvalue(type=m_typeref(
                  name=IsEmpty(),
                  language="objc",
                  namespace=IsNone(),
                  args=[
                      m_parameter(
                          name=IsEmpty(),
                          type=m_typeref(
                              name="id",
                              prefix=IsEmpty(),
                              suffix=IsEmpty(),
                              nested=[
                                  m_typeref(name="ADTrafficEvent"),
                              ],
                          ),
                      ),
                      m_parameter(
                          name="delay",
                          type=m_typeref(
                              name="NSInteger",
                              prefix=IsEmpty(),
                              suffix=IsEmpty(),
                              nested=IsEmpty(),
                          ),
                      ),
                  ],
              ), ),
          ),
          id="Block"),
    param(dict(name="TrafficEventData", kind="class", lang="objc"),
          m_compound(
              id="objc-interface_traffic_event_data",
              name="TrafficEventData",
              full_name="TrafficEventData",
              language="objc",
              kind="class",
              include="ADTrafficEvent.h",
              namespace=IsNone(),
              prot="public",
              brief="Details about a traffic event.",
              description="Use the cause and delay to properly inform your users.",
              members=Unordered(
                  m_compound(
                      id="objc-interface_traffic_event_data_1a2b685c89f864a1bc00a329d00ce0b273",
                      name="ADSeverity",
                      full_name="ADSeverity",
                      language="objc",
                      kind="enum",
                      include="ADTrafficEvent.h",
                      namespace=IsNone(),
                      prot="public",
                      brief="Severity scale for traffic events.",
                      description="The more severe the traffic event, the more likely it is to "
                      "have a large delay.",
                      members=Unordered(
                          m_compound(
                              id="objc-interface_traffic_event_data_"
                              "1a2b685c89f864a1bc00a329d00ce0b273a2e99d30bdeb60d88efab9c1f1b0f941d",
                              name="ADSeverityLow",
                              full_name="ADSeverityLow",
                              language="objc",
                              kind="enumvalue",
                              brief="Low severity.",
                              description=IsEmpty(),
                              initializer="= 1",
                              prot="public",
                          ),
                          m_compound(
                              id="objc-interface_traffic_event_data_"
                              "1a2b685c89f864a1bc00a329d00ce0b273a30638ab30516654ec0bc609510e92f38",
                              name="ADSeverityMedium",
                              full_name="ADSeverityMedium",
                              language="objc",
                              kind="enumvalue",
                              brief="Medium severity.",
                              description=IsEmpty(),
                              initializer="= 2",
                              prot="public",
                          ),
                          m_compound(
                              id="objc-interface_traffic_event_data_"
                              "1a2b685c89f864a1bc00a329d00ce0b273ae0df39be1faf7f462fac153063744958",
                              name="ADSeverityHigh",
                              full_name="ADSeverityHigh",
                              language="objc",
                              kind="enumvalue",
                              brief="High severity.",
                              description="Better stay away here.",
                              initializer="= 3",
                              prot="public",
                          ),
                          m_compound(
                              id="objc-interface_traffic_event_data_"
                              "1a2b685c89f864a1bc00a329d00ce0b273a505a6b31acd5b18078487c3ddad40701",
                              name="ADSeverityUnknown",
                              full_name="ADSeverityUnknown",
                              language="objc",
                              kind="enumvalue",
                              brief="Severity unknown.",
                              description=IsEmpty(),
                              initializer="= 4",
                              prot="public",
                          ),
                      ),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_1a8353496d09d78db82e9e62f8c2808d34",
                      name="cause",
                      full_name="TrafficEventData.cause",
                      language="objc",
                      kind="variable",
                      include="ADTrafficEvent.h",
                      namespace="TrafficEventData",
                      prot="protected",
                      brief="TPEG cause code.",
                      description=IsEmpty(),
                      definition="TpegCauseCode TrafficEventData::cause",
                      returns=m_returnvalue(type=m_typeref(
                          id="objc-_a_d_traffic_event_8h_1a929385fc78158cf2be0d44416a5df884",
                          name="TpegCauseCode",
                          language="objc",
                          namespace="TrafficEventData",
                          kind="typedef",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                      )),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_1ab4a315c870a75cc68f5bba648b9b8be0",
                      name="delay",
                      full_name="TrafficEventData.delay",
                      language="objc",
                      kind="variable",
                      include="ADTrafficEvent.h",
                      namespace="TrafficEventData",
                      prot="protected",
                      brief="Delay caused by the traffic event in seconds.",
                      description=IsEmpty(),
                      definition="NSInteger TrafficEventData::delay",
                      returns=m_returnvalue(type=m_typeref(
                          id=IsNone(),
                          name="NSInteger",
                          language="objc",
                          namespace="TrafficEventData",
                          kind=IsNone(),
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                      )),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_1a3136b600b8d16811c66914ff3afa48ca",
                      name="severity",
                      full_name="TrafficEventData.severity",
                      language="objc",
                      kind="variable",
                      include="ADTrafficEvent.h",
                      namespace="TrafficEventData",
                      prot="protected",
                      brief="Severity of the event.",
                      description="",
                      definition="Severity TrafficEventData::severity",
                      returns=m_returnvalue(type=m_typeref(
                          id=IsNone(),
                          name="Severity",
                          language="objc",
                          namespace="TrafficEventData",
                          kind=IsNone(),
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                      )),
                  ),
              ),
          ),
          id="Nested types"),
    param(dict(name="ADSeverity", kind="enum", lang="objc"),
          m_compound(
              id="objc-interface_traffic_event_data_1a2b685c89f864a1bc00a329d00ce0b273",
              name="ADSeverity",
              full_name="ADSeverity",
              language="objc",
              kind="enum",
              include="ADTrafficEvent.h",
              namespace=IsNone(),
              prot="public",
              brief="Severity scale for traffic events.",
              description="The more severe the traffic event, the more likely it is to have a "
              "large delay.",
              members=[
                  m_compound(
                      id="objc-interface_traffic_event_data_"
                      "1a2b685c89f864a1bc00a329d00ce0b273a2e99d30bdeb60d88efab9c1f1b0f941d",
                      name="ADSeverityLow",
                      full_name="ADSeverityLow",
                      language="objc",
                      kind="enumvalue",
                      brief="Low severity.",
                      description=IsEmpty(),
                      initializer="= 1",
                      prot="public",
                      namespace=IsNone(),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_"
                      "1a2b685c89f864a1bc00a329d00ce0b273a30638ab30516654ec0bc609510e92f38",
                      name="ADSeverityMedium",
                      full_name="ADSeverityMedium",
                      language="objc",
                      kind="enumvalue",
                      brief="Medium severity.",
                      description=IsEmpty(),
                      initializer="= 2",
                      prot="public",
                      namespace=IsNone(),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_"
                      "1a2b685c89f864a1bc00a329d00ce0b273ae0df39be1faf7f462fac153063744958",
                      name="ADSeverityHigh",
                      full_name="ADSeverityHigh",
                      language="objc",
                      kind="enumvalue",
                      brief="High severity.",
                      description="Better stay away here.",
                      initializer="= 3",
                      prot="public",
                      namespace=IsNone(),
                  ),
                  m_compound(
                      id="objc-interface_traffic_event_data_"
                      "1a2b685c89f864a1bc00a329d00ce0b273a505a6b31acd5b18078487c3ddad40701",
                      name="ADSeverityUnknown",
                      full_name="ADSeverityUnknown",
                      language="objc",
                      kind="enumvalue",
                      brief="Severity unknown.",
                      description=IsEmpty(),
                      initializer="= 4",
                      prot="public",
                      namespace=IsNone(),
                  ),
              ],
          ),
          id="Ignore nesting for enums"),
    param(dict(name="ADSeverityLow", kind="enumvalue", lang="objc"),
          m_compound(
              id="objc-interface_traffic_event_data_"
              "1a2b685c89f864a1bc00a329d00ce0b273a2e99d30bdeb60d88efab9c1f1b0f941d",
              name="ADSeverityLow",
              full_name="ADSeverityLow",
              language="objc",
              kind="enumvalue",
              brief="Low severity.",
              description="",
              initializer="= 1",
              prot="public",
              namespace=IsNone(),
          ),
          id="Ignore nesting for enum values"),
])
def test_parse_objc(api_reference, search_params, matcher):
    matcher.assert_matches(api_reference.find(**search_params))


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
