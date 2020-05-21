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
"""Read API reference information from Doxygen XML output."""

import logging

import xml.etree.ElementTree as ET

from typing import List, Mapping, Optional, Set

from tqdm import tqdm

from .cpp import CppParser
from .driver_base import DriverBase
from .java import JavaParser
from .objc import ObjectiveCParser
from .parser_base import ParserBase
from .python import PythonParser
from ..api_reference import AmbiguousLookupError, ApiReference
from ..model import (ReferableElement, TypeRefBase)

logger = logging.getLogger(__name__)


class Driver(DriverBase):
    """Driver for parsing Doxygen XML output."""
    api_reference: ApiReference
    _unresolved_refs: List[TypeRefBase]
    _force_language: Optional[str]

    _parsers: Mapping[str, ParserBase]

    def __init__(self, force_language: Optional[str] = None):
        self.api_reference = ApiReference()
        self._unresolved_refs = []
        self._force_language = safe_language_tag(force_language)

        self._parsers = {
            CppParser.TRAITS.TAG: CppParser(self),
            JavaParser.TRAITS.TAG: JavaParser(self),
            ObjectiveCParser.TRAITS.TAG: ObjectiveCParser(self),
            PythonParser.TRAITS.TAG: PythonParser(self),
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

    def parse(self, file_or_path) -> bool:
        """Parse all objects in an XML file and make them available for API reference generation.

        Params:
            file_or_path: File object or path for the XML file to parse.

        Returns:
            True if file is parsed. False if the file is invalid.
        """

        tree = ET.parse(file_or_path)
        root = tree.getroot()
        if root.tag != "doxygen":
            return False

        for e in root:
            self._parse_element(e)
        return True

    def register(self, element: ReferableElement) -> None:
        self.api_reference.append(element)

    def unresolved_ref(self, ref: TypeRefBase) -> None:
        self._unresolved_refs.append(ref)

    def resolve_references(self, progress: Optional[tqdm] = None) -> None:
        """Resolve all references between objects from different XML files."""

        unresolved_names: Set[str] = set()
        still_unresolved = []
        if progress is not None:
            progress.total = len(self._unresolved_refs)
        for ref in self._unresolved_refs:
            if progress is not None:
                progress.update()
            assert ref.name

            # Try perfect match
            try:
                class_match = self.api_reference.find(ref.name,
                                                      target_id=ref.id,
                                                      lang=ref.language,
                                                      namespace=ref.namespace)
                if class_match is not None:
                    ref.resolve(class_match)
                    continue
            except AmbiguousLookupError:
                pass

            # Find partial matches in namespaces or other scopes
            matches = []
            for compound in self.api_reference.elements:
                if compound.name and compound.full_name.endswith(f"::{ref.name}"):
                    matches.append(compound)
            if len(matches) == 1:
                ref.resolve(matches[0])
                continue
            elif len(matches) > 1:
                logger.debug(f"Multiple matches: {ref.name} ")

            still_unresolved.append(ref)
            unresolved_names.add(ref.name)

        logger.debug(f"Resolved refs: {len(self._unresolved_refs) - len(still_unresolved)}")
        logger.debug(f"Still unresolved: {len(still_unresolved)}: {', '.join(unresolved_names)}")
        self._unresolved_refs = still_unresolved


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
