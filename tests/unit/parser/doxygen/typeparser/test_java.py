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
"""Tests for parsing Java types."""

import xml.etree.ElementTree as ET

import pytest

from asciidoxy.parser.doxygen.java import JavaTypeParser
from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.type_parser import Token
from tests.unit.matchers import IsEmpty, IsNone, m_typeref
from tests.unit.shared import sub_element


@pytest.fixture(params=["", "final ", "synchronized ", "synchronized final "])
def java_type_prefix(request):
    return request.param


def test_parse_java_type_from_text_simple(driver_mock, java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}double"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="double",
        prefix=java_type_prefix,
        suffix=IsEmpty(),
        nested=IsEmpty(),
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


def test_parse_java_type_with_mangled_annotation(driver_mock, java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}__AT__Nullable__ Data"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="Data",
        prefix=f"{java_type_prefix}@Nullable ",
        suffix=IsEmpty(),
        nested=IsEmpty(),
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("Data")


def test_parse_java_type_with_original_annotation(driver_mock, java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}@Nullable Data"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="Data",
        prefix=f"{java_type_prefix}@Nullable ",
        suffix=IsEmpty(),
        nested=IsEmpty(),
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("Data")


@pytest.mark.parametrize("generic_prefix, generic_name",
                         [("? extends ", "Unit"), ("T extends ", "Unit"), ("T extends ", "Unit "),
                          ("? super ", "Unit"), ("T super ", "Unit"), ("", "T "), ("", "T")])
def test_parse_java_type_with_generic(driver_mock, java_type_prefix, generic_prefix, generic_name):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}Position<{generic_prefix or ''}{generic_name}>"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="Position",
        prefix=java_type_prefix,
        suffix=IsEmpty(),
        nested=[
            m_typeref(
                name=generic_name.strip(),
                prefix=generic_prefix,
                suffix=IsEmpty(),
            ),
        ],
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))

    if generic_name.strip() == "T":
        driver_mock.assert_unresolved("Position")
        assert driver_mock.unresolved_ref.call_count == 1
    else:
        driver_mock.assert_unresolved("Position", generic_name.strip())


def test_parse_java_type_with_nested_wildcard_generic(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "Position<? extends Getter<?>>"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="Position",
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=[
            m_typeref(
                name="Getter",
                prefix="? extends ",
                suffix=IsEmpty(),
                nested=[
                    m_typeref(
                        name="?",
                        prefix=IsEmpty(),
                        suffix=IsEmpty(),
                    ),
                ],
            ),
        ],
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("Position", "Getter")


def test_parse_java_type_with_separate_wildcard_bounds(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "<T extends Getter<?>> T"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="java",
        name="T",
        prefix="<T extends Getter<?>> ",
        suffix=IsEmpty(),
        nested=IsEmpty(),
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_java_type__array(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType[]"

    m_typeref(
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_java_type__array__brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[]")
    ET.dump(type_element)

    m_typeref(
        id="java-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_java_type__array__multiple_brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[][]")
    ET.dump(type_element)

    m_typeref(
        id="java-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[][]",
    ).assert_matches(JavaTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


@pytest.mark.parametrize("tokens,expected", [
    ([
        Token("?", TokenCategory.WILDCARD),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ], [
        Token("?", TokenCategory.WILDCARD),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ]),
    ([
        Token("T", TokenCategory.NAME),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ], [
        Token("T", TokenCategory.WILDCARD),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ]),
    ([
        Token("Type", TokenCategory.NAME),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ], [
        Token("Type", TokenCategory.WILDCARD),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ]),
],
                         ids=lambda tokens: "".join(t.text for t in tokens))
def test_java_type_parser__adapt_tokens__wildcard_bounds(tokens, expected):
    assert JavaTypeParser.adapt_tokens(tokens) == expected


@pytest.mark.parametrize("tokens,expected", [
    ([
        Token("private", TokenCategory.INVALID),
        Token(" ", TokenCategory.WHITESPACE),
        Token("private", TokenCategory.INVALID),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
        Token("private", TokenCategory.INVALID),
    ], [
        Token(" ", TokenCategory.WHITESPACE),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
    ]),
],
                         ids=lambda tokens: "".join(t.text for t in tokens))
def test_java_type_parser__adapt_tokens__invalid_tokens(tokens, expected):
    assert JavaTypeParser.adapt_tokens(tokens) == expected


@pytest.mark.parametrize("tokens,expected", [
    ([
        Token("<", TokenCategory.NESTED_START),
        Token("?", TokenCategory.WILDCARD),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
        Token(">", TokenCategory.NESTED_END),
        Token(" ", TokenCategory.WHITESPACE),
        Token("T", TokenCategory.NAME),
    ], [
        Token("<", TokenCategory.UNKNOWN),
        Token("?", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.UNKNOWN),
        Token("extends", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.UNKNOWN),
        Token("MyType", TokenCategory.UNKNOWN),
        Token(">", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.WHITESPACE),
        Token("T", TokenCategory.NAME),
    ]),
    ([
        Token("private", TokenCategory.INVALID),
        Token(" ", TokenCategory.WHITESPACE),
        Token("<", TokenCategory.NESTED_START),
        Token("T", TokenCategory.NAME),
        Token(" ", TokenCategory.WHITESPACE),
        Token("extends", TokenCategory.WILDCARD_BOUNDS),
        Token(" ", TokenCategory.WHITESPACE),
        Token("MyType", TokenCategory.NAME),
        Token(">", TokenCategory.NESTED_END),
        Token(" ", TokenCategory.WHITESPACE),
        Token("T", TokenCategory.NAME),
    ], [
        Token(" ", TokenCategory.WHITESPACE),
        Token("<", TokenCategory.UNKNOWN),
        Token("T", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.UNKNOWN),
        Token("extends", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.UNKNOWN),
        Token("MyType", TokenCategory.UNKNOWN),
        Token(">", TokenCategory.UNKNOWN),
        Token(" ", TokenCategory.WHITESPACE),
        Token("T", TokenCategory.NAME),
    ]),
],
                         ids=lambda tokens: "".join(t.text for t in tokens))
def test_java_type_parser__adapt_tokens__separate_wildcard_bounds_are_ignored(tokens, expected):
    assert JavaTypeParser.adapt_tokens(tokens) == expected
