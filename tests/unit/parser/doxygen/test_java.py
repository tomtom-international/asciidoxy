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
"""Tests for parsing Java from Doxygen XML files."""

import pytest
from pytest import param

from tests.unit.matchers import (
    AtLeast,
    IsEmpty,
    IsFalse,
    SizeIs,
    Unordered,
    m_compound,
    m_parameter,
    m_returnvalue,
    m_typeref,
)


@pytest.mark.parametrize("api_reference_set", [["java/default"]], ids=[""])
@pytest.mark.parametrize("search_params,matcher", [
    param(dict(name="com.asciidoxy.geometry.Coordinate", kind="class", lang="java"),
          m_compound(
              id="java-classcom_1_1asciidoxy_1_1geometry_1_1_coordinate",
              name="Coordinate",
              full_name="com.asciidoxy.geometry.Coordinate",
              language="java",
              kind="class",
              brief="Class to hold information about a coordinate.",
              description="A coordinate has a latitude, longitude, and an altitude.",
              namespace="com.asciidoxy.geometry",
              members=Unordered(
                  m_compound(name="Coordinate"),
                  m_compound(name="Latitude"),
                  m_compound(name="Longitude"),
                  m_compound(name="Altitude"),
                  m_compound(name="IsValid"),
                  m_compound(name="latitude_"),
                  m_compound(name="longitude_"),
                  m_compound(name="altitude_"),
              ),
          ),
          id="Basic class"),
    param(dict(name="com.asciidoxy.traffic.TrafficEvent", kind="class", lang="java"),
          m_compound(
              id="java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event",
              namespace="com.asciidoxy.traffic",
              members=AtLeast(
                  m_compound(
                      kind="enum",
                      full_name="com.asciidoxy.traffic.TrafficEvent.Severity",
                      namespace="com.asciidoxy.traffic.TrafficEvent",
                      language="java",
                      id="java-enumcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_1_1_severity",
                      prot="public",
                  ),
                  m_compound(
                      kind="class",
                      full_name="com.asciidoxy.traffic.TrafficEvent.TrafficEventData",
                      namespace="com.asciidoxy.traffic.TrafficEvent",
                      id=("java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_1_1_"
                          "traffic_event_data"),
                      language="java",
                      prot="public",
                  ),
              ),
          ),
          id="Class with nested class and enum"),
    param(dict(name="com.asciidoxy.traffic.TrafficEvent.Update", kind="function", lang="java"),
          m_compound(
              id=("java-classcom_1_1asciidoxy_1_1traffic_1_1_traffic_event_"
                  "1a72847da5fa4e03763f089c5d044085d4"),
              name="Update",
              full_name="com.asciidoxy.traffic.TrafficEvent.Update",
              language="java",
              kind="function",
              definition="boolean com.asciidoxy.traffic.TrafficEvent.Update",
              args="(int cause, int delay)",
              brief="Update the traffic event data.",
              description="Verifies the new information before updating.",
              prot="public",
              static=IsFalse(),
              namespace="com.asciidoxy.traffic.TrafficEvent",
              params=SizeIs(2),
              exceptions=IsEmpty(),
              returns=m_returnvalue(
                  description="True if the update is valid.",
                  type=m_typeref(
                      id=IsEmpty(),
                      kind=IsEmpty(),
                      language="java",
                      name="boolean",
                      namespace="com.asciidoxy.traffic.TrafficEvent",
                      prefix=IsEmpty(),
                      suffix=IsEmpty(),
                      nested=IsEmpty(),
                  ),
              ),
          ),
          id="Method"),
    param(dict(name="com.asciidoxy.Nullability.getData", kind="function", lang="java"),
          m_compound(returns=m_returnvalue(type=m_typeref(
              prefix="@Nullable ",
              name="DataClass",
          ), ), ),
          id="Method with return type annotation"),
    param(dict(name="com.asciidoxy.Nullability.setData", kind="function", lang="java"),
          m_compound(params=[
              m_parameter(type=m_typeref(
                  prefix="@Nullable ",
                  name="DataClass",
              ), ),
          ], ),
          id="Method with parameter type annotation"),
])
def test_parse_java(api_reference, search_params, matcher):
    matcher.assert_matches(api_reference.find(**search_params))
