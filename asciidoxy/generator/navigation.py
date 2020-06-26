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
"""Support for navigating multi page output."""

import logging
import os
import re
import xml.dom.minidom

import xml.etree.ElementTree as ET

from pathlib import Path
from typing import List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class DocumentTreeNode(object):
    """A node in the hierarchical tree of documents.

    The tree represents the structure of the documentation. The node can represent either a root
    document, an intermediate document or a leaf document.

    Attributes:
        in_file: File from which the node was read.
        parent: Parent node in the tree.
        children: Child nodes in the tree.
    """
    in_file: Path
    parent: Optional["DocumentTreeNode"]
    children: List["DocumentTreeNode"]
    _title: Optional[str] = None

    def __init__(self, in_file: Path, parent: "DocumentTreeNode" = None):
        self.in_file = Path(in_file)
        self.parent = parent
        self.children = []

    @property
    def title(self) -> str:
        if self._title is None:
            self._title = self._read_title()
        return self._title

    def preorder_traversal_next(self):
        if len(self.children) > 0:
            return self.children[0]
        return self._next_subtree()

    def preorder_traversal_prev(self):
        if self.parent is None:
            return None
        i, this_doc = self.parent._find_child(self.in_file)
        assert this_doc is not None
        return self.parent.children[i - 1]._last_leaf() if i > 0 else self.parent

    def find_child(self, child_in_file: Path):
        _, child = self._find_child(child_in_file)
        return child

    def root(self):
        return self if self.parent is None else self.parent.root()

    def all_documents_in_tree(self):
        return self.root()._all_documents_in_subtree()

    def _next_subtree(self):
        if self.parent is None:
            return None
        i, this_doc = self.parent._find_child(self.in_file)
        assert this_doc is not None
        if len(self.parent.children) > i + 1:
            return self.parent.children[i + 1]
        return self.parent._next_subtree()

    def _last_leaf(self):
        if len(self.children) == 0:
            return self
        return self.children[-1]._last_leaf()

    def _find_child(self, in_file: Path) -> Tuple[int, Optional["DocumentTreeNode"]]:
        for i, elem in enumerate(self.children):
            if (elem.in_file == in_file):
                return (i, elem)
        return (0, None)

    def _all_documents_in_subtree(self):
        yield self
        for child in self.children:
            for d in child._all_documents_in_subtree():
                yield d

    def _read_title(self) -> str:
        try:
            with self.in_file.open(mode="r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("= "):
                        return self._clean_title(line)
        except OSError:
            logger.exception(f"Failed to read title from AsciiDoc file {self.in_file}.")
        logger.exception(f"Did not find title in AsciiDoc file {self.in_file}.")
        return self.in_file.stem

    @staticmethod
    def _clean_title(title: str) -> str:
        title = title[2:]
        title = re.sub(r"\[.*\]", "", title)
        title = re.sub(r"\{.*\}", "", title)
        title = re.sub(r"[*_`^~#]", "", title)
        title = title.strip()
        return title


def relative_path(from_file: Path, to_file: Path):
    assert from_file.is_absolute()
    assert to_file.is_absolute()

    path = Path()
    for ancestor in from_file.parents:
        try:
            path = path / to_file.relative_to(ancestor)
            break
        except ValueError:
            path = path / '..'

    return path


def navigation_bar(doc: DocumentTreeNode) -> str:
    next_doc: DocumentTreeNode = doc.preorder_traversal_next()
    prev_doc: DocumentTreeNode = doc.preorder_traversal_prev()

    # Don't generate navigation bar for single page documents
    if next_doc is None and prev_doc is None:
        return ""

    up_doc: Optional[DocumentTreeNode] = doc.parent
    root_doc: DocumentTreeNode = doc.root()

    def _xref_string(referencing_file: Path, doc: Optional[DocumentTreeNode], link_text: str):
        if doc is None:
            return ""
        return f"<<{relative_path(referencing_file, doc.in_file)}#,{link_text}>>"

    home_row = f" +\n{_xref_string(doc.in_file, root_doc, 'Home')}" if root_doc != doc else ''
    return (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|{_xref_string(doc.in_file, prev_doc, 'Prev')}

|{_xref_string(doc.in_file, up_doc, 'Up')}{home_row}

|{_xref_string(doc.in_file, next_doc, 'Next')}
|===""")


def _toc_div(side: str = "left") -> ET.Element:
    div = ET.Element("div", id="toc", attrib={"class": "toc2"})

    if side == "left":
        div.set("style", "left: 0; right: unset; border-right-width: 1px; border-left-width: 0px")
    else:
        div.set("style", "left: unset; right: 0; border-right-width: 0px; border-left-width: 1px")

    return div


def _toc_title(parent: ET.Element, link: str, text: str) -> ET.Element:
    div = ET.SubElement(parent, "div", id="toctitle")
    a = ET.SubElement(div, "a", href=link)
    a.text = text
    return div


def _toc_ul(parent: ET.Element, level: int) -> ET.Element:
    return ET.SubElement(parent, "ul", attrib={"class": f"sectlevel{level}"})


def _toc_li(parent: ET.Element, link: str, text: str) -> ET.Element:
    li = ET.SubElement(parent, "li")
    a = ET.SubElement(li, "a", href=link)
    a.text = text
    return li


def _pretty_html(element: ET.Element) -> str:
    ugly_html = ET.tostring(element, encoding="unicode", method="html")
    pretty_xml = xml.dom.minidom.parseString(ugly_html).toprettyxml(indent="  ")

    # Remove XML header
    _, pretty_html = pretty_xml.split("\n", maxsplit=1)
    return pretty_html


def multipage_toc(doc: DocumentTreeNode, side: str = "left") -> str:
    current_doc = doc
    breadcrumbs = {doc}
    while doc.parent is not None:
        doc = doc.parent
        breadcrumbs.add(doc)

    toc = _toc_div(side)
    _toc_title(toc, link=_relative_html_link(current_doc, doc), text=doc.title)

    if doc is not None:
        _toc(parent=toc, doc=doc, current_doc=current_doc, level=1, breadcrumbs=breadcrumbs)

    script = _toc_script(side)

    return _pretty_html(toc) + _pretty_html(script)


def _toc(parent: ET.Element, doc: DocumentTreeNode, current_doc: DocumentTreeNode, level: int,
         breadcrumbs: Set[DocumentTreeNode]) -> None:
    ul = _toc_ul(parent, level)
    for child in doc.children:
        li = _toc_li(ul, link=_relative_html_link(current_doc, child), text=child.title)
        if len(child.children) > 0 and child in breadcrumbs:
            _toc(parent=li,
                 doc=child,
                 current_doc=current_doc,
                 level=level + 1,
                 breadcrumbs=breadcrumbs)


def _toc_script(side: str = "left") -> ET.Element:
    script = ET.Element("script")
    script.text = f"document.body.style = 'padding-{side}: 20em'"
    return script


def _relative_html_link(current_doc: DocumentTreeNode, target_doc: DocumentTreeNode) -> str:
    adoc_link = relative_path(current_doc.in_file, target_doc.in_file)
    return os.fspath(adoc_link.with_suffix(".html"))
