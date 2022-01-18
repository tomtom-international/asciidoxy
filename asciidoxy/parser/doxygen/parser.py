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
"""Read API reference information from Doxygen XML output."""

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Mapping, Optional, Union

from ...api_reference import ApiReference
from ..factory import ReferenceParserBase
from .language.cpp import CppParser
from .language.java import JavaParser
from .language.objc import ObjectiveCParser
from .language.python import PythonParser
from .language_parser import LanguageParser

logger = logging.getLogger(__name__)


class Parser(ReferenceParserBase):
    """Parser Doxygen XML output."""
    api_reference: ApiReference

    _parsers: Mapping[str, LanguageParser]

    def __init__(self, api_reference: ApiReference):
        ReferenceParserBase.__init__(self, api_reference)

        self._parsers = {
            CppParser.TRAITS.TAG: CppParser(api_reference),
            JavaParser.TRAITS.TAG: JavaParser(api_reference),
            ObjectiveCParser.TRAITS.TAG: ObjectiveCParser(api_reference),
            PythonParser.TRAITS.TAG: PythonParser(api_reference),
        }

    def _parse_element(self, xml_element: ET.Element) -> None:
        language_tag = safe_language_tag(xml_element.get("language"))
        if not language_tag:
            return
        if language_tag not in self._parsers:
            logger.debug(f"Unknown language: {language_tag}")
            return

        if xml_element.tag == "compounddef":
            self._parsers[language_tag].parse_compounddef(xml_element)
        else:
            logger.debug(f"Unhandled element: {xml_element.tag}")

    def parse(self, reference_path: Union[Path, str]) -> bool:
        """Parse reference documentation from the given path.

        Args:
            reference_path File or directory containing the reference documentation.

        Returns:
            True if the reference has been parsed. False if the reference path does not contain
            valid content for this parser.
        """
        reference_path = Path(reference_path)
        if reference_path.is_file():
            return self._parse_file(reference_path)
        else:
            for xml_file in reference_path.glob("**/*.xml"):
                if xml_file.stem in ("index", "Doxyfile"):
                    continue
                if not self._parse_file(xml_file):
                    return False
            return True

    def _parse_file(self, file: Path) -> bool:
        tree = ET.parse(file)
        root = tree.getroot()
        if root.tag != "doxygen":
            return False

        for e in root:
            self._parse_element(e)
        return True


def safe_language_tag(name: Optional[str]) -> str:
    """Convert language names to tags that are safe to use for identifiers and file names.

    Args:
        name: Name to convert to a safe name. Can be `None`.

    Returns:
        A safe string to use for identifiers and file names.
    """
    if name is None:
        return ""

    name = name.lower()
    return {"c++": "cpp", "objective-c": "objc"}.get(name, name)
