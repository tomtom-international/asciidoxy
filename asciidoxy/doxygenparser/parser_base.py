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

from abc import ABC
from typing import List, Optional, Tuple, Type, Union

from .description_parser import DescriptionParser, select_descriptions
from .driver_base import DriverBase
from .language_traits import LanguageTraits
from .type_parser import parse_type
from ..model import (Compound, EnumValue, Member, Parameter, ReturnValue, ThrowsClause, TypeRef,
                     InnerTypeReference)

logger = logging.getLogger(__name__)


def _yes_no_to_bool(yes_no: str) -> bool:
    if yes_no == "yes":
        return True
    return False


class ParserBase(ABC):
    """Base functionality for language parsers."""
    TRAITS: Type[LanguageTraits]

    _driver: DriverBase

    def __init__(self, driver: DriverBase):
        self._driver = driver

    def parse_description(self, description_element: Optional[ET.Element]) -> str:
        if description_element is None:
            return ""

        return DescriptionParser(self.TRAITS.TAG).parse(description_element)

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
            self.parse_array(param_element.find("array"), param)

            matching_descriptions = [desc for name, desc in descriptions if name == param.name]
            if matching_descriptions:
                if len(matching_descriptions) > 1:
                    logger.debug(f"Multiple descriptions for parameter {param.name}")
                param.description = matching_descriptions[0]

            params.append(param)
        return params

    def parse_array(self, array_element: Optional[ET.Element], param: Parameter):
        pass

    def parse_type(self,
                   type_element: Optional[ET.Element],
                   parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
        if type_element is None:
            return None

        type_ref = parse_type(self.TRAITS, self._driver, type_element, parent)

        if type_ref is not None and type_ref.name:
            return type_ref
        else:
            return None

    def parse_exceptions(self, memberdef_element: ET.Element, parent: Member) -> List[ThrowsClause]:
        exceptions = []
        for name, desc in self.parse_parameterlist(memberdef_element, "exception"):
            exception = ThrowsClause(self.TRAITS.TAG)
            exception.type = TypeRef(name=name, language=self.TRAITS.TAG)
            exception.type.namespace = parent.namespace
            exception.description = desc
            exceptions.append(exception)
            self._driver.unresolved_ref(exception.type)
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
            v = EnumValue(self.TRAITS.TAG)
            v.id = self.TRAITS.unique_id(enumvalue_element.get("id"))

            name = self.TRAITS.cleanup_name(enumvalue_element.findtext("name", ""))
            v.name = self.TRAITS.short_name(name)
            v.full_name = self.TRAITS.full_name(name, parent_name)

            v.initializer = enumvalue_element.findtext("initializer", "")
            v.brief, v.description = select_descriptions(
                self.parse_description(enumvalue_element.find("briefdescription")),
                self.parse_description(enumvalue_element.find("detaileddescription")))

            values.append(v)
            self._driver.register(v)

        return values

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Member]:
        member = Member(self.TRAITS.TAG)
        member.id = self.TRAITS.unique_id(memberdef_element.get("id"))
        member.kind = memberdef_element.get("kind", "")
        member.prot = memberdef_element.get("prot", "")

        name = self.TRAITS.cleanup_name(memberdef_element.findtext("name", ""))
        member.name = self.TRAITS.short_name(name)
        member.full_name = self.TRAITS.full_name(name, parent.full_name)
        member.namespace = self.TRAITS.namespace(member.full_name)
        member.include = parent.include

        if self.TRAITS.is_member_blacklisted(member.kind, member.name):
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

        self._driver.register(member)
        return member

    def parse_innerclass(self, parent: Compound, parent_compound: ET.Element) \
            -> List[InnerTypeReference]:
        inner_classes = []

        for xml_inner_class in parent_compound.iterfind("innerclass"):
            type_visibility = xml_inner_class.get("prot")
            if type_visibility not in ("public", "protected", None):
                continue

            inner_type = InnerTypeReference(parent.language)
            inner_type.id = self.TRAITS.unique_id(xml_inner_class.get("refid"))
            inner_type.name = \
                self.TRAITS.cleanup_name(xml_inner_class.text if xml_inner_class.text else "")
            inner_type.namespace = parent.full_name

            inner_classes.append(inner_type)
            self._driver.unresolved_ref(inner_type)

        return inner_classes

    def parse_compounddef(self, compounddef_element: ET.Element) -> None:
        compound = Compound(self.TRAITS.TAG)
        compound.id = self.TRAITS.unique_id(compounddef_element.get("id"))
        compound.kind = compounddef_element.get("kind", "")

        name = self.TRAITS.cleanup_name(compounddef_element.findtext("compoundname", ""))
        compound.name = self.TRAITS.short_name(name)
        compound.full_name = self.TRAITS.full_name(name)
        compound.namespace = self.TRAITS.namespace(compound.full_name)
        compound.include = self.find_include(compounddef_element)

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

        self._driver.register(compound)

    def find_include(self, element: ET.Element) -> Optional[str]:
        include = element.findtext("includes")

        if include is None:
            location_element = element.find("location")
            if location_element is not None:
                include = location_element.get("file", None)

        return include
