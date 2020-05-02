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

import xml.etree.ElementTree as ET

from typing import Optional

from .language_base import Language
from ..model import Compound, Member, Parameter, ReturnValue


class ObjectiveCLanguage(Language):
    """Language support for Objective C."""
    TAG: str = "objc"

    TYPE_PREFIXES = re.compile(r"((nullable|const|__weak|__strong)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"(\s*\*\s*?)+")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"((unsigned|signed|short|long)\s+)*[a-zA-Z0-9_:]+")

    BLOCK = re.compile(r"typedef (.+)\(\^(.+)\)\s*\((.*)\)")

    LANGUAGE_BUILD_IN_TYPES = ("char", "unsigned char", "signed char", "int", "unsigned int",
                               "short", "unsigned short", "long", "unsigned long", "float",
                               "double", "long double", "void", "bool", "BOOL", "id",
                               "instancetype")

    def is_language_standard_type(self, type_name: str) -> bool:
        return type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("NS")

    def cleanup_name(self, name: str) -> str:
        if name.endswith("-p"):
            return name[:-2]
        return name

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        if parent.endswith(".h"):
            # Parent is a header file, do not prepend
            return name
        return f"{parent}.{name}"

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = super().parse_member(memberdef_element, parent)
        if member is None:
            return None

        if member.kind in ("variable", "typedef") and "^" in member.definition:
            self._redefine_as_block(member, parent)

        return member

    def _redefine_as_block(self, member: Member, parent: Compound) -> None:
        block_match = self.BLOCK.search(member.definition)
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

    def namespace(self, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return kind == "function" and name == "NS_ENUM"
