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
"""Support for parsing C++ documentation."""

import re
import string
import xml.etree.ElementTree as ET
from typing import List, Optional

from ...model import Compound, Parameter
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
    QUALIFIERS = "const", "volatile", "mutable", "enum", "class",
    BUILT_IN_NAMES = ("void", "bool", "signed", "unsigned", "char", "wchar_t", "char16_t",
                      "char32_t", "char8_t", "float", "double", "long", "short", "int")
    # constexpr should not be part of the return type
    INVALID = "constexpr",

    TOKENS = {
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.ARGS_START: ARGS_STARTS,
        TokenCategory.ARGS_END: ARGS_ENDS,
        TokenCategory.SEPARATOR: SEPARATORS,
        TokenCategory.OPERATOR: OPERATORS,
        TokenCategory.QUALIFIER: QUALIFIERS,
        TokenCategory.BUILT_IN_NAME: BUILT_IN_NAMES,
        TokenCategory.INVALID: INVALID,
    }
    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + ARGS_STARTS + ARGS_ENDS + SEPARATORS +
                        OPERATORS + NAMESPACE_SEPARATORS + INVALID + tuple(string.whitespace))
    SEPARATOR_TOKENS_OVERLAP = True

    ALLOWED_PREFIXES = (TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
                        TokenCategory.INVALID)
    ALLOWED_SUFFIXES = (TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
                        TokenCategory.NAME, TokenCategory.NAMESPACE_SEPARATOR,
                        TokenCategory.INVALID)
    ALLOWED_NAMES = (TokenCategory.WHITESPACE, TokenCategory.NAME,
                     TokenCategory.NAMESPACE_SEPARATOR, TokenCategory.BUILT_IN_NAME)

    NESTING_BOUNDARY = "<"
    NAMESPACE_SEPARATOR = "::"
    FILE_EXTENSIONS = ".h", ".hpp", ".c", ".cpp"

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name in cls.LANGUAGE_BUILT_IN_TYPES or type_name.startswith("std::")

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
        tokens = [t for t in tokens if t.category != TokenCategory.INVALID]

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

        # Typedefs for function types can leave a trailing (*
        if (len(tokens) > 2 and tokens[-2].category == TokenCategory.ARGS_START
                and tokens[-1].category == TokenCategory.OPERATOR):
            tokens = tokens[:-2]
        if (len(tokens) > 3 and tokens[-3].category == TokenCategory.ARGS_START
                and tokens[-2].category == TokenCategory.OPERATOR):
            tokens = tokens[:-3]

        return tokens


class CppParser(ParserBase):
    """Parser for C++ documentation."""
    TRAITS = CppTraits
    TYPE_PARSER = CppTypeParser

    DEFAULTED_RE = re.compile(r"=\s*default\s*$")
    DELETED_RE = re.compile(r"=\s*delete\s*$")

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Compound]:
        member = super().parse_member(memberdef_element, parent)

        if member is not None and member.kind == "function" and member.args:
            member.default = self.DEFAULTED_RE.search(member.args) is not None
            member.deleted = self.DELETED_RE.search(member.args) is not None

        if (member is not None and member.kind == "typedef" and member.definition
                and member.definition.startswith("using")):
            member.kind = "alias"

        member = self._fix_function_typedef(member, memberdef_element)
        return member

    def _fix_function_typedef(self, member: Optional[Compound],
                              memberdef_element: ET.Element) -> Optional[Compound]:
        if member is None:
            return None
        if member.kind != "typedef" or not member.args:
            return member

        tokens = self.TYPE_PARSER.tokenize_text(member.args)
        while tokens and tokens[0].category in (TokenCategory.WHITESPACE, TokenCategory.ARGS_START,
                                                TokenCategory.ARGS_END):
            tokens.pop(0)
        while tokens and tokens[-1].category in (TokenCategory.WHITESPACE, TokenCategory.ARGS_END):
            tokens.pop(-1)

        while tokens:
            type_tokens = []
            while tokens and tokens[0].category != TokenCategory.SEPARATOR:
                type_tokens.append(tokens.pop(0))
            if tokens:
                # Still tokens left, so there must be a separator here
                tokens.pop(0)

            if type_tokens:
                ref = self.TYPE_PARSER.type_from_tokens(type_tokens, self._driver, member.full_name)
                if ref is not None:
                    member.params.append(Parameter(type=ref))

        return member
