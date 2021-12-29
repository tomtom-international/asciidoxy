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
"""Parse the Doxygen XML schema and verify all elements are supported by the AsciiDoxy parser."""

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Set

from asciidoxy.parser.doxygen.description_parser import (
    IGNORE,
    NEW_ELEMENT,
    UNSUPPORTED,
    UPDATE_PARENT,
    USE_PARENT,
    SpecialCharacter,
)


def _xsd(tag: str) -> str:
    return f"{{http://www.w3.org/2001/XMLSchema}}{tag}"


class XsdElement:
    name: str
    type: str

    def __init__(self, name: str, type: str):
        self.name = name
        self.type = type

    @classmethod
    def from_xml(cls, element: ET.Element) -> "XsdElement":
        return cls(name=element.get("name", ""), type=element.get("type", ""))


class XsdGroup:
    name: str
    elements: Dict[str, XsdElement]

    def __init__(self, name: str):
        self.name = name
        self.elements = {}

    @classmethod
    def from_xml(cls, element: ET.Element) -> "XsdGroup":
        instance = cls(name=element.get("name", ""))
        instance.elements = parse_element_sequence(element, _xsd("choice"))
        return instance


class XsdComplexType(XsdGroup):
    groups: List[str]

    def __init__(self, name: str):
        super().__init__(name)
        self.groups = []

    @classmethod
    def from_xml(cls, element: ET.Element) -> "XsdComplexType":
        instance = cls(name=element.get("name", ""))
        instance.elements = parse_element_sequence(element, _xsd("sequence"))
        instance.groups = [xml_group.get("ref", "") for xml_group in element.findall(_xsd("group"))]
        return instance


def parse_element_sequence(xml_parent: ET.Element, name: str) -> Dict[str, XsdElement]:
    sequence_element = xml_parent.find(name)

    if sequence_element is not None:
        return {
            element.name: element
            for element in (XsdElement.from_xml(xml_element)
                            for xml_element in sequence_element.findall(_xsd("element")))
        }

    else:
        return {}


class XsdSchema:
    groups: Dict[str, XsdGroup]
    complex_types: Dict[str, XsdComplexType]

    def __init__(self):
        self.groups = {}
        self.complex_types = {}

    @classmethod
    def from_file(cls, file_path: Path) -> "XsdSchema":
        return cls.from_xml(ET.parse(file_path).getroot())

    @classmethod
    def from_xml(cls, element: ET.Element) -> "XsdSchema":
        assert element.tag == _xsd("schema")
        instance = cls()
        instance.groups = {
            group.name: group
            for group in (XsdGroup.from_xml(xml_group)
                          for xml_group in element.findall(_xsd("group")))
        }
        instance.complex_types = {
            complex_type.name: complex_type
            for complex_type in (XsdComplexType.from_xml(xml_complex_type)
                                 for xml_complex_type in element.findall(_xsd("complexType")))
        }
        return instance

    def find_all_elements(self, parent_type_name: str) -> Set[str]:
        unique_element_names = set()
        checked_group_names = set()
        checked_type_names = set()
        unchecked_type_names = {parent_type_name}

        while unchecked_type_names:
            type_name_to_check = unchecked_type_names.pop()
            checked_type_names.add(type_name_to_check)

            current_type = self.complex_types.get(type_name_to_check)
            if current_type is None:
                # Probably a primitive
                continue

            for element_name, element in current_type.elements.items():
                unique_element_names.add(element_name)
                if element.type not in checked_type_names:
                    unchecked_type_names.add(element.type)

            for group_name in current_type.groups:
                if group_name in checked_group_names:
                    continue

                current_group = self.groups.get(group_name)
                assert current_group is not None

                for element_name, element in current_group.elements.items():
                    unique_element_names.add(element_name)
                    if element.type not in checked_type_names:
                        unchecked_type_names.add(element.type)

        return unique_element_names


def test_doxygen_schema__description_parser(xml_data):
    compound_xsd = xml_data / "cpp/default/xml/compound.xsd"
    assert compound_xsd.is_file()
    schema = XsdSchema.from_file(compound_xsd)

    compounddef_type = schema.complex_types.get("compounddefType")
    assert compounddef_type is not None

    assert "briefdescription" in compounddef_type.elements
    assert "detaileddescription" in compounddef_type.elements
    assert (compounddef_type.elements["briefdescription"].type ==
            compounddef_type.elements["detaileddescription"].type)
    all_elements = schema.find_all_elements(compounddef_type.elements["briefdescription"].type)

    unsupported_elements = (all_elements - NEW_ELEMENT.keys() - UPDATE_PARENT.keys() -
                            USE_PARENT.keys() - IGNORE - SpecialCharacter.SPECIAL_CHARACTERS.keys())

    assert not unsupported_elements - UNSUPPORTED.keys()
