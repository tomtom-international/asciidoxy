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
"""Support for parsing C++ documentation."""

import string

from typing import Optional

from .language_traits import LanguageTraits, TokenType
from .parser_base import ParserBase
from .type_parser import TypeParser


class CppTraits(LanguageTraits):
    """Traits for parsing C++ documentation."""
    TAG: str = "cpp"

    LANGUAGE_BUILD_IN_TYPES = ("void", "bool", "signed char", "unsigned char", "char", "wchar_t",
                               "char16_t", "char32_t", "char8_t", "float", "double", "long double",
                               "short", "short int", "signed short", "signed short int",
                               "unsigned short", "unsigned short int", "int", "signed",
                               "signed int", "unsigned", "unsigned int", "long", "long int",
                               "signed long", "signed long int", "unsigned long",
                               "unsigned long int", "long long", "long long int",
                               "signed long long", "signed long long int", "unsigned long long",
                               "unsigned long long int")

    NESTED_STARTS = "<",
    NESTED_ENDS = ">",
    NESTED_SEPARATORS = ",",
    NAMESPACE_SEPARATORS = ":",
    OPERATORS = "*", "&", "...",
    QUALIFIERS = "const", "volatile", "constexpr", "mutable", "enum", "class",

    TOKENS = {
        TokenType.NESTED_START: NESTED_STARTS,
        TokenType.NESTED_END: NESTED_ENDS,
        TokenType.NESTED_SEPARATOR: NESTED_SEPARATORS,
        TokenType.OPERATOR: OPERATORS,
        TokenType.QUALIFIER: QUALIFIERS,
    }

    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + OPERATORS +
                        NAMESPACE_SEPARATORS + tuple(string.whitespace))

    ALLOWED_PREFIXES = TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
    ALLOWED_SUFFIXES = (TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
                        TokenType.NAME, TokenType.NAMESPACE_SEPARATOR)
    ALLOWED_NAMES = TokenType.WHITESPACE, TokenType.NAME, TokenType.NAMESPACE_SEPARATOR,

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name in cls.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("std::")

    @classmethod
    def short_name(cls, name: str) -> str:
        return name.split("::")[-1]

    @classmethod
    def full_name(cls, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}::{name}"

    @classmethod
    def namespace(cls, full_name: str) -> Optional[str]:
        if "::" in full_name:
            namespace, _ = full_name.rsplit("::", maxsplit=1)
            return namespace
        else:
            return None

    @classmethod
    def is_member_blacklisted(cls, kind: str, name: str) -> bool:
        return kind == "friend"


class CppTypeParser(TypeParser):
    """Parser for C++ types."""
    TRAITS = CppTraits


class CppParser(ParserBase):
    """Parser for C++ documentation."""
    TRAITS = CppTraits
    TYPE_PARSER = CppTypeParser
