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
"""Base support for parsing documentation for different languages."""

import logging
import xml.etree.ElementTree as ET
from abc import ABC
from typing import Dict, List, Optional, Type

from ...model import Compound, Parameter, ReturnValue, ThrowsClause, TypeRef
from .description_parser import (
    Admonition,
    NestedDescriptionElement,
    ParaContainer,
    ParameterItem,
    ParameterList,
    Ref,
    parse_description,
    select_descriptions,
)
from .driver_base import DriverBase
from .language_traits import LanguageTraits
from .type_parser import TypeParseError, TypeParser

logger = logging.getLogger(__name__)


def _yes_no_to_bool(yes_no: str) -> bool:
    if yes_no == "yes":
        return True
    return False


def _to_asciidoc_or_empty(description: Optional[NestedDescriptionElement]) -> str:
    if description is not None:
        if isinstance(description, (Admonition, Ref)):
            # Use a clean Para container to prevent creating a "sidebar" or link.
            return ParaContainer(description.language_tag, *description.contents).to_asciidoc()
        else:
            return description.to_asciidoc()
    return ""


def _pop_sections(description: Optional[ParaContainer]) -> Dict[str, str]:
    if description is None:
        return {}

    sections = {}
    for section_name, section_title in {
            "author": "Author",
            "bug": "Bug",
            "copyright": "Copyright",
            "date": "Date",
            "deprecated": "Deprecated",
            "pre": "Precondition",
            "post": "Postcondition",
            "since": "Since",
            "todo": "Todo",
    }.items():
        section = description.pop_section(Admonition, section_name)
        if section is not None:
            sections[section_title] = _to_asciidoc_or_empty(section)
    return sections


def _find_parameter_documentation(descriptions: ParameterList,
                                  name: str) -> Optional[ParameterItem]:
    for param_item in descriptions.children_of_type(ParameterItem):
        for param_name in param_item.names():
            if param_name.name == name:
                return param_item
    return None


class ParserBase(ABC):
    """Base functionality for language parsers.

    The parser is mostly anemic by design: there is no internal state that changes during parsing.

    Attributes:
        TRAITS:      Specifics for the language grammar to parse.
        TYPE_PARSER: Specific type parser for the langugage.
    """
    TRAITS: Type[LanguageTraits]
    TYPE_PARSER: Type[TypeParser]

    _driver: DriverBase

    def __init__(self, driver: DriverBase):
        self._driver = driver

    def parse_parameters(self, memberdef_element: ET.Element, parent: Compound,
                         descriptions: Optional[ParameterList]) -> List[Parameter]:
        params = []
        for param_element in memberdef_element.iterfind("param"):
            param = Parameter()
            param.type = self.parse_type(param_element.find("type"),
                                         param_element.find("array"),
                                         namespace=parent.namespace)
            param.name = param_element.findtext("declname", "")
            param.default_value = param_element.findtext("defval", "")

            if descriptions:
                documentation = _find_parameter_documentation(descriptions, param.name)
                if documentation:
                    param.description = _to_asciidoc_or_empty(documentation.description())

            params.append(param)
        return params

    def parse_type(self,
                   type_element: Optional[ET.Element],
                   array_element: Optional[ET.Element] = None,
                   namespace: Optional[str] = None) -> Optional[TypeRef]:
        if type_element is None:
            return None

        try:
            return self.TYPE_PARSER.parse_xml(type_element,
                                              array_element,
                                              driver=self._driver,
                                              namespace=namespace)
        except TypeParseError:
            logger.exception(
                f"Failed to parse type {ET.tostring(type_element, encoding='unicode')}.")
            return None

    def parse_exceptions(self, memberdef_element: ET.Element, parent: Compound,
                         descriptions: Optional[ParameterList]) -> List[ThrowsClause]:
        exceptions = []
        if descriptions:
            for desc in descriptions.children_of_type(ParameterItem):
                exception = ThrowsClause(self.TRAITS.TAG)

                name = desc.first_name()
                assert name is not None
                ref = name.first_child_of_type(Ref)
                if name.contents and ref is not None:
                    refid = None
                    if ref.refid:
                        refid = f"{self.TRAITS.TAG}-{ref.refid}"
                    exception.type = TypeRef(id=refid,
                                             kind=ref.kindref,
                                             name=_to_asciidoc_or_empty(ref),
                                             language=self.TRAITS.TAG)
                elif name.name:
                    exception.type = TypeRef(name=name.name, language=self.TRAITS.TAG)
                else:
                    assert False, "Expected either type ref or name"

                exception.type.namespace = parent.namespace
                exception.description = _to_asciidoc_or_empty(desc.description())

                exceptions.append(exception)
                if not exception.type.id:
                    self._driver.unresolved_ref(exception.type)
        return exceptions

    def parse_returns(self, memberdef_element: ET.Element, parent: Compound,
                      description: Optional[Admonition]) -> Optional[ReturnValue]:
        returns = ReturnValue()
        returns.type = self.parse_type(memberdef_element.find("type"), namespace=parent.namespace)
        returns.description = _to_asciidoc_or_empty(description)

        if returns.type:
            return returns
        else:
            return None

    def parse_enumvalues(self, container_element: ET.Element, parent_name: str) -> List[Compound]:
        return [
            self.parse_enumvalue(enumvalue_element, parent_name)
            for enumvalue_element in container_element.iterfind("enumvalue")
        ]

    def parse_enumvalue(self, enumvalue_element: ET.Element, parent_name: str) -> Compound:
        enumvalue = Compound(self.TRAITS.TAG, kind="enumvalue")
        enumvalue.id = self.TRAITS.unique_id(enumvalue_element.get("id"))
        enumvalue.prot = enumvalue_element.get("prot", "")

        enumvalue.name, enumvalue.full_name, _ = self.TRAITS.names(
            enumvalue_element.findtext("name", ""), parent_name, "enumvalue")

        enumvalue.initializer = enumvalue_element.findtext("initializer", "")
        enumvalue.brief, enumvalue.description = select_descriptions(
            parse_description(enumvalue_element.find("briefdescription"), self.TRAITS.TAG),
            parse_description(enumvalue_element.find("detaileddescription"), self.TRAITS.TAG))

        self._driver.register(enumvalue)
        return enumvalue

    def parse_member(self, memberdef_element: ET.Element, parent: Compound) -> Optional[Compound]:
        member = Compound(self.TRAITS.TAG)
        member.id = self.TRAITS.unique_id(memberdef_element.get("id"))
        member.kind = memberdef_element.get("kind", "")
        member.prot = memberdef_element.get("prot", "")

        member.name, member.full_name, member.namespace = self.TRAITS.names(
            memberdef_element.findtext("name", ""), parent.full_name, member.kind)
        member.include = self.find_include(memberdef_element)

        if self.TRAITS.is_member_blacklisted(member.kind, member.name):
            return None

        brief = parse_description(memberdef_element.find("briefdescription"), self.TRAITS.TAG)
        detailed = parse_description(memberdef_element.find("detaileddescription"), self.TRAITS.TAG)

        # First extract other descriptions
        member.returns = self.parse_returns(memberdef_element, member,
                                            detailed.pop_section(Admonition, "return"))
        member.params = self.parse_parameters(memberdef_element, member,
                                              detailed.pop_section(ParameterList, "param"))
        member.exceptions = self.parse_exceptions(memberdef_element, member,
                                                  detailed.pop_section(ParameterList, "exception"))
        member.sections = _pop_sections(detailed)

        # Then generate description with unused sections
        member.brief, member.description = select_descriptions(brief, detailed)

        member.definition = memberdef_element.findtext("definition", "")
        member.args = memberdef_element.findtext("argsstring", "")
        member.members = self.parse_enumvalues(memberdef_element, member.full_name)
        member.static = _yes_no_to_bool(memberdef_element.get("static", "no"))
        member.const = _yes_no_to_bool(memberdef_element.get("const", "no"))
        member.constexpr = _yes_no_to_bool(memberdef_element.get("constexpr", "no"))

        self._driver.register(member)
        return member

    def parse_innerclass(self, parent: Compound, innerclass_element: ET.Element) -> None:
        inner_type = TypeRef(parent.language)
        inner_type.id = self.TRAITS.unique_id(innerclass_element.get("refid"))
        inner_type.name = \
            self.TRAITS.cleanup_name(innerclass_element.text if innerclass_element.text else "")
        inner_type.namespace = parent.full_name
        inner_type.prot = innerclass_element.get("prot", "")

        self._driver.inner_type_ref(parent, inner_type)

    def parse_compounddef(self, compounddef_element: ET.Element) -> None:
        compound = Compound(self.TRAITS.TAG)
        compound.id = self.TRAITS.unique_id(compounddef_element.get("id"))
        compound.kind = compounddef_element.get("kind", "")
        compound.prot = compounddef_element.get("prot", "")

        compound.name, compound.full_name, compound.namespace = self.TRAITS.names(
            compounddef_element.findtext("compoundname", ""), kind=compound.kind)
        compound.include = self.find_include(compounddef_element)

        compound.members = [
            member
            for member in (self.parse_member(memberdef, compound)
                           for memberdef in compounddef_element.iterfind("sectiondef/memberdef"))
            if member is not None
        ] + self.parse_enumvalues(compounddef_element, compound.full_name)

        brief = parse_description(compounddef_element.find("briefdescription"), self.TRAITS.TAG)
        detailed = parse_description(compounddef_element.find("detaileddescription"),
                                     self.TRAITS.TAG)

        # First extract other descriptions
        compound.sections = _pop_sections(detailed)

        # Then generate description with unused sections
        compound.brief, compound.description = select_descriptions(brief, detailed)

        for innerclass_element in compounddef_element.iterfind("innerclass"):
            self.parse_innerclass(compound, innerclass_element)

        self._driver.register(compound)

    def find_include(self, element: ET.Element) -> Optional[str]:
        include = element.findtext("includes")

        if include is None:
            location_element = element.find("location")
            if location_element is not None:
                include = location_element.get("declfile", None)
                if include is None:
                    include = location_element.get("file", None)

        return include
