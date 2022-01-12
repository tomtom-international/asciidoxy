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
"""Information about documents being parsed and generated."""

import logging
import re
from pathlib import Path
from typing import Any, Iterator, List, Mapping, Optional, Union

from .path_utils import relative_path

logger = logging.getLogger(__name__)


def path_from_toml(data: Mapping[str, Any], key: str, root: Path) -> Optional[Path]:
    value = data.get(key, None)
    if value is not None:
        return root / value
    return None


class Package:
    """A package that is ready to be used by AsciiDoxy.

    Attributes:
        name:              Name of the package.
        reference_type:    Type of API reference information in the package.
        reference_dir:     Directory containing API reference information.
        adoc_src_dir:      Directory containing AsciiDoc files and other files to include in the
                               documentation. Image files should be separate in `adoc_image_dir`.
        adoc_image_dir:    Directory containing images to include in the documentation.
        adoc_root_doc:     Entry point document for the package. To be linked to if no specific file
                               in the package is mentioned.
        scoped:            True if this is a new-style, scoped package.
        copy_adoc_src_dir: True if the content of `adoc_src_dir` should be copied to the working
                               directory.
    """
    INPUT_PACKAGE_NAME: str = "INPUT"

    name: str
    reference_type: Optional[str] = None
    reference_dir: Optional[Path] = None
    adoc_src_dir: Optional[Path] = None
    adoc_image_dir: Optional[Path] = None
    adoc_root_doc: Optional[Path] = None
    scoped: bool = False
    copy_adoc_src_dir: bool = True

    def __init__(self, name: str):
        self.name = name

    @property
    def is_input_package(self):
        """Does this package refer to the input files from the command-line."""
        return self.name == self.INPUT_PACKAGE_NAME

    def load_from_toml(self, pkg_root: Path, data: Mapping[str, Any]) -> None:
        package = data.get("package", None)
        if package is not None:
            self.name = package.get("name", self.name)

        reference = data.get("reference", None)
        if reference is not None:
            self.reference_type = reference.get("type", None)
            self.reference_dir = path_from_toml(reference, "dir", pkg_root)

        adoc = data.get("asciidoc", None)
        if adoc is not None:
            self.adoc_src_dir = path_from_toml(adoc, "src_dir", pkg_root)
            self.adoc_image_dir = path_from_toml(adoc, "image_dir", pkg_root)
            if self.adoc_src_dir is not None:
                self.adoc_root_doc = path_from_toml(adoc, "root_doc", self.adoc_src_dir)

        self.scoped = True


class Document:
    """An AsciiDoc document being processed by AsciiDoxy.

    Attributes:
        relative_path: Relative path from the root of the workspace or package.
        package:       Package containing the file.
        work_dir:      Root of the workspace for temporary files.
        children:      Other documents included in this document.
        included_in:   Document including this document, if present.
        stylesheet:    Name of the stylesheet to apply.
    """
    relative_path: Path
    package: Package
    work_dir: Path

    children: List["Document"]
    included_in: Optional["Document"]
    embedded_in: List["Document"]
    is_root: bool
    stylesheet: Optional[str]

    _title: Optional[str] = None

    def __init__(self, relative_path: Path, package: Package, work_dir: Path):
        self.relative_path = relative_path
        self.package = package
        self.work_dir = work_dir

        self.children = []
        self.included_in = None
        self.embedded_in = []
        self.is_root = False
        self.stylesheet = None

    @property
    def original_file(self) -> Path:
        """The absolute path to the original input file."""
        assert self.package.adoc_src_dir
        return self.package.adoc_src_dir / self.relative_path

    @property
    def work_file(self) -> Path:
        """The absolute path to the copied or generated work version of the file."""
        return self.work_dir / self.relative_path

    @property
    def docinfo_footer_file(self) -> Path:
        """The absolute path to the file containing the docinfo footer."""
        return self.work_file.with_name(f"{self.relative_path.stem}-docinfo-footer.html")

    @property
    def stylesheet_file(self) -> Path:
        assert self.stylesheet
        return self.work_dir / self.stylesheet

    @property
    def is_used(self) -> bool:
        return self.is_root or self.is_included or self.is_embedded

    @property
    def is_included(self) -> bool:
        """Is this document included anywhere?"""
        return self.included_in is not None

    @property
    def is_embedded(self) -> bool:
        """Is this document embedded in another document?"""
        return len(self.embedded_in) > 0

    @property
    def title(self) -> str:
        if self._title is None:
            self._title = self._read_title()
        return self._title

    def __str__(self) -> str:
        if self.package.is_input_package:
            return str(self.relative_path)
        else:
            return f"[{self.package.name}]:/{self.relative_path}"

    __repr__ = __str__

    def relative_path_to(self, doc: "Document") -> Path:
        """Return the relative path from this document to another document.

        Args:
            doc: The other document to create the relative path to.

        Returns:
            The relative path from the current document.
        """
        return relative_path(self.work_file, doc.work_file)

    def resolve_relative_path(self, to: Union[str, Path]) -> Path:
        """Determine a workspace/package relative path from a relative path starting at the current
        document.

        Args:
            to: The relative path to resolve.

        Returns:
            A path relative to the workspace/package root.
        """
        abs_path = (self.work_file.parent / to).resolve()
        return relative_path(self.work_dir / "does_not_matter", abs_path)

    def include(self, child: "Document") -> None:
        """Include another document in this document."""
        assert child is not self
        child.included_in = self
        self.children.append(child)

    def embed(self, child: "Document") -> None:
        """Embed another document in this document.

        While a document can only be included once, it can be embedded multiple times.
        """
        assert child is not self
        child.embedded_in.append(self)
        self.children.append(child)

    def with_relative_path(self, rel_path: Union[str, Path]) -> "Document":
        """Create an empty copy of this document with a different relative path."""
        return Document(Path(rel_path), self.package, self.work_dir)

    def root(self) -> "Document":
        """Find the root of the document tree."""
        if self.included_in is not None:
            return self.included_in.root()
        elif len(self.embedded_in) > 0:
            # Assume we have a single root. Every parent should lead to the same root.
            return self.embedded_in[0].root()
        else:
            return self

    def find_embedder(self) -> "Document":
        """Find the nearest parent file that embeds this document, but is not embedded itself."""
        if not self.is_embedded:
            return self
        return self.embedded_in[0].find_embedder()

    def is_embedded_in(self, document: "Document") -> bool:
        """Determine whether this document is (indirectly) embedded in another document."""
        if document in self.embedded_in:
            return True
        for embedder in self.embedded_in:
            if embedder.is_embedded_in(document):
                return True
        else:
            return False

    def preorder_next(self) -> Optional["Document"]:
        for child in self.children:
            if child.included_in is self:
                return child
        return self._next_subtree()

    def preorder_prev(self) -> Optional["Document"]:
        parent = self.parent()
        if parent is None:
            return None

        i = parent.children.index(self)
        while i > 0:
            i -= 1
            if parent.children[i].included_in is parent:
                return parent.children[i]._last_leaf()
        return parent

    def iter_all(self) -> Iterator["Document"]:
        return self.root()._all_documents_in_subtree()

    def parent(self) -> Optional["Document"]:
        if self.included_in is not None:
            return self.included_in
        elif len(self.embedded_in) > 0:
            return self.embedded_in[0]
        else:
            return None

    def _next_subtree(self) -> Optional["Document"]:
        parent = self.parent()
        if parent is None:
            return None

        i = parent.children.index(self)
        while i + 1 < len(parent.children):
            i += 1
            if parent.children[i].included_in is parent:
                return parent.children[i]
        return parent._next_subtree()

    def _last_leaf(self) -> Optional["Document"]:
        for child in reversed(self.children):
            if child.included_in is self:
                return child._last_leaf()
        else:
            return self

    def _all_documents_in_subtree(self) -> Iterator["Document"]:
        yield self
        for child in self.children:
            if child.included_in is self:
                for d in child._all_documents_in_subtree():
                    yield d

    def _read_title(self) -> str:
        try:
            with self.original_file.open(mode="r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("= "):
                        return self._clean_title(line)
        except OSError:
            logger.exception(f"Failed to read title from AsciiDoc file {self}.")
        logger.exception(f"Did not find title in AsciiDoc file {self}.")
        return self.relative_path.stem

    @staticmethod
    def _clean_title(title: str) -> str:
        title = title[2:]
        title = re.sub(r"\[.*\]", "", title)
        title = re.sub(r"\{.*\}", "", title)
        title = re.sub(r"[*_`^~#]", "", title)
        title = title.strip()
        return title
