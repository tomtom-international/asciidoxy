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
"""Context of the document being generated."""

import logging

from pathlib import Path
from typing import Dict, List, MutableMapping, Optional

from tqdm import tqdm

from ..api_reference import ApiReference
from ..model import ReferableElement
from .errors import ConsistencyError
from .filters import InsertionFilter
from .navigation import DocumentTreeNode, relative_path

logger = logging.getLogger(__name__)


class Context(object):
    """Contextual information about the document being generated.

    This information is meant to be shared with all included documents as well.

    Attributes:
        base_dir:           Base directory from which the documentation is generated. Relative
                                paths are relative to the base directory.
        build_dir:          Directory for (temporary) build artifacts.
        fragment_dir:       Directory containing generated fragments to be included in the
                                documentation.
        namespace:          Current namespace to use when looking up references.
        language:           Default language to use when looking up references.
        insert_filter:      Filter used to select members of elements to insert.
        preprocessing_run:  True when preprocessing. During preprocessing no files are generated.
        warnings_are_errors:True to treat every warning as an error.
        multi_page:         True when multi page output is enabled.
        reference:          API reference information.
        linked:             All elements to which links are inserted in the documentation.
        inserted:           All elements that have been inserted in the documentation.
        in_to_out_file_map: Mapping from input files for AsciiDoctor to the resulting output files.
        current_document:   Node in the Document Tree that is currently being processed.
    """
    base_dir: Path
    build_dir: Path
    fragment_dir: Path

    namespace: Optional[str] = None
    language: Optional[str] = None
    insert_filter: InsertionFilter

    preprocessing_run: bool = True
    warnings_are_errors: bool = False
    multi_page: bool = False

    reference: ApiReference
    progress: Optional[tqdm] = None

    linked: List[ReferableElement]
    inserted: MutableMapping[str, Path]
    in_to_out_file_map: Dict[Path, Path]
    current_document: DocumentTreeNode

    def __init__(self, base_dir: Path, build_dir: Path, fragment_dir: Path, reference: ApiReference,
                 current_document: DocumentTreeNode):
        self.base_dir = base_dir
        self.build_dir = build_dir
        self.fragment_dir = fragment_dir

        self.insert_filter = InsertionFilter()

        self.reference = reference

        self.linked = []
        self.inserted = {}
        self.in_to_out_file_map = {}
        self.current_document = current_document

    def insert(self, element) -> str:
        if self.preprocessing_run:
            if element.id in self.inserted:
                msg = f"Duplicate insertion of {element.name}"
                if self.warnings_are_errors:
                    raise ConsistencyError(msg)
                else:
                    logger.warning(msg)
            self.inserted[element.id] = self.current_document.in_file

        return ""  # Prevent output in templates

    def sub_context(self) -> "Context":
        sub = Context(base_dir=self.base_dir,
                      build_dir=self.build_dir,
                      fragment_dir=self.fragment_dir,
                      reference=self.reference,
                      current_document=self.current_document)

        # Copies
        sub.namespace = self.namespace
        sub.language = self.language
        sub.preprocessing_run = self.preprocessing_run
        sub.warnings_are_errors = self.warnings_are_errors
        sub.multi_page = self.multi_page

        # References
        sub.linked = self.linked
        sub.inserted = self.inserted
        sub.in_to_out_file_map = self.in_to_out_file_map
        sub.insert_filter = self.insert_filter
        sub.progress = self.progress

        return sub

    def link_to_element(self,
                        element_id: str,
                        link_text: str,
                        element: Optional[ReferableElement] = None) -> str:
        def file_part():
            if not self.multi_page or element_id not in self.inserted:
                return ""
            containing_file = self.inserted[element_id]
            assert containing_file is not None
            if self.current_document.in_file != containing_file:
                return f"{relative_path(self.current_document.in_file, containing_file)}#"

        if element is None:
            element = self.reference.find(target_id=element_id)
        if element is not None:
            self.linked.append(element)

        return f"xref:{file_part() or ''}{element_id}[{link_text}]"
