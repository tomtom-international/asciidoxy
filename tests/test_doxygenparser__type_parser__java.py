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
"""Tests for parsing Java types."""

import pytest

import xml.etree.ElementTree as ET

from unittest.mock import MagicMock

from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.java import JavaTypeParser
from asciidoxy.parser.doxygen.type_parser import Token
from tests.shared import assert_equal_or_none_if_empty


@pytest.fixture(params=["", "final ", "synchronized ", "synchronized final "])
def java_type_prefix(request):
    return request.param


def test_parse_java_type_from_text_simple(java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}double"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "java"
    assert type_ref.name == "double"
    assert_equal_or_none_if_empty(type_ref.prefix, java_type_prefix)
    assert not type_ref.suffix
    assert not type_ref.nested


def test_parse_java_type_with_mangled_annotation(java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}__AT__Nullable__ Data"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_called_once_with(type_ref)

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "java"
    assert type_ref.name == "Data"
    assert type_ref.prefix == f"{java_type_prefix}@Nullable "
    assert not type_ref.suffix
    assert not type_ref.nested


def test_parse_java_type_with_original_annotation(java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}@Nullable Data"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_called_once_with(type_ref)

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "java"
    assert type_ref.name == "Data"
    assert type_ref.prefix == f"{java_type_prefix}@Nullable "
    assert not type_ref.suffix
    assert not type_ref.nested


@pytest.mark.parametrize("generic_prefix, generic_name",
                         [("? extends ", "Unit"), ("T extends ", "Unit"), ("T extends ", "Unit "),
                          ("? super ", "Unit"), ("T super ", "Unit"), ("", "T "), ("", "T")])
def test_parse_java_type_with_generic(java_type_prefix, generic_prefix, generic_name):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}Position<{generic_prefix or ''}{generic_name}>"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "java"
    assert type_ref.name == "Position"
    assert_equal_or_none_if_empty(type_ref.prefix, java_type_prefix)
    assert not type_ref.suffix
    assert len(type_ref.nested) == 1
    assert type_ref.nested[0].prefix == generic_prefix
    assert type_ref.nested[0].name == generic_name.strip()
    assert not type_ref.nested[0].suffix

    if generic_name.strip() == "T":
        driver_mock.unresolved_ref.assert_called_with(type_ref)
        assert driver_mock.unresolved_ref.call_count == 1
    else:
        assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                        ]) == sorted(["Position", generic_name.strip()]))


def test_parse_java_type_with_nested_wildcard_generic():
    type_element = ET.Element("type")
    type_element.text = "Position<? extends Getter<?>>"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)

    assert type_ref is not None
    assert type_ref.language == "java"
    assert not type_ref.prefix
    assert type_ref.name == "Position"
    assert not type_ref.suffix
    assert len(type_ref.nested) == 1

    assert type_ref.nested[0].prefix == "? extends "
    assert type_ref.nested[0].name == "Getter"
    assert not type_ref.nested[0].suffix
    assert len(type_ref.nested[0].nested) == 1

    assert not type_ref.nested[0].nested[0].prefix
    assert type_ref.nested[0].nested[0].name == "?"
    assert not type_ref.nested[0].nested[0].suffix

    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["Position", "Getter"]))


def test_parse_java_type_with_separate_wildcard_bounds():
    type_element = ET.Element("type")
    type_element.text = "<T extends Getter<?>> T"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver=driver_mock)

    assert type_ref is not None
    assert type_ref.language == "java"
    assert type_ref.prefix == "<T extends Getter<?>> "
    assert type_ref.name == "T"
    assert not type_ref.suffix
    assert not type_ref.nested

    driver_mock.unresolved_ref.assert_not_called()


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
