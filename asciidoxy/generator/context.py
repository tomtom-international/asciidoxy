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
"""Context of the document being generated."""

import copy
import logging
import uuid

from pathlib import Path
from typing import Dict, MutableMapping, Optional, Set, Tuple

from tqdm import tqdm

from ..api_reference import ApiReference
from ..model import ReferableElement
from ..packaging import Package, PackageManager
from .errors import ConsistencyError
from .filters import InsertionFilter
from .navigation import DocumentTreeNode, relative_path

logger = logging.getLogger(__name__)


class Environment(object):
    """Namespace for holding environment variables to be shared between different AsciiDoc files.

    AsciiDoc files can assign variables in the environment namespace to be reused in other AsciiDoc
    files that are included from it. Like other concepts in AsciiDoxy, the changes should only
    apply to the current file, and any include from the current file. The parent namespace should
    remain unchanged.

    This class is intentionaly simple. New variables can be added to an instance by simply
    assigining them:

      env = Environment()
      env.new_var = "value"

    To copy the environment to subcontexts use copy.copy(). This prevents changing the variables
    in the parent scopes.
    """


class Context(object):
    """Contextual information about the document being generated.

    This information is meant to be shared with all included documents as well.

    Attributes:
        base_dir:           Base directory from which the documentation is generated. Relative
                                paths are relative to the base directory.
        fragment_dir:       Directory containing generated fragments to be included in the
                                documentation.
        namespace:          Current namespace to use when looking up references.
        language:           Default language to use when looking up references.
        insert_filter:      Filter used to select members of elements to insert.
        env:                Environment variables to share with subdocuments.
        warnings_are_errors:True to treat every warning as an error.
        multipage:          True when multi page output is enabled.
        reference:          API reference information.
        linked:             All elements to which links are inserted in the documentation.
        inserted:           All elements that have been inserted in the documentation.
        in_to_out_file_map: Mapping from input files for AsciiDoctor to the resulting output files.
        current_document:   Node in the Document Tree that is currently being processed.
        current_package:    Package containing the current files.
    """
    base_dir: Path
    fragment_dir: Path

    namespace: Optional[str] = None
    language: Optional[str] = None
    source_language: Optional[str] = None
    insert_filter: InsertionFilter
    env: Environment

    warnings_are_errors: bool = False
    multipage: bool = False
    embedded: bool = False

    reference: ApiReference
    package_manager: PackageManager
    progress: Optional[tqdm] = None

    linked: Set[str]
    inserted: MutableMapping[str, Path]
    in_to_out_file_map: Dict[Path, Path]
    embedded_file_map: Dict[Tuple[Path, Path], Path]
    current_document: DocumentTreeNode
    current_package: Package

    def __init__(self, base_dir: Path, fragment_dir: Path, reference: ApiReference,
                 package_manager: PackageManager, current_document: DocumentTreeNode,
                 current_package: Package):
        self.base_dir = base_dir
        self.fragment_dir = fragment_dir

        self.insert_filter = InsertionFilter(members={"prot": ["+public", "+protected"]})
        self.env = Environment()

        self.reference = reference
        self.package_manager = package_manager

        self.linked = set()
        self.inserted = {}
        self.in_to_out_file_map = {}
        self.embedded_file_map = {}
        self.current_document = current_document
        self.current_package = current_package

    def insert(self, element: ReferableElement) -> None:
        assert element.id
        if element.id in self.inserted:
            msg = f"Duplicate insertion of {element.name}"
            if self.warnings_are_errors:
                raise ConsistencyError(msg)
            else:
                logger.warning(msg)
        self.inserted[element.id] = self.current_document.in_file

    def sub_context(self) -> "Context":
        sub = Context(base_dir=self.base_dir,
                      fragment_dir=self.fragment_dir,
                      reference=self.reference,
                      package_manager=self.package_manager,
                      current_document=self.current_document,
                      current_package=self.current_package)

        # Copies
        sub.namespace = self.namespace
        sub.language = self.language
        sub.source_language = self.source_language
        sub.warnings_are_errors = self.warnings_are_errors
        sub.multipage = self.multipage
        sub.embedded = self.embedded
        sub.env = copy.copy(self.env)
        sub.insert_filter = copy.deepcopy(self.insert_filter)

        # References
        sub.linked = self.linked
        sub.inserted = self.inserted
        sub.in_to_out_file_map = self.in_to_out_file_map
        sub.embedded_file_map = self.embedded_file_map
        sub.progress = self.progress

        return sub

    def file_with_element(self, element_id: str) -> Optional[Path]:
        if not self.multipage or element_id not in self.inserted:
            return None

        containing_file = self.inserted[element_id]
        assert containing_file is not None
        if self.current_document.in_file != containing_file:
            return containing_file
        else:
            return None

    def link_to_element(self, element_id: str) -> None:
        self.linked.add(element_id)

    def register_adoc_file(self, in_file: Path) -> Path:
        assert in_file.is_absolute()
        if self.embedded:
            out_file = self.embedded_file_map.get((in_file, self.current_document.in_file), None)
        else:
            out_file = self.in_to_out_file_map.get(in_file, None)

        if out_file is None:
            if self.embedded:
                out_file = _embedded_out_file_name(in_file)
                self.embedded_file_map[(in_file, self.current_document.in_file)] = out_file
            else:
                out_file = _out_file_name(in_file)
                self.in_to_out_file_map[in_file] = out_file

        return out_file

    def link_to_adoc_file(self, file_name: Path):
        """Determine the correct path to link to a file.

        The exact path differs for single and multipage mode and whether a file is embedded or not.
        AsciiDoctor processes links in included files as if they are originating from the top level
        file.
        """
        assert file_name.is_absolute()

        if self.multipage:
            embedded_file = self.embedded_file_map.get((file_name, self.current_document.in_file))
            if embedded_file is not None:
                # File is embedded in the current document, link to generated embedded file
                return relative_path(self.current_document.in_file, embedded_file)
            else:
                # File is not embedded, link to original file name
                return relative_path(self.current_document.in_file, file_name)

        else:
            # In singlepage mode all links need to be relative to the root file
            embedded_file = self.embedded_file_map.get((file_name, self.current_document.in_file))
            if embedded_file is not None:
                # File is embedded in the current document, link to generated embedded file
                return relative_path(self.current_document.root().in_file, embedded_file)

            out_file = self.in_to_out_file_map.get(file_name, None)
            if out_file is not None:
                # File has been processed, and as we are in single page mode, it is embedded as
                # well
                return relative_path(self.current_document.root().in_file, out_file)

            else:
                # File is not processed, create relative link from current top level document
                return relative_path(self.current_document.root().in_file, file_name)

    def docinfo_footer_file(self) -> Path:
        if self.multipage:
            in_file = self.current_document.in_file
        else:
            in_file = self.current_document.root().in_file

        out_file = self.in_to_out_file_map.get(in_file, None)
        if out_file is None:
            out_file = _out_file_name(in_file)

        return _docinfo_footer_file_name(out_file)


def _out_file_name(in_file: Path) -> Path:
    return in_file.parent / f".asciidoxy.{in_file.name}"


def _embedded_out_file_name(in_file: Path) -> Path:
    return in_file.parent / f".asciidoxy.{uuid.uuid4()}.{in_file.name}"


def _docinfo_footer_file_name(out_file: Path) -> Path:
    return out_file.parent / f"{out_file.stem}-docinfo-footer.html"
