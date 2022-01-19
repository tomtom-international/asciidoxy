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
"""Tests generating and comparing a full generated document."""

from pathlib import Path

import pytest

from asciidoxy.document import Document
from asciidoxy.generator.asciidoc import process_adoc
from asciidoxy.generator.errors import ConsistencyError, IncludeFileNotFoundError

from ..shared import ProgressMock


@pytest.fixture
def api_reference(api_reference_loader, all_doxygen_versions):
    return api_reference_loader.version(all_doxygen_versions).load_all()


@pytest.fixture
def cpp_api_reference(api_reference_loader, all_doxygen_versions):
    return api_reference_loader.version(all_doxygen_versions).add("doxygen", "cpp/default").add(
        "doxygen", "cpp/consumer").load()


@pytest.fixture
def adoc_data_document(adoc_data, package_manager):
    def prepare(adoc_file):
        package_manager.set_input_files(adoc_data / adoc_file, adoc_data)
        return package_manager.prepare_work_directory(adoc_data / adoc_file)

    return prepare


@pytest.fixture
def check_adoc_expected_result(compare_to_file):
    def check(doc: Document, *, multipage: bool) -> None:
        assert doc.work_file.is_file()
        base_file = Path("generator") / doc.relative_path.with_suffix("")
        mode = "multipage" if multipage else "singlepage"
        actual_content = doc.work_file.read_text(encoding="utf-8")
        compare_to_file(base_file, actual_content, mode)

    return check


@pytest.mark.parametrize("warnings_are_errors", [True, False],
                         ids=["warnings-are-errors", "warnings-are-not-errors"])
@pytest.mark.parametrize("test_file_name", ["simple_test", "link_to_member"])
def test_process_adoc_single_file(warnings_are_errors, test_file_name, single_and_multipage,
                                  adoc_data, api_reference, package_manager, default_config,
                                  check_adoc_expected_result):
    input_file = adoc_data / f"{test_file_name}.adoc"
    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = warnings_are_errors
    output_doc = process_adoc(doc,
                              api_reference,
                              package_manager,
                              config=default_config,
                              progress=progress_mock)[0]
    check_adoc_expected_result(output_doc, multipage=single_and_multipage)
    assert output_doc.stylesheet == "asciidoxy-no-toc.css"
    assert output_doc.stylesheet_file.is_file()

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2


def test_process_adoc_multi_file(single_and_multipage, api_reference, package_manager,
                                 adoc_data_document, adoc_data, default_config,
                                 check_adoc_expected_result):
    main_doc = adoc_data_document("multifile_test.adoc")

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = True
    default_config.multipage = single_and_multipage
    output_docs = process_adoc(main_doc,
                               api_reference,
                               package_manager,
                               config=default_config,
                               progress=progress_mock)
    assert len(output_docs) == 3
    for doc in output_docs:
        check_adoc_expected_result(doc, multipage=single_and_multipage)
        assert doc.stylesheet == "asciidoxy-no-toc.css"
        assert doc.stylesheet_file.is_file()

    assert sorted([doc.relative_path for doc in output_docs]) == sorted([
        Path("multifile_test.adoc"),
        Path("sub_directory/multifile_subdoc_test.adoc"),
        Path("sub_directory/multifile_subdoc_in_table_test.adoc")
    ])

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 6


def test_process_adoc_env_variables(single_and_multipage, api_reference, package_manager,
                                    adoc_data_document, adoc_data, default_config,
                                    check_adoc_expected_result):
    main_doc = adoc_data_document("env_variables.adoc")

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = True
    default_config.multipage = single_and_multipage
    output_docs = process_adoc(main_doc,
                               api_reference,
                               package_manager,
                               config=default_config,
                               progress=progress_mock)
    assert len(output_docs) == 2
    for doc in output_docs:
        check_adoc_expected_result(doc, multipage=single_and_multipage)

    assert sorted([doc.relative_path for doc in output_docs]) == sorted([
        Path("env_variables.adoc"),
        Path("env_variables_include.adoc"),
    ])

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 4


def test_process_adoc__embedded_doc_included(single_and_multipage, api_reference, package_manager,
                                             adoc_data_document, default_config):
    main_doc = adoc_data_document("embeddedfile_test.adoc")

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = True
    default_config.multipage = single_and_multipage
    output_docs = process_adoc(main_doc,
                               api_reference,
                               package_manager,
                               config=default_config,
                               progress=progress_mock)
    assert len(output_docs) == 2
    assert sorted([doc.relative_path for doc in output_docs]) == sorted([
        Path("embeddedfile_test.adoc"),
        Path("sub_directory/embeddedfile_subdoc_test.adoc"),
    ])

    assert progress_mock.ready == progress_mock.total
    assert progress_mock.total == 2


def test_process_adoc_custom_templates(warnings_are_errors, single_and_multipage, adoc_data,
                                       api_reference, package_manager, tmp_path, default_config,
                                       check_adoc_expected_result):
    template_dir = tmp_path / "templates"
    (template_dir / "cpp").mkdir(parents=True)
    (template_dir / "cpp" / "class.mako").write_text("Custom class template")
    (template_dir / "cpp" / "myclass.mako").write_text("My class template")

    input_file = adoc_data / "custom_templates.adoc"
    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = warnings_are_errors
    default_config.template_dir = template_dir
    output_doc = process_adoc(doc,
                              api_reference,
                              package_manager,
                              config=default_config,
                              progress=progress_mock)[0]
    check_adoc_expected_result(output_doc, multipage=single_and_multipage)


def test_process_adoc_access_config(warnings_are_errors, single_and_multipage, adoc_data,
                                    api_reference, package_manager, tmp_path, default_config):
    input_file = adoc_data / "access_config.adoc"
    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = warnings_are_errors
    output_doc = process_adoc(doc,
                              api_reference,
                              package_manager,
                              config=default_config,
                              progress=progress_mock)[0]
    assert output_doc.work_file.is_file()

    content = output_doc.work_file.read_text()
    assert f"Build dir: {default_config.build_dir}" in content


def test_process_adoc_include_python(warnings_are_errors, single_and_multipage, adoc_data,
                                     api_reference, package_manager, tmp_path, default_config):
    input_file = adoc_data / "include_python.adoc"

    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)

    progress_mock = ProgressMock()
    default_config.warnings_are_errors = warnings_are_errors
    output_doc = process_adoc(doc,
                              api_reference,
                              package_manager,
                              config=default_config,
                              progress=progress_mock)[0]
    assert output_doc.work_file.is_file()

    content = output_doc.work_file.read_text()
    assert "This is included python code" in content


@pytest.mark.parametrize(
    "test_file_name",
    ["dangling_link", "dangling_cross_doc_ref", "double_insert", "dangling_link_in_insert"])
def test_process_adoc_file_warning(test_file_name, single_and_multipage, adoc_data,
                                   cpp_api_reference, package_manager, default_config,
                                   check_adoc_expected_result):
    input_file = adoc_data / f"{test_file_name}.adoc"
    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)
    default_config.multipage = single_and_multipage
    output_doc = process_adoc(doc, cpp_api_reference, package_manager, config=default_config)[0]
    check_adoc_expected_result(output_doc, multipage=single_and_multipage)


@pytest.mark.parametrize("test_file_name, error",
                         [("dangling_link", ConsistencyError),
                          ("dangling_cross_doc_ref", IncludeFileNotFoundError),
                          ("double_insert", ConsistencyError),
                          ("dangling_link_in_insert", ConsistencyError)])
def test_process_adoc_file_warning_as_error(test_file_name, error, single_and_multipage, adoc_data,
                                            cpp_api_reference, package_manager, default_config):
    input_file = adoc_data / f"{test_file_name}.adoc"
    package_manager.set_input_files(input_file)
    doc = package_manager.prepare_work_directory(input_file)

    default_config.warnings_are_errors = True
    with pytest.raises(error):
        process_adoc(doc, cpp_api_reference, package_manager, default_config)
