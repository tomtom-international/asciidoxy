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
"""Tests for parsing python from Doxygen XML files."""

import pytest
from pytest import param

from tests.unit.matchers import (
    AtLeast,
    IsEmpty,
    IsFalse,
    IsNone,
    IsTrue,
    Unordered,
    m_compound,
    m_parameter,
    m_returnvalue,
    m_typeref,
)


@pytest.mark.parametrize("api_reference_set", [["python/default"]], ids=[""])
@pytest.mark.parametrize(
    "search_params,matcher",
    [
        param(dict(name="asciidoxy.geometry.Coordinate", kind="class", lang="python"),
              m_compound(
                  id="python-classasciidoxy_1_1geometry_1_1_coordinate",
                  name="Coordinate",
                  full_name="asciidoxy.geometry.Coordinate",
                  language="python",
                  kind="class",
                  brief="Class to hold information about a coordinate.",
                  description="A coordinate has a latitude, longitude, and an altitude.",
                  namespace="asciidoxy.geometry",
                  members=Unordered(
                      m_compound(name="altitude"),
                      m_compound(name="latitude"),
                      m_compound(name="longitude"),
                      m_compound(name="is_valid"),
                      m_compound(name="__init__"),
                      m_compound(name="from_string"),
                      m_compound(name="combine"),
                      m_compound(name="from_string_safe"),
                  ),
              ),
              id="Class"),
        param(dict(name="asciidoxy.traffic.TrafficEvent", kind="class", lang="python"),
              m_compound(
                  id="python-classasciidoxy_1_1traffic_1_1_traffic_event",
                  namespace="asciidoxy.traffic",
                  members=AtLeast(
                      m_compound(
                          kind="class",
                          full_name="asciidoxy.traffic.TrafficEvent.Severity",
                          namespace="asciidoxy.traffic.TrafficEvent",
                          language="python",
                          id="python-classasciidoxy_1_1traffic_1_1_traffic_event_1_1_severity",
                          prot="public",
                      ),
                      m_compound(
                          kind="class",
                          full_name="asciidoxy.traffic.TrafficEvent.TrafficEventData",
                          namespace="asciidoxy.traffic.TrafficEvent",
                          id=("python-classasciidoxy_1_1traffic_1_1_traffic_event_1_1_"
                              "traffic_event_data"),
                          language="python",
                          prot="public",
                      ),
                  ),
              ),
              id="Class with nested classes"),
        param(
            dict(name="asciidoxy.traffic.TrafficEvent.update", kind="function", lang="python"),
            m_compound(
                id=("python-classasciidoxy_1_1traffic_1_1_traffic_event_"
                    "1a3eb310fb6cb4929eabe8eea356e59f2e"),
                name="update",
                full_name="asciidoxy.traffic.TrafficEvent.update",
                language="python",
                kind="function",
                definition=" bool asciidoxy.traffic.TrafficEvent.update",
                args="(self, int cause, int delay)",
                brief="Update the traffic event data.",
                # TODO: See if we can improve here, even though it is already in Doxygen.
                description="""\
----
   Verifies the new information before updating.
----""",
                prot="public",
                static=IsFalse(),
                namespace="asciidoxy.traffic.TrafficEvent",
                params=[
                    m_parameter(
                        type=m_typeref(name="self"),
                        name=IsEmpty(),
                        description=IsEmpty(),
                        default_value=IsEmpty(),
                    ),
                    m_parameter(
                        type=m_typeref(name="int"),
                        name="cause",
                        default_value=IsEmpty(),
                        description="New TPEG cause code.",
                    ),
                    m_parameter(
                        type=m_typeref(name="int"),
                        name="delay",
                        default_value=IsEmpty(),
                        description="New delay in seconds.",
                    ),
                ],
                exceptions=IsEmpty(),
                returns=m_returnvalue(
                    description="True if the update is valid.",
                    type=m_typeref(
                        id=IsEmpty(),
                        kind=IsEmpty(),
                        language="python",
                        name="bool",
                        namespace="asciidoxy.traffic.TrafficEvent",
                        prefix=IsEmpty(),
                        suffix=IsEmpty(),
                        nested=IsEmpty(),
                    ),
                ),
            ),
            id="Method"),
        param(dict(name="asciidoxy.geometry.Coordinate.from_string", kind="function",
                   lang="python"),
              m_compound(
                  id=("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a993b41d0a7518e83d751aa90e0d15fbe"),
                  name="from_string",
                  prot="public",
                  static=IsFalse(),
                  params=[
                      m_parameter(
                          type=m_typeref(name="cls", ),
                          name=IsEmpty(),
                          description=IsEmpty(),
                      ),
                      m_parameter(
                          type=m_typeref(name="str", ),
                          name="value",
                          description=IsEmpty(),
                      ),
                  ],
                  returns=m_returnvalue(
                      type=m_typeref(
                          id="python-classasciidoxy_1_1geometry_1_1_coordinate",
                          kind="class",
                          language="python",
                          name="Coordinate",
                          namespace="asciidoxy.geometry.Coordinate",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                          nested=IsEmpty(),
                      ),
                      description=IsEmpty(),
                  ),
              ),
              id="Class method"),
        param(dict(name="asciidoxy.geometry.Coordinate.combine", kind="function", lang="python"),
              m_compound(
                  id=("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a4b820d9d0bdf81ddd7e22c243a41421d"),
                  name="combine",
                  prot="public",
                  static=IsTrue(),
                  params=[
                      m_parameter(
                          type=m_typeref(name="Coordinate"),
                          name="left",
                          description=IsEmpty(),
                      ),
                      m_parameter(
                          type=m_typeref(name="Coordinate"),
                          name="right",
                          description=IsEmpty(),
                      ),
                  ],
              ),
              id="Static method"),
        param(
            dict(name="asciidoxy.geometry.Coordinate.longitude", kind="variable", lang="python"),
            m_compound(
                id=("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                    "1a0eb652e91c894dc2e49d9fbf3f224aa5"),
                name="longitude",
                prot="public",
                static=IsFalse(),
                params=IsEmpty(),
                exceptions=IsEmpty(),
                # Not supported by Doxygen yet
                # returns=m_returnvalue(
                #     type=m_typeref(
                #         id=IsEmpty(),
                #         kind=IsEmpty(),
                #         language="python",
                #         name="float",
                #         namespace="asciidoxy.geometry.Coordinate",
                #         prefix=IsEmpty(),
                #         suffix=IsEmpty(),
                #         nested=IsEmpty(),
                #         description=IsEmpty(),
                #     ),
                # ),
            ),
            id="Variable"),
        param(dict(name="asciidoxy.geometry.Coordinate.__init__", kind="function", lang="python"),
              m_compound(
                  id=("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1ae2c5561a335e7d226ae84bd561abb95f"),
                  name="__init__",
                  full_name="asciidoxy.geometry.Coordinate.__init__",
                  language="python",
                  kind="function",
                  definition="def asciidoxy.geometry.Coordinate.__init__",
                  args="(self)",
                  brief=IsEmpty(),
                  description=IsEmpty(),
                  prot="public",
                  static=IsFalse(),
                  namespace="asciidoxy.geometry.Coordinate",
                  params=[
                      m_parameter(
                          type=m_typeref(name="self"),
                          name=IsEmpty(),
                          description=IsEmpty(),
                      ),
                  ],
                  exceptions=IsEmpty(),
                  returns=IsNone(),
              ),
              id="Constructor"),
        param(dict(
            name="asciidoxy.geometry.Coordinate.from_string_safe", kind="function", lang="python"),
              m_compound(
                  id=("python-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a6711de457ebaf61c48358c2d2a37dbfa"),
                  name="from_string_safe",
                  prot="public",
                  static=IsFalse(),
                  params=[
                      m_parameter(
                          type=m_typeref(name="cls"),
                          name=IsEmpty(),
                          description=IsEmpty(),
                      ),
                      m_parameter(
                          type=m_typeref(
                              name="Optional",
                              nested=[
                                  m_typeref(name="str"),
                              ],
                          ),
                          name="value",
                          description=IsEmpty(),
                      ),
                  ],
                  exceptions=IsEmpty(),
                  returns=m_returnvalue(
                      type=m_typeref(
                          id=IsEmpty(),
                          kind=IsEmpty(),
                          language="python",
                          name="Optional",
                          namespace="asciidoxy.geometry.Coordinate",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                          nested=[
                              m_typeref(
                                  name="Coordinate",
                                  namespace="asciidoxy.geometry.Coordinate",
                              ),
                          ],
                      ),
                      description=IsEmpty(),
                  ),
              ),
              id="Nested argument and return type"),
        param(dict(name="asciidoxy.default_values.Point.__init__"),
              m_compound(params=[
                  m_parameter(
                      name=IsEmpty(),
                      default_value=IsEmpty(),
                  ),
                  m_parameter(
                      name="x",
                      default_value="0",
                  ),
                  m_parameter(
                      name="y",
                      default_value="1",
                  ),
              ], ),
              id="Constructor with default parameter values"),
        param(dict(name="asciidoxy.default_values.Point.increment"),
              m_compound(params=[
                  m_parameter(
                      name=IsEmpty(),
                      default_value=IsEmpty(),
                  ),
                  m_parameter(
                      name="x",
                      default_value="2",
                  ),
                  m_parameter(
                      name="y",
                      default_value="3",
                  ),
              ], ),
              id="Method with default parameter values"),
    ])
def test_parse_python(api_reference, search_params, matcher):
    matcher.assert_matches(api_reference.find(**search_params))
