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
    _force_language: Optional[str]

    _parsers: Mapping[str, LanguageParser]

    def __init__(self, api_reference: ApiReference, force_language: Optional[str] = None):
        ReferenceParserBase.__init__(self, api_reference)

        self._force_language = safe_language_tag(force_language)

        self._parsers = {
            CppParser.TRAITS.TAG: CppParser(api_reference),
            JavaParser.TRAITS.TAG: JavaParser(api_reference),
            ObjectiveCParser.TRAITS.TAG: ObjectiveCParser(api_reference),
            PythonParser.TRAITS.TAG: PythonParser(api_reference),
        }

        if not self._force_language:
            self._force_language = None
        elif self._force_language not in self._parsers:
            logger.error(f"Unknown forced language: {self._force_language}. Falling back to auto"
                         " detection.")
            self._force_language = None

    def _parse_element(self, xml_element: ET.Element) -> None:
        if self._force_language is not None:
            language_tag = self._force_language
        else:
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
        try:
            tree = ET.parse(file)
        except ET.ParseError:
            logger.exception(f"Failure while parsing XML from `{file}`. The XML may be"
                             " malformed or the file has encoding errors.")
            return False

        root = tree.getroot()
        if root.tag != "doxygen":
            if root.tag != "doxygenindex":
                logger.error(f"File `{file}` does not contain valid Doxygen XML.")
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
