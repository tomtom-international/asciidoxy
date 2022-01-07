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
"""Support for navigating multi page output."""

import os
import xml.dom.minidom
import xml.etree.ElementTree as ET
from typing import Optional, Set

from ..document import Document


def navigation_bar(doc: Document) -> str:
    next_doc = doc.preorder_next()
    prev_doc = doc.preorder_prev()

    # Don't generate navigation bar for single page documents
    if next_doc is None and prev_doc is None:
        return ""

    up_doc = doc.parent()
    root_doc = doc.root()

    def _xref_string(origin: Document, doc: Optional[Document], link_text: str):
        if doc is None:
            return ""
        return f"<<{origin.relative_path_to(doc)}#,{link_text}>>"

    home_row = f" +\n{_xref_string(doc, root_doc, 'Home')}" if root_doc != doc else ''
    return f"""\
ifdef::backend-html5[]
++++
<div id="navigation">
++++
endif::[]
[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|{_xref_string(doc, prev_doc, 'Prev')}

|{_xref_string(doc, up_doc, 'Up')}{home_row}

|{_xref_string(doc, next_doc, 'Next')}
|===
ifdef::backend-html5[]
++++
</div>
++++
endif::[]"""


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


def multipage_toc(doc: Document, side: str = "left") -> str:
    current_doc = doc
    breadcrumbs = {doc}
    parent = doc.parent()
    while parent is not None:
        doc = parent
        breadcrumbs.add(doc)
        parent = doc.parent()

    toc = _toc_div(side)
    _toc_title(toc, link=_relative_html_link(current_doc, doc), text=doc.title)

    if doc is not None:
        _toc(parent=toc, doc=doc, current_doc=current_doc, level=1, breadcrumbs=breadcrumbs)

    return _pretty_html(toc)


def _toc(parent: ET.Element, doc: Document, current_doc: Document, level: int,
         breadcrumbs: Set[Document]) -> None:
    if not any(child.included_in is doc for child in doc.children):
        return

    ul = _toc_ul(parent, level)
    for child in doc.children:
        if child.included_in is doc:
            li = _toc_li(ul, link=_relative_html_link(current_doc, child), text=child.title)
            if len(child.children) > 0 and child in breadcrumbs:
                _toc(parent=li,
                     doc=child,
                     current_doc=current_doc,
                     level=level + 1,
                     breadcrumbs=breadcrumbs)


def _relative_html_link(current_doc: Document, target_doc: Document) -> str:
    return os.fspath(current_doc.relative_path_to(target_doc).with_suffix(".html"))
