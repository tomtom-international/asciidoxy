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
"""
Tests for the `asciidoxy.asciidoc`.
"""

import os
import pytest

from pathlib import Path

from asciidoxy.asciidoc import (AmbiguousReferenceError, Api, ConsistencyError, DocumentTreeNode,
                                IncludeFileNotFoundError, ReferenceNotFoundError,
                                TemplateMissingError, navigation_bar, process_adoc)
from asciidoxy.model import ReferableElement


@pytest.fixture
def sub_document_file(input_file):
    f = input_file.parent / "sub_dir" / "sub_doc.adoc"
    f.parent.mkdir(parents=True)
    f.touch()
    return f


@pytest.fixture
def sub_document_api(sub_document_file, context):
    return Api(sub_document_file, context)


@pytest.fixture
def preprocessing_api(input_file, context):
    context.preprocessing_run = True
    return Api(input_file, context)


@pytest.fixture
def warnings_are_errors():
    import asciidoxy.asciidoc
    asciidoxy.asciidoc.warnings_are_errors = True
    yield
    asciidoxy.asciidoc.warnings_are_errors = False


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def warnings_are_and_are_not_errors(request):
    import asciidoxy.asciidoc
    asciidoxy.asciidoc.warnings_are_errors = request.param
    yield
    asciidoxy.asciidoc.warnings_are_errors = False


@pytest.fixture
def multi_page():
    import asciidoxy.asciidoc
    asciidoxy.asciidoc.multi_page = True
    yield
    asciidoxy.asciidoc.multi_page = False


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def single_and_multi_page(request):
    import asciidoxy.asciidoc
    asciidoxy.asciidoc.multi_page = request.param
    yield
    asciidoxy.asciidoc.multi_page = False


@pytest.fixture
def document_tree_two_subpages():
    root = DocumentTreeNode(Path("/project/index.adoc"))
    sub_page1 = DocumentTreeNode(root.in_file.parent / "sub_page1.adoc", root)
    root.children.append(sub_page1)
    sub_page2 = DocumentTreeNode(root.in_file.parent / "sub_page2.adoc", root)
    root.children.append(sub_page2)
    return root


@pytest.fixture
def document_tree_two_levels_deep(document_tree_two_subpages):
    sub_page1 = document_tree_two_subpages.children[0]
    sub_page1.children.append(
        DocumentTreeNode(sub_page1.in_file.parent / "sub_page1_1.adoc", sub_page1))
    sub_page1.children.append(
        DocumentTreeNode(sub_page1.in_file.parent / "sub_page1_2.adoc", sub_page1))
    return document_tree_two_subpages


def _check_inserted_file_contains(inserted_adoc, expected):
    file_name = Path(inserted_adoc[9:-16])
    assert file_name.is_file()

    content = file_name.read_text(encoding="UTF-8")
    assert expected in content


def test_insert_class(api):
    result = api.insert("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_kind(api):
    result = api.insert_class("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_language(api):
    result = api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_all(api):
    result = api.insert_class("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_cpp_class_with_leveloffset(api):
    result = api.insert("asciidoxy::geometry::Coordinate", leveloffset="+3")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+3]")


def test_insert_cpp_enum(api):
    result = api.insert_enum("asciidoxy::traffic::TrafficEvent::Severity")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "enum asciidoxy::traffic::TrafficEvent::Severity")


def test_insert_cpp_class_with_alternative_tag(api):
    result = api.insert("asciidoxy::geometry::Coordinate", lang="c++")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_cpp_typedef(api):
    result = api.insert("asciidoxy::traffic::TpegCauseCode")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "TpegCauseCode =")


def test_insert_cpp_interface(api):
    result = api.insert("asciidoxy::system::Service", kind="interface")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::system::Service")


def test_insert_cpp_function(api):
    result = api.insert("asciidoxy::geometry::Coordinate::IsValid")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "bool IsValid()")

def test_insert_with_default_language(api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        api.insert("Logger")
    assert len(exception.value.candidates) == 2

    api.language("java")
    result = api.insert("Logger")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class Logger")


def test_insert_with_default_language_other_languages_are_ignored(api):
    api.language("objc")
    with pytest.raises(ReferenceNotFoundError):
        api.insert_class("Logger")


def test_insert_with_default_language_can_be_overridden(api):
    api.language("java")
    result = api.insert_class("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_relative_name_with_namespace(api):
    api.namespace("asciidoxy::geometry::")
    result = api.insert("Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_with_namespace_falls_back_to_full_name(api):
    api.namespace("asciidoxy::geometry::")
    result = api.insert("asciidoxy::traffic::TrafficEvent")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::traffic::TrafficEvent")


def test_insert_error_when_lang_not_supported(api):
    with pytest.raises(ReferenceNotFoundError):
        api.insert("asciidoxy::geometry::Coordinate", lang="smalltalk")


def test_insert_error_when_reference_not_found(api):
    with pytest.raises(ReferenceNotFoundError):
        api.insert("asciidoxy::geometry::Sphere")

@pytest.mark.parametrize("xml_data,api_reference_set", [(Path(__file__).parent / "data", [""])])
def test_insert_error_when_kind_not_supported(api):
    with pytest.raises(TemplateMissingError):
        api.insert("asciidoxy::unsupported_kind::kUnsupportedKindSample")


def test_insert_error_when_ambiguous(api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        api.insert_function("asciidoxy::traffic::TrafficEvent::TrafficEvent")
    assert len(exception.value.candidates) == 2
    exception_message = str(exception.value)
    assert (
        "Multiple matches for asciidoxy::traffic::TrafficEvent::TrafficEvent" in exception_message)
    assert "cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent()" in exception_message
    assert ("cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)" in
            exception_message)


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
def test_insert_tracks_all_references(api):
    api.insert("asciidoxy::positioning::Positioning")
    assert len(api._context.linked) == 10
    linked_names = [link.name for link in api._context.linked]
    assert "Coordinate" in linked_names
    assert "TrafficEvent" in linked_names


def test_link_class(api):
    result = api.link("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_function(api):
    result = api.link("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[IsValid]")


def test_link_class_explicit(api):
    result = api.link_class("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_function_explicit(api):
    result = api.link_function("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[IsValid]")


def test_link_class_with_full_name(api):
    result = api.link("asciidoxy::geometry::Coordinate", full_name=True)
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[asciidoxy::geometry::"
                      "Coordinate]")


def test_link_class_with_custom_text(api):
    result = api.link("asciidoxy::geometry::Coordinate", text="LINK HERE")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[LINK HERE]")


def test_link_class_with_alternative_language_tag(api):
    result = api.link("asciidoxy::geometry::Coordinate", lang="c++")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_class_not_found_warning(api):
    result = api.link("std::vector")
    assert result == "std::vector"


def test_link_class_not_found_error(warnings_are_errors, api):
    with pytest.raises(ReferenceNotFoundError):
        api.link("std::vector")


def test_link_cannot_mix_text_and_full_name(warnings_are_errors, api):
    with pytest.raises(ValueError):
        api.link("asciidoxy::geometry::Coordinate", text="ALT", full_name=True)


def test_cross_document_ref_with_relative_path(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file_rel, anchor)
    assert result == (f"<<{target_file_rel_to_base_dir.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{anchor}>>")


def test_cross_document_ref_with_relative_path_multipage(sub_document_api, sub_document_file,
                                                         multi_page):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"

    result = sub_document_api.cross_document_ref(target_file_rel, anchor)
    assert result == (f"<<{target_file_rel}#{anchor},{anchor}>>")


def test_cross_document_ref_with_absolute_path(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    target_file = sub_document_file.parent / "includes" / "other_file.adoc"

    result = sub_document_api.cross_document_ref(target_file, anchor)
    assert result == (f"<<{target_file.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{anchor}>>")


def test_cross_document_ref_with_absolute_path_multipage(sub_document_api, sub_document_file,
                                                         multi_page):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel

    result = sub_document_api.cross_document_ref(target_file, anchor)
    assert result == (f"<<{target_file}#{anchor},{anchor}>>")


def test_cross_document_ref_with_link_text(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    link_text = "Link"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file_rel, anchor, link_text)
    assert result == (f"<<{target_file_rel_to_base_dir.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{link_text}>>")


def test_include_relative_path(api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include("includes/another_file.adoc")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")

    file_name = input_file.parent / result[9:-16]
    assert file_name.is_file()
    assert file_name.name == ".asciidoxy.another_file.adoc"


def test_include_relative_path_multipage(api, context, input_file, multi_page):
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(include_file_rel)
    assert result == f"<<{include_file_rel}#,{include_file_rel}>>"
    assert include_file.with_name(f".asciidoxy.{include_file.name}").is_file()


def test_include_absolute_path(api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(os.fspath(include_file))
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")

    file_name = input_file.parent / result[9:-16]
    assert file_name.is_file()
    assert file_name.name == ".asciidoxy.another_file.adoc"


def test_include_absolute_path_multipage(api, context, input_file, multi_page):
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(include_file)
    assert result == f"<<{include_file_rel}#,{include_file_rel}>>"
    assert include_file.with_name(f".asciidoxy.{include_file.name}").is_file()


def test_include_with_leveloffset(api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include("includes/another_file.adoc", leveloffset="-1")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=-1]")


def test_include_multipage_with_link_text(api, context, input_file, multi_page):
    link_text = "Link"
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(include_file_rel, link_text=link_text)
    assert result == f"<<{include_file_rel}#,{link_text}>>"


def test_include_multipage_with_prefix_text(api, context, input_file, multi_page):
    prefix = ". "
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(include_file_rel, link_prefix=prefix)
    assert result == f"{prefix}<<{include_file_rel}#,{include_file_rel}>>"


def test_include_multipage_without_link(api, context, input_file, multi_page):
    prefix = ". "
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    result = api.include(include_file_rel, link_prefix=prefix, multi_page_link=False)
    assert result == ""


def test_include_error_file_not_found(api, input_file):
    with pytest.raises(IncludeFileNotFoundError):
        api.include("non_existing_file.adoc")


@pytest.mark.parametrize("test_file_name", ["simple_test", "link_to_member"])
def test_process_adoc_single_file(warnings_are_and_are_not_errors, build_dir, test_file_name,
                                  single_and_multi_page, adoc_data, xml_data):
    input_file = adoc_data / f"{test_file_name}.input.adoc"
    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"

    output_file = process_adoc(input_file, build_dir, [xml_data])[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(build_dir), "BUILD_DIR")
    assert content == expected_output_file.read_text()


def test_process_adoc_multi_file(warnings_are_errors, build_dir, single_and_multi_page, adoc_data,
                                 xml_data):
    from asciidoxy.asciidoc import multi_page

    main_doc_file = adoc_data / "multifile_test.input.adoc"
    sub_doc_file = main_doc_file.parent / "sub_directory" / "multifile_subdoc_test.input.adoc"
    sub_doc_in_table_file = main_doc_file.parent / "sub_directory" \
        / "multifile_subdoc_in_table_test.input.adoc"

    output_files = process_adoc(main_doc_file, build_dir, [xml_data])
    assert len(output_files) == 3
    assert (
        output_files[main_doc_file] == main_doc_file.with_name(f".asciidoxy.{main_doc_file.name}"))
    assert (output_files[sub_doc_file] == sub_doc_file.with_name(f".asciidoxy.{sub_doc_file.name}"))
    assert (output_files[sub_doc_in_table_file] ==
            sub_doc_file.with_name(f".asciidoxy.{sub_doc_in_table_file.name}"))
    for input_file, output_file in output_files.items():
        assert output_file.is_file()
        expected_output_file = input_file.with_suffix(
            ".expected.multipage.adoc" if multi_page else ".expected.singlepage.adoc")
        content = output_file.read_text()
        content = content.replace(os.fspath(build_dir), "BUILD_DIR")
        assert content == expected_output_file.read_text()


@pytest.mark.parametrize("test_file_name",
                         ["dangling_link", "dangling_cross_doc_ref", "double_insert",
                          "dangling_link_in_insert"])
def test_process_adoc_file_warning(build_dir, test_file_name, single_and_multi_page, adoc_data,
                                   xml_data):
    from asciidoxy.asciidoc import multi_page

    input_file = adoc_data / f"{test_file_name}.input.adoc"

    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"
    if multi_page:
        expected_output_file_multipage = expected_output_file.with_suffix('.multipage.adoc')
        if expected_output_file_multipage.is_file():
            expected_output_file = expected_output_file_multipage

    output_file = process_adoc(input_file, build_dir, [xml_data])[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(build_dir), "BUILD_DIR")
    assert content == expected_output_file.read_text()


@pytest.mark.parametrize("test_file_name, error", [("dangling_link", ConsistencyError),
                                                   ("dangling_cross_doc_ref", ConsistencyError),
                                                   ("double_insert", ConsistencyError),
                                                   ("dangling_link_in_insert", ConsistencyError)])
def test_process_adoc_file_warning_as_error(warnings_are_errors, build_dir, test_file_name, error,
                                            single_and_multi_page, adoc_data, xml_data):
    input_file = adoc_data / f"{test_file_name}.input.adoc"

    with pytest.raises(error):
        process_adoc(input_file, build_dir, [xml_data])


def test_context_create_sub_context(context):
    context.namespace = "ns"
    context.language = "lang"

    sub = context.sub_context()
    assert sub is not context

    assert sub.base_dir == context.base_dir
    assert sub.build_dir == context.build_dir
    assert sub.fragment_dir == context.fragment_dir

    assert sub.namespace == context.namespace
    assert sub.language == context.language

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


def test_document_tree_node():
    # Test tree:
    #
    #       root
    #        /|\
    #       / | \
    #      /  |  \
    #     /   |   \
    #    a    b    c
    #    /\        /\
    #   /  \      /  \
    # a_a  a_b  c_a  c_b
    #      / \
    #     /   \
    #    /     \
    #  a_b_a  a_b_b
    root = DocumentTreeNode('root')
    a = DocumentTreeNode('a', root)
    root.children.append(a)
    b = DocumentTreeNode('b', root)
    root.children.append(b)
    c = DocumentTreeNode('c', root)
    root.children.append(c)
    a_a = DocumentTreeNode('a_a', a)
    a.children.append(a_a)
    a_b = DocumentTreeNode('a_b', a)
    a.children.append(a_b)
    a_b_a = DocumentTreeNode('a_b_a', a_b)
    a_b.children.append(a_b_a)
    a_b_b = DocumentTreeNode('a_b_b', a_b)
    a_b.children.append(a_b_b)
    c_a = DocumentTreeNode('c_a', c)
    c.children.append(c_a)
    c_b = DocumentTreeNode('c_b', c)
    c.children.append(c_b)

    def verify_node(node: DocumentTreeNode, expected_parent: DocumentTreeNode,
                    expected_prev: DocumentTreeNode, expected_next: DocumentTreeNode):
        assert node.root() is root
        assert node.parent is expected_parent
        assert node.preorder_traversal_prev() is expected_prev
        assert node.preorder_traversal_next() is expected_next

    verify_node(root, expected_parent=None, expected_prev=None, expected_next=a)
    verify_node(a, expected_parent=root, expected_prev=root, expected_next=a_a)
    verify_node(a_a, expected_parent=a, expected_prev=a, expected_next=a_b)
    verify_node(a_b, expected_parent=a, expected_prev=a_a, expected_next=a_b_a)
    verify_node(a_b_a, expected_parent=a_b, expected_prev=a_b, expected_next=a_b_b)
    verify_node(a_b_b, expected_parent=a_b, expected_prev=a_b_a, expected_next=b)
    verify_node(b, expected_parent=root, expected_prev=a_b_b, expected_next=c)
    verify_node(c, expected_parent=root, expected_prev=b, expected_next=c_a)
    verify_node(c, expected_parent=root, expected_prev=b, expected_next=c_a)
    verify_node(c_a, expected_parent=c, expected_prev=c, expected_next=c_b)
    verify_node(c_b, expected_parent=c, expected_prev=c_a, expected_next=None)


def test_document_tree_node_all_documents_from_root_node(document_tree_two_levels_deep):

    assert ({str(d.in_file)
             for d in document_tree_two_levels_deep.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_document_tree_node_all_documents_from_middle_node(document_tree_two_levels_deep):
    middle_doc = document_tree_two_levels_deep.children[1]

    assert ({str(d.in_file)
             for d in middle_doc.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_document_tree_node_all_documents_from_leaf_node(document_tree_two_levels_deep):
    leaf_doc = document_tree_two_levels_deep.children[0].children[0]

    assert ({str(d.in_file)
             for d in leaf_doc.all_documents_in_tree()} == {
                 "/project/index.adoc", "/project/sub_page1.adoc", "/project/sub_page2.adoc",
                 "/project/sub_page1_1.adoc", "/project/sub_page1_2.adoc"
             })


def test_navigation_bar_first_document(document_tree_two_subpages):
    next_doc = document_tree_two_subpages.children[0]
    assert navigation_bar(document_tree_two_subpages) == (
        f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|

|

|<<{next_doc.in_file.relative_to(document_tree_two_subpages.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_middle_document(document_tree_two_subpages):
    doc = document_tree_two_subpages.children[0]
    next_doc = document_tree_two_subpages.children[1]
    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Home>>

|<<{next_doc.in_file.relative_to(document_tree_two_subpages.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_last_document(document_tree_two_subpages):
    doc = document_tree_two_subpages.children[1]
    prev_doc = document_tree_two_subpages.children[0]
    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{prev_doc.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_subpages.in_file.relative_to(doc.in_file.parent)}#,Home>>

|
|===""")


def test_navigation_bar_all_links_different(document_tree_two_levels_deep):
    doc = document_tree_two_levels_deep.children[0].children[1]
    prev_doc = document_tree_two_levels_deep.children[0].children[0]
    next_doc = document_tree_two_levels_deep.children[1]
    up_doc = document_tree_two_levels_deep.children[0]

    assert navigation_bar(doc) == (f"""[frame=none, grid=none, cols="<.^,^.^,>.^"]
|===
|<<{prev_doc.in_file.relative_to(doc.in_file.parent)}#,Prev>>

|<<{up_doc.in_file.relative_to(doc.in_file.parent)}#,Up>> +
<<{document_tree_two_levels_deep.in_file.relative_to(doc.in_file.parent)}#,Home>>

|<<{next_doc.in_file.relative_to(doc.in_file.parent)}#,Next>>
|===""")


def test_navigation_bar_single_document():
    doc = DocumentTreeNode("/project/index.adoc")
    assert not navigation_bar(doc)
