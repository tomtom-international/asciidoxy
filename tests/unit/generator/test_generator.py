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
"""
Tests for the `asciidoxy.generator.asciidoc`.
"""

from pathlib import Path

import pytest

from asciidoxy import __version__
from asciidoxy.generator.asciidoc import GeneratingApi, PreprocessingApi
from asciidoxy.generator.cache import TemplateCache
from asciidoxy.generator.context import InsertData, StackFrame
from asciidoxy.generator.errors import (
    AmbiguousReferenceError,
    ConsistencyError,
    DuplicateIncludeError,
    IncludeFileNotFoundError,
    IncompatibleVersionError,
    InvalidApiCallError,
    MissingPackageError,
    MissingPackageFileError,
    ReferenceNotFoundError,
    TemplateMissingError,
    UnknownAnchorError,
)
from asciidoxy.packaging import Package
from asciidoxy.parser import parser_factory


@pytest.fixture
def api_reference(api_reference_loader, latest_doxygen_version):
    return api_reference_loader.version(latest_doxygen_version).add("doxygen",
                                                                    "cpp/consumer").load_all()


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def tdb_single_and_multipage(request, file_builder):
    file_builder.multipage = request.param
    return request.param


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def tdb_warnings_are_and_are_not_errors(request, file_builder):
    file_builder.warnings_are_errors = request.param
    return request.param


def test_insert__preprocessing(preprocessing_api):
    result = preprocessing_api.insert("asciidoxy::geometry::Coordinate")
    assert not result


def test_insert_class(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_class_explicit_kind(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", kind="class")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_class_explicit_language(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_class_explicit_all(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp", kind="class")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_cpp_class_with_leveloffset(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", leveloffset="+3")
    assert "==== Coordinate" in result
    assert "===== Members" in result


def test_insert_cpp_enum(generating_api):
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent::Severity", kind="enum")
    assert "enum asciidoxy::traffic::TrafficEvent::Severity" in result


def test_insert_cpp_class_with_alternative_tag(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="c++")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_cpp_typedef(generating_api):
    result = generating_api.insert("asciidoxy::traffic::TpegCauseCode")
    assert "TpegCauseCode =" in result


def test_insert_cpp_interface(generating_api):
    result = generating_api.insert("asciidoxy::system::Service", kind="interface")
    assert "class asciidoxy::system::Service" in result


def test_insert_cpp_function(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate::IsValid")
    assert "bool IsValid()" in result


def test_insert_with_default_language(generating_api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        generating_api.insert("Logger")
    assert len(exception.value.candidates) == 2

    generating_api.language("java")
    result = generating_api.insert("Logger")
    assert "class Logger" in result


def test_insert_with_default_language_other_languages_are_ignored(generating_api):
    generating_api.language("objc")
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert("Logger")


def test_insert_with_default_language_can_be_overridden(generating_api):
    generating_api.language("java")
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_with_custom_template(generating_api, context, tmp_path):
    template_dir = tmp_path / "templates"
    (template_dir / "cpp").mkdir(parents=True)
    (template_dir / "cpp" / "class.mako").write_text("Hello my class")
    context.templates = TemplateCache(template_dir)

    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result == "Hello my class"


def test_insert_with_custom_template_override_name(generating_api, context, tmp_path):
    template_dir = tmp_path / "templates"
    (template_dir / "cpp").mkdir(parents=True)
    (template_dir / "cpp" / "myclass.mako").write_text("Hello my class")
    context.templates = TemplateCache(template_dir)

    result = generating_api.insert("asciidoxy::geometry::Coordinate",
                                   lang="cpp",
                                   template="myclass")
    assert result == "Hello my class"


def test_insert__transcode__explicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate", lang="kotlin")
    assert "class com.asciidoxy.geometry.Coordinate" in result
    assert "kotlin" in result


def test_insert__transcode__implicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate")
    assert "class com.asciidoxy.geometry.Coordinate" in result
    assert "kotlin" in result


def test_insert__transcode__reset(generating_api):
    generating_api.language("kotlin", source="java")
    generating_api.language(None)
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate")
    assert "class com.asciidoxy.geometry.Coordinate" in result
    assert "kotlin" not in result


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
    assert "class asciidoxy::geometry::Coordinate" in result


def test_insert_with_namespace_falls_back_to_full_name(generating_api):
    generating_api.namespace("asciidoxy::geometry::")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent")
    assert "class asciidoxy::traffic::TrafficEvent" in result


def test_insert_error_when_lang_not_supported(generating_api):
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert("asciidoxy::geometry::Coordinate", lang="smalltalk")


def test_insert_error_when_reference_not_found(generating_api):
    with pytest.raises(ReferenceNotFoundError):
        generating_api.insert("asciidoxy::geometry::Sphere")


def test_insert_error_when_kind_not_supported(api_reference, generating_api, default_config,
                                              test_data):
    parser = parser_factory("doxygen", api_reference, default_config)
    parser.parse(test_data / "namespaceasciidoxy_1_1unsupported__kind.xml")
    with pytest.raises(TemplateMissingError):
        generating_api.insert("asciidoxy::unsupported_kind::kUnsupportedKindSample")


def test_insert_error_when_ambiguous(generating_api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        generating_api.insert("asciidoxy::traffic::TrafficEvent::TrafficEvent")
    assert len(exception.value.candidates) == 2
    exception_message = str(exception.value)
    assert ("Multiple matches for asciidoxy::traffic::TrafficEvent::TrafficEvent"
            in exception_message)
    assert "cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent()" in exception_message
    assert ("cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)"
            in exception_message)


def test_insert_tracks_all_references(preprocessing_api, context):
    preprocessing_api.insert("asciidoxy::positioning::Positioning")
    assert len(context.linked) == 3
    assert "cpp-classasciidoxy_1_1geometry_1_1_coordinate" in context.linked
    assert "cpp-classasciidoxy_1_1traffic_1_1_traffic_event" in context.linked
    assert "cpp-classasciidoxy_1_1geometry_1_1_invalid_coordinate" in context.linked


def test_link_stores_stack_trace(preprocessing_api, context, document):
    preprocessing_api.link("asciidoxy::geometry::Coordinate")
    assert "cpp-classasciidoxy_1_1geometry_1_1_coordinate" in context.linked
    traces = context.linked["cpp-classasciidoxy_1_1geometry_1_1_coordinate"]

    assert traces == [[
        StackFrame("link('asciidoxy::geometry::Coordinate')",
                   file=document.relative_path,
                   package=Package.INPUT_PACKAGE_NAME,
                   internal=False),
        StackFrame("link('Coordinate')",
                   file=None,
                   package=Package.INPUT_PACKAGE_NAME,
                   internal=True)
    ]]


def test_link_stores_stack_trace_nested_insert(preprocessing_api, context, document):
    preprocessing_api.insert("asciidoxy::positioning::Positioning")
    assert "cpp-classasciidoxy_1_1geometry_1_1_coordinate" in context.linked
    traces = context.linked["cpp-classasciidoxy_1_1geometry_1_1_coordinate"]

    assert traces == [
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::CurrentPosition')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ],
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::CurrentPosition')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ],
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::IsNearby')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ],
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::IsNearby')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ],
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::Override')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ],
        [
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=document.relative_path,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=False),
            StackFrame(command="insert('asciidoxy::positioning::Positioning')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="insert('asciidoxy::positioning::Positioning::Override')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True),
            StackFrame(command="link('asciidoxy::geometry::Coordinate')",
                       file=None,
                       package=Package.INPUT_PACKAGE_NAME,
                       internal=True)
        ]
    ]


def test_link_in_include_stores_stack_trace_with_correct_file(preprocessing_api, context, document):
    document.original_file.touch()
    include_doc = document.with_relative_path("include.adoc")
    include_doc.original_file.write_text("""${link("asciidoxy::geometry::Coordinate")}""")
    preprocessing_api.include(include_doc.relative_path.name)

    assert "cpp-classasciidoxy_1_1geometry_1_1_coordinate" in context.linked
    traces = context.linked["cpp-classasciidoxy_1_1geometry_1_1_coordinate"]

    assert traces == [[
        StackFrame("include('include.adoc')",
                   file=document.relative_path,
                   package=Package.INPUT_PACKAGE_NAME,
                   internal=False),
        StackFrame("link('asciidoxy::geometry::Coordinate')",
                   file=include_doc.relative_path,
                   package=Package.INPUT_PACKAGE_NAME,
                   internal=False),
        StackFrame("link('Coordinate')",
                   file=None,
                   package=Package.INPUT_PACKAGE_NAME,
                   internal=True)
    ]]


def test_insert_class__global_filter_members(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent")
    assert "SharedData" not in result
    assert "Update" in result
    assert "CalculateDelay" in result


def test_insert_class__global_filter_members__ignore(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent", ignore_global_filter=True)
    assert "SharedData" in result
    assert "Update" in result
    assert "CalculateDelay" in result


def test_insert_class__global_filter_members__extend(generating_api):
    generating_api.filter(members="-SharedData")
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent", members="-Update")
    assert "SharedData" not in result
    assert "Update" not in result
    assert "CalculateDelay" in result


def test_link_class(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[++Coordinate++]")


def test_link_function(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[++IsValid++]")


def test_link_class_explicit(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", kind="class")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[++Coordinate++]")


def test_link_function_explicit(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate::IsValid", kind="function")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[++IsValid++]")


def test_link_class_with_full_name(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", full_name=True)
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[++asciidoxy::geometry::"
                      "Coordinate++]")


def test_link_class_with_custom_text(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", text="LINK HERE")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[++LINK HERE++]")


def test_link_class_with_alternative_language_tag(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", lang="c++")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[++Coordinate++]")


def test_link_class_with_transcoding(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.link("com.asciidoxy.geometry.Coordinate")
    assert result == ("xref:kotlin-classcom_1_1asciidoxy_1_1geometry_1_1_coordinate"
                      "[++Coordinate++]")


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
    with pytest.raises(InvalidApiCallError):
        generating_api.link("asciidoxy::geometry::Coordinate", text="ALT", full_name=True)


def test_cross_document_ref(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc", anchor="anchor")
        if isinstance(api, GeneratingApi):
            assert result == "<<includes/other_file.adoc#anchor,anchor>>"


def test_cross_document_ref__with_absolute_path(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    target_file = file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref(target_file.original_file, anchor="anchor")


def test_cross_document_ref__requires_filename_packagename_or_anchor(file_builder,
                                                                     tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref(link_text="text")


def test_cross_document_ref__requires_filename_packagename_or_anchor_not_empty(
        file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref("", package_name="", anchor="", link_text="text")


def test_cross_document_ref__file_not_in_workdirectory(file_builder, tdb_single_and_multipage,
                                                       tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(IncludeFileNotFoundError):
                api.cross_document_ref("includes/unknown_file.adoc", anchor="anchor")
        else:
            result = api.cross_document_ref("includes/unknown_file.adoc", anchor="anchor")
            assert result == ""


def test_cross_document_ref__package_missing(file_builder, tdb_single_and_multipage,
                                             tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageError):
                api.cross_document_ref("includes/other_file.adoc",
                                       package_name="unknown",
                                       anchor="anchor")
        else:
            result = api.cross_document_ref("includes/other_file.adoc",
                                            package_name="unknown",
                                            anchor="anchor")
            assert result == ""


def test_cross_document_ref__package_file_missing(file_builder, tdb_single_and_multipage,
                                                  tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package1", "other_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageFileError):
                api.cross_document_ref("another_file.adoc",
                                       package_name="package1",
                                       anchor="anchor")
        else:
            result = api.cross_document_ref("another_file.adoc",
                                            package_name="package1",
                                            anchor="anchor")
            assert result == ""


def test_cross_document_ref__file_in_different_package(file_builder, tdb_single_and_multipage,
                                                       tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package1", "other_file.adoc")
    file_builder.add_package_file("package2", "another_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageFileError):
                api.cross_document_ref("another_file.adoc",
                                       package_name="package1",
                                       anchor="anchor")
        else:
            result = api.cross_document_ref("another_file.adoc",
                                            package_name="package1",
                                            anchor="anchor")
            assert result == ""


def test_cross_document_ref__package_must_be_explicit(file_builder, tdb_single_and_multipage,
                                                      tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package", "another_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(IncludeFileNotFoundError):
                api.cross_document_ref("another_file.adoc", anchor="anchor")
        else:
            result = api.cross_document_ref("another_file.adoc", anchor="anchor")
            assert result == ""


def test_cross_document_ref__with_link_text(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc",
                                        anchor="anchor",
                                        link_text="Link")
        if isinstance(api, GeneratingApi):
            assert result == "<<includes/other_file.adoc#anchor,Link>>"


def test_cross_document_ref__link_text_document_title(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/other_file.adoc")
    include_file.original_file.write_text("= Other file\n\n")

    for api in file_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#,Other file>>"
            else:
                assert result == ("<<includes/other_file.adoc"
                                  "#top-includes-other_file-top,Other file>>")


def test_cross_document_ref__link_text_document_name(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/other_file.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#,other_file>>"
            else:
                assert result == ("<<includes/other_file.adoc"
                                  "#top-includes-other_file-top,other_file>>")


def test_cross_document_ref__to_other_package(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package", "include.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref("include.adoc", package_name="package", link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<include.adoc#,bla>>"
            else:
                assert result == "<<include.adoc#top-include-top,bla>>"


def test_cross_document_ref__to_package_default(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_default_file("package", "include.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref(package_name="package", link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<include.adoc#,bla>>"
            else:
                assert result == "<<include.adoc#top-include-top,bla>>"


def test_cross_document_ref__links_to_package_are_relative_to_package_root(
        file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("some_dir/input.adoc")
    file_builder.add_package_file("package", "other_dir/include.adoc")

    for api in file_builder.apis():
        result = api.cross_document_ref("other_dir/include.adoc",
                                        package_name="package",
                                        link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<../other_dir/include.adoc#,bla>>"
            else:
                assert result == "<<../other_dir/include.adoc#top-other_dir-include-top,bla>>"


def test_cross_document_ref__document_not_in_tree(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("some_dir/input.adoc")
    file_builder.add_package_file("package", "other_dir/include.adoc", register=False)
    file_builder.warnings_are_errors = True

    for api in file_builder.apis():
        if isinstance(api, PreprocessingApi):
            result = api.cross_document_ref("other_dir/include.adoc",
                                            package_name="package",
                                            link_text="bla")
            # TODO: Fix this!
            if isinstance(api, GeneratingApi):
                assert result == "<<../other_dir/include.adoc#,bla>>"
        else:
            with pytest.raises(ConsistencyError):
                api.cross_document_ref("other_dir/include.adoc",
                                       package_name="package",
                                       link_text="bla")


def test_anchor(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")

    for api in file_builder.apis():
        result = api.anchor("my-anchor", link_text="anchor text")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "[#my-anchor,reftext='anchor text']"


def test_anchor__no_link_text(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")

    for api in file_builder.apis():
        result = api.anchor("my-anchor")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "[#my-anchor]"


def test_cross_document_ref__flexible_anchor__same_package(file_builder, tdb_single_and_multipage):
    input_doc = file_builder.add_input_file("input.adoc")
    include_doc = file_builder.add_include_file("include.adoc")

    for api in file_builder.apis():
        api._context.document = include_doc
        api.anchor("my-anchor", link_text="my anchor link text")

        api._context.document = input_doc
        result = api.cross_document_ref(anchor="my-anchor")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "<<include.adoc#my-anchor,my anchor link text>>"


def test_cross_document_ref__flexible_anchor__other_package(file_builder, tdb_single_and_multipage):
    input_doc = file_builder.add_input_file("input.adoc")
    include_doc = file_builder.add_package_file("pacA", "include.adoc")

    for api in file_builder.apis():
        api._context.document = include_doc
        api.anchor("my-anchor", link_text="my anchor link text")

        api._context.document = input_doc
        result = api.cross_document_ref(anchor="my-anchor")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "<<include.adoc#my-anchor,my anchor link text>>"


def test_cross_document_ref__flexible_anchor__link_text(file_builder, tdb_single_and_multipage):
    input_doc = file_builder.add_input_file("input.adoc")
    include_doc = file_builder.add_include_file("include.adoc")

    for api in file_builder.apis():
        api._context.document = include_doc
        api.anchor("my-anchor", link_text="my anchor link text")

        api._context.document = input_doc
        result = api.cross_document_ref(anchor="my-anchor", link_text="other text")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "<<include.adoc#my-anchor,other text>>"


def test_cross_document_ref__flexible_anchor__no_link_text(file_builder, tdb_single_and_multipage):
    input_doc = file_builder.add_input_file("input.adoc")
    include_doc = file_builder.add_include_file("include.adoc")

    for api in file_builder.apis():
        api._context.document = include_doc
        api.anchor("my-anchor")

        api._context.document = input_doc
        result = api.cross_document_ref(anchor="my-anchor")
        if isinstance(api, PreprocessingApi):
            assert result == ""
        else:
            assert result == "<<include.adoc#my-anchor,my-anchor>>"


def test_cross_document_ref__flexible_anchor__missing_anchor(file_builder, tdb_single_and_multipage,
                                                             tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("include.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors and isinstance(api, GeneratingApi):
            with pytest.raises(UnknownAnchorError):
                api.cross_document_ref(anchor="my-anchor")

        else:
            result = api.cross_document_ref(anchor="my-anchor")
            if isinstance(api, PreprocessingApi):
                assert result == ""
            else:
                assert result == "<<input.adoc#my-anchor,my-anchor>>"


def test_include__relative_path(file_builder):
    input_file = file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[#top-includes-another_file-top]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.work_dir / lines[1][9:-16]
        assert file_name.is_file()
        assert file_name.name == "another_file.adoc"
        assert file_name.is_absolute()


def test_include__relative_path__parent_directory(file_builder):
    input_file = file_builder.add_input_file("src/input_file.adoc")
    file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        result = api.include("../includes/another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[#top-includes-another_file-top]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.work_dir / "src" / lines[1][9:-16]
        assert file_name.is_file()
        assert file_name.name == "another_file.adoc"
        assert file_name.is_absolute()


def test_include__relative_path_multipage(file_builder):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/another_file.adoc")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,another_file>>"
        assert include_file.work_file.is_file()


def test_include__absolute_path_not_allowed(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.include(str(include_file.original_file))


def test_include__from_package(file_builder):
    input_file = file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc")

    for api in file_builder.apis():
        result = api.include("another_file.adoc", package_name="package-a")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[#top-another_file-top]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.work_dir / lines[1][9:-16]
        assert file_name.is_file()
        assert file_name.name == "another_file.adoc"
        assert file_name.is_absolute()


def test_include__inside_package(file_builder):
    input_file = file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_package_file("package-a", "another_file.adoc", register=False)
    file_builder.add_package_file("package-a", "yet_another_file.adoc", register=False)

    include_file.work_file.write_text("""\
= Another file

${include("yet_another_file.adoc")}
""")

    for api in file_builder.apis():
        result = api.include("another_file.adoc", package_name="package-a")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[#top-another_file-top]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.work_dir / lines[1][9:-16]
        assert file_name.is_file()
        assert file_name.name == "another_file.adoc"
        assert file_name.is_absolute()


def test_include__from_wrong_package(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc")
    file_builder.add_package_file("package-b", "the_right_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageFileError):
                api.include("the_right_file.adoc", package_name="package-a")
        else:
            assert api.include("the_right_file.adoc", package_name="package-a") == ""


def test_include__package_does_not_exist(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc")

    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageError):
                api.include("the_right_file.adoc", package_name="package-b")
        else:
            assert api.include("the_right_file.adoc", package_name="package-b") == ""


def test_include__with_leveloffset(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", leveloffset="-1")
        assert result.endswith("[leveloffset=-1]")


def test_include__without_leveloffset(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", leveloffset=None)
        assert result.endswith("[]")


def test_include__multipage_with_link_text(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", link_text="Link")
        assert result == "<<includes/another_file.adoc#,Link>>"


def test_include__multipage_with_document_title(file_builder):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/another_file.adoc")
    include_file.original_file.write_text("= Another file's title\n\n")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,Another file's title>>"


def test_include__multipage_with_document_stem(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,another_file>>"


def test_include__multipage_with_prefix_text(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", link_prefix=". ")
        assert result == ". <<includes/another_file.adoc#,another_file>>"


def test_include__multipage_without_link(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")
    file_builder.multipage = True

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", link_prefix=". ", multipage_link=False)
        assert result == ""


def test_include__with_extra_options(file_builder):
    file_builder.add_input_file("input.adoc")
    file_builder.add_include_file("includes/another_file.adoc")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", lines="1..10", indent=12)
        assert result.endswith("[lines=1..10,indent=12,leveloffset=+1]")


def test_include__error_file_not_found(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    for api in file_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(IncludeFileNotFoundError):
                api.include("non_existing_file.adoc")
        else:
            assert api.include("non_existing_file.adoc") == ""


def test_include__always_embed(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/another_file.adoc")
    include_file.original_file.write_text("Embedded")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", always_embed=True)
        assert result == "Embedded"


def test_include__always_embed__correct_sub_context(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc")
    include_file = file_builder.add_include_file("includes/another_file.adoc")
    include_file.original_file.write_text(
        """${cross_document_ref("../input.adoc", anchor="bla")}""")

    for api in file_builder.apis():
        result = api.include("includes/another_file.adoc", always_embed=True)

        if isinstance(api, GeneratingApi):
            assert result == "<<input.adoc#bla,bla>>"


def test_include__store_document_tree(file_builder, tdb_single_and_multipage):
    file_builder.add_input_file("input.adoc", register=False)
    include_file = file_builder.add_include_file("include.adoc", register=False)
    include_file.original_file.write_text("""\
${include("first.adoc")}
${include("second.adoc")}
${include("third.adoc", always_embed=True)}""")
    file_builder.add_include_file("first.adoc", register=False)
    file_builder.add_include_file("second.adoc", register=False)
    file_builder.add_include_file("third.adoc", register=False)

    for api in file_builder.apis():
        api.include("include.adoc")

        input_doc = api._context.find_document(None, Path("input.adoc"))
        assert input_doc is not None
        include_doc = api._context.find_document(None, Path("include.adoc"))
        assert include_doc is not None
        first_doc = api._context.find_document(None, Path("first.adoc"))
        assert first_doc is not None
        second_doc = api._context.find_document(None, Path("second.adoc"))
        assert second_doc is not None
        third_doc = api._context.find_document(None, Path("third.adoc"))
        assert third_doc is not None

        assert input_doc.is_root is True
        assert input_doc.is_used is True
        assert input_doc.is_included is False
        assert input_doc.is_embedded is False
        assert len(input_doc.children) == 1
        assert include_doc in input_doc.children

        assert include_doc.is_root is False
        assert include_doc.is_used is True
        assert include_doc.is_included is True
        assert include_doc.is_embedded is False
        assert include_doc.included_in is input_doc
        assert include_doc.parent() is input_doc
        assert len(include_doc.children) == 3
        assert first_doc in include_doc.children
        assert second_doc in include_doc.children
        assert third_doc in include_doc.children

        assert first_doc.is_root is False
        assert first_doc.is_used is True
        assert first_doc.is_included is True
        assert first_doc.is_embedded is False
        assert first_doc.included_in is include_doc
        assert first_doc.parent() is include_doc
        assert len(first_doc.children) == 0

        assert second_doc.is_root is False
        assert second_doc.is_used is True
        assert second_doc.is_included is True
        assert second_doc.is_embedded is False
        assert second_doc.included_in is include_doc
        assert second_doc.parent() is include_doc
        assert len(second_doc.children) == 0

        assert third_doc.is_root is False
        assert third_doc.is_used is True
        assert third_doc.is_included is False
        assert third_doc.is_embedded is True
        assert third_doc.included_in is None
        assert include_doc in third_doc.embedded_in
        assert third_doc.parent() is include_doc
        assert len(third_doc.children) == 0


def test_include__duplicate_include(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc", register=False)

    for api in file_builder.apis():
        api.include("another_file.adoc", package_name="package-a")
        if tdb_warnings_are_and_are_not_errors and isinstance(api, PreprocessingApi):
            with pytest.raises(DuplicateIncludeError):
                api.include("another_file.adoc", package_name="package-a")
        else:
            api.include("another_file.adoc", package_name="package-a")


def test_include__embed_and_include(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc", register=False)

    for api in file_builder.apis():
        api.include("another_file.adoc", package_name="package-a", always_embed=True)
        if tdb_warnings_are_and_are_not_errors and isinstance(api, PreprocessingApi):
            with pytest.raises(DuplicateIncludeError):
                api.include("another_file.adoc", package_name="package-a")
        else:
            api.include("another_file.adoc", package_name="package-a")


def test_include__include_and_embed(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc", register=False)

    for api in file_builder.apis():
        api.include("another_file.adoc", package_name="package-a")
        if tdb_warnings_are_and_are_not_errors and isinstance(api, PreprocessingApi):
            with pytest.raises(DuplicateIncludeError):
                api.include("another_file.adoc", package_name="package-a", always_embed=True)
        else:
            api.include("another_file.adoc", package_name="package-a", always_embed=True)


def test_include__duplicate_embed(file_builder, tdb_warnings_are_and_are_not_errors):
    file_builder.add_input_file("input.adoc")
    file_builder.add_package_file("package-a", "another_file.adoc", register=False)

    for api in file_builder.apis():
        api.include("another_file.adoc", package_name="package-a", always_embed=True)
        api.include("another_file.adoc", package_name="package-a", always_embed=True)


def test_multipage_toc__default(generating_api, document, multipage):
    result = generating_api.multipage_toc()
    assert result == """\
:docinfo: private
:stylesheet: asciidoxy-toc-left.css"""

    assert document.docinfo_footer_file.is_file()
    assert document.stylesheet == "asciidoxy-toc-left.css"


def test_multipage_toc__left(generating_api, document, multipage):
    result = generating_api.multipage_toc(side="left")
    assert result == """\
:docinfo: private
:stylesheet: asciidoxy-toc-left.css"""

    assert document.docinfo_footer_file.is_file()
    assert document.stylesheet == "asciidoxy-toc-left.css"


def test_multipage_toc__right(generating_api, document, multipage):
    result = generating_api.multipage_toc(side="right")
    assert result == """\
:docinfo: private
:stylesheet: asciidoxy-toc-right.css"""

    assert document.docinfo_footer_file.is_file()
    assert document.stylesheet == "asciidoxy-toc-right.css"


def test_multipage_toc__in_subdir(context, generating_api, document, multipage):
    context.document = document.with_relative_path("dir/subdir/document.adoc")
    context.document.work_file.parent.mkdir(parents=True)
    result = generating_api.multipage_toc()
    assert result == """\
:docinfo: private
:stylesheet: ../../asciidoxy-toc-left.css"""

    assert context.document.docinfo_footer_file.is_file()
    assert context.document.stylesheet == "asciidoxy-toc-left.css"


def test_multipage_toc__multipage_off(generating_api, document):
    result = generating_api.multipage_toc()
    assert not result

    assert not document.docinfo_footer_file.exists()


def test_multipage_toc__preprocessing_run(preprocessing_api, document, multipage):
    result = preprocessing_api.multipage_toc()
    assert not result

    assert not document.docinfo_footer_file.exists()


def test_require_version__exact_match(preprocessing_api):
    preprocessing_api.require_version(f"=={__version__}")


def test_require_version__exact_match__fail(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    version_parts = base_version.split(".")
    version_parts[2] = str(int(version_parts[2]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"=={version}")


def test_require_version__current_is_minimum(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    preprocessing_api.require_version(f">={base_version}")


def test_require_version__current_is_below_minimum(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    version_parts = base_version.split(".")
    version_parts[1] = str(int(version_parts[1]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f">={version}")


def test_require_version__current_is_minimum_optimistic(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    preprocessing_api.require_version(f"~={base_version}")


def test_require_version__current_is_below_minimum_optimistic(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    version_parts = base_version.split(".")
    version_parts[1] = str(int(version_parts[1]) + 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"~={version}")


def test_require_version__allow_minor_increase(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    version_parts = base_version.split(".")
    version_parts[1] = str(int(version_parts[1]) - 1)
    version = ".".join(version_parts)
    preprocessing_api.require_version(f">={version}")


def test_require_version__optimistic_no_minor_increase(preprocessing_api):
    base_version, _, _ = __version__.partition("+")
    version_parts = base_version.split(".")
    version_parts[1] = str(int(version_parts[1]) - 1)
    version = ".".join(version_parts)
    with pytest.raises(IncompatibleVersionError):
        preprocessing_api.require_version(f"~={version}")


def test_context_link_to_element_singlepage(context, generating_api):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = InsertData(
        context.document.with_relative_path(file_containing_element), [])
    assert generating_api.link_to_element(element_id,
                                          link_text) == f"xref:{element_id}[++{link_text}++]"


def test_context_link_to_element_multipage(context, multipage, generating_api):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = InsertData(
        context.document.with_relative_path(file_containing_element), [])
    assert (generating_api.link_to_element(
        element_id, link_text) == f"xref:{file_containing_element}#{element_id}[++{link_text}++]")


def test_context_link_to_element_multipage_element_in_the_same_document(
        context, multipage, generating_api):
    element_id = "element"
    link_text = "Link"
    context.inserted[element_id] = InsertData(context.document, [])
    assert (generating_api.link_to_element(element_id,
                                           link_text) == f"xref:{element_id}[++{link_text}++]")


def test_context_link_to_element_element_not_inserted(context, single_and_multipage,
                                                      generating_api):
    element_id = "element"
    link_text = "Link"
    assert element_id not in context.inserted
    assert generating_api.link_to_element(element_id,
                                          link_text) == f"xref:{element_id}[++{link_text}++]"
