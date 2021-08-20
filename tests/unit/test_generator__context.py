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
"""Tests for the generator's context."""

import pytest

from pathlib import Path

from asciidoxy.generator.context import StackFrame, stacktrace
from asciidoxy.generator.errors import ConsistencyError, DuplicateAnchorError, UnknownAnchorError
from asciidoxy.generator.navigation import DocumentTreeNode

from .builders import make_compound


def test_create_sub_context(empty_context):
    context = empty_context
    context.namespace = "ns"
    context.language = "lang"
    context.source_language = "java"
    context.warnings_are_errors = True
    context.multipage = True
    context.embedded = True
    context.env.variable = 42

    sub = context.sub_context()
    assert sub is not context

    assert sub.base_dir == context.base_dir

    assert sub.namespace == "ns"
    assert sub.language == "lang"
    assert sub.source_language == "java"

    assert sub.env is not context.env
    assert sub.env.variable == 42

    assert sub.warnings_are_errors is True
    assert sub.multipage is True
    assert sub.embedded is True

    assert sub.reference is context.reference
    assert sub.progress is context.progress

    assert sub.linked is context.linked
    assert sub.inserted is context.inserted
    assert sub.anchors is context.anchors
    assert sub.in_to_out_file_map is context.in_to_out_file_map
    assert sub.embedded_file_map is context.embedded_file_map
    assert sub.current_document is context.current_document
    assert sub.current_package is context.current_package
    assert sub.call_stack is context.call_stack

    assert sub.insert_filter is not context.insert_filter

    sub.namespace = "other"
    sub.language = "objc"
    sub.source_language = "python"
    sub.env.variable = 50
    assert context.namespace == "ns"
    assert context.language == "lang"
    assert context.source_language == "java"
    assert context.env.variable == 42

    assert "element" not in context.linked
    assert "element" not in context.inserted
    sub.linked["element"].append([])
    sub.inserted["element"] = Path("path")
    assert "element" in context.linked
    assert "element" in context.inserted


def test_file_with_element__different_file(empty_context):
    empty_context.multipage = True

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") == Path("file_1.adoc")
    assert empty_context.file_with_element("lang-type2") == Path("file_1.adoc")


def test_file_with_element__same_file(empty_context):
    empty_context.multipage = True

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__not_in_singlepage(empty_context):
    empty_context.multipage = False

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") is None
    assert empty_context.file_with_element("lang-type2") is None
    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__element_not_found(empty_context):
    empty_context.multipage = True
    assert empty_context.file_with_element("element-id-1") is None


def test_register_adoc_file(empty_context, input_file):
    out_file = empty_context.register_adoc_file(input_file)
    assert out_file.parent == input_file.parent
    assert out_file.name.endswith(input_file.name)
    assert out_file.name.startswith(".asciidoxy.")
    assert out_file != input_file


def test_register_adoc_file__always_returns_same_file(empty_context, input_file):
    out_file = empty_context.register_adoc_file(input_file)
    assert empty_context.register_adoc_file(input_file) == out_file


def test_register_adoc_file__embedded(empty_context, input_file):
    empty_context.embedded = True
    embedded_file = input_file.with_name("embedded.adoc")

    out_file = empty_context.register_adoc_file(embedded_file)
    assert out_file.parent == embedded_file.parent
    assert out_file.name.endswith(embedded_file.name)
    assert out_file.name.startswith(".asciidoxy.")
    assert out_file != embedded_file


def test_register_adoc_file__embedded__always_returns_same_file(empty_context, input_file):
    empty_context.embedded = True
    embedded_file = input_file.with_name("embedded.adoc")

    out_file = empty_context.register_adoc_file(embedded_file)
    assert empty_context.register_adoc_file(embedded_file) == out_file


def test_register_adoc_file__embedded__different_file_when_embedded_in_different_file(
        empty_context, input_file):
    empty_context.embedded = True
    embedded_file = input_file.with_name("embedded.adoc")

    out_file = empty_context.register_adoc_file(embedded_file)

    other_input_file = input_file.with_name("other_file.adoc")
    empty_context.current_document.in_file = other_input_file

    assert empty_context.register_adoc_file(embedded_file) != out_file


def test_link_to_adoc_file__singlepage__known_file(empty_context, input_file):
    linked_file = input_file.with_name("linked_file.adoc")
    linked_out_file = empty_context.register_adoc_file(linked_file)
    assert empty_context.link_to_adoc_file(linked_file) == linked_out_file.relative_to(
        input_file.parent)


def test_link_to_adoc_file__singlepage__unknown_file(empty_context, input_file):
    linked_file = input_file.with_name("linked_file.adoc")
    assert empty_context.link_to_adoc_file(linked_file) == linked_file.relative_to(
        input_file.parent)


def test_link_to_adoc_file__singlepage__embedded_file(empty_context, input_file):
    empty_context.embedded = True
    linked_file = input_file.with_name("linked_file.adoc")
    linked_out_file = empty_context.register_adoc_file(linked_file)
    empty_context.embedded = False
    assert empty_context.link_to_adoc_file(linked_file) == linked_out_file.relative_to(
        input_file.parent)


def test_link_to_adoc_file__multipage__known_file(empty_context, input_file):
    empty_context.multipage = True
    linked_file = input_file.with_name("linked_file.adoc")
    empty_context.register_adoc_file(linked_file)
    assert empty_context.link_to_adoc_file(linked_file) == linked_file.relative_to(
        input_file.parent)


def test_link_to_adoc_file__multipage__unknown_file(empty_context, input_file):
    empty_context.multipage = True
    linked_file = input_file.with_name("linked_file.adoc")
    assert empty_context.link_to_adoc_file(linked_file) == linked_file.relative_to(
        input_file.parent)


def test_link_to_adoc_file__multipage__embedded_file(empty_context, input_file):
    empty_context.multipage = True
    empty_context.embedded = True
    linked_file = input_file.with_name("linked_file.adoc")
    linked_out_file = empty_context.register_adoc_file(linked_file)
    empty_context.embedded = False
    assert empty_context.link_to_adoc_file(linked_file) == linked_out_file.relative_to(
        input_file.parent)


def test_docinfo_footer_file__singlepage(empty_context, input_file):
    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{input_file.stem}-docinfo-footer.html"


def test_docinfo_footer_file__singlepage__included(empty_context, input_file):
    empty_context.register_adoc_file(input_file)

    included_file = input_file.with_name("sub_doc.adoc")
    empty_context.current_document = DocumentTreeNode(included_file, empty_context.current_document)
    empty_context.register_adoc_file(included_file)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{input_file.stem}-docinfo-footer.html"


def test_docinfo_footer_file__singlepage__embedded(empty_context, input_file):
    empty_context.register_adoc_file(input_file)

    embedded_file = input_file.with_name("sub_doc.adoc")
    empty_context.embedded = True
    empty_context.register_adoc_file(embedded_file)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{input_file.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage(empty_context, input_file):
    empty_context.multipage = True

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{input_file.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage__included(empty_context, input_file):
    empty_context.multipage = True
    empty_context.register_adoc_file(input_file)

    included_file = input_file.with_name("sub_doc.adoc")
    empty_context.current_document = DocumentTreeNode(included_file, empty_context.current_document)
    empty_context.register_adoc_file(included_file)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{included_file.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage__embedded(empty_context, input_file):
    empty_context.multipage = True
    empty_context.register_adoc_file(input_file)

    embedded_file = input_file.with_name("sub_doc.adoc")
    empty_context.embedded = True
    empty_context.register_adoc_file(embedded_file)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == input_file.parent
    assert footer_file.name == f".asciidoxy.{input_file.stem}-docinfo-footer.html"


def test_register_and_link_to_anchor__same_file(empty_context, input_file):
    empty_context.register_anchor("my-anchor", "anchor text", input_file)
    assert empty_context.link_to_anchor("my-anchor") == (Path(input_file.name), "anchor text")


def test_register_and_link_to_anchor__different_file(empty_context, input_file):
    other_file = input_file.with_name("other.adoc")
    empty_context.register_anchor("my-anchor", "anchor text", other_file)
    assert empty_context.link_to_anchor("my-anchor") == (Path(other_file.name), "anchor text")


def test_register_and_link_to_anchor__no_link_text(empty_context, input_file):
    empty_context.register_anchor("my-anchor", None, input_file)
    assert empty_context.link_to_anchor("my-anchor") == (Path(input_file.name), None)


def test_register_anchor__duplicate_name(empty_context, input_file):
    empty_context.register_anchor("my-anchor", None, input_file)
    with pytest.raises(DuplicateAnchorError):
        empty_context.register_anchor("my-anchor", None, input_file)


def test_link_to_anchor__unknown(empty_context, input_file):
    with pytest.raises(UnknownAnchorError):
        empty_context.link_to_anchor("my-anchor")


def test_link_to_element__single_link(empty_context, input_file):
    empty_context.push_stack("link(\"MyElement\")", input_file, "INPUT")
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    assert "my-element-id" in empty_context.linked
    assert empty_context.linked["my-element-id"] == [
        [
            StackFrame("link(\"MyElement\")", input_file, "INPUT", False),
        ],
    ]


def test_link_to_element__multiple_links(empty_context, input_file):
    empty_context.push_stack("link(\"MyElement\")", input_file, "INPUT")
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    other_file = input_file.parent / "other_file.adoc"
    empty_context.push_stack("link(\"MyElement\")", other_file, "INPUT")
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    assert "my-element-id" in empty_context.linked
    assert empty_context.linked["my-element-id"] == [
        [
            StackFrame("link(\"MyElement\")", input_file, "INPUT", False),
        ],
        [
            StackFrame("link(\"MyElement\")", other_file, "INPUT", False),
        ],
    ]


def test_link_to_element__nested_call_stack(empty_context, input_file):
    empty_context.push_stack("include(\"other_file.adoc\")", input_file, "INPUT")
    other_file = input_file.parent / "other_file.adoc"
    empty_context.push_stack("insert(\"MyElement\")", other_file)
    empty_context.push_stack("link(\"OtherElement\")")
    empty_context.link_to_element("other-element-id")
    empty_context.pop_stack()
    empty_context.pop_stack()
    empty_context.pop_stack()

    assert "other-element-id" in empty_context.linked
    assert empty_context.linked["other-element-id"] == [
        [
            StackFrame("include(\"other_file.adoc\")", input_file, "INPUT", False),
            StackFrame("insert(\"MyElement\")", other_file, None, False),
            StackFrame("link(\"OtherElement\")", None, None, False),
        ],
    ]


def test_insert__store_stacktrace(empty_context, input_file):
    empty_context.push_stack("include(\"other_file.adoc\")", input_file, "INPUT")

    element = make_compound(id="cpp-my_element", name="MyElement")
    empty_context.insert(element)

    empty_context.pop_stack()

    assert element.id in empty_context.inserted
    assert empty_context.inserted[element.id] == (input_file, [
        StackFrame("include(\"other_file.adoc\")", input_file, "INPUT", False),
    ])


def test_insert__duplicate(empty_context, input_file):
    empty_context.warnings_are_errors = True

    element = make_compound(id="cpp-my_element", name="MyElement")
    other_file = input_file.parent / "other_file.adoc"

    empty_context.push_stack("include(\"other_file.adoc\")", input_file)
    empty_context.insert(element)
    empty_context.pop_stack()

    empty_context.push_stack("insert(\"MyElement\")", other_file)
    with pytest.raises(ConsistencyError) as exc_info:
        empty_context.insert(element)
    empty_context.pop_stack()

    assert exc_info.value.msg == f"""\
Duplicate insertion of MyElement.
Trying to insert at:
  Commands in input files:
    {other_file}:
      insert("MyElement")
Previously inserted at:
  Commands in input files:
    {input_file}:
      include("other_file.adoc")"""


def test_stacktrace__external_only(input_file):
    other_file = input_file.parent / "other_file.adoc"

    trace = [
        StackFrame("include('other_file.adoc')", input_file, "INPUT", False),
        StackFrame("insert('MyElement')", other_file, "INPUT", False),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  {input_file}:
    include('other_file.adoc')
  {other_file}:
    insert('MyElement')"""


def test_stacktrace__external_only__other_package(input_file):
    other_file = input_file.parent / "other_file.adoc"

    trace = [
        StackFrame("include('other_file.adoc')", input_file, "pkga", False),
        StackFrame("insert('MyElement')", other_file, "pkgb", False),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  pkga:/{input_file}:
    include('other_file.adoc')
  pkgb:/{other_file}:
    insert('MyElement')"""


def test_stacktrace__external_and_internal(input_file):
    other_file = input_file.parent / "other_file.adoc"

    trace = [
        StackFrame("include('other_file.adoc')", input_file, "INPUT", False),
        StackFrame("insert('MyElement')", other_file, "INPUT", False),
        StackFrame("insert('OtherElement')", None, None, True),
        StackFrame("link('GreatElement')", None, None, True),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  {input_file}:
    include('other_file.adoc')
  {other_file}:
    insert('MyElement')
Internal AsciiDoxy commands:
    insert('OtherElement')
    link('GreatElement')"""


def test_stacktrace__internal_only(input_file):
    trace = [
        StackFrame("insert('OtherElement')", None, None, True),
        StackFrame("link('GreatElement')", None, None, True),
    ]
    assert stacktrace(trace) == """\
Internal AsciiDoxy commands:
    insert('OtherElement')
    link('GreatElement')"""


def test_stacktrace__empty(input_file):
    assert stacktrace([]) == ""
