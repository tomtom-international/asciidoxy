# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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

from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.python import PythonTypeParser
from asciidoxy.parser.doxygen.type_parser import Token


def test_adapt_tokens__remove_def():
    assert PythonTypeParser.adapt_tokens([
        Token(" ", TokenCategory.WHITESPACE),
        Token("def", TokenCategory.NAME),
        Token(" ", TokenCategory.WHITESPACE),
        Token("Type", TokenCategory.NAME),
        Token("[", TokenCategory.NESTED_START),
        Token("def", TokenCategory.NAME),
        Token(",", TokenCategory.NESTED_SEPARATOR),
        Token("OtherType", TokenCategory.NAME),
        Token("]", TokenCategory.NESTED_END),
        Token(" ", TokenCategory.WHITESPACE),
    ]) == [
        Token(" ", TokenCategory.WHITESPACE),
        Token(" ", TokenCategory.WHITESPACE),
        Token("Type", TokenCategory.NAME),
        Token("[", TokenCategory.NESTED_START),
        Token(",", TokenCategory.NESTED_SEPARATOR),
        Token("OtherType", TokenCategory.NAME),
        Token("]", TokenCategory.NESTED_END),
        Token(" ", TokenCategory.WHITESPACE),
    ]


def test_adapt_tokens__add_nested_type_hint():
    assert PythonTypeParser.adapt_tokens([
        Token("Type", TokenCategory.NAME),
    ], [
        Token("[", TokenCategory.NESTED_START),
        Token("NestedType", TokenCategory.NAME),
        Token("]", TokenCategory.NESTED_END),
    ]) == [
        Token("Type", TokenCategory.NAME),
        Token("[", TokenCategory.NESTED_START),
        Token("NestedType", TokenCategory.NAME),
        Token("]", TokenCategory.NESTED_END),
    ]


def test_adapt_tokens__add_nested_type_hint__double_nested():
    assert PythonTypeParser.adapt_tokens(
        [
            Token("Type", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),  # Bug in Doxygen
        ],
        [
            Token("[", TokenCategory.NESTED_START),
            Token("NestedType", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("DoubleNestedType", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),
        ]) == [
            Token("Type", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("NestedType", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("DoubleNestedType", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),
            Token("]", TokenCategory.NESTED_END),
        ]


def test_adapt_tokens__add_nested_type_hint__double_nested_with_whitespace():
    assert PythonTypeParser.adapt_tokens(
        [
            Token("Type", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),  # Bug in Doxygen
            Token(" ", TokenCategory.WHITESPACE),
        ],
        [
            Token("[", TokenCategory.NESTED_START),
            Token("NestedType", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("DoubleNestedType", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),
        ]) == [
            Token("Type", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("NestedType", TokenCategory.NAME),
            Token("[", TokenCategory.NESTED_START),
            Token("DoubleNestedType", TokenCategory.NAME),
            Token("]", TokenCategory.NESTED_END),
            Token("]", TokenCategory.NESTED_END),
        ]
