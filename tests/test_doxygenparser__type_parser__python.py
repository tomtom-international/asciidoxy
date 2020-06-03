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
"""Tests for parsing python types."""

from asciidoxy.doxygenparser.language_traits import TokenType
from asciidoxy.doxygenparser.python import PythonTypeParser
from asciidoxy.doxygenparser.type_parser import Token


def test_adapt_tokens__remove_def():
    assert PythonTypeParser.adapt_tokens([
        Token(" ", TokenType.WHITESPACE),
        Token("def", TokenType.NAME),
        Token(" ", TokenType.WHITESPACE),
        Token("Type", TokenType.NAME),
        Token("[", TokenType.NESTED_START),
        Token("def", TokenType.NAME),
        Token(",", TokenType.NESTED_SEPARATOR),
        Token("OtherType", TokenType.NAME),
        Token("]", TokenType.NESTED_END),
        Token(" ", TokenType.WHITESPACE),
    ]) == [
        Token(" ", TokenType.WHITESPACE),
        Token(" ", TokenType.WHITESPACE),
        Token("Type", TokenType.NAME),
        Token("[", TokenType.NESTED_START),
        Token(",", TokenType.NESTED_SEPARATOR),
        Token("OtherType", TokenType.NAME),
        Token("]", TokenType.NESTED_END),
        Token(" ", TokenType.WHITESPACE),
    ]


def test_adapt_tokens__add_nested_type_hint():
    assert PythonTypeParser.adapt_tokens([
        Token("Type", TokenType.NAME),
    ], [
        Token("[", TokenType.NESTED_START),
        Token("NestedType", TokenType.NAME),
        Token("]", TokenType.NESTED_END),
    ]) == [
        Token("Type", TokenType.NAME),
        Token("[", TokenType.NESTED_START),
        Token("NestedType", TokenType.NAME),
        Token("]", TokenType.NESTED_END),
    ]


def test_adapt_tokens__add_nested_type_hint__double_nested():
    assert PythonTypeParser.adapt_tokens(
        [
            Token("Type", TokenType.NAME),
            Token("]", TokenType.NESTED_END),  # Bug in Doxygen
        ],
        [
            Token("[", TokenType.NESTED_START),
            Token("NestedType", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("DoubleNestedType", TokenType.NAME),
            Token("]", TokenType.NESTED_END),
        ]) == [
            Token("Type", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("NestedType", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("DoubleNestedType", TokenType.NAME),
            Token("]", TokenType.NESTED_END),
            Token("]", TokenType.NESTED_END),
        ]


def test_adapt_tokens__add_nested_type_hint__double_nested_with_whitespace():
    assert PythonTypeParser.adapt_tokens(
        [
            Token("Type", TokenType.NAME),
            Token("]", TokenType.NESTED_END),  # Bug in Doxygen
            Token(" ", TokenType.WHITESPACE),
        ],
        [
            Token("[", TokenType.NESTED_START),
            Token("NestedType", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("DoubleNestedType", TokenType.NAME),
            Token("]", TokenType.NESTED_END),
        ]) == [
            Token("Type", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("NestedType", TokenType.NAME),
            Token("[", TokenType.NESTED_START),
            Token("DoubleNestedType", TokenType.NAME),
            Token("]", TokenType.NESTED_END),
            Token("]", TokenType.NESTED_END),
        ]
