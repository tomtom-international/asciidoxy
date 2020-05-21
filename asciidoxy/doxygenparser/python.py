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
"""Support for parsing python documentation."""

import re

import xml.etree.ElementTree as ET

from typing import Optional

from ..model import Compound, Member, Parameter
from .language_traits import LanguageTraits
from .parser_base import ParserBase


class PythonTraits(LanguageTraits):
    """Traits for parsing python documentation."""
    TAG: str = "python"

    TYPE_PREFIXES = None
    TYPE_SUFFIXES = None
    TYPE_NESTED_START = re.compile(r"\s*\[\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*\]")
    TYPE_NAME = re.compile(r"\"?[a-zA-Z0-9_.]+\"?")

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        return name.replace("::", ".").replace('"', "").strip()

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


class PythonParser(ParserBase):
    """Parser for python documentation."""
    TRAITS = PythonTraits

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = super().parse_member(memberdef_element, parent)

        if member and member.returns and member.returns.type and member.returns.type.name == "def":
            # Workaround for Doxygen issue
            member.returns = None

        return member

    def parse_array(self, array_element: Optional[ET.Element], param: Parameter):
        if array_element is None or param.type is None:
            return
        if not array_element.text:
            return

        # TODO: This is ugly. Type parsing needs refactoring.
        type_element = ET.Element("type")
        type_element.text = f"{param.type.name}{array_element.text}"
        type_ref = self.parse_type(type_element)

        if type_ref is not None and type_ref.nested:
            param.type.nested = type_ref.nested
