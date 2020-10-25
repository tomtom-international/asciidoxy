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
Tests for the `asciidoxy.generator.asciidoc`.
"""

import os
import pytest

from pathlib import Path

from asciidoxy.generator.asciidoc import GeneratingApi, PreprocessingApi, process_adoc
from asciidoxy.generator.navigation import DocumentTreeNode
from asciidoxy.generator.errors import (AmbiguousReferenceError, ConsistencyError,
                                        IncludeFileNotFoundError, IncompatibleVersionError,
                                        InvalidApiCallError, ReferenceNotFoundError,
                                        TemplateMissingError)
from asciidoxy import __version__
from .shared import ProgressMock


@pytest.fixture
def sub_document_file(input_file):
    f = input_file.parent / "sub_dir" / "sub_doc.adoc"
    f.parent.mkdir(parents=True)
    f.touch()
    return f


@pytest.fixture
def sub_document_api(sub_document_file, context):
    context.current_document = DocumentTreeNode(sub_document_file, context.current_document)
    context.base_dir = sub_document_file.parent
    return GeneratingApi(sub_document_file, context)


def _check_inserted_file_contains(inserted_adoc, expected):
    start_attributes = inserted_adoc.find("[")
    file_name = Path(inserted_adoc[9:start_attributes])
    assert file_name.is_file()

    content = file_name.read_text(encoding="UTF-8")
    assert expected in content


def _check_inserted_file_does_not_contain(inserted_adoc, expected):
    file_name = Path(inserted_adoc[9:-16])
    assert file_name.is_file()

    content = file_name.read_text(encoding="UTF-8")
    assert expected not in content


def test_insert__preprocessing(preprocessing_api):
    result = preprocessing_api.insert("asciidoxy::geometry::Coordinate")
    assert not result


def test_insert_class(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_kind(generating_api):
    result = generating_api.insert_class("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_language(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_all(generating_api):
    result = generating_api.insert_class("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_cpp_class_with_leveloffset(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", leveloffset="+3")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+3]")


def test_insert_class_with_extra_options(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", indent=2)
    assert result.startswith("include::")
    assert result.endswith("[indent=2,leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_cpp_enum(generating_api):
    result = generating_api.insert_enum("asciidoxy::traffic::TrafficEvent::Severity")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "enum asciidoxy::traffic::TrafficEvent::Severity")


def test_insert_cpp_class_with_alternative_tag(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="c++")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_cpp_typedef(generating_api):
    result = generating_api.insert("asciidoxy::traffic::TpegCauseCode")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "TpegCauseCode =")


def test_insert_cpp_interface(generating_api):
    result = generating_api.insert("asciidoxy::system::Service", kind="interface")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::system::Service")


def test_insert_cpp_function(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate::IsValid")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "bool IsValid()")


def test_insert_with_default_language(generating_api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        generating_api.insert("Logger")
    assert len(exception.value.candidates) == 2

    generating_api.language("java")
    result = generating_api.insert("Logger")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class Logger")


def test_insert_with_default_language_other_languages_are_ignored(generating_api):
    generating_api.language("objc")
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert_class("Logger")


def test_insert_with_default_language_can_be_overridden(generating_api):
    generating_api.language("java")
    result = generating_api.insert_class("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert__transcode__explicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert_class("com.asciidoxy.geometry.Coordinate", lang="kotlin")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class com.asciidoxy.geometry.Coordinate")
    _check_inserted_file_contains(result, "kotlin")


def test_insert__transcode__implicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert_class("com.asciidoxy.geometry.Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class com.asciidoxy.geometry.Coordinate")
    _check_inserted_file_contains(result, "kotlin")


def test_insert__transcode__reset(generating_api):
    generating_api.language("kotlin", source="java")
    generating_api.language(None)
    result = generating_api.insert_class("com.asciidoxy.geometry.Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class com.asciidoxy.geometry.Coordinate")
    _check_inserted_file_does_not_contain(result, "kotlin")


def test_language__source_requires_lang(generating_api):
    with pytest.raises(InvalidApiCallError):
        generating_api.language("", source="java")

    with pytest.raises(InvalidApiCallError):
        generating_api.language(None, source="java")


def test_language__source_cannot_be_the_same_as_lang(generating_api):
    with pytest.raises(InvalidApiCallError):
        generating_api.language("java", source="java")

    with pytest.raises(InvalidApiCallError):
        generating_api.language("c++", source="cpp")


def test_insert_relative_name_with_namespace(generating_api):
    generating_api.namespace("asciidoxy::geometry::")
    result = generating_api.insert("Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_with_namespace_falls_back_to_full_name(generating_api):
    generating_api.namespace("asciidoxy::geometry::")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::traffic::TrafficEvent")


def test_insert_error_when_lang_not_supported(generating_api):
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert("asciidoxy::geometry::Coordinate", lang="smalltalk")


def test_insert_error_when_reference_not_found(generating_api):
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert("asciidoxy::geometry::Sphere")


@pytest.mark.parametrize("xml_data,api_reference_set", [(Path(__file__).parent / "data", [""])])
def test_insert_error_when_kind_not_supported(generating_api):
    with pytest.raises(TemplateMissingError):
        generating_api.insert("asciidoxy::unsupported_kind::kUnsupportedKindSample")


def test_insert_error_when_ambiguous(generating_api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        generating_api.insert_function("asciidoxy::traffic::TrafficEvent::TrafficEvent")
    assert len(exception.value.candidates) == 2
    exception_message = str(exception.value)
    assert ("Multiple matches for asciidoxy::traffic::TrafficEvent::TrafficEvent"
            in exception_message)
    assert "cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent()" in exception_message
    assert ("cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)"
            in exception_message)


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
def test_insert_tracks_all_references(preprocessing_api, generating_api, context):
    for api in (preprocessing_api, generating_api):
        context.linked = []
        api.insert("asciidoxy::positioning::Positioning")
        assert len(context.linked) == 10
        linked_names = [link.name for link in context.linked]
        assert "Coordinate" in linked_names
        assert "TrafficEvent" in linked_names


def test_insert_class__global_filter_members(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent")
    _check_inserted_file_does_not_contain(result, "SharedData")
    _check_inserted_file_contains(result, "Update")
    _check_inserted_file_contains(result, "CalculateDelay")


def test_insert_class__global_filter_members__ignore(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent", ignore_global_filter=True)
    _check_inserted_file_contains(result, "SharedData")
    _check_inserted_file_contains(result, "Update")
    _check_inserted_file_contains(result, "CalculateDelay")


def test_insert_class__global_filter_members__extend(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent", members="-Update")
    _check_inserted_file_does_not_contain(result, "SharedData")
    _check_inserted_file_does_not_contain(result, "Update")
    _check_inserted_file_contains(result, "CalculateDelay")


def test_link_class(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_function(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[IsValid]")


def test_link_class_explicit(generating_api):
    result = generating_api.link_class("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_function_explicit(generating_api):
    result = generating_api.link_function("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[IsValid]")


def test_link_class_with_full_name(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", full_name=True)
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[asciidoxy::geometry::"
                      "Coordinate]")


def test_link_class_with_custom_text(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", text="LINK HERE")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[LINK HERE]")


def test_link_class_with_alternative_language_tag(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", lang="c++")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[Coordinate]")


def test_link_class_with_transcoding(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.link("com.asciidoxy.geometry.Coordinate")
    assert result == "xref:kotlin-classcom_1_1asciidoxy_1_1geometry_1_1_coordinate[Coordinate]"


def test_link_class_with_transcoding__not_found_warning(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.link("com.asciidoxy.world.Coordinate")
    assert result == "com.asciidoxy.world.Coordinate"


def test_link_class_with_transcoding__not_found_error(warnings_are_errors, generating_api):
    generating_api.language("kotlin", source="java")
    with pytest.raises(ReferenceNotFoundError):
        generating_api.link("com.asciidoxy.world.Coordinate")


def test_link_class_not_found_warning(generating_api):
    result = generating_api.link("std::vector")
    assert result == "std::vector"


def test_link_class_not_found_error(warnings_are_errors, generating_api):
    with pytest.raises(ReferenceNotFoundError):
        generating_api.link("std::vector")


def test_link_cannot_mix_text_and_full_name(warnings_are_errors, generating_api):
    with pytest.raises(ValueError):
        generating_api.link("asciidoxy::geometry::Coordinate", text="ALT", full_name=True)


def test_cross_document_ref_with_relative_path(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file_rel, anchor)
    assert result == (f"<<{target_file_rel_to_base_dir.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{anchor}>>")


def test_cross_document_ref_with_relative_path_multipage(sub_document_api, sub_document_file,
                                                         multipage):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"

    result = sub_document_api.cross_document_ref(target_file_rel, anchor)
    assert result == (f"<<{target_file_rel}#{anchor},{anchor}>>")


def test_cross_document_ref_with_absolute_path(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    target_file = sub_document_file.parent / "includes" / "other_file.adoc"
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file, anchor)
    assert result == (f"<<{target_file_rel_to_base_dir.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{anchor}>>")


def test_cross_document_ref_with_absolute_path_multipage(sub_document_api, sub_document_file,
                                                         multipage, context):
    anchor = "anchor"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file, anchor)
    assert result == (f"<<{target_file_rel_to_base_dir}#{anchor},{anchor}>>")


def test_cross_document_ref_with_link_text(sub_document_api, sub_document_file, context):
    anchor = "anchor"
    link_text = "Link"
    target_file_rel = Path("includes") / "other_file.adoc"
    target_file = sub_document_file.parent / target_file_rel
    target_file_rel_to_base_dir = target_file.relative_to(context.base_dir)

    result = sub_document_api.cross_document_ref(target_file_rel, anchor, link_text)
    assert result == (f"<<{target_file_rel_to_base_dir.with_name(f'.asciidoxy.{target_file.name}')}"
                      f"#{anchor},{link_text}>>")


def test_include_relative_path(preprocessing_api, generating_api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc")
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = input_file.parent / result[9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include_relative_path__parent_directory(context, tmp_path):
    input_file = tmp_path / "src" / "input_file.adoc"
    input_file.parent.mkdir(parents=True)
    input_file.touch()

    include_file = tmp_path / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))
    context.current_document.in_file = input_file

    for api_class in (PreprocessingApi, GeneratingApi):
        api = api_class(input_file, context)
        result = api.include("../includes/another_file.adoc")
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = input_file.parent / result[9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include_relative_path_multipage(preprocessing_api, generating_api, context, input_file,
                                         multipage):
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(include_file_rel)
        assert result == f"<<{include_file_rel}#,{include_file_rel}>>"
        assert include_file.with_name(f".asciidoxy.{include_file.name}").is_file() == isinstance(
            api, GeneratingApi)


def test_include_absolute_path(preprocessing_api, generating_api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(os.fspath(include_file))
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = input_file.parent / result[9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include_absolute_path_multipage(preprocessing_api, generating_api, context, input_file,
                                         multipage):
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(include_file)
        assert result == f"<<{include_file_rel}#,{include_file_rel}>>"
        assert include_file.with_name(f".asciidoxy.{include_file.name}").is_file() == isinstance(
            api, GeneratingApi)


def test_include_with_leveloffset(preprocessing_api, generating_api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc", leveloffset="-1")
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=-1]")


def test_include_without_leveloffset(preprocessing_api, generating_api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc", leveloffset=None)
        assert result.startswith("include::")
        assert result.endswith("[]")


def test_include_multipage_with_link_text(preprocessing_api, generating_api, context, input_file,
                                          multipage):
    link_text = "Link"
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(include_file_rel, link_text=link_text)
        assert result == f"<<{include_file_rel}#,{link_text}>>"


def test_include_multipage_with_prefix_text(preprocessing_api, generating_api, context, input_file,
                                            multipage):
    prefix = ". "
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(include_file_rel, link_prefix=prefix)
        assert result == f"{prefix}<<{include_file_rel}#,{include_file_rel}>>"


def test_include_multipage_without_link(preprocessing_api, generating_api, context, input_file,
                                        multipage):
    prefix = ". "
    include_file_rel = Path("includes") / "another_file.adoc"
    include_file = input_file.parent / include_file_rel
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include(include_file_rel, link_prefix=prefix, multipage_link=False)
        assert result == ""


def test_include_with_extra_options(preprocessing_api, generating_api, context, input_file):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc", lines="1..10", indent=12)
        assert result.startswith("include::")
        assert result.endswith("[lines=1..10,indent=12,leveloffset=+1]")


def test_include_error_file_not_found(preprocessing_api, generating_api, input_file):
    for api in (preprocessing_api, generating_api):
        with pytest.raises(IncludeFileNotFoundError):
            api.include("non_existing_file.adoc")


def test_include__always_embed(preprocessing_api, generating_api, context, input_file,
                               single_and_multipage):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.in_file = input_file
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc", always_embed=True)
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = Path(result[9:-16])
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.is_absolute()


def test_include__always_embed__unique_name(preprocessing_api, generating_api, context, input_file,
                                            single_and_multipage):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.touch()
    context.current_document.in_file = input_file
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    file_names = []

    for _ in range(10):
        for api in (preprocessing_api, generating_api):
            result = api.include("includes/another_file.adoc", always_embed=True)
            assert result.startswith("include::")
            assert result.endswith("[leveloffset=+1]")

            file_name = Path(result[9:-16])
            assert file_name.is_file() == isinstance(api, GeneratingApi)
            assert file_name.is_absolute()

            if isinstance(api, PreprocessingApi):
                assert file_name not in file_names
                file_names.append(file_name)


def test_include__always_embed__correct_sub_context(preprocessing_api, generating_api, context,
                                                    input_file, single_and_multipage):
    include_file = input_file.parent / "includes" / "another_file.adoc"
    include_file.parent.mkdir(parents=True)
    include_file.write_text(f"""
${{api.cross_document_ref("../{input_file.name}", "")}}
""")
    context.current_document.in_file = input_file
    context.current_document.children.append(
        DocumentTreeNode(include_file, context.current_document))

    for api in (preprocessing_api, generating_api):
        result = api.include("includes/another_file.adoc", always_embed=True)
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = Path(result[9:-16])
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.is_absolute()

    contents = file_name.read_text()
    if single_and_multipage:
        # multipage
        assert "<<input_file.adoc#,>>" in contents
    else:
        # singlepage
        assert "<<includes/.asciidoxy.input_file.adoc#,>>" in contents


def test_multipage_toc__default(generating_api, input_file, multipage):
    result = generating_api.multipage_toc()
    assert result == ":docinfo: private"

    toc_file = input_file.parent / f".asciidoxy.{input_file.stem}-docinfo-footer.html"
    assert toc_file.is_file()


def test_multipage_toc__multipage_off(generating_api, input_file):
    result = generating_api.multipage_toc()
    assert not result

    toc_file = input_file.parent / f".asciidoxy.{input_file.stem}-docinfo-footer.html"
    assert not toc_file.exists()


def test_multipage_toc__preprocessing_run(preprocessing_api, input_file, multipage):
    result = preprocessing_api.multipage_toc()
    assert not result

    toc_file = input_file.parent / f".asciidoxy.{input_file.stem}-docinfo-footer.html"
    assert not toc_file.exists()


@pytest.mark.parametrize("warnings_are_errors", [True, False],
                         ids=["warnings-are-errors", "warnings-are-not-errors"])
@pytest.mark.parametrize("test_file_name", ["simple_test", "link_to_member"])
def test_process_adoc_single_file(warnings_are_errors, build_dir, test_file_name,
                                  single_and_multipage, adoc_data, api_reference):
    input_file = adoc_data / f"{test_file_name}.input.adoc"
    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"

    progress_mock = ProgressMock()
    output_file = process_adoc(input_file,
                               build_dir,
                               api_reference,
                               warnings_are_errors=warnings_are_errors,
                               progress=progress_mock)[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(build_dir), "BUILD_DIR")
    assert content == expected_output_file.read_text()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2


def test_process_adoc_multi_file(build_dir, single_and_multipage, adoc_data, api_reference):
    main_doc_file = adoc_data / "multifile_test.input.adoc"
    sub_doc_file = main_doc_file.parent / "sub_directory" / "multifile_subdoc_test.input.adoc"
    sub_doc_in_table_file = main_doc_file.parent / "sub_directory" \
        / "multifile_subdoc_in_table_test.input.adoc"

    progress_mock = ProgressMock()
    output_files = process_adoc(main_doc_file,
                                build_dir,
                                api_reference,
                                warnings_are_errors=True,
                                multipage=single_and_multipage,
                                progress=progress_mock)
    assert len(output_files) == 3
    assert (
        output_files[main_doc_file] == main_doc_file.with_name(f".asciidoxy.{main_doc_file.name}"))
    assert (output_files[sub_doc_file] == sub_doc_file.with_name(f".asciidoxy.{sub_doc_file.name}"))
    assert (output_files[sub_doc_in_table_file] == sub_doc_file.with_name(
        f".asciidoxy.{sub_doc_in_table_file.name}"))
    for input_file, output_file in output_files.items():
        assert output_file.is_file()
        expected_output_file = input_file.with_suffix(
            ".expected.multipage.adoc" if single_and_multipage else ".expected.singlepage.adoc")
        content = output_file.read_text()
        content = content.replace(os.fspath(build_dir), "BUILD_DIR")
        content = content.replace(os.fspath(adoc_data), "SRC_DIR")
        assert content == expected_output_file.read_text()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2 * len(output_files)


def test_process_adoc__embedded_file_not_in_output_map(build_dir, single_and_multipage, adoc_data,
                                                       api_reference):
    main_doc_file = adoc_data / "embeddedfile_test.input.adoc"

    progress_mock = ProgressMock()
    output_files = process_adoc(main_doc_file,
                                build_dir,
                                api_reference,
                                warnings_are_errors=True,
                                multipage=single_and_multipage,
                                progress=progress_mock)
    assert len(output_files) == 1
    assert (
        output_files[main_doc_file] == main_doc_file.with_name(f".asciidoxy.{main_doc_file.name}"))

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 4


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
@pytest.mark.parametrize(
    "test_file_name",
    ["dangling_link", "dangling_cross_doc_ref", "double_insert", "dangling_link_in_insert"])
def test_process_adoc_file_warning(build_dir, test_file_name, single_and_multipage, adoc_data,
                                   api_reference):
    input_file = adoc_data / f"{test_file_name}.input.adoc"

    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"
    if single_and_multipage:
        expected_output_file_multipage = expected_output_file.with_suffix('.multipage.adoc')
        if expected_output_file_multipage.is_file():
            expected_output_file = expected_output_file_multipage

    output_file = process_adoc(input_file, build_dir, api_reference,
                               multipage=single_and_multipage)[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(build_dir), "BUILD_DIR")
    assert content == expected_output_file.read_text()


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
@pytest.mark.parametrize("test_file_name, error", [("dangling_link", ConsistencyError),
                                                   ("dangling_cross_doc_ref", ConsistencyError),
                                                   ("double_insert", ConsistencyError),
                                                   ("dangling_link_in_insert", ConsistencyError)])
def test_process_adoc_file_warning_as_error(build_dir, test_file_name, error, single_and_multipage,
                                            adoc_data, api_reference):
    input_file = adoc_data / f"{test_file_name}.input.adoc"

    with pytest.raises(error):
        process_adoc(input_file, build_dir, api_reference, warnings_are_errors=True)


def test_require_version__exact_match(preprocessing_api):
    preprocessing_api.require_version(f"=={__version__}")


def test_require_version__exact_match__fail(preprocessing_api):
    version_parts = __version__.split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"=={version}")


def test_require_version__current_is_minimum(preprocessing_api):
    preprocessing_api.require_version(f">={__version__}")


def test_require_version__current_is_below_minimum(preprocessing_api):
    version_parts = __version__.split(".")
    version_parts[1] = str(int(version_parts[1]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f">={version}")


def test_require_version__current_is_minimum_optimistic(preprocessing_api):
    preprocessing_api.require_version(f"~={__version__}")


def test_require_version__current_is_below_minimum_optimistic(preprocessing_api):
    version_parts = __version__.split(".")
    version_parts[1] = str(int(version_parts[1]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"~={version}")


def test_require_version__allow_minor_increase(preprocessing_api):
    version_parts = __version__.split(".")
    version_parts[1] = str(int(version_parts[1]) - 1)
    version = ".".join(version_parts)
    preprocessing_api.require_version(f">={version}")


def test_require_version__optimistic_no_minor_increase(preprocessing_api):
    version_parts = __version__.split(".")
    version_parts[1] = str(int(version_parts[1]) - 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"~={version}")
