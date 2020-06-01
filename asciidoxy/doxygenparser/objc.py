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
"""Support for Objective-C documentation."""

import re
import string

import xml.etree.ElementTree as ET

from typing import Optional

from .language_traits import LanguageTraits, TokenType
from .parser_base import ParserBase
from .type_parser import TypeParser
from ..model import Compound, Member, Parameter, ReturnValue


class ObjectiveCTraits(LanguageTraits):
    """Traits for parsing Objective C documentation."""
    TAG: str = "objc"

    LANGUAGE_BUILD_IN_TYPES = ("char", "unsigned char", "signed char", "int", "short", "long",
                               "float", "double", "void", "bool", "BOOL", "id", "instancetype",
                               "short int", "signed short", "signed short int", "unsigned short",
                               "unsigned short int", "signed int", "unsigned int", "long int",
                               "signed long", "signed long int", "unsigned long",
                               "unsigned long int", "long long", "long long int",
                               "signed long long", "signed long long int", "unsigned long long",
                               "unsigned long long int", "signed char", "long double")

    BLOCK = re.compile(r"typedef (.+)\(\^(.+)\)\s*\((.*)\)")

    NESTED_STARTS = "<",
    NESTED_ENDS = ">",
    NESTED_SEPARATORS = ",",
    OPERATORS = "*",
    QUALIFIERS = "nullable", "const", "__weak", "__strong",

    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + OPERATORS +
                        tuple(string.whitespace))

    ALLOWED_PREFIXES = TokenType.WHITESPACE, TokenType.QUALIFIER,
    ALLOWED_SUFFIXES = TokenType.WHITESPACE, TokenType.OPERATOR
    ALLOWED_NAMES = TokenType.WHITESPACE, TokenType.NAME,

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name in cls.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("NS")

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        if name.endswith("-p"):
            return name[:-2]
        return name

    @classmethod
    def full_name(cls, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        if parent.endswith(".h"):
            # Parent is a header file, do not prepend
            return name
        return f"{parent}.{name}"

    @classmethod
    def namespace(cls, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None

    @classmethod
    def is_member_blacklisted(cls, kind: str, name: str) -> bool:
        return kind == "function" and name == "NS_ENUM"


class ObjectiveCTypeParser(TypeParser):
    "Parser for Objective C types." ""
    TRAITS = ObjectiveCTraits


class ObjectiveCParser(ParserBase):
    """Parser for Objective C documentation."""
    TRAITS = ObjectiveCTraits
    TYPE_PARSER = ObjectiveCTypeParser

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = super().parse_member(memberdef_element, parent)
        if member is None:
            return None

        if member.kind in ("variable", "typedef") and "^" in member.definition:
            self._redefine_as_block(member, parent)

        return member

    def _redefine_as_block(self, member: Member, parent: Compound) -> None:
        block_match = self.TRAITS.BLOCK.search(member.definition)
        if not block_match:
            return

        return_type = block_match.group(1)
        name = block_match.group(2).strip()
        args = block_match.group(3).strip()

        member.kind = "block"
        member.name = name

        def type_from_text(text):
            type_element = ET.Element("type")
            type_element.text = text
            return self.parse_type(type_element, member)

        member.returns = ReturnValue()
        member.returns.type = type_from_text(return_type)

        if args:
            for arg in args.split(","):
                param = Parameter()
                param.type = type_from_text(arg.strip())
                member.params.append(param)
