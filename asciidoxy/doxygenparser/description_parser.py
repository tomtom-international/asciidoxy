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
"""Parser for descriptions in Doxygen XML output."""

import functools
import re

import xml.etree.ElementTree as ET

from typing import List, Optional, Tuple


def select_descriptions(brief: str, detailed: str) -> Tuple[str, str]:
    """Select the approprate brief and detailed descriptions.

    Sometimes one of the descriptions is missing. This method makes sure there is always at least
    a brief description.

    Args:
        brief: Brief description as found in the XML.
        detailed: Detailed description as found in the XML.

    Returns:
        brief: Brief description to use.
        detailed: Detailed description to use.
    """
    if not brief and detailed:
        if "\n" in detailed:
            brief, detailed = detailed.split("\n", maxsplit=1)
            return brief, detailed.strip()
        return detailed, ""

    return brief, detailed


class DescriptionParser(object):
    """Parse a description from XML and convert it to AsciiDoc.

    Attributes:
        language: Language to parse and return.
    """

    language: str
    _parts: List[str]

    def __init__(self, language: str):
        self.language = language
        self._parts = []

    def parse(self, element: ET.Element) -> str:
        """Parse a description from XML and convert it to AsciiDoc.

        Args:
            element: XML element to convert to AsciiDoc text.

        Returns:
            AsciiDoc text representation of the element.
        """
        self._parts = []
        self.parse_children(element)
        text = "".join(self._parts).strip()

        # Remove spaces before a line break
        text = re.sub(" *$", "", text, flags=re.MULTILINE)

        # Remove single space on new line
        text = re.sub(r"^ (\S)", r"\1", text, flags=re.MULTILINE)

        # No more than 2 consecutive line breaks
        text = re.sub("\n{3,}", "\n\n", text)

        return text

    def parse_children(self, element: ET.Element) -> None:
        for sub_element in element:
            method = getattr(self, f"parse_{sub_element.tag}")
            method(sub_element)

    def _default_parse(self, element: ET.Element, prefix=None, suffix=None) -> None:
        self.append(prefix)
        self.append(DescriptionParser._strip_line_ends(element.text))
        self.parse_children(element)
        self.append(suffix)
        self.append(DescriptionParser._strip_line_ends(element.tail))

    @staticmethod
    def _strip_line_ends(text: Optional[str]) -> Optional[str]:
        if text is None:
            return None
        return re.sub("\n$", " ", text, flags=re.MULTILINE)

    parse_para = functools.partialmethod(_default_parse, suffix="\n\n")
    parse_itemizedlist = functools.partialmethod(_default_parse, prefix="\n\n", suffix="\n")
    parse_listitem = functools.partialmethod(_default_parse, prefix="* ")
    parse_bold = functools.partialmethod(_default_parse, prefix="**", suffix="**")
    parse_computeroutput = functools.partialmethod(_default_parse, prefix="`", suffix="`")
    parse_codeline = functools.partialmethod(_default_parse, suffix="\n")
    parse_sp = functools.partialmethod(_default_parse, prefix=" ")
    parse_row = functools.partialmethod(_default_parse, prefix="\n\n", suffix="\n")
    parse_entry = functools.partialmethod(_default_parse, prefix="|")

    def parse_ulink(self, element: ET.Element) -> None:
        self._default_parse(element, prefix=f"{element.get('url')}[", suffix="]")

    def parse_ref(self, element: ET.Element) -> None:
        self._default_parse(element,
                            prefix=f"xref:{self.language}-{element.get('refid')}[",
                            suffix="]")

    def parse_parameterlist(self, element) -> None:
        pass

    def parse_simplesect(self, element: ET.Element) -> None:
        kind = element.get("kind")
        if kind in ["note", "tip", "important", "caution", "warning"]:
            self._default_parse(element, prefix=f"\n[{kind.upper()}]\n====\n", suffix="====\n")

    def parse_programlisting(self, element: ET.Element) -> None:
        self._default_parse(element, prefix=f"\n[source,{self.language}]\n----\n", suffix="----\n")

    def parse_highlight(self, element: ET.Element) -> None:
        if element.get("class") == "normal":
            self._default_parse(element)
        else:
            self._default_parse(element, prefix="__", suffix="__")

    def parse_table(self, element: ET.Element) -> None:
        caption_prefix = ""
        caption = element.find('caption')
        if caption is not None:
            caption_prefix = f".{caption.text}\n"

        header_option = ""
        first_row = element.find('row')
        if first_row is not None:
            first_entry = first_row.find('entry')
            if first_entry is not None and first_entry.get('thead') == 'yes':
                header_option = "%header,"

        prefix = f"\n\n{caption_prefix}[{header_option}cols={element.get('cols')}*]\n|===\n"
        self._default_parse(element, prefix=prefix, suffix="|===\n")

    def parse_caption(self, element: ET.Element) -> None:
        pass

    def __getattr__(self, name):
        return self._default_parse

    def append(self, text: Optional[str]) -> None:
        if text:
            self._parts.append(text)
