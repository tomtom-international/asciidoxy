# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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

from typing import List, Mapping, Optional, Set, Tuple

from tqdm import tqdm

from .cpp import CppParser
from .driver_base import DriverBase
from .java import JavaParser
from .objc import ObjectiveCParser
from .parser_base import ParserBase
from .python import PythonParser
from ...api_reference import AmbiguousLookupError, ApiReference
from ...model import Compound, ReferableElement, TypeRef

logger = logging.getLogger(__name__)


class Driver(DriverBase):
    """Driver for parsing Doxygen XML output."""
    api_reference: ApiReference
    _unresolved_refs: List[TypeRef]
    _inner_type_refs: List[Tuple[Compound, TypeRef]]
    _force_language: Optional[str]

    _parsers: Mapping[str, ParserBase]

    def __init__(self, force_language: Optional[str] = None):
        self.api_reference = ApiReference()
        self._unresolved_refs = []
        self._inner_type_refs = []
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

    def unresolved_ref(self, ref: TypeRef) -> None:
        self._unresolved_refs.append(ref)

    def inner_type_ref(self, parent: Compound, ref: TypeRef) -> None:
        self._inner_type_refs.append((parent, ref))

    def resolve_references(self, progress: Optional[tqdm] = None) -> None:
        """Resolve all references between objects from different XML files."""

        unresolved_names: Set[str] = set()
        if progress is not None:
            progress.total = len(self._unresolved_refs) + len(self._inner_type_refs)

        still_unresolved_refs = []
        for ref in self._unresolved_refs:
            if progress is not None:
                progress.update()
            assert ref.name
            element = self.resolve_reference(ref)
            if element is not None:
                ref.resolve(element)
            else:
                still_unresolved_refs.append(ref)
                unresolved_names.add(ref.name)

        still_unresolved_inner_type_refs: List[Tuple[Compound, TypeRef]] = []
        for parent, ref in self._inner_type_refs:
            if progress is not None:
                progress.update()
            assert ref.name
            element = self.resolve_reference(ref)
            if element is not None:
                assert isinstance(element, Compound)
                if ref.prot:
                    element.prot = ref.prot
                parent.members.append(element)
            else:
                still_unresolved_inner_type_refs.append((parent, ref))
                unresolved_names.add(ref.name)

        resolved_ref_count = len(self._unresolved_refs) - len(still_unresolved_refs)
        resolved_inner_type_ref_count = (len(self._inner_type_refs) -
                                         len(still_unresolved_inner_type_refs))
        unresolved_ref_count = len(still_unresolved_refs) + len(still_unresolved_inner_type_refs)
        logger.debug(f"Resolved refs: {resolved_ref_count + resolved_inner_type_ref_count}")
        logger.debug(f"Still unresolved: {unresolved_ref_count}: {', '.join(unresolved_names)}")

        self._unresolved_refs = still_unresolved_refs
        self._inner_type_refs = still_unresolved_inner_type_refs

    def resolve_reference(self, ref: TypeRef) -> Optional[ReferableElement]:
        try:
            perfect_match = self.api_reference.find(ref.name,
                                                    target_id=ref.id,
                                                    lang=ref.language,
                                                    namespace=ref.namespace)
            if perfect_match is not None:
                return perfect_match
        except AmbiguousLookupError:
            pass

        partial_matches = []
        for compound in self.api_reference.elements:
            if compound.name and compound.full_name.endswith(f"::{ref.name}"):
                partial_matches.append(compound)
        if len(partial_matches) == 1:
            return partial_matches[0]
        elif len(partial_matches) > 1:
            logger.debug(f"Multiple partial matches: {ref.name} ")

        return None


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
