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

from .language_traits import LanguageTraits, TokenCategory
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
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.NESTED_SEPARATOR: NESTED_SEPARATORS,
        TokenCategory.QUALIFIER: QUALIFIERS,
        TokenCategory.WILDCARD_BOUNDS: WILDCARD_BOUNDS,
        TokenCategory.INVALID: INVALID,
    }

    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + tuple(string.whitespace))

    ALLOWED_PREFIXES = (TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
                        TokenCategory.WILDCARD, TokenCategory.WILDCARD_BOUNDS,
                        TokenCategory.UNKNOWN, TokenCategory.ANNOTATION)
    ALLOWED_SUFFIXES = TokenCategory.WHITESPACE,
    ALLOWED_NAMES = TokenCategory.WHITESPACE, TokenCategory.NAME,

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
    def full_name(cls, name: str, parent: str = "", kind: Optional[str] = None) -> str:
        if not parent or name.startswith(f"{parent}."):
            return name
        return f"{parent}.{name}"

    @classmethod
    def namespace(cls, full_name: str, kind: Optional[str] = None) -> Optional[str]:
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
        tokens = [t for t in tokens if t.category != TokenCategory.INVALID]
        tokens = cls.mark_separate_wildcard_bounds(tokens)
        tokens = cls.detect_wildcards(tokens)
        tokens = cls.detect_annotations(tokens)
        return tokens

    @staticmethod
    def mark_separate_wildcard_bounds(tokens: List[Token]) -> List[Token]:

        # Separate wildcard bounds are not supported yet
        nested = 0
        for token in tokens:
            if nested == 0 and token.category == TokenCategory.NAME:
                break

            elif token.category == TokenCategory.NESTED_START:
                nested += 1
                token.category = TokenCategory.UNKNOWN

            elif token.category == TokenCategory.NESTED_END:
                nested -= 1
                token.category = TokenCategory.UNKNOWN

            elif nested > 0:
                token.category = TokenCategory.UNKNOWN

        return tokens

    @staticmethod
    def detect_wildcards(tokens: List[Token]) -> List[Token]:
        for match in find_tokens(tokens, [
            [TokenCategory.NAME],
            [TokenCategory.WHITESPACE],
            [TokenCategory.WILDCARD_BOUNDS],
        ]):
            match[0].category = TokenCategory.WILDCARD
        return tokens

    @staticmethod
    def detect_annotations(tokens: List[Token]) -> List[Token]:
        for token in tokens:
            if token.category == TokenCategory.NAME and token.text:
                if token.text.startswith("__AT__") and token.text.endswith("__"):
                    token.category = TokenCategory.ANNOTATION
                    token.text = f"@{token.text[6:-2]}"
                elif token.text.startswith("@"):
                    token.category = TokenCategory.ANNOTATION

        return tokens


class JavaParser(ParserBase):
    """Parser for Java documentation."""
    TRAITS = JavaTraits
    TYPE_PARSER = JavaTypeParser
