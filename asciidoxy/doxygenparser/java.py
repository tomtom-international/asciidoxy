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
"""Support for Java documentation."""

import string

from typing import List, Optional

from .language_traits import LanguageTraits, TokenType
from .parser_base import ParserBase
from .type_parser import TypeParser, Token, find_tokens


class JavaTraits(LanguageTraits):
    """Traits for parsing Java documentation."""
    TAG: str = "java"

    LANGUAGE_BUILD_IN_TYPES = ("void", "long", "int", "boolean", "byte", "char", "short", "float",
                               "double", "String")
    COMMON_GENERIC_NAMES = ("T", "?", "T ", "? ")

    NESTED_STARTS = "<",
    NESTED_ENDS = ">",
    NESTED_SEPARATORS = ",",
    QUALIFIERS = "final", "synchronized", "transient",
    WILDCARD_BOUNDS = "extends", "super",
    INVALID = "private",

    TOKENS = {
        TokenType.NESTED_START: NESTED_STARTS,
        TokenType.NESTED_END: NESTED_ENDS,
        TokenType.NESTED_SEPARATOR: NESTED_SEPARATORS,
        TokenType.QUALIFIER: QUALIFIERS,
        TokenType.WILDCARD_BOUNDS: WILDCARD_BOUNDS,
        TokenType.INVALID: INVALID,
    }

    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + tuple(string.whitespace))

    ALLOWED_PREFIXES = (TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
                        TokenType.WILDCARD, TokenType.WILDCARD_BOUNDS, TokenType.UNKNOWN)
    ALLOWED_SUFFIXES = TokenType.WHITESPACE,
    ALLOWED_NAMES = TokenType.WHITESPACE, TokenType.NAME,

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return (type_name in cls.LANGUAGE_BUILD_IN_TYPES or type_name in cls.COMMON_GENERIC_NAMES
                or type_name.startswith("java.") or type_name.startswith("android.")
                or type_name.startswith("native "))

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        return name.replace("::", ".").strip()

    @classmethod
    def short_name(cls, name: str) -> str:
        return name.split(".")[-1]

    @classmethod
    def full_name(cls, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}.{name}"

    @classmethod
    def namespace(cls, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None


class JavaTypeParser(TypeParser):
    """Parser for Java types."""
    TRAITS = JavaTraits

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        tokens = [t for t in tokens if t.type_ != TokenType.INVALID]
        tokens = cls.mark_separate_wildcard_bounds(tokens)
        tokens = cls.detect_wildcards(tokens)
        return tokens

    @staticmethod
    def mark_separate_wildcard_bounds(tokens: List[Token]) -> List[Token]:

        # Separate wildcard bounds are not supported yet
        nested = 0
        for token in tokens:
            if nested == 0 and token.type_ == TokenType.NAME:
                break

            elif token.type_ == TokenType.NESTED_START:
                nested += 1
                token.type_ = TokenType.UNKNOWN

            elif token.type_ == TokenType.NESTED_END:
                nested -= 1
                token.type_ = TokenType.UNKNOWN

            elif nested > 0:
                token.type_ = TokenType.UNKNOWN

        return tokens

    @staticmethod
    def detect_wildcards(tokens: List[Token]) -> List[Token]:
        for match in find_tokens(tokens, [
            [TokenType.NAME],
            [TokenType.WHITESPACE],
            [TokenType.WILDCARD_BOUNDS],
        ]):
            match[0].type_ = TokenType.WILDCARD
        return tokens


class JavaParser(ParserBase):
    """Parser for Java documentation."""
    TRAITS = JavaTraits
    TYPE_PARSER = JavaTypeParser
