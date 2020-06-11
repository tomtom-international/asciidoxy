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

from asciidoxy.doxygenparser.language_traits import TokenType
from asciidoxy.doxygenparser.java import JavaTypeParser
from asciidoxy.doxygenparser.type_parser import Token, TypeParseError
from tests.shared import assert_equal_or_none_if_empty


@pytest.fixture(params=["", "final ", "synchronized ", "synchronized final "])
def java_type_prefix(request):
    return request.param


def test_parse_java_type_from_text_simple(java_type_prefix):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}double"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "java"
    assert type_ref.name == "double"
    assert_equal_or_none_if_empty(type_ref.prefix, java_type_prefix)
    assert not type_ref.suffix
    assert len(type_ref.nested) == 0


@pytest.mark.parametrize("generic_prefix, generic_name", [("? extends ", "Unit"),
                                                          ("T extends ", "Unit"),
                                                          ("T extends ", "Unit "), ("", "T "),
                                                          ("", "T")])
def test_parse_java_type_with_generic(java_type_prefix, generic_prefix, generic_name):
    type_element = ET.Element("type")
    type_element.text = f"{java_type_prefix}Position<{generic_prefix or ''}{generic_name}>"

    driver_mock = MagicMock()
    type_ref = JavaTypeParser.parse_xml(type_element, driver_mock)

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


@pytest.mark.parametrize("tokens,expected", [
    ([
        Token("?", TokenType.NAME),
        Token(" ", TokenType.WHITESPACE),
        Token("extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ], [
        Token("? extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ]),
    ([
        Token("T", TokenType.NAME),
        Token(" ", TokenType.WHITESPACE),
        Token("extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ], [
        Token("T extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ]),
    ([
        Token("Type", TokenType.NAME),
        Token(" ", TokenType.WHITESPACE),
        Token("extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ], [
        Token("Type extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ]),
], ids=lambda tokens: "".join(t.text for t in tokens))
def test_java_type_parser__adapt_tokens__extends(tokens, expected):
    assert JavaTypeParser.adapt_tokens(tokens) == expected


@pytest.mark.parametrize("tokens", [
    [
        Token(" ", TokenType.WHITESPACE),
        Token("extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ],
    [
        Token("final", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("extends", TokenType.QUALIFIER),
        Token(" ", TokenType.WHITESPACE),
        Token("MyType", TokenType.NAME),
    ],
], ids=lambda tokens: "".join(t.text for t in tokens))
def test_java_type_parser__adapt_tokens__extends__error(tokens):
    with pytest.raises(TypeParseError):
        JavaTypeParser.adapt_tokens(tokens)
