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

from typing import List, Optional

from .language_traits import LanguageTraits, TokenCategory
from .parser_base import ParserBase
from .type_parser import Token, TypeParser, find_tokens


class CppTraits(LanguageTraits):
    """Traits for parsing C++ documentation."""
    TAG: str = "cpp"

    LANGUAGE_BUILT_IN_TYPES = ("void", "bool", "signed char", "unsigned char", "char", "wchar_t",
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
    ARGS_STARTS = "(",
    ARGS_ENDS = ")",
    SEPARATORS = ",",
    NAMESPACE_SEPARATORS = ":",
    OPERATORS = "*", "&", "...",
    QUALIFIERS = "const", "volatile", "constexpr", "mutable", "enum", "class",
    BUILT_IN_NAMES = ("void", "bool", "signed", "unsigned", "char", "wchar_t", "char16_t",
                      "char32_t", "char8_t", "float", "double", "long", "short", "int")

    TOKENS = {
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.ARGS_START: ARGS_STARTS,
        TokenCategory.ARGS_END: ARGS_ENDS,
        TokenCategory.SEPARATOR: SEPARATORS,
        TokenCategory.OPERATOR: OPERATORS,
        TokenCategory.QUALIFIER: QUALIFIERS,
        TokenCategory.BUILT_IN_NAME: BUILT_IN_NAMES,
    }
    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + ARGS_STARTS + ARGS_ENDS + SEPARATORS +
                        OPERATORS + NAMESPACE_SEPARATORS + tuple(string.whitespace))
    SEPARATOR_TOKENS_OVERLAP = True

    ALLOWED_PREFIXES = TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
    ALLOWED_SUFFIXES = (TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
                        TokenCategory.NAME, TokenCategory.NAMESPACE_SEPARATOR)
    ALLOWED_NAMES = (TokenCategory.WHITESPACE, TokenCategory.NAME,
                     TokenCategory.NAMESPACE_SEPARATOR, TokenCategory.BUILT_IN_NAME)

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name in cls.LANGUAGE_BUILT_IN_TYPES or type_name.startswith("std::")

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

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        tokens = super().adapt_tokens(tokens, array_tokens)

        suffixes_without_name: List[Optional[TokenCategory]] = list(cls.TRAITS.ALLOWED_SUFFIXES)
        suffixes_without_name.remove(TokenCategory.NAME)
        suffixes_without_name.remove(TokenCategory.NAMESPACE_SEPARATOR)
        for match in find_tokens(tokens, [
            (TokenCategory.NESTED_END, ) + cls.TRAITS.ALLOWED_NAMES,
                suffixes_without_name,
                suffixes_without_name + [None],
                suffixes_without_name + [None],
                suffixes_without_name + [None],
                suffixes_without_name + [None],
                suffixes_without_name + [None],
                suffixes_without_name + [None],
            [TokenCategory.NAME],
            [TokenCategory.WHITESPACE, None],
            [TokenCategory.ARGS_END, TokenCategory.ARGS_SEPARATOR],
        ]):
            if match[-2].category == TokenCategory.NAME:
                match[-2].category = TokenCategory.ARG_NAME
            elif match[-3].category == TokenCategory.NAME:
                match[-3].category = TokenCategory.ARG_NAME

        return tokens


class CppParser(ParserBase):
    """Parser for C++ documentation."""
    TRAITS = CppTraits
    TYPE_PARSER = CppTypeParser
