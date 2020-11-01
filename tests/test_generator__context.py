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
"""Tests for the generator's context."""

from pathlib import Path

from asciidoxy.model import ReferableElement

from .builders import make_compound


def test_create_sub_context(empty_context):
    context = empty_context
    context.namespace = "ns"
    context.language = "lang"
    context.source_language = "java"
    context.warnings_are_errors = True
    context.multipage = True
    context.embedded = True

    sub = context.sub_context()
    assert sub is not context

    assert sub.base_dir == context.base_dir
    assert sub.build_dir == context.build_dir
    assert sub.fragment_dir == context.fragment_dir

    assert sub.namespace == "ns"
    assert sub.language == "lang"
    assert sub.source_language == "java"

    assert sub.warnings_are_errors is True
    assert sub.multipage is True
    assert sub.embedded is True

    assert sub.reference is context.reference
    assert sub.progress is context.progress

    assert sub.linked is context.linked
    assert sub.inserted is context.inserted
    assert sub.in_to_out_file_map is context.in_to_out_file_map
    assert sub.embedded_file_map is context.embedded_file_map
    assert sub.current_document is context.current_document

    sub.namespace = "other"
    sub.language = "objc"
    sub.source_language = "python"
    assert context.namespace == "ns"
    assert context.language == "lang"
    assert context.source_language == "java"

    assert len(context.linked) == 0
    assert "element" not in context.inserted
    sub.linked.add(ReferableElement("element"))
    sub.inserted["element"] = Path("path")
    assert len(context.linked) == 1
    assert "element" in context.inserted


def test_file_with_element__different_file(empty_context):
    empty_context.multipage = True

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(lang="lang", name="type1"))
    empty_context.insert(make_compound(lang="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(lang="lang", name="type3"))
    empty_context.insert(make_compound(lang="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") == Path("file_1.adoc")
    assert empty_context.file_with_element("lang-type2") == Path("file_1.adoc")


def test_file_with_element__same_file(empty_context):
    empty_context.multipage = True

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(lang="lang", name="type1"))
    empty_context.insert(make_compound(lang="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(lang="lang", name="type3"))
    empty_context.insert(make_compound(lang="lang", name="type4"))

    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__not_in_singlepage(empty_context):
    empty_context.multipage = False

    empty_context.current_document.in_file = Path("file_1.adoc")
    empty_context.insert(make_compound(lang="lang", name="type1"))
    empty_context.insert(make_compound(lang="lang", name="type2"))

    empty_context.current_document.in_file = Path("file_2.adoc")
    empty_context.insert(make_compound(lang="lang", name="type3"))
    empty_context.insert(make_compound(lang="lang", name="type4"))

    assert empty_context.file_with_element("lang-type1") is None
    assert empty_context.file_with_element("lang-type2") is None
    assert empty_context.file_with_element("lang-type3") is None
    assert empty_context.file_with_element("lang-type4") is None


def test_file_with_element__element_not_found(empty_context):
    empty_context.multipage = True
    assert empty_context.file_with_element("element-id-1") is None
