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


def test_context_create_sub_context(context):
    context.namespace = "ns"
    context.language = "lang"
    context.preprocessing_run = False
    context.warnings_are_errors = True
    context.mult_page = True

    sub = context.sub_context()
    assert sub is not context

    assert sub.base_dir == context.base_dir
    assert sub.build_dir == context.build_dir
    assert sub.fragment_dir == context.fragment_dir

    assert sub.namespace == context.namespace
    assert sub.language == context.language

    assert sub.preprocessing_run == context.preprocessing_run
    assert sub.warnings_are_errors == context.warnings_are_errors
    assert sub.multi_page == context.multi_page

    assert sub.reference is context.reference
    assert sub.linked is context.linked
    assert sub.inserted is context.inserted

    sub.namespace = "other"
    sub.language = "objc"
    assert sub.namespace != context.namespace
    assert sub.language != context.language

    assert len(context.linked) == 0
    assert "element" not in context.inserted
    sub.linked.append(ReferableElement("element"))
    sub.inserted["element"] = Path("path")
    assert len(context.linked) == 1
    assert "element" in context.inserted


def test_context_link_to_element_singlepage(context):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file.parent / file_containing_element
    assert context.link_to_element(element_id, link_text) == f"xref:{element_id}[{link_text}]"


def test_context_link_to_element_multipage(context, multi_page):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file.parent / file_containing_element
    assert (context.link_to_element(
        element_id, link_text) == f"xref:{file_containing_element}#{element_id}[{link_text}]")


def test_context_link_to_element_multipage_element_in_the_same_document(context, multi_page):
    element_id = "element"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file
    assert (context.link_to_element(element_id, link_text) == f"xref:{element_id}[{link_text}]")


def test_context_link_to_element_element_not_inserted(context, single_and_multi_page):
    element_id = "element"
    link_text = "Link"
    assert element_id not in context.inserted
    assert context.link_to_element(element_id, link_text) == f"xref:{element_id}[{link_text}]"
