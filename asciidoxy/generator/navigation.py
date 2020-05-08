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

from pathlib import Path
from typing import List, Optional, Tuple


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

    def __init__(self, in_file: Path, parent: "DocumentTreeNode" = None):
        self.in_file = in_file
        self.parent = parent
        self.children = []

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
