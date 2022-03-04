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
import pytest
from pytest import param

from asciidoxy.api_reference import ApiReference
from asciidoxy.parser import parser_factory
from tests.unit.api_reference_loader import ApiReferenceLoader
from tests.unit.matchers import (
    IsEmpty,
    IsNone,
    Unordered,
    m_compound,
    m_parameter,
    m_returnvalue,
    m_typeref,
)


@pytest.fixture(scope="module")
def api_reference():
    return ApiReferenceLoader().add("dokka", "kotlin/default").load()


def test_create_dokka_parser(generated_test_data):
    api_reference = ApiReference()
    parser = parser_factory("dokka", api_reference)
    assert parser is not None

    parser.parse(generated_test_data("dokka", "kotlin/default/asciidoxy.json"))

    element = api_reference.find(name="asciidoxy.Coordinate", kind="class")
    assert element is not None


@pytest.mark.parametrize(
    "search_params,matcher",
    [
        param(dict(name="asciidoxy.Coordinate", kind="class", lang="kotlin"),
              m_compound(
                  language="kotlin",
                  id="kotlin-asciidoxy1_1_Coordinate",
                  name="Coordinate",
                  full_name="asciidoxy.Coordinate",
                  namespace="asciidoxy",
                  kind="class",
                  prot="public",
                  brief="Class to hold information about a coordinate.",
                  description="A coordinate has a latitude, longitude, and an altitude.",
                  members=Unordered(
                      m_compound(name="isValid"),
                      m_compound(name="latitude"),
                      m_compound(name="longitude"),
                      m_compound(name="altitude"),
                      m_compound(name="Coordinate"),
                  ),
              ),
              id="Basic class"),
        param(
            dict(name="asciidoxy.Coordinate.isValid", kind="function", lang="kotlin"),
            m_compound(
                language="kotlin",
                id="kotlin-asciidoxy1_1_Coordinate1_1_isValid1_1_2_",
                name="isValid",
                full_name="asciidoxy.Coordinate.isValid",
                namespace="asciidoxy.Coordinate",
                kind="function",
                prot="public",
                brief="Check if the coordinate is valid.",
                description="A coordinate is valid if its values are within WGS84 bounds.",
                params=[],
                returns=m_returnvalue(
                    description="True if valid, false if not.",
                    type=m_typeref(
                        name="Boolean",
                        id=IsNone(),  # TODO: id="kotlin-kotlin1_1_Boolean",
                    ),
                ),
            ),
            id="Basic method"),
        param(
            dict(name="asciidoxy.Coordinate.latitude", kind="property", lang="kotlin"),
            m_compound(
                language="kotlin",
                id="kotlin-asciidoxy1_1_Coordinate1_1_latitude1_1_2_",
                name="latitude",
                full_name="asciidoxy.Coordinate.latitude",
                namespace="asciidoxy.Coordinate",
                kind="property",
                prot="public",
                brief="The latitude in degrees.",
                description=IsEmpty(),
                returns=m_returnvalue(
                    description=IsEmpty(),
                    type=m_typeref(
                        name="Double",
                        id=IsNone(),  # TODO: id="kotlin-kotlin1_1_Double",
                    ),
                ),
            ),
            id="Basic property"),
        param(
            dict(name="asciidoxy.Coordinate.Coordinate", kind="constructor", lang="kotlin"),
            m_compound(
                language="kotlin",
                id=("kotlin-asciidoxy1_1_Coordinate1_1_Coordinate1_1_2_kotlin1_1_Double2_kotlin"
                    "1_1_Double2_kotlin1_1_Double"),
                name="Coordinate",
                full_name="asciidoxy.Coordinate.Coordinate",
                namespace="asciidoxy.Coordinate",
                kind="constructor",
                prot="public",
                brief=IsEmpty(),
                params=[
                    m_parameter(
                        name="latitude",
                        description="The latitude in degrees.",
                        type=m_typeref(
                            name="Double",
                            id=IsNone(),  # TODO: id="kotlin-kotlin1_1_Double",
                        ),
                    ),
                    m_parameter(
                        name="longitude",
                        description="The longitude in degrees.",
                        type=m_typeref(
                            name="Double",
                            id=IsNone(),  # TODO: id="kotlin-kotlin1_1_Double",
                        ),
                    ),
                    m_parameter(
                        name="altitude",
                        description="The altitude in meters.",
                        type=m_typeref(
                            name="Double",
                            id=IsNone(),  # TODO: id="kotlin-kotlin1_1_Double",
                        ),
                    ),
                ],
                returns=m_returnvalue(
                    description=IsEmpty(),
                    type=m_typeref(
                        name="Coordinate",
                        id="kotlin-asciidoxy1_1_Coordinate",
                    ),
                ),
            ),
            id="Basic constructor"),
    ])
def test_parse_kotlin(api_reference, search_params, matcher):
    matcher.assert_matches(api_reference.find(**search_params))
