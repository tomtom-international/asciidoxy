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

from .language_traits import LanguageTraits, TokenType
from .parser_base import ParserBase
from .type_parser import Token, TypeParser


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
        TokenType.NESTED_START: NESTED_STARTS,
        TokenType.NESTED_END: NESTED_ENDS,
        TokenType.ARGS_START: ARGS_STARTS,
        TokenType.ARGS_END: ARGS_ENDS,
        TokenType.SEPARATOR: SEPARATORS,
        TokenType.OPERATOR: OPERATORS,
        TokenType.QUALIFIER: QUALIFIERS,
        TokenType.BUILT_IN_NAME: BUILT_IN_NAMES,
    }
    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + ARGS_STARTS + ARGS_ENDS + SEPARATORS +
                        OPERATORS + NAMESPACE_SEPARATORS + tuple(string.whitespace))
    SEPARATOR_TOKENS_OVERLAP = True

    ALLOWED_PREFIXES = TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
    ALLOWED_SUFFIXES = (TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
                        TokenType.NAME, TokenType.NAMESPACE_SEPARATOR)
    ALLOWED_NAMES = (TokenType.WHITESPACE, TokenType.NAME, TokenType.NAMESPACE_SEPARATOR,
                     TokenType.BUILT_IN_NAME)

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

        scope_types = []
        name_tokens: List[Token] = []
        for i, token in enumerate(tokens):
            if token.type_ in (TokenType.NESTED_START, TokenType.ARGS_START):
                scope_types.append(token.type_)

            if token.type_ in (TokenType.ARGS_SEPARATOR, TokenType.ARGS_END):
                if len(name_tokens) > 1 and name_tokens[-1].type_ != TokenType.BUILT_IN_NAME:
                    name_tokens[-1].type_ = TokenType.ARG_NAME

            if token.type_ in (TokenType.ARGS_SEPARATOR, TokenType.ARGS_START):
                name_tokens.clear()

            if (token.type_ in (TokenType.NAME, TokenType.BUILT_IN_NAME) and scope_types
                    and scope_types[-1] == TokenType.ARGS_START):
                name_tokens.append(token)

            if token.type_ in (TokenType.NESTED_END, TokenType.ARGS_END):
                scope_types.pop(-1)

        return tokens


class CppParser(ParserBase):
    """Parser for C++ documentation."""
    TRAITS = CppTraits
    TYPE_PARSER = CppTypeParser
