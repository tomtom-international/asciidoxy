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
"""Base support for parsing documentation for different languages."""

import logging

import xml.etree.ElementTree as ET

from abc import ABC, abstractmethod
from typing import List, Optional, Pattern, Tuple, Union

from .description_parser import DescriptionParser, select_descriptions
from ..model import (Compound, EnumValue, Member, Parameter, ReturnValue, ThrowsClause, TypeRef,
                     InnerTypeReference, ReferableElement, TypeRefBase)

logger = logging.getLogger(__name__)


def _yes_no_to_bool(yes_no: str) -> bool:
    if yes_no == "yes":
        return True
    return False


class ParserBase(ABC):
    """Base class for parsers."""
    @abstractmethod
    def register(self, element: ReferableElement) -> None:
        """Register a new element."""
        pass

    @abstractmethod
    def unresolved_ref(self, ref: TypeRefBase) -> None:
        """Register an unresolved reference."""
        pass


class Language(object):
    """Definition of language support for parsing Doxygen XML output.

    Attributes:
        TAG:                   Tag for identifying the language.
        TYPE_PREFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a prefix to the type.
        TYPE_SUFFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a suffix to the type.
        TYPE_NESTED_START:     Pattern matching the start of a nested type.
        TYPE_NESTED_SEPARATOR: Pattern matching a separator between multiple nested types.
        TYPE_NESTED_END:       Pattern matching the end of a nested type.
        TYPE_NAME:             Pattern matching a type's name.
    """

    TAG: str

    TYPE_PREFIXES: Optional[Pattern]
    TYPE_SUFFIXES: Optional[Pattern]
    TYPE_NESTED_START: Pattern
    TYPE_NESTED_SEPARATOR: Pattern
    TYPE_NESTED_END: Pattern
    TYPE_NAME: Pattern

    _parser: ParserBase

    def __init__(self, parser: ParserBase):
        self._parser = parser

    def parse_description(self, description_element: Optional[ET.Element]) -> str:
        if description_element is None:
            return ""

        return DescriptionParser(self.TAG).parse(description_element)

    def parse_parameterlist(self, memberdef_element: ET.Element,
                            kind: str) -> List[Tuple[str, str]]:
        descriptions = []
        for parameter_item in memberdef_element.iterfind(
                f"detaileddescription/para/parameterlist[@kind='{kind}']/parameteritem"):
            desc = self.parse_description(parameter_item.find("parameterdescription"))
            for parameter_name in parameter_item.iterfind("parameternamelist/parametername"):
                if parameter_name.text:
                    descriptions.append((parameter_name.text, desc))
        return descriptions

    def parse_parameters(self, memberdef_element: ET.Element, parent: Member) -> List[Parameter]:
        descriptions = self.parse_parameterlist(memberdef_element, "param")
        params = []
        for param_element in memberdef_element.iterfind("param"):
            param = Parameter()
            param.type = self.parse_type(param_element.find("type"), parent)
            param.name = param_element.findtext("declname") or ""

            matching_descriptions = [desc for name, desc in descriptions if name == param.name]
            if matching_descriptions:
                if len(matching_descriptions) > 1:
                    logger.debug(f"Multiple descriptions for parameter {param.name}")
                param.description = matching_descriptions[0]

            params.append(param)
        return params

    def parse_type(self,
                   type_element: Optional[ET.Element],
                   parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
        if type_element is None:
            return None

        def match_and_extract(regex, text):
            if regex is not None and text:
                match = regex.match(text)
                if match:
                    return match.group(0), text[match.end():]

            return None, text

        def extract_type(element_iter, text):
            type_ref = TypeRef(self.TAG)
            if isinstance(parent, Compound):
                type_ref.namespace = parent.full_name
            elif isinstance(parent, Member):
                type_ref.namespace = parent.namespace

            type_ref.prefix, text = match_and_extract(self.TYPE_PREFIXES, text)

            if not text:
                try:
                    element = next(element_iter)
                    type_ref.id = self.unique_id(element.get("refid"))
                    type_ref.kind = element.get("kindref", None)
                    type_ref.name = self.cleanup_name(element.text or "")
                    text = element.tail

                except StopIteration:
                    pass
            else:
                type_ref.name, text = match_and_extract(self.TYPE_NAME, text)
                if type_ref.name is not None:
                    type_ref.name = self.cleanup_name(type_ref.name)

            start_nested, text = match_and_extract(self.TYPE_NESTED_START, text)
            if start_nested:
                while True:
                    nested_type_ref, text = extract_type(element_iter, text)
                    if nested_type_ref and nested_type_ref.name:
                        type_ref.nested.append(nested_type_ref)
                    else:
                        # TODO Error?
                        break

                    end_nested, text = match_and_extract(self.TYPE_NESTED_END, text)
                    if end_nested:
                        break

                    _, text = match_and_extract(self.TYPE_NESTED_SEPARATOR, text)

            type_ref.suffix, text = match_and_extract(self.TYPE_SUFFIXES, text)

            # doxygen inserts empty <type> tag for return value in constructors,
            # this fake types should be filtered out
            if type_ref.name:
                if not type_ref.id and not self.is_language_standard_type(type_ref.name):
                    self._parser.unresolved_ref(type_ref)

            return type_ref, text

        type_ref, _ = extract_type(type_element.iter("ref"), type_element.text)

        if type_ref.name:
            return type_ref
        else:
            return None

    def parse_exceptions(self, memberdef_element: ET.Element, parent: Member) -> List[ThrowsClause]:
        exceptions = []
        for name, desc in self.parse_parameterlist(memberdef_element, "exception"):
            exception = ThrowsClause(self.TAG)
            exception.type = TypeRef(name=name, language=self.TAG)
            exception.type.namespace = parent.namespace
            exception.description = desc
            exceptions.append(exception)
            self._parser.unresolved_ref(exception.type)
        return exceptions

    def parse_returns(self, memberdef_element: ET.Element, parent: Member) -> Optional[ReturnValue]:
        returns = ReturnValue()
        returns.type = self.parse_type(memberdef_element.find("type"), parent)

        description = memberdef_element.find("detaileddescription/para/simplesect[@kind='return']")
        if description:
            returns.description = self.parse_description(description)

        if returns.type:
            return returns
        else:
            return None

    def parse_enumvalues(self, container_element: ET.Element, parent_name: str) -> List[EnumValue]:
        values = []
        for enumvalue_element in container_element.iterfind("enumvalue"):
            v = EnumValue(self.TAG)
            v.id = self.unique_id(enumvalue_element.get("id"))

            name = self.cleanup_name(enumvalue_element.findtext("name", ""))
            v.name = self.short_name(name)
            v.full_name = self.full_name(name, parent_name)

            v.initializer = enumvalue_element.findtext("initializer", "")
            v.brief, v.description = select_descriptions(
                self.parse_description(enumvalue_element.find("briefdescription")),
                self.parse_description(enumvalue_element.find("detaileddescription")))

            values.append(v)
            self._parser.register(v)

        return values

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = Member(self.TAG)
        member.id = self.unique_id(memberdef_element.get("id"))
        member.kind = memberdef_element.get("kind", "")
        member.prot = memberdef_element.get("prot", "")

        name = self.cleanup_name(memberdef_element.findtext("name", ""))
        member.name = self.short_name(name)
        member.full_name = self.full_name(name, parent.full_name)
        member.namespace = self.namespace(member.full_name)

        if self.is_member_blacklisted(member.kind, member.name):
            return None

        member.definition = memberdef_element.findtext("definition", "")
        member.args = memberdef_element.findtext("argsstring", "")
        member.params = self.parse_parameters(memberdef_element, member)
        member.exceptions = self.parse_exceptions(memberdef_element, member)
        member.brief, member.description = select_descriptions(
            self.parse_description(memberdef_element.find("briefdescription")),
            self.parse_description(memberdef_element.find("detaileddescription")))
        member.returns = self.parse_returns(memberdef_element, member)
        member.enumvalues = self.parse_enumvalues(memberdef_element, member.full_name)
        member.static = _yes_no_to_bool(memberdef_element.get("static", "false"))

        self._parser.register(member)
        return member

    def parse_innerclass(self, parent: Compound, parent_compound: ET.Element) \
            -> List[InnerTypeReference]:
        inner_classes = []

        for xml_inner_class in parent_compound.iterfind("innerclass"):
            type_visibility = xml_inner_class.get("prot")
            if type_visibility not in ("public", "protected", None):
                continue

            inner_type = InnerTypeReference(parent.language)
            inner_type.id = self.unique_id(xml_inner_class.get("refid"))
            inner_type.name = \
                self.cleanup_name(xml_inner_class.text if xml_inner_class.text else "")
            inner_type.namespace = parent.full_name

            inner_classes.append(inner_type)
            self._parser.unresolved_ref(inner_type)

        return inner_classes

    def parse_compounddef(self, compounddef_element: ET.Element) -> None:
        compound = Compound(self.TAG)
        compound.id = self.unique_id(compounddef_element.get("id"))
        compound.kind = compounddef_element.get("kind", "")

        name = self.cleanup_name(compounddef_element.findtext("compoundname", ""))
        compound.name = self.short_name(name)
        compound.full_name = self.full_name(name)
        compound.namespace = self.namespace(compound.full_name)

        compound.members = [
            member
            for member in (self.parse_member(memberdef, compound)
                           for memberdef in compounddef_element.iterfind("sectiondef/memberdef"))
            if member is not None
        ]
        compound.inner_classes = self.parse_innerclass(compound, compounddef_element)

        compound.brief, compound.description = select_descriptions(
            self.parse_description(compounddef_element.find("briefdescription")),
            self.parse_description(compounddef_element.find("detaileddescription")))
        compound.enumvalues = self.parse_enumvalues(compounddef_element, compound.full_name)
        compound.include = compounddef_element.findtext("includes")

        self._parser.register(compound)

    def unique_id(self, id: Optional[str]) -> Optional[str]:
        if not id:
            return None

        # Workaround a bug in asciidoctor: if there is an occurrence of __ the anchor is not parsed
        # correctly: #2746
        id = id.replace("__", "-")

        return f"{self.TAG}-{id}"

    def is_language_standard_type(self, type_name: str) -> bool:
        return False

    def cleanup_name(self, name: str) -> str:
        return name

    def short_name(self, name: str) -> str:
        return name

    def full_name(self, name: str, parent: str = "") -> str:
        return name

    def namespace(self, full_name: str) -> Optional[str]:
        return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return False
