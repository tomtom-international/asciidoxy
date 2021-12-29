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
"""Tests for the generator's context."""

from pathlib import Path

import pytest

from asciidoxy.document import Package
from asciidoxy.generator.context import StackFrame, stacktrace
from asciidoxy.generator.errors import ConsistencyError, DuplicateAnchorError, UnknownAnchorError
from asciidoxy.packaging import UnknownFileError, UnknownPackageError

from ..builders import make_compound


def test_initial_document_is_registered(empty_context, document):
    assert empty_context.document is document
    assert document.relative_path in empty_context.documents
    assert empty_context.documents[document.relative_path] is document
    assert empty_context.document_stack == [document]


def test_create_sub_context(empty_context, document):
    context = empty_context
    context.namespace = "ns"
    context.language = "lang"
    context.source_language = "java"
    context.env.variable = 42

    sub_doc = document.with_relative_path("other.adoc")
    sub = context.sub_context(sub_doc)
    assert sub is not context
    assert sub.document is sub_doc
    assert sub.document_stack == [document, sub_doc]

    assert sub.namespace == "ns"
    assert sub.language == "lang"
    assert sub.source_language == "java"

    assert sub.env is not context.env
    assert sub.env.variable == 42

    assert sub.reference is context.reference
    assert sub.progress is context.progress

    assert sub.linked is context.linked
    assert sub.inserted is context.inserted
    assert sub.anchors is context.anchors
    assert sub.call_stack is context.call_stack
    assert sub.documents is context.documents
    assert sub.templates is context.templates
    assert sub.document_cache is context.document_cache
    assert sub.config is context.config

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

    assert context.document_stack == [document]
    sub.document_stack.append(document.with_relative_path("bla"))
    assert context.document_stack == [document]


def test_file_with_element__different_file(empty_context):
    empty_context.config.multipage = True

    doc1 = empty_context.document.with_relative_path("file_1.adoc")
    empty_context.document = doc1
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    doc2 = empty_context.document.with_relative_path("file_2.adoc")
    empty_context.document = doc2
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") is doc1
    assert empty_context.file_with_element("lang-type2") is doc1


def test_file_with_element__same_file(empty_context):
    empty_context.config.multipage = True

    doc1 = empty_context.document.with_relative_path("file_1.adoc")
    empty_context.document = doc1
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    doc2 = empty_context.document.with_relative_path("file_2.adoc")
    empty_context.document = doc2
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__not_in_singlepage(empty_context):
    empty_context.config.multipage = False

    doc1 = empty_context.document.with_relative_path("file_1.adoc")
    empty_context.document = doc1
    empty_context.insert(make_compound(language="lang", name="type1"))
    empty_context.insert(make_compound(language="lang", name="type2"))

    doc2 = empty_context.document.with_relative_path("file_2.adoc")
    empty_context.document = doc2
    empty_context.insert(make_compound(language="lang", name="type3"))
    empty_context.insert(make_compound(language="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") is None
    assert empty_context.file_with_element("lang-type2") is None
    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__element_not_found(empty_context):
    empty_context.config.multipage = True
    assert empty_context.file_with_element("element-id-1") is None


def test_link_to_document__singlepage__included(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    document.include(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("../dir2/linked_file.adoc")


def test_link_to_document__singlepage__not_included(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    assert empty_context.link_to_document(linked_doc) == Path("../dir2/linked_file.adoc")


def test_link_to_document__singlepage__embedded__same_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    document.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("index.adoc")


def test_link_to_document__singlepage__embedded__other_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    other_doc = document.with_relative_path("other_file.adoc")
    other_doc.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("../other_file.adoc")


def test_link_to_document__singlepage__embedded_multiple_times__same_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    document.embed(linked_doc)
    other_doc = document.with_relative_path("dir3/other_file.adoc")
    other_doc.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("index.adoc")


def test_link_to_document__singlepage__embedded_multiple_times__other_files(
        empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    linked_doc = document.with_relative_path("linked_file.adoc")
    other_doc = document.with_relative_path("other_file.adoc")
    other_doc.embed(linked_doc)
    another_doc = document.with_relative_path("another_file.adoc")
    another_doc.embed(linked_doc)
    with pytest.raises(ConsistencyError):
        empty_context.link_to_document(linked_doc)


def test_link_to_document__multipage__included(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("linked_file.adoc")
    document.include(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("../linked_file.adoc")


def test_link_to_document__multipage__not_included(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("linked_file.adoc")
    assert empty_context.link_to_document(linked_doc) == Path("../linked_file.adoc")


def test_link_to_document__multipage__embedded__same_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    document.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("index.adoc")


def test_link_to_document__multipage__embedded__other_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    other_doc = document.with_relative_path("dir3/other_file.adoc")
    other_doc.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("../dir3/other_file.adoc")


def test_link_to_document__multipage__embedded_multiple_times__same_file(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("linked_file.adoc")
    document.embed(linked_doc)
    other_doc = document.with_relative_path("dir3/other_file.adoc")
    other_doc.embed(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("index.adoc")


def test_link_to_document__multipage__embedded_multiple_times__other_files(empty_context, document):
    document.relative_path = Path("dir1/index.adoc")
    empty_context.config.multipage = True
    linked_doc = document.with_relative_path("linked_file.adoc")
    other_doc = document.with_relative_path("other_file.adoc")
    other_doc.embed(linked_doc)
    another_doc = document.with_relative_path("another_file.adoc")
    another_doc.embed(linked_doc)
    with pytest.raises(ConsistencyError):
        empty_context.link_to_document(linked_doc)


def test_link_to_document__multipage__inside_embedded_file(empty_context, document):
    empty_context.config.multipage = True
    document.relative_path = Path("dir1/index.adoc")
    document.is_root = False
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.embed(document)
    empty_context.document_stack.insert(0, parent)
    linked_doc = document.with_relative_path("dir2/linked_file.adoc")
    document.include(linked_doc)
    assert empty_context.link_to_document(linked_doc) == Path("dir2/linked_file.adoc")


def test_docinfo_footer_file__singlepage(empty_context, document):
    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == document.work_file.parent
    assert footer_file.name == f"{document.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__singlepage__included(empty_context, document):
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.include(document)
    document.is_root = False

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == parent.work_file.parent
    assert footer_file.name == f"{parent.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__singlepage__embedded(empty_context, document):
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.embed(document)
    document.is_root = False

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == parent.work_file.parent
    assert footer_file.name == f"{parent.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage(empty_context, document):
    empty_context.config.multipage = True

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == document.work_file.parent
    assert footer_file.name == f"{document.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage__included(empty_context, document):
    empty_context.config.multipage = True
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.include(document)
    document.is_root = False

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == document.work_file.parent
    assert footer_file.name == f"{document.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage__embedded(empty_context, document):
    empty_context.config.multipage = True
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.embed(document)
    document.is_root = False
    empty_context.document_stack.insert(0, parent)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == parent.work_file.parent
    assert footer_file.name == f"{parent.relative_path.stem}-docinfo-footer.html"


def test_docinfo_footer_file__multipage__embedded_multiple_times(empty_context, document):
    empty_context.config.multipage = True
    other_parent = document.with_relative_path("other_parent.adoc")
    other_parent.embed(document)
    parent = document.with_relative_path("parent.adoc")
    parent.is_root = True
    parent.embed(document)
    document.is_root = False
    empty_context.document_stack.insert(0, parent)

    footer_file = empty_context.docinfo_footer_file()
    assert footer_file.parent == parent.work_file.parent
    assert footer_file.name == f"{parent.relative_path.stem}-docinfo-footer.html"


def test_register_and_link_to_anchor__same_file(empty_context, document):
    empty_context.register_anchor("my-anchor", "anchor text")
    assert empty_context.link_to_anchor("my-anchor") == (document.relative_path, "anchor text")


def test_register_and_link_to_anchor__different_file(empty_context, document):
    empty_context.document = document.with_relative_path("other.adoc")
    empty_context.register_anchor("my-anchor", "anchor text")
    empty_context.document = document
    assert empty_context.link_to_anchor("my-anchor") == (Path("other.adoc"), "anchor text")


def test_register_and_link_to_anchor__no_link_text(empty_context, document):
    empty_context.register_anchor("my-anchor", None)
    assert empty_context.link_to_anchor("my-anchor") == (document.relative_path, None)


def test_register_anchor__duplicate_name(empty_context):
    empty_context.register_anchor("my-anchor", None)
    with pytest.raises(DuplicateAnchorError):
        empty_context.register_anchor("my-anchor", None)


def test_link_to_anchor__unknown(empty_context):
    with pytest.raises(UnknownAnchorError):
        empty_context.link_to_anchor("my-anchor")


def test_link_to_element__single_link(empty_context, document):
    empty_context.push_stack("link(\"MyElement\")", document, Package.INPUT_PACKAGE_NAME)
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    assert "my-element-id" in empty_context.linked
    assert empty_context.linked["my-element-id"] == [
        [
            StackFrame("link(\"MyElement\")", document.relative_path, Package.INPUT_PACKAGE_NAME,
                       False),
        ],
    ]


def test_link_to_element__multiple_links(empty_context, document):
    empty_context.push_stack("link(\"MyElement\")", document, Package.INPUT_PACKAGE_NAME)
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    other_doc = document.with_relative_path("other_file.adoc")
    empty_context.push_stack("link(\"MyElement\")", other_doc, Package.INPUT_PACKAGE_NAME)
    empty_context.link_to_element("my-element-id")
    empty_context.pop_stack()

    assert "my-element-id" in empty_context.linked
    assert empty_context.linked["my-element-id"] == [
        [
            StackFrame("link(\"MyElement\")", document.relative_path, Package.INPUT_PACKAGE_NAME,
                       False),
        ],
        [
            StackFrame("link(\"MyElement\")", other_doc.relative_path, Package.INPUT_PACKAGE_NAME,
                       False),
        ],
    ]


def test_link_to_element__nested_call_stack(empty_context, document):
    empty_context.push_stack("include(\"other_file.adoc\")", document, Package.INPUT_PACKAGE_NAME)
    other_doc = document.with_relative_path("other_file.adoc")
    empty_context.push_stack("insert(\"MyElement\")", other_doc)
    empty_context.push_stack("link(\"OtherElement\")")
    empty_context.link_to_element("other-element-id")
    empty_context.pop_stack()
    empty_context.pop_stack()
    empty_context.pop_stack()

    assert "other-element-id" in empty_context.linked
    assert empty_context.linked["other-element-id"] == [
        [
            StackFrame("include(\"other_file.adoc\")", document.relative_path,
                       Package.INPUT_PACKAGE_NAME, False),
            StackFrame("insert(\"MyElement\")", other_doc.relative_path, None, False),
            StackFrame("link(\"OtherElement\")", None, None, False),
        ],
    ]


def test_insert__store_stacktrace(empty_context, document):
    empty_context.push_stack("include(\"other_file.adoc\")", document, Package.INPUT_PACKAGE_NAME)

    element = make_compound(id="cpp-my_element", name="MyElement")
    empty_context.insert(element)

    empty_context.pop_stack()

    assert element.id in empty_context.inserted
    assert empty_context.inserted[element.id] == (document, [
        StackFrame("include(\"other_file.adoc\")", document.relative_path,
                   Package.INPUT_PACKAGE_NAME, False),
    ])


def test_insert__duplicate(empty_context, document):
    empty_context.config.warnings_are_errors = True

    element = make_compound(id="cpp-my_element", name="MyElement")
    other_doc = document.with_relative_path("other_file.adoc")

    empty_context.push_stack("include(\"other_file.adoc\")", document)
    empty_context.insert(element)
    empty_context.pop_stack()

    empty_context.push_stack("insert(\"MyElement\")", other_doc)
    with pytest.raises(ConsistencyError) as exc_info:
        empty_context.insert(element)
    empty_context.pop_stack()

    assert exc_info.value.msg == f"""\
Duplicate insertion of MyElement.
Trying to insert at:
  Commands in input files:
    {other_doc.relative_path}:
      insert("MyElement")
Previously inserted at:
  Commands in input files:
    {document.relative_path}:
      include("other_file.adoc")"""


def test_find_document__input_pkg__explicit_file(file_builder):
    doc = file_builder.add_input_file("base/index.adoc", register=False)
    context = file_builder.context()

    new_doc = context.find_document(Package.INPUT_PACKAGE_NAME, doc.relative_path)
    assert new_doc.relative_path == doc.relative_path
    assert new_doc.package.name == Package.INPUT_PACKAGE_NAME

    known_doc = context.find_document(Package.INPUT_PACKAGE_NAME, doc.relative_path)
    assert known_doc.relative_path == doc.relative_path
    assert known_doc.package.name == Package.INPUT_PACKAGE_NAME

    assert new_doc is known_doc


def test_find_document__input_pkg__default_file(file_builder):
    doc = file_builder.add_input_file("base/index.adoc", register=False)
    context = file_builder.context()

    new_doc = context.find_document(Package.INPUT_PACKAGE_NAME, None)
    assert new_doc.relative_path == doc.relative_path
    assert new_doc.package.name == Package.INPUT_PACKAGE_NAME

    known_doc = context.find_document(Package.INPUT_PACKAGE_NAME, None)
    assert known_doc.relative_path == doc.relative_path
    assert known_doc.package.name == Package.INPUT_PACKAGE_NAME

    assert new_doc is known_doc


def test_find_document__input_pkg__file_not_found(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    context = file_builder.context()

    with pytest.raises(UnknownFileError):
        context.find_document(Package.INPUT_PACKAGE_NAME, Path("unknown.adoc"))
    with pytest.raises(UnknownFileError):
        context.find_document(Package.INPUT_PACKAGE_NAME, Path("unknown.adoc"))


def test_find_document__pkg__explicit_file(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    doc = file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    new_doc = context.find_document("my-package", doc.relative_path)
    assert new_doc.relative_path == doc.relative_path
    assert new_doc.package.name == "my-package"

    known_doc = context.find_document("my-package", doc.relative_path)
    assert known_doc.relative_path == doc.relative_path
    assert known_doc.package.name == "my-package"

    assert new_doc is known_doc


def test_find_document__pkg__file_not_found(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    with pytest.raises(UnknownFileError):
        context.find_document("my-package", Path("other-file.adoc"))
    with pytest.raises(UnknownFileError):
        context.find_document("my-package", Path("other-file.adoc"))


def test_find_document__pkg__wrong_package_name(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    doc = file_builder.add_package_file("other-package", "other-doc.adoc", register=False)
    context = file_builder.context()

    with pytest.raises(UnknownFileError):
        context.find_document("my-package", doc.relative_path)
    with pytest.raises(UnknownFileError):
        context.find_document("my-package", doc.relative_path)


def test_find_document__pkg__package_name_must_match_for_known_files_too(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    doc = file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    new_doc = context.find_document("my-package", doc.relative_path)
    assert new_doc.relative_path == doc.relative_path
    assert new_doc.package.name == "my-package"

    with pytest.raises(UnknownFileError):
        context.find_document("other-package", doc.relative_path)


def test_find_document__pkg__unknown_package(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    doc = file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    with pytest.raises(UnknownPackageError):
        context.find_document("other-package", doc.relative_path)
    with pytest.raises(UnknownPackageError):
        context.find_document("other-package", doc.relative_path)


def test_find_document__pkg__default_file(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    doc = file_builder.add_package_default_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    new_doc = context.find_document("my-package", None)
    assert new_doc.relative_path == doc.relative_path
    assert new_doc.package.name == "my-package"

    known_doc = context.find_document("my-package", None)
    assert known_doc.relative_path == doc.relative_path
    assert known_doc.package.name == "my-package"

    assert new_doc is known_doc


def test_find_document__pkg__no_default_file(file_builder):
    file_builder.add_input_file("base/index.adoc", register=False)
    file_builder.add_package_file("my-package", "nice-doc.adoc", register=False)
    context = file_builder.context()

    with pytest.raises(UnknownFileError):
        context.find_document("my-package", None)
    with pytest.raises(UnknownFileError):
        context.find_document("my-package", None)


def test_output_document__singlepage__root_document(empty_context, document):
    assert empty_context.output_document is document


def test_output_document__multipage__root_document(empty_context, document):
    empty_context.config.multipage = True
    assert empty_context.output_document is document


def test_output_document__singlepage__included_document(empty_context, document):
    sub_doc = document.with_relative_path("sub.adoc")
    sub_context = empty_context.sub_context(sub_doc)
    document.include(sub_doc)
    assert sub_context.output_document is document


def test_output_document__multipage__included_document(empty_context, document):
    empty_context.config.multipage = True
    sub_doc = document.with_relative_path("sub.adoc")
    document.include(sub_doc)
    sub_context = empty_context.sub_context(sub_doc)
    assert sub_context.output_document is sub_doc


def test_output_document__singlepage__embedded_document(empty_context, document):
    sub_doc = document.with_relative_path("sub.adoc")
    sub_context = empty_context.sub_context(sub_doc)
    document.embed(sub_doc)
    assert sub_context.output_document is document


def test_output_document__multipage__embedded_document(empty_context, document):
    empty_context.config.multipage = True
    sub_doc = document.with_relative_path("sub.adoc")
    document.embed(sub_doc)
    sub_context = empty_context.sub_context(sub_doc)
    assert sub_context.output_document is document


def test_output_document__singlepage__multiple_embedded_document(empty_context, document):
    other_doc = document.with_relative_path("other.adoc")
    sub_doc = document.with_relative_path("sub.adoc")
    document.include(other_doc)
    other_doc.embed(sub_doc)

    sub_context = empty_context.sub_context(sub_doc)
    document.embed(sub_doc)
    assert sub_context.output_document is document


def test_output_document__multipage__multiple_embedded_document(empty_context, document):
    empty_context.config.multipage = True
    other_doc = document.with_relative_path("other.adoc")
    sub_doc = document.with_relative_path("sub.adoc")
    other_doc.embed(sub_doc)

    document.embed(sub_doc)
    sub_context = empty_context.sub_context(sub_doc)
    assert sub_context.output_document is document


def test_stacktrace__external_only(document):
    other_doc = document.with_relative_path("other_file.adoc")

    trace = [
        StackFrame("include('other_file.adoc')", document, Package.INPUT_PACKAGE_NAME, False),
        StackFrame("insert('MyElement')", other_doc, Package.INPUT_PACKAGE_NAME, False),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  {document.relative_path}:
    include('other_file.adoc')
  {other_doc.relative_path}:
    insert('MyElement')"""


def test_stacktrace__external_only__other_package(document):
    other_doc = document.with_relative_path("other_file.adoc")

    trace = [
        StackFrame("include('other_file.adoc')", document, "pkga", False),
        StackFrame("insert('MyElement')", other_doc, "pkgb", False),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  pkga:/{document.relative_path}:
    include('other_file.adoc')
  pkgb:/{other_doc.relative_path}:
    insert('MyElement')"""


def test_stacktrace__external_and_internal(document):
    other_doc = document.with_relative_path("other_file.adoc")

    trace = [
        StackFrame("include('other_file.adoc')", document, Package.INPUT_PACKAGE_NAME, False),
        StackFrame("insert('MyElement')", other_doc, Package.INPUT_PACKAGE_NAME, False),
        StackFrame("insert('OtherElement')", None, None, True),
        StackFrame("link('GreatElement')", None, None, True),
    ]
    assert stacktrace(trace) == f"""\
Commands in input files:
  {document.relative_path}:
    include('other_file.adoc')
  {other_doc.relative_path}:
    insert('MyElement')
Internal AsciiDoxy commands:
    insert('OtherElement')
    link('GreatElement')"""


def test_stacktrace__internal_only():
    trace = [
        StackFrame("insert('OtherElement')", None, None, True),
        StackFrame("link('GreatElement')", None, None, True),
    ]
    assert stacktrace(trace) == """\
Internal AsciiDoxy commands:
    insert('OtherElement')
    link('GreatElement')"""


def test_stacktrace__empty():
    assert stacktrace([]) == ""
