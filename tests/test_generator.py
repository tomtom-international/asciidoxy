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
from typing import Optional

from asciidoxy.api_reference import ApiReference
from asciidoxy.generator.asciidoc import ApiProxy, GeneratingApi, PreprocessingApi, process_adoc
from asciidoxy.generator.context import Context
from asciidoxy.generator.navigation import DocumentTreeNode
from asciidoxy.generator.errors import (AmbiguousReferenceError, ConsistencyError,
                                        IncludeFileNotFoundError, IncompatibleVersionError,
                                        InvalidApiCallError, MissingPackageError,
                                        MissingPackageFileError, ReferenceNotFoundError,
                                        TemplateMissingError)
from asciidoxy.packaging import Package, PackageManager

from asciidoxy import __version__
from .shared import ProgressMock


class _TestDataBuilder:
    def __init__(self, base_dir: Path, build_dir: Path, fragment_dir: Path):
        self.package_manager = PackageManager(build_dir)
        self.fragment_dir = fragment_dir

        self.packages_dir = base_dir / "packages"
        self.packages_dir.mkdir(parents=True, exist_ok=True)

        self.input_dir = self.packages_dir / "INPUT"
        self.input_dir.mkdir(parents=True, exist_ok=True)

        self.work_dir = self.package_manager.work_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

        self.input_file = None
        self.parent_file = None

        self.adoc_files_to_register = []
        self.multipage = False
        self.warnings_are_errors = False

    def add_input_file(self, name: str, register: bool = True):
        self.input_file = self.add_include_file(name, register)
        self.package_manager.set_input_files(self.input_file, self.input_dir)
        return self.input_file

    def add_input_parent_file(self, name: str, register: bool = True):
        self.parent_file = self.add_include_file(name, register)
        return self.parent_file

    def add_include_file(self, name: str, register: bool = True):
        return self.add_file("INPUT", name, register)

    def add_package_file(self, package: str, name: str, register: bool = True):
        self.add_package(package)
        return self.add_file(package, name, register)

    def add_package_default_file(self, package: str, name: str, register: bool = True):
        self.add_package(package, name)
        return self.add_file(package, name, register)

    def add_file(self, package: str, name: str, register: bool = True):
        input_file = self.packages_dir / package / name
        input_file.parent.mkdir(parents=True, exist_ok=True)
        input_file.touch()

        work_file = self.work_dir / name
        work_file.parent.mkdir(parents=True, exist_ok=True)
        work_file.touch()

        if register:
            self.adoc_files_to_register.append(work_file)

        return work_file

    def add_package(self, package: str, default_file: Optional[str] = None):
        if package not in self.package_manager.packages:
            pkg = Package(package)
            pkg.adoc_src_dir = self.packages_dir / package
            if default_file:
                pkg.adoc_root_doc = pkg.adoc_src_dir / default_file
            pkg.scoped = True
            self.package_manager.packages[package] = pkg

    def context(self):
        if self.parent_file:
            parent_node = DocumentTreeNode(self.parent_file)
        else:
            parent_node = None

        c = Context(base_dir=self.work_dir,
                    fragment_dir=self.fragment_dir,
                    reference=ApiReference(),
                    package_manager=self.package_manager,
                    current_document=DocumentTreeNode(self.input_file, parent_node),
                    current_package=self.package_manager.input_package())

        for file in self.adoc_files_to_register:
            c.register_adoc_file(file)
        c.current_document.children = [
            DocumentTreeNode(f, c.current_document) for f in self.adoc_files_to_register
        ]

        c.multipage = self.multipage
        c.warnings_are_errors = self.warnings_are_errors

        return c

    def apis(self):
        context = self.context()
        yield PreprocessingApi(self.input_file, context)
        yield GeneratingApi(self.input_file, context)


@pytest.fixture
def test_data_builder(tmp_path, build_dir, fragment_dir):
    return _TestDataBuilder(tmp_path, build_dir, fragment_dir)


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def tdb_single_and_multipage(request, test_data_builder):
    test_data_builder.multipage = request.param
    return request.param


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def tdb_warnings_are_and_are_not_errors(request, test_data_builder):
    test_data_builder.warnings_are_errors = request.param
    return request.param


@pytest.fixture
def adoc_data_work_file(adoc_data, package_manager):
    def prepare(adoc_file):
        package_manager.set_input_files(adoc_data / adoc_file, adoc_data)
        return package_manager.prepare_work_directory(adoc_data / adoc_file)

    return prepare


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
    result = generating_api.insert("asciidoxy::geometry::Coordinate", kind="class")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_language(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert_class_explicit_all(generating_api):
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp", kind="class")
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
    result = generating_api.insert("asciidoxy::traffic::TrafficEvent::Severity", kind="enum")
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
        generating_api.insert("Logger")


def test_insert_with_default_language_can_be_overridden(generating_api):
    generating_api.language("java")
    result = generating_api.insert("asciidoxy::geometry::Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_insert__transcode__explicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate", lang="kotlin")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class com.asciidoxy.geometry.Coordinate")
    _check_inserted_file_contains(result, "kotlin")


def test_insert__transcode__implicit(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class com.asciidoxy.geometry.Coordinate")
    _check_inserted_file_contains(result, "kotlin")


def test_insert__transcode__reset(generating_api):
    generating_api.language("kotlin", source="java")
    generating_api.language(None)
    result = generating_api.insert("com.asciidoxy.geometry.Coordinate")
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
        generating_api.insert("asciidoxy::traffic::TrafficEvent::TrafficEvent")
    assert len(exception.value.candidates) == 2
    exception_message = str(exception.value)
    assert ("Multiple matches for asciidoxy::traffic::TrafficEvent::TrafficEvent"
            in exception_message)
    assert "cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent()" in exception_message
    assert ("cpp function asciidoxy::traffic::TrafficEvent::TrafficEvent(TrafficEventData)"
            in exception_message)


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
def test_insert_tracks_all_references(preprocessing_api, context):
    preprocessing_api.insert("asciidoxy::positioning::Positioning")
    assert len(context.linked) == 2
    assert "cpp-classasciidoxy_1_1geometry_1_1_coordinate" in context.linked
    assert "cpp-classasciidoxy_1_1traffic_1_1_traffic_event" in context.linked


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
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++Coordinate+++]")


def test_link_function(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate::IsValid")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[+++IsValid+++]")


def test_link_class_explicit(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", kind="class")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++Coordinate+++]")


def test_link_function_explicit(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate::IsValid", kind="function")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate_"
                      "1a8d7e0eac29549fa4666093e36914deac[+++IsValid+++]")


def test_link_class_with_full_name(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", full_name=True)
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++asciidoxy::geometry::"
                      "Coordinate+++]")


def test_link_class_with_custom_text(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", text="LINK HERE")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++LINK HERE+++]")


def test_link_class_with_alternative_language_tag(generating_api):
    result = generating_api.link("asciidoxy::geometry::Coordinate", lang="c++")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++Coordinate+++]")


def test_link_class_with_transcoding(generating_api):
    generating_api.language("kotlin", source="java")
    result = generating_api.link("com.asciidoxy.geometry.Coordinate")
    assert result == ("xref:kotlin-classcom_1_1asciidoxy_1_1geometry_1_1_coordinate"
                      "[+++Coordinate+++]")


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


def test_cross_document_ref(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc", anchor="anchor")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#anchor,anchor>>"
            else:
                assert result == "<<includes/.asciidoxy.other_file.adoc#anchor,anchor>>"


def test_cross_document_ref__with_absolute_path(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    target_file = test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref(target_file, anchor="anchor")


def test_cross_document_ref__requires_filename_or_packagename(test_data_builder,
                                                              tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref(anchor="anchor")


def test_cross_document_ref__requires_filename_or_packagename_not_empty(
        test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.cross_document_ref("", package_name="", anchor="anchor")


def test_cross_document_ref__file_not_in_workdirectory(test_data_builder, tdb_single_and_multipage,
                                                       tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(IncludeFileNotFoundError):
                api.cross_document_ref("includes/unknown_file.adoc", anchor="anchor")
        else:
            result = api.cross_document_ref("includes/unknown_file.adoc", anchor="anchor")
            assert result == ""


def test_cross_document_ref__package_missing(test_data_builder, tdb_single_and_multipage,
                                             tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")

    for api in test_data_builder.apis():
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


def test_cross_document_ref__package_file_missing(test_data_builder, tdb_single_and_multipage,
                                                  tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package1", "other_file.adoc")

    for api in test_data_builder.apis():
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


def test_cross_document_ref__file_in_different_package(test_data_builder, tdb_single_and_multipage,
                                                       tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package1", "other_file.adoc")
    test_data_builder.add_package_file("package2", "another_file.adoc")

    for api in test_data_builder.apis():
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


def test_cross_document_ref__package_must_be_explicit(test_data_builder, tdb_single_and_multipage,
                                                      tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package", "another_file.adoc")

    for api in test_data_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageFileError):
                api.cross_document_ref("another_file.adoc", anchor="anchor")
        else:
            result = api.cross_document_ref("another_file.adoc", anchor="anchor")
            assert result == ""


def test_cross_document_ref__direct_access_to_other_package_for_old_style_packages(
        test_data_builder, tdb_single_and_multipage, tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package", "include.adoc")
    test_data_builder.package_manager.input_package().scoped = False

    for api in test_data_builder.apis():
        result = api.cross_document_ref("include.adoc", link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<include.adoc#,bla>>"
            else:
                assert result == "<<.asciidoxy.include.adoc#top-include-top,bla>>"


def test_cross_document_ref__with_link_text(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc",
                                        anchor="anchor",
                                        link_text="Link")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#anchor,Link>>"
            else:
                assert result == "<<includes/.asciidoxy.other_file.adoc#anchor,Link>>"


def test_cross_document_ref__link_text_document_title(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_include_file("includes/other_file.adoc")
    include_file.write_text("= Other file\n\n")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#,Other file>>"
            else:
                assert result == ("<<includes/.asciidoxy.other_file.adoc"
                                  "#top-includes-other_file-top,Other file>>")


def test_cross_document_ref__link_text_document_name(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("includes/other_file.adoc")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#,other_file>>"
            else:
                assert result == ("<<includes/.asciidoxy.other_file.adoc"
                                  "#top-includes-other_file-top,other_file>>")


def test_cross_document_ref__to_other_package(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package", "include.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("include.adoc", package_name="package", link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<include.adoc#,bla>>"
            else:
                assert result == "<<.asciidoxy.include.adoc#top-include-top,bla>>"


def test_cross_document_ref__to_package_default(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_default_file("package", "include.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref(package_name="package", link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<include.adoc#,bla>>"
            else:
                assert result == "<<.asciidoxy.include.adoc#top-include-top,bla>>"


def test_cross_document_ref__links_to_package_are_relative_to_package_root(
        test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("some_dir/input.adoc")
    test_data_builder.add_package_file("package", "other_dir/include.adoc")

    for api in test_data_builder.apis():
        result = api.cross_document_ref("other_dir/include.adoc",
                                        package_name="package",
                                        link_text="bla")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<../other_dir/include.adoc#,bla>>"
            else:
                assert result == ("<<../other_dir/.asciidoxy.include.adoc#"
                                  "top-other_dir-include-top,bla>>")


def test_cross_document_ref__document_not_in_tree(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("some_dir/input.adoc")
    test_data_builder.add_package_file("package", "other_dir/include.adoc", register=False)
    test_data_builder.warnings_are_errors = True

    for api in test_data_builder.apis():
        if isinstance(api, PreprocessingApi):
            result = api.cross_document_ref("other_dir/include.adoc",
                                            package_name="package",
                                            link_text="bla")
            if isinstance(api, GeneratingApi):
                assert result == "<<../other_dir/include.adoc#,bla>>"
        else:
            with pytest.raises(ConsistencyError):
                api.cross_document_ref("other_dir/include.adoc",
                                       package_name="package",
                                       link_text="bla")


def test_include__relative_path(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-includes-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include__relative_path__parent_directory(test_data_builder):
    input_file = test_data_builder.add_input_file("src/input_file.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("../includes/another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-includes-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include__relative_path_multipage(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_include_file("includes/another_file.adoc")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,another_file>>"
        assert include_file.with_name(".asciidoxy.another_file.adoc").is_file() == isinstance(
            api, GeneratingApi)


def test_include__absolute_path_not_allowed(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        with pytest.raises(InvalidApiCallError):
            api.include(str(include_file))


def test_include__from_package(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package-a", "another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("another_file.adoc", package_name="package-a")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include__inside_package(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_package_file("package-a",
                                                      "another_file.adoc",
                                                      register=False)
    test_data_builder.add_package_file("package-a", "yet_another_file.adoc", register=False)

    include_file.write_text("""\
= Another file

${include("yet_another_file.adoc")}
""")

    for api in test_data_builder.apis():
        result = api.include("another_file.adoc", package_name="package-a")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include__from_wrong_package(test_data_builder, tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package-a", "another_file.adoc")
    test_data_builder.add_package_file("package-b", "the_right_file.adoc")

    for api in test_data_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageFileError):
                api.include("the_right_file.adoc", package_name="package-a")
        else:
            assert api.include("the_right_file.adoc", package_name="package-a") == ""


def test_include__package_does_not_exist(test_data_builder, tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package-a", "another_file.adoc")

    for api in test_data_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(MissingPackageError):
                api.include("the_right_file.adoc", package_name="package-b")
        else:
            assert api.include("the_right_file.adoc", package_name="package-b") == ""


def test_include__direct_access_to_other_package_for_old_style_packages(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_package_file("package-a", "another_file.adoc")
    test_data_builder.package_manager.input_package().scoped = False

    for api in test_data_builder.apis():
        result = api.include("another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_include__with_leveloffset(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", leveloffset="-1")
        assert result.endswith("[leveloffset=-1]")


def test_include__without_leveloffset(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", leveloffset=None)
        assert result.endswith("[]")


def test_include__multipage_with_link_text(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", link_text="Link")
        assert result == "<<includes/another_file.adoc#,Link>>"


def test_include__multipage_with_document_title(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_include_file("includes/another_file.adoc")
    include_file.write_text("= Another file's title\n\n")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,Another file's title>>"


def test_include__multipage_with_document_stem(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc")
        assert result == "<<includes/another_file.adoc#,another_file>>"


def test_include__multipage_with_prefix_text(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", link_prefix=". ")
        assert result == ". <<includes/another_file.adoc#,another_file>>"


def test_include__multipage_without_link(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")
    test_data_builder.multipage = True

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", link_prefix=". ", multipage_link=False)
        assert result == ""


def test_include__with_extra_options(test_data_builder):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", lines="1..10", indent=12)
        assert result.endswith("[lines=1..10,indent=12,leveloffset=+1]")


def test_include__error_file_not_found(test_data_builder, tdb_warnings_are_and_are_not_errors):
    test_data_builder.add_input_file("input.adoc")
    for api in test_data_builder.apis():
        if tdb_warnings_are_and_are_not_errors:
            with pytest.raises(IncludeFileNotFoundError):
                api.include("non_existing_file.adoc")
        else:
            assert api.include("non_existing_file.adoc") == ""


def test_include__always_embed(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", always_embed=True)
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = Path(result[9:-16])
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.is_absolute()


def test_include__always_embed__unique_name_for_each_including_file(test_data_builder,
                                                                    tdb_single_and_multipage):
    test_data_builder.add_include_file("includes/another_file.adoc")

    file_names = []

    for i in range(10):
        test_data_builder.add_input_file(f"base{i}.adoc")
        for api in test_data_builder.apis():
            result = api.include("includes/another_file.adoc", always_embed=True)
            assert result.startswith("include::")
            assert result.endswith("[leveloffset=+1]")

            file_name = Path(result[9:-16])
            assert file_name.is_file() == isinstance(api, GeneratingApi)
            assert file_name.is_absolute()

            if isinstance(api, PreprocessingApi):
                assert file_name not in file_names
                file_names.append(file_name)


def test_include__always_embed__correct_sub_context(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    include_file = test_data_builder.add_include_file("includes/another_file.adoc")
    include_file.write_text("""
${cross_document_ref("../input.adoc", anchor="bla")}}
""")

    for api in test_data_builder.apis():
        result = api.include("includes/another_file.adoc", always_embed=True)
        assert result.startswith("include::")
        assert result.endswith("[leveloffset=+1]")

        file_name = Path(result[9:-16])
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.is_absolute()

    contents = file_name.read_text()
    if tdb_single_and_multipage:
        # multipage
        assert "<<input.adoc#bla,bla>>" in contents, contents
    else:
        # singlepage
        assert "<<.asciidoxy.input.adoc#bla,bla>>" in contents, contents


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
def test_process_adoc_single_file(warnings_are_errors, fragment_dir, test_file_name,
                                  single_and_multipage, adoc_data, api_reference, package_manager):
    input_file = adoc_data / f"{test_file_name}.input.adoc"
    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"

    progress_mock = ProgressMock()
    output_file = process_adoc(input_file,
                               api_reference,
                               package_manager,
                               warnings_are_errors=warnings_are_errors,
                               progress=progress_mock)[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(fragment_dir), "FRAGMENT_DIR")
    assert content == expected_output_file.read_text()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2


def test_process_adoc_multi_file(fragment_dir, single_and_multipage, api_reference, package_manager,
                                 adoc_data_work_file):
    main_doc_file = adoc_data_work_file("multifile_test.input.adoc")
    sub_doc_file = main_doc_file.parent / "sub_directory" / "multifile_subdoc_test.input.adoc"
    sub_doc_in_table_file = main_doc_file.parent / "sub_directory" \
        / "multifile_subdoc_in_table_test.input.adoc"

    progress_mock = ProgressMock()
    output_files = process_adoc(main_doc_file,
                                api_reference,
                                package_manager,
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
        content = content.replace(os.fspath(fragment_dir), "FRAGMENT_DIR")
        content = content.replace(os.fspath(main_doc_file.parent), "SRC_DIR")
        assert content == expected_output_file.read_text()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2 * len(output_files)


def test_process_adoc_env_variables(fragment_dir, single_and_multipage, api_reference,
                                    package_manager, adoc_data_work_file):
    main_doc_file = adoc_data_work_file("env_variables.adoc")
    sub_doc_file = main_doc_file.parent / "env_variables_include.adoc"

    progress_mock = ProgressMock()
    output_files = process_adoc(main_doc_file,
                                api_reference,
                                package_manager,
                                warnings_are_errors=True,
                                multipage=single_and_multipage,
                                progress=progress_mock)
    assert len(output_files) == 2
    assert (
        output_files[main_doc_file] == main_doc_file.with_name(f".asciidoxy.{main_doc_file.name}"))
    assert (output_files[sub_doc_file] == sub_doc_file.with_name(f".asciidoxy.{sub_doc_file.name}"))
    for input_file, output_file in output_files.items():
        assert output_file.is_file()
        expected_output_file = input_file.with_suffix(
            ".expected.multipage.adoc" if single_and_multipage else ".expected.singlepage.adoc")
        content = output_file.read_text()
        content = content.replace(os.fspath(fragment_dir), "FRAGMENT_DIR")
        content = content.replace(os.fspath(main_doc_file.parent), "SRC_DIR")
        assert content == expected_output_file.read_text()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2 * len(output_files)


def test_process_adoc__embedded_file_not_in_output_map(single_and_multipage, api_reference,
                                                       package_manager, adoc_data_work_file):
    main_doc_file = adoc_data_work_file("embeddedfile_test.input.adoc")

    progress_mock = ProgressMock()
    output_files = process_adoc(main_doc_file,
                                api_reference,
                                package_manager,
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
def test_process_adoc_file_warning(fragment_dir, test_file_name, single_and_multipage, adoc_data,
                                   api_reference, package_manager):
    input_file = adoc_data / f"{test_file_name}.input.adoc"

    expected_output_file = adoc_data / f"{test_file_name}.expected.adoc"
    if single_and_multipage:
        expected_output_file_multipage = expected_output_file.with_suffix('.multipage.adoc')
        if expected_output_file_multipage.is_file():
            expected_output_file = expected_output_file_multipage

    output_file = process_adoc(input_file,
                               api_reference,
                               package_manager,
                               multipage=single_and_multipage)[input_file]
    assert output_file.is_file()

    content = output_file.read_text()
    content = content.replace(os.fspath(fragment_dir), "FRAGMENT_DIR")
    assert content == expected_output_file.read_text()


@pytest.mark.parametrize("api_reference_set", [("cpp/default", "cpp/consumer")])
@pytest.mark.parametrize("test_file_name, error",
                         [("dangling_link", ConsistencyError),
                          ("dangling_cross_doc_ref", IncludeFileNotFoundError),
                          ("double_insert", ConsistencyError),
                          ("dangling_link_in_insert", ConsistencyError)])
def test_process_adoc_file_warning_as_error(test_file_name, error, single_and_multipage, adoc_data,
                                            api_reference, package_manager):
    input_file = adoc_data / f"{test_file_name}.input.adoc"

    with pytest.raises(error):
        process_adoc(input_file, api_reference, package_manager, warnings_are_errors=True)


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


def test_context_link_to_element_singlepage(context, generating_api):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file.parent / file_containing_element
    assert generating_api.link_to_element(element_id,
                                          link_text) == f"xref:{element_id}[+++{link_text}+++]"


def test_context_link_to_element_multipage(context, multipage, generating_api):
    element_id = "element"
    file_containing_element = "other_file.adoc"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file.parent / file_containing_element
    assert (generating_api.link_to_element(
        element_id, link_text) == f"xref:{file_containing_element}#{element_id}[+++{link_text}+++]")


def test_context_link_to_element_multipage_element_in_the_same_document(
        context, multipage, generating_api):
    element_id = "element"
    link_text = "Link"
    context.inserted[element_id] = context.current_document.in_file
    assert (generating_api.link_to_element(element_id,
                                           link_text) == f"xref:{element_id}[+++{link_text}+++]")


def test_context_link_to_element_element_not_inserted(context, single_and_multipage,
                                                      generating_api):
    element_id = "element"
    link_text = "Link"
    assert element_id not in context.inserted
    assert generating_api.link_to_element(element_id,
                                          link_text) == f"xref:{element_id}[+++{link_text}+++]"


def test_api_proxy__filter(generating_api):
    api = ApiProxy(generating_api)
    api.filter(members="-SharedData")
    result = api.insert("asciidoxy::traffic::TrafficEvent")
    _check_inserted_file_does_not_contain(result, "SharedData")
    _check_inserted_file_contains(result, "Update")
    _check_inserted_file_contains(result, "CalculateDelay")


def test_api_proxy__insert(generating_api):
    api = ApiProxy(generating_api)
    result = api.insert("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_api_proxy__insert_class(generating_api):
    api = ApiProxy(generating_api)
    result = api.insert_class("asciidoxy::geometry::Coordinate")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_api_proxy__link(generating_api):
    api = ApiProxy(generating_api)
    result = api.link("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++Coordinate+++]")


def test_api_proxy__link_class(generating_api):
    api = ApiProxy(generating_api)
    result = api.link_class("asciidoxy::geometry::Coordinate")
    assert result == ("xref:cpp-classasciidoxy_1_1geometry_1_1_coordinate[+++Coordinate+++]")


def test_api_proxy__cross_document_ref(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        proxy = ApiProxy(api)
        result = proxy.cross_document_ref("includes/other_file.adoc", anchor="anchor")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#anchor,anchor>>"
            else:
                assert result == "<<includes/.asciidoxy.other_file.adoc#anchor,anchor>>"


def test_api_proxy__cross_document_ref__old_syntax(test_data_builder, tdb_single_and_multipage):
    test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/other_file.adoc")

    for api in test_data_builder.apis():
        proxy = ApiProxy(api)
        result = proxy.cross_document_ref("includes/other_file.adoc", "anchor")
        if isinstance(api, GeneratingApi):
            if tdb_single_and_multipage:
                assert result == "<<includes/other_file.adoc#anchor,anchor>>"
            else:
                assert result == "<<includes/.asciidoxy.other_file.adoc#anchor,anchor>>"


def test_api_proxy__include(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        proxy = ApiProxy(api)
        result = proxy.include("includes/another_file.adoc")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-includes-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+1]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_api_proxy__include__old_syntax(test_data_builder):
    input_file = test_data_builder.add_input_file("input.adoc")
    test_data_builder.add_include_file("includes/another_file.adoc")

    for api in test_data_builder.apis():
        proxy = ApiProxy(api)
        result = proxy.include("includes/another_file.adoc", "+2")
        lines = result.splitlines()
        assert len(lines) == 2

        assert lines[0] == "[[top-includes-another_file-top]]"

        assert lines[1].startswith("include::")
        assert lines[1].endswith("[leveloffset=+2]")

        file_name = input_file.parent / lines[1][9:-16]
        assert file_name.is_file() == isinstance(api, GeneratingApi)
        assert file_name.name == ".asciidoxy.another_file.adoc"
        assert file_name.is_absolute()


def test_api_proxy__language(generating_api):
    with pytest.raises(AmbiguousReferenceError) as exception:
        generating_api.insert("Logger")
    assert len(exception.value.candidates) == 2

    api = ApiProxy(generating_api)
    api.language("java")
    result = generating_api.insert("Logger")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class Logger")


def test_api_proxy__namespace(generating_api):
    api = ApiProxy(generating_api)
    api.namespace("asciidoxy::geometry::")
    result = api.insert("Coordinate", lang="cpp")
    assert result.startswith("include::")
    assert result.endswith("[leveloffset=+1]")
    _check_inserted_file_contains(result, "class asciidoxy::geometry::Coordinate")


def test_api_proxy__require_version(preprocessing_api):
    ApiProxy(preprocessing_api).require_version(f"=={__version__}")


def test_api_proxy__multipage_toc(generating_api, input_file, multipage):
    result = generating_api.multipage_toc()
    assert result == ":docinfo: private"

    toc_file = input_file.parent / f".asciidoxy.{input_file.stem}-docinfo-footer.html"
    assert toc_file.is_file()
