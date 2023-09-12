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
"""Support for Objective-C documentation."""

import string
import xml.etree.ElementTree as ET
from typing import List, Optional, Tuple

from ....model import Compound
from ..language_parser import LanguageParser
from ..language_traits import LanguageTraits, TokenCategory
from ..type_parser import Token, TypeParser, find_tokens


class ObjectiveCTraits(LanguageTraits):
    """Traits for parsing Objective C documentation."""
    TAG: str = "objc"

    LANGUAGE_BUILT_IN_TYPES = ("char", "unsigned char", "signed char", "int", "short", "long",
                               "float", "double", "void", "bool", "BOOL", "id", "instancetype",
                               "short int", "signed short", "signed short int", "unsigned short",
                               "unsigned short int", "signed int", "unsigned int", "long int",
                               "signed long", "signed long int", "unsigned long",
                               "unsigned long int", "long long", "long long int",
                               "signed long long", "signed long long int", "unsigned long long",
                               "unsigned long long int", "signed char", "long double")

    NESTED_STARTS = "<",
    NESTED_ENDS = ">",
    ARGS_STARTS = "(",
    ARGS_ENDS = ")",
    ARRAY_STARTS = "[",
    ARRAY_ENDS = "]",
    SEPARATORS = ",",
    OPERATORS = "*",
    QUALIFIERS = ("nullable", "const", "__weak", "__strong", "__nonnull", "_Nullable", "_Nonnull",
                  "__autoreleasing")
    BUILT_IN_NAMES = ("char", "unsigned", "signed", "int", "short", "long", "float", "double",
                      "void", "bool", "BOOL", "id", "instancetype")
    BLOCKS = "^",

    TOKENS = {
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.ARGS_START: ARGS_STARTS,
        TokenCategory.ARGS_END: ARGS_ENDS,
        TokenCategory.ARRAY_START: ARRAY_STARTS,
        TokenCategory.ARRAY_END: ARRAY_ENDS,
        TokenCategory.SEPARATOR: SEPARATORS,
        TokenCategory.OPERATOR: OPERATORS,
        TokenCategory.QUALIFIER: QUALIFIERS,
        TokenCategory.BUILT_IN_NAME: BUILT_IN_NAMES,
        TokenCategory.BLOCK: BLOCKS,
    }
    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + ARGS_STARTS + ARGS_ENDS + ARRAY_STARTS +
                        ARRAY_ENDS + SEPARATORS + OPERATORS + BLOCKS + tuple(string.whitespace))
    SEPARATOR_TOKENS_OVERLAP = True

    ALLOWED_PREFIXES = TokenCategory.WHITESPACE, TokenCategory.QUALIFIER,
    ALLOWED_SUFFIXES = (
        TokenCategory.WHITESPACE,
        TokenCategory.OPERATOR,
        TokenCategory.QUALIFIER,
        TokenCategory.ARG_NAME,
    )
    ALLOWED_NAMES = TokenCategory.WHITESPACE, TokenCategory.NAME, TokenCategory.BUILT_IN_NAME,

    NESTING_BOUNDARY = "<"
    NAMESPACE_SEPARATOR = "."
    FILE_EXTENSIONS = ".h", ".m", ".mm"

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name in cls.LANGUAGE_BUILT_IN_TYPES or type_name.startswith("NS")

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        if name.endswith("-p"):
            return name[:-2]
        return name

    @classmethod
    def full_name(cls, name: str, parent: str = "", kind: Optional[str] = None) -> str:
        if kind in ("enum", "enumvalue", "interface", "protocol"):
            return name
        return super().full_name(name, parent, kind)

    @classmethod
    def namespace_and_name(cls,
                           full_name: str,
                           kind: Optional[str] = None) -> Tuple[Optional[str], str]:
        if kind in ("enum", "enumvalue", "interface", "protocol"):
            return None, full_name
        return super().namespace_and_name(full_name, kind)

    @classmethod
    def is_member_blacklisted(cls, kind: str, name: str) -> bool:
        return kind == "function" and name == "NS_ENUM"


class ObjectiveCTypeParser(TypeParser):
    "Parser for Objective C types." ""
    TRAITS = ObjectiveCTraits

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        tokens = super().adapt_tokens(tokens, array_tokens)
        tokens = cls.remove_block_prefix(tokens)
        tokens = cls.classify_arg_names(tokens, list(cls.TRAITS.ALLOWED_SUFFIXES))
        tokens = cls.remove_invalid(tokens)
        tokens = cls.move_array_definition(tokens)
        tokens = cls.classify_array_size(tokens)
        return tokens

    @staticmethod
    def remove_block_prefix(tokens: List[Token]) -> List[Token]:
        """Remove `(^)` from blocks."""
        for match in find_tokens(tokens, [
            [TokenCategory.ARGS_START],
            [TokenCategory.WHITESPACE, None],
            [TokenCategory.BLOCK],
            [TokenCategory.WHITESPACE, None],
            [TokenCategory.ARGS_END],
        ]):
            for t in match:
                t.category = TokenCategory.INVALID
        return tokens


class ObjectiveCParser(LanguageParser):
    """Parser for Objective C documentation."""
    TRAITS = ObjectiveCTraits
    TYPE_PARSER = ObjectiveCTypeParser

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Compound]:
        memberdef_element = self._fix_block_element(memberdef_element)
        member = super().parse_member(memberdef_element, parent)
        member = self._fix_enclosed_type_visibility(member, parent)
        return member

    def parse_enumvalue(self, enumvalue_element: ET.Element, parent_name: str) -> Compound:
        enumvalue = super().parse_enumvalue(enumvalue_element, parent_name)
        enumvalue.prot = "public"
        return enumvalue

    def _fix_block_element(self, memberdef_element: ET.Element) -> ET.Element:
        if memberdef_element.get("kind", "") not in ("variable", "typedef"):
            return memberdef_element

        type_element = memberdef_element.find("type")
        if type_element is None:
            return memberdef_element

        type_text = type_element.text
        args_string = memberdef_element.findtext("argsstring", "")
        if not type_text or "(^" not in type_text or ")(" not in args_string:
            return memberdef_element

        type_text = type_text[:type_text.find("(^")]
        type_text += args_string[args_string.find(")(") + 1:]

        type_element.text = type_text
        memberdef_element.set("kind", "block")

        return memberdef_element

    def _fix_enclosed_type_visibility(self, member: Optional[Compound],
                                      parent: Compound) -> Optional[Compound]:
        """Match the visibility of enclosed types to the enclosing type's visibility.

        There is no such thing as protected or private enclosed types in Objective C. When an object
        is exposed in a header file, it is accessible, period.
        """
        if member is None:
            return None

        if (member.kind in ("enum", "typedef", "class", "protocol", "enumvalue")
                and parent.kind in ("class", "protocol", "enum")):
            member.prot = parent.prot
        return member
