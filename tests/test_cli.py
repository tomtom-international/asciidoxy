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

import pytest
import shutil

from unittest.mock import patch

from asciidoxy.cli import main


@pytest.fixture
def asciidoctor_mock():
    with patch("asciidoxy.cli.asciidoctor") as mock:
        yield mock


@pytest.fixture
def build_dir(tmp_path):
    d = tmp_path / "build"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def simple_package(tmp_path, xml_data):
    package_dir = tmp_path / "package"
    (package_dir / "xml").mkdir(parents=True)
    shutil.copy(
        xml_data / "cpp" / "default" / "xml" / "classasciidoxy_1_1geometry_1_1_coordinate.xml",
        package_dir / "xml")
    return package_dir


@pytest.fixture
def version_file(tmp_path):
    version_file = tmp_path / "versions.csv"
    version_file.write_text("Component name,Version\n" "package,4.1.2")
    return version_file


@pytest.fixture
def spec_file(tmp_path, simple_package):
    spec_file = tmp_path / "package_spec.toml"
    spec_file.write_text(f"""
[packages]
[packages.package]
type= "local"
xml_subdir = "xml"
include_subdir = "include"
package_dir = "{simple_package}"
""")
    return spec_file


@pytest.fixture
def destination_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir(parents=True)
    return d


def test_no_arguments():
    with pytest.raises(SystemExit) as exc_info:
        main([])
    assert exc_info.value.code != 0


def test_help():
    with pytest.raises(SystemExit) as exc_info:
        main(["-h"])
    assert exc_info.value.code == 0

    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])
    assert exc_info.value.code == 0


def test_process_file(asciidoctor_mock, build_dir, spec_file, destination_dir, adoc_data):
    in_file = adoc_data / "simple_test.input.adoc"

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir)
    ])

    output_file = destination_dir / "simple_test.input.html"
    processed_file = build_dir / "intermediate" / ".asciidoxy.simple_test.input.adoc"
    asciidoctor_mock.assert_called_once_with(destination_dir, output_file, processed_file, False,
                                             "html5", [])
    assert processed_file.is_file()


def test_process_file_backend_pdf(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                  adoc_data):
    in_file = adoc_data / "simple_test.input.adoc"

    main([
        str(in_file),
        "--spec-file",
        str(spec_file),
        "--destination-dir",
        str(destination_dir),
        "--build-dir",
        str(build_dir),
        "--backend",
        "pdf",
    ])

    output_file = destination_dir / "simple_test.input.pdf"
    processed_file = build_dir / "intermediate" / ".asciidoxy.simple_test.input.adoc"
    asciidoctor_mock.assert_called_once_with(destination_dir, output_file, processed_file, False,
                                             "pdf", [])
    assert processed_file.is_file()


def test_all_options(asciidoctor_mock, build_dir, spec_file, version_file, destination_dir,
                     adoc_data):
    in_file = adoc_data / "simple_test.input.adoc"

    main([
        str(in_file),
        "--spec-file",
        str(spec_file),
        "--version-file",
        str(version_file),
        "--destination-dir",
        str(destination_dir),
        "--build-dir",
        str(build_dir),
        "--backend",
        "html5",
        "--warnings-are-errors",
        "--debug",
        "--log",
        "WARNING",
    ])

    output_file = destination_dir / "simple_test.input.html"
    processed_file = build_dir / "intermediate" / ".asciidoxy.simple_test.input.adoc"
    asciidoctor_mock.assert_called_once_with(destination_dir, output_file, processed_file, False,
                                             "html5", [])
    assert processed_file.is_file()


def test_forward_unknown_options(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                 adoc_data):
    in_file = adoc_data / "simple_test.input.adoc"

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir), "--verbose", "-a", "specialoption"
    ])

    output_file = destination_dir / "simple_test.input.html"
    processed_file = build_dir / "intermediate" / ".asciidoxy.simple_test.input.adoc"
    asciidoctor_mock.assert_called_once_with(destination_dir, output_file, processed_file, False,
                                             "html5", ["--verbose", "-a", "specialoption"])
    assert processed_file.is_file()


def test_all_short_options(asciidoctor_mock, build_dir, spec_file, version_file, destination_dir,
                           adoc_data):
    in_file = adoc_data / "simple_test.input.adoc"

    main([
        str(in_file),
        "-s",
        str(spec_file),
        "-v",
        str(version_file),
        "-D",
        str(destination_dir),
        "-B",
        str(build_dir),
        "-b",
        "html5",
        "-W",
        "--debug",
        "--log",
        "WARNING",
    ])

    output_file = destination_dir / "simple_test.input.html"
    processed_file = build_dir / "intermediate" / ".asciidoxy.simple_test.input.adoc"
    asciidoctor_mock.assert_called_once_with(destination_dir, output_file, processed_file, False,
                                             "html5", [])
    assert processed_file.is_file()
