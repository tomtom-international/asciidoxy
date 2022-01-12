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
"""Tests for parsing C++ from Doxygen XML files."""

import pytest
from pytest import param

from tests.unit.matchers import (
    AtLeast,
    HasNot,
    IsEmpty,
    IsFalse,
    IsNone,
    IsNotEmpty,
    IsTrue,
    SizeIs,
    Unordered,
    m_compound,
    m_parameter,
    m_returnvalue,
    m_throwsclause,
    m_typeref,
)


@pytest.mark.parametrize("api_reference_set", [["cpp/default"]], ids=[""])
@pytest.mark.parametrize("search_params,matcher", [
    param(dict(name="asciidoxy::geometry::Coordinate", kind="class", lang="cpp"),
          m_compound(
              id="cpp-classasciidoxy_1_1geometry_1_1_coordinate",
              name="Coordinate",
              full_name="asciidoxy::geometry::Coordinate",
              language="cpp",
              kind="class",
              brief="Class to hold information about a coordinate.",
              description="A coordinate has a latitude, longitude, and an altitude.",
              include="coordinate.hpp",
              namespace="asciidoxy::geometry",
              members=Unordered(
                  m_compound(name="longitude_"),
                  m_compound(name="latitude_"),
                  m_compound(name="altitude_"),
                  m_compound(name="Coordinate"),
                  m_compound(name="~Coordinate"),
                  m_compound(name="operator+"),
                  m_compound(name="Latitude"),
                  m_compound(name="Longitude"),
                  m_compound(name="Altitude"),
                  m_compound(name="IsValid"),
                  m_compound(name="Update"),
                  m_compound(name="Update"),
                  m_compound(name="Update"),
                  m_compound(name="Update"),
                  m_compound(name="Update"),
              ),
          ),
          id="Basic class"),
    param(dict(name="asciidoxy::traffic::TrafficEvent", kind="class", lang="cpp"),
          m_compound(
              id="cpp-classasciidoxy_1_1traffic_1_1_traffic_event",
              namespace="asciidoxy::traffic",
              members=AtLeast(
                  m_compound(
                      kind="struct",
                      full_name="asciidoxy::traffic::TrafficEvent::TrafficEventData",
                      namespace="asciidoxy::traffic::TrafficEvent",
                      id="cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1_traffic_event_data",
                      language="cpp",
                      prot="public",
                  )),
          ),
          id="Class with nested class"),
    param(dict(name="asciidoxy::system::ServiceStarter", kind="class", lang="cpp"),
          m_compound(members=HasNot(m_compound(kind="friend"))),
          id="Ignore friend declarations"),
    param(dict(name="asciidoxy::geometry::Coordinate::Coordinate", kind="function", lang="cpp"),
          m_compound(
              id=("cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                  "1a69ac21cad618c0c033815f2cbdc86318"),
              name="Coordinate",
              full_name="asciidoxy::geometry::Coordinate::Coordinate",
              language="cpp",
              kind="function",
              definition="asciidoxy::geometry::Coordinate::Coordinate",
              args="()",
              brief="Default constructor.",
              description=IsEmpty(),
              prot="public",
              static=IsFalse(),
              include="coordinate.hpp",
              namespace="asciidoxy::geometry::Coordinate",
              const=IsFalse(),
              params=IsEmpty(),
              exceptions=IsEmpty(),
              returns=IsNone(),
          ),
          id="Method without return value"),
    param(dict(name="asciidoxy::geometry::Coordinate::IsValid", kind="function", lang="cpp"),
          m_compound(
              id="cpp-classasciidoxy_1_1geometry_1_1_coordinate_1a8d7e0eac29549fa4666093e36914deac",
              name="IsValid",
              full_name="asciidoxy::geometry::Coordinate::IsValid",
              language="cpp",
              kind="function",
              definition="bool asciidoxy::geometry::Coordinate::IsValid",
              args="() const",
              brief="Check if the coordinate is valid.",
              description="A coordinate is valid if its values are within WGS84 bounds.",
              prot="public",
              static=IsFalse(),
              include="coordinate.hpp",
              namespace="asciidoxy::geometry::Coordinate",
              const=IsTrue(),
              params=IsEmpty(),
              exceptions=IsEmpty(),
              returns=m_returnvalue(
                  description="True if valid, false if not.",
                  type=m_typeref(
                      id=IsNone(),
                      kind=IsNone(),
                      language="cpp",
                      name="bool",
                      prefix=IsEmpty(),
                      suffix=IsEmpty(),
                      nested=IsEmpty(),
                      namespace="asciidoxy::geometry::Coordinate",
                  ),
              ),
          ),
          id="Method with only a return value"),
    param(
        dict(name="asciidoxy::traffic::TrafficEvent::Update", kind="function", lang="cpp"),
        m_compound(
            id="cpp-classasciidoxy_1_1traffic_1_1_traffic_event_1a829eda83200a17d2d2f8a5fced5f000b",
            name="Update",
            full_name="asciidoxy::traffic::TrafficEvent::Update",
            language="cpp",
            kind="function",
            definition="bool asciidoxy::traffic::TrafficEvent::Update",
            args="(int cause, int delay)",
            brief="Update the traffic event data.",
            description="Verifies the new information before updating.",
            prot="public",
            static=IsFalse(),
            include="traffic_event.hpp",
            namespace="asciidoxy::traffic::TrafficEvent",
            const=IsFalse(),
            exceptions=IsEmpty(),
            params=[
                m_parameter(
                    name="cause",
                    description="New TPEG cause code.",
                    default_value=IsEmpty(),
                    type=m_typeref(
                        id=IsNone(),
                        kind=IsNone(),
                        language="cpp",
                        name="int",
                        namespace="asciidoxy::traffic::TrafficEvent",
                        prefix=IsEmpty(),
                        suffix=IsEmpty(),
                        nested=IsEmpty(),
                    ),
                    kind="param",
                ),
                m_parameter(
                    name="delay",
                    description="New delay in seconds.",
                    default_value=IsEmpty(),
                    type=m_typeref(
                        id=IsNone(),
                        kind=IsNone(),
                        language="cpp",
                        name="int",
                        namespace="asciidoxy::traffic::TrafficEvent",
                        prefix=IsEmpty(),
                        suffix=IsEmpty(),
                        nested=IsEmpty(),
                    ),
                    kind="param",
                ),
            ],
            returns=m_returnvalue(
                description="True if the update is valid.",
                type=m_typeref(
                    id=IsNone(),
                    kind=IsNone(),
                    language="cpp",
                    name="bool",
                    namespace="asciidoxy::traffic::TrafficEvent",
                    prefix=IsEmpty(),
                    suffix=IsEmpty(),
                    nested=IsEmpty(),
                ),
            ),
        ),
        id="Method with parameters and return value"),
    param(dict(name="asciidoxy::traffic::TrafficEvent::SharedData", kind="function", lang="cpp"),
          m_compound(
              name="SharedData",
              namespace="asciidoxy::traffic::TrafficEvent",
              include="traffic_event.hpp",
              returns=m_returnvalue(
                  description="The shared pointer.",
                  type=m_typeref(
                      id=IsNone(),
                      kind=IsNone(),
                      language="cpp",
                      name="std::shared_ptr",
                      namespace="asciidoxy::traffic::TrafficEvent",
                      prefix=IsEmpty(),
                      suffix=IsEmpty(),
                      nested=[
                          m_typeref(
                              id=("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1"
                                  "_traffic_event_data"),
                              kind="compound",
                              language="cpp",
                              name="TrafficEventData",
                              namespace="asciidoxy::traffic::TrafficEvent",
                              prefix=IsEmpty(),
                              suffix=IsEmpty(),
                              nested=IsEmpty(),
                          ),
                      ],
                  ),
              ),
          ),
          id="Method with nested return type"),
    param(
        dict(name="asciidoxy::traffic::TrafficEvent::Severity", kind="enum", lang="cpp"),
        m_compound(
            name="Severity",
            brief="Severity scale for traffic events.",
            description=("The more severe the traffic event, the more likely it is to have a large "
                         "delay."),
            include="traffic_event.hpp",
            members=[
                m_compound(kind="enumvalue", name="Low"),
                m_compound(kind="enumvalue", name="Medium"),
                m_compound(
                    id=("cpp-classasciidoxy_1_1traffic_1_1_traffic_event_"
                        "1a47c51b1f1f014cb943377fb67ad903b9a655d20c1ca69519ca647684edbb2db35"),
                    name="High",
                    full_name="asciidoxy::traffic::TrafficEvent::Severity::High",
                    language="cpp",
                    initializer="= 3",
                    brief="High severity.",
                    description="Better stay away here.",
                    kind="enumvalue",
                    prot="public",
                ),
                m_compound(kind="enumvalue", name="Unknown"),
            ],
        ),
        id="Member enum"),
    param(dict(
        name="asciidoxy::traffic::TrafficEvent::CalculateDelay()", kind="function", lang="cpp"),
          m_compound(
              name="CalculateDelay",
              namespace="asciidoxy::traffic::TrafficEvent",
              include="traffic_event.hpp",
              exceptions=[
                  m_throwsclause(
                      type=m_typeref(
                          name="std::runtime_exception",
                          namespace="asciidoxy::traffic::TrafficEvent",
                      ),
                      description="Thrown when the update encounters a critical error.",
                  ),
              ],
          ),
          id="Method throwing an exception"),
    param(
        dict(name="asciidoxy::traffic::TrafficEvent::RegisterTrafficCallback",
             kind="function",
             lang="cpp"),
        m_compound(
            name="RegisterTrafficCallback",
            namespace="asciidoxy::traffic::TrafficEvent",
            include="traffic_event.hpp",
            params=[
                m_parameter(
                    name="callback",
                    description="A function to call on updates.",
                    type=m_typeref(
                        id=IsEmpty(),
                        prefix=IsEmpty(),
                        name="std::function",
                        suffix=IsEmpty(),
                        language="cpp",
                        namespace="asciidoxy::traffic::TrafficEvent",
                        args=IsEmpty(),
                        nested=[
                            m_typeref(
                                kind="closure",
                                id=IsEmpty(),
                                prefix=IsEmpty(),
                                name=IsEmpty(),
                                suffix=IsEmpty(),
                                nested=IsEmpty(),
                                args=[
                                    m_parameter(
                                        name=IsEmpty(),
                                        type=m_typeref(
                                            id=("cpp-structasciidoxy_1_1traffic_1_1_traffic_event_1_1"
                                                "_traffic_event_data"),
                                            prefix="const ",
                                            name="TrafficEventData",
                                            suffix=" &",
                                            nested=IsEmpty(),
                                            args=IsEmpty(),
                                        ),
                                    ),
                                    m_parameter(
                                        name="delay",
                                        type=m_typeref(
                                            id=IsEmpty(),
                                            prefix=IsEmpty(),
                                            name="int",
                                            suffix=IsEmpty(),
                                            nested=IsEmpty(),
                                            args=IsEmpty(),
                                        ),
                                    ),
                                ],
                                returns=m_typeref(
                                    id=IsEmpty(),
                                    prefix=IsEmpty(),
                                    name="void",
                                    suffix=IsEmpty(),
                                    nested=IsEmpty(),
                                    args=IsEmpty(),
                                ),
                            ),
                        ],
                    ),
                    kind="param",
                ),
            ],
        ),
        id="Method with std::function argument"),
    param(dict(name="asciidoxy::relative_namespace::InterfaceWithDetailClasses::DoSomething",
               kind="function",
               lang="cpp"),
          m_compound(params=[
              m_parameter(
                  name="text",
                  type=m_typeref(),
                  kind="param",
              ),
              m_parameter(
                  name="success_callback",
                  type=m_typeref(
                      name="std::function",
                      args=IsEmpty(),
                      nested=[
                          m_typeref(
                              name=IsEmpty(),
                              returns=m_typeref(name="void", ),
                              args=[
                                  m_parameter(
                                      name=IsEmpty(),
                                      type=m_typeref(
                                          name="std::shared_ptr",
                                          prefix="const ",
                                          suffix=" &",
                                          nested=[
                                              m_typeref(
                                                  name="detail::SuccessDescriptor",
                                                  id=IsNotEmpty(),
                                                  args=IsNone(),
                                                  nested=IsNone(),
                                              ),
                                          ],
                                      ),
                                  ),
                              ],
                          ),
                      ],
                  ),
                  kind="param",
              ),
              m_parameter(
                  name="error_callback",
                  type=m_typeref(
                      name="std::function",
                      nested=[
                          m_typeref(
                              name=IsEmpty(),
                              returns=m_typeref(name="void", ),
                              args=[
                                  m_parameter(
                                      name=IsEmpty(),
                                      type=m_typeref(
                                          name="detail::ErrorDescriptor",
                                          args=IsNone(),
                                          nested=IsNone(),
                                      ),
                                  ),
                              ],
                          ),
                      ],
                      args=IsNone(),
                  ),
                  kind="param",
              ),
          ], ),
          id="Method with complex std::function argument"),
    param(dict(
        name="asciidoxy::system::MoveOnly::MoveOnly(const MoveOnly&)", kind="function", lang="cpp"),
          m_compound(
              deleted=IsTrue(),
              default=IsFalse(),
          ),
          id="Deleted method"),
    param(dict(
        name="asciidoxy::system::MoveOnly::operator=(MoveOnly&&)", kind="function", lang="cpp"),
          m_compound(
              deleted=IsFalse(),
              default=IsTrue(),
          ),
          id="Defaulted method"),
    param(dict(name="asciidoxy::system::CreateService", kind="function", lang="cpp"),
          m_compound(include="service.hpp", ),
          id="Provide correct include file for free functions"),
    param(dict(name="asciidoxy::geometry::Point::Point", kind="function", lang="cpp"),
          m_compound(params=[
              m_parameter(
                  name="x",
                  default_value="0",
                  kind="param",
              ),
              m_parameter(
                  name="y",
                  default_value="1",
                  kind="param",
              ),
          ], ),
          id="Constructor with default parameter values"),
    param(dict(name="asciidoxy::geometry::Point::increment", kind="function", lang="cpp"),
          m_compound(params=[
              m_parameter(
                  name="x",
                  default_value="2",
                  kind="param",
              ),
              m_parameter(
                  name="y",
                  default_value="3",
                  kind="param",
              ),
          ], ),
          id="Method with default parameter values"),
    param(dict(name="ConstInt::ConstInt", kind="function", lang="cpp"),
          m_compound(
              params=SizeIs(1),
              returns=IsNone(),
              constexpr=IsTrue(),
          ),
          id="Constexpr constructor"),
    param(dict(name="asciidoxy::geometry::Coordinate::Update(double, double, double)",
               kind="function",
               lang="cpp"),
          m_compound(
              id="cpp-classasciidoxy_1_1geometry_1_1_coordinate_1a0671d16a083d785878eac6a712afa891",
              name="Update",
              full_name="asciidoxy::geometry::Coordinate::Update",
              language="cpp",
              kind="function",
              include="coordinate.hpp",
              namespace="asciidoxy::geometry::Coordinate",
              prot="public",
              definition="void asciidoxy::geometry::Coordinate::Update",
              args="(double latitude, double longitude, double altitude)",
              brief="Update from separate values.",
              sections={
                  "Precondition": "The coordinate exists.",
                  "Postcondition": "New values are used for the coordinate.",
              },
              params=[
                  m_parameter(
                      name="latitude",
                      default_value="",
                      type=m_typeref(name="double",
                                     language="cpp",
                                     namespace="asciidoxy::geometry::Coordinate",
                                     prefix=IsEmpty(),
                                     suffix=IsEmpty()),
                      kind="param",
                  ),
                  m_parameter(
                      name="longitude",
                      default_value="",
                      type=m_typeref(name="double",
                                     language="cpp",
                                     namespace="asciidoxy::geometry::Coordinate",
                                     prefix=IsEmpty(),
                                     suffix=IsEmpty()),
                      kind="param",
                  ),
                  m_parameter(
                      name="altitude",
                      default_value="",
                      type=m_typeref(name="double",
                                     language="cpp",
                                     namespace="asciidoxy::geometry::Coordinate",
                                     prefix=IsEmpty(),
                                     suffix=IsEmpty()),
                      kind="param",
                  ),
              ],
              returns=m_returnvalue(type=m_typeref(name="void",
                                                   language="cpp",
                                                   namespace="asciidoxy::geometry::Coordinate",
                                                   prefix=IsEmpty(),
                                                   suffix=IsEmpty())),
          ),
          id="Method with pre and post condition"),
    param(dict(name="asciidoxy::descriptions::Sections", kind="class", lang="cpp"),
          m_compound(
              name="Sections",
              brief="Using sections in the description.",
              description="""\
This class demonstrates how all sections supported by Doxygen are handled.

[CAUTION]
====
Be carefull with this class. It **could** blow up.
====

[NOTE]
====
Don't forget about ``this!``
====

[NOTE]
====
This class does not make much sense.
====

[WARNING]
====
Do not use this class ever!
====""",
              sections={
                  "Author": "Rob van der Most",
                  "Bug": "Not all sections may be rendered correctly.",
                  "Copyright": "MIT license.",
                  "Date": "28 August 2021",
                  "Deprecated": "This empty class should no longer be used.",
                  "Precondition": "The class should not exist yet.",
                  "Postcondition": "The class suddenly exists.",
                  "Since": "0.7.6",
                  "Todo": "Create some content here.",
              },
          ),
          id="Class with sections in the description"),
    param(dict(name="asciidoxy::geometry::Coordinate::Update(const Coordinate&)",
               kind="function",
               lang="cpp"),
          m_compound(exceptions=[
              m_throwsclause(type=m_typeref(
                  id="cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate",
                  kind="compound",
                  name="InvalidCoordinate"), ),
          ], ),
          id="Exception with explicit id in XML"),
    param(dict(name="asciidoxy::tparam::is_container", kind="struct", lang="cpp"),
          m_compound(
              name="is_container",
              full_name="asciidoxy::tparam::is_container",
              namespace="asciidoxy::tparam",
          ),
          id="Struct with template parameters"),
    param(dict(
        name="asciidoxy::tparam::is_container< std::array< T, N > >", kind="struct", lang="cpp"),
          m_compound(
              name="is_container< std::array< T, N > >",
              full_name="asciidoxy::tparam::is_container< std::array< T, N > >",
              namespace="asciidoxy::tparam",
          ),
          id="Struct with template parameter specialization"),
    param(dict(name="asciidoxy::traffic::TpegCauseCode", lang="cpp"),
          m_compound(
              kind="alias",
              name="TpegCauseCode",
              full_name="asciidoxy::traffic::TpegCauseCode",
              namespace="asciidoxy::traffic",
          ),
          id="Type alias"),
    param(dict(name="asciidoxy::traffic::Delay", lang="cpp"),
          m_compound(
              kind="typedef",
              name="Delay",
              full_name="asciidoxy::traffic::Delay",
              namespace="asciidoxy::traffic",
          ),
          id="Typedef"),
    param(dict(name="DEFAULT_CB", lang="cpp"),
          m_compound(
              kind="typedef",
              name="DEFAULT_CB",
              full_name="DEFAULT_CB",
              namespace=IsEmpty(),
              returns=m_returnvalue(type=m_typeref(name="uint32_t", ), ),
              params=[
                  m_parameter(type=m_typeref(
                      name="void",
                      suffix=" *pvArg",
                  )),
                  m_parameter(type=m_typeref(name="uint32_t ulResult", )),
              ],
          ),
          id="Function type typedef"),
    param(
        dict(name="asciidoxy::arrays::StructArray", lang="cpp"),
        m_compound(
            kind="alias",
            name="StructArray",
            returns=m_returnvalue(type=m_typeref(name="SomeStruct", prefix=IsEmpty(), suffix="[]")),
        ),
        id="Alias for array type"),
    param(
        dict(name="asciidoxy::arrays::AnotherArray", lang="cpp"),
        m_compound(
            kind="typedef",
            name="AnotherArray",
            returns=m_returnvalue(type=m_typeref(name="SomeStruct", prefix=IsEmpty(), suffix="[]")),
        ),
        id="Typedef for array type"),
    param(
        dict(name="asciidoxy::arrays::process", lang="cpp"),
        m_compound(
            kind="function",
            name="process",
            returns=m_returnvalue(type=m_typeref(name="SomeStruct", prefix=IsEmpty(), suffix="[]")),
            params=[m_parameter(type=m_typeref(
                name="SomeStruct",
                prefix="const ",
                suffix="[]",
            ))],
        ),
        id="Function with array types"),
    param(dict(name="asciidoxy::tparam::IsEven", lang="cpp"),
          m_compound(
              kind="function",
              name="IsEven",
              returns=m_returnvalue(type=m_typeref(name="bool")),
              params=[
                  m_parameter(
                      name="value",
                      type=m_typeref(
                          name="T",
                          prefix=IsEmpty(),
                          suffix=IsEmpty(),
                      ),
                      description="The value to check.",
                      kind="param",
                  ),
                  m_parameter(
                      name=IsEmpty(),
                      type=m_typeref(
                          name="T",
                          prefix="typename ",
                          suffix=IsEmpty(),
                      ),
                      description="A numeric type.",
                      kind="tparam",
                  ),
              ],
          ),
          id="Function with template parameters"),
    param(dict(name="asciidoxy::tparam::Mapping", lang="cpp"),
          m_compound(
              kind="struct",
              brief="Simple mapping between keys and values.",
              description=IsEmpty(),
              params=[
                  m_parameter(
                      name=IsEmpty(),
                      type=m_typeref(
                          prefix="typename ",
                          name="K",
                          suffix=IsEmpty(),
                      ),
                      description="Key type.",
                      kind="tparam",
                  ),
                  m_parameter(
                      name=IsEmpty(),
                      type=m_typeref(
                          prefix="class ",
                          name="V",
                          suffix=IsEmpty(),
                      ),
                      description="Value type.",
                      kind="tparam",
                  ),
              ],
              members=[
                  m_compound(
                      name="Insert",
                      kind="function",
                  ),
              ],
          ),
          id="Class with template parameters"),
])
def test_parse_cpp(api_reference, search_params, matcher):
    matcher.assert_matches(api_reference.find(**search_params))
