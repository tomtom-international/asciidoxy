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

import shutil
from unittest.mock import patch

import pytest

from asciidoxy.cli import main


@pytest.fixture
def asciidoctor_mock():
    with patch("asciidoxy.asciidoctor.run_ruby") as mock:
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
    shutil.copy(
        xml_data / "cpp" / "default" / "xml" /
        "classasciidoxy_1_1geometry_1_1_invalid_coordinate.xml", package_dir / "xml")

    (package_dir / "contents.toml").write_text("""\
[package]
name = "package"

[reference]
type = "doxygen"
dir = "xml"
""")

    return package_dir


@pytest.fixture
def version_file(tmp_path):
    version_file = tmp_path / "versions.csv"
    version_file.write_text("Component name,Version\n"
                            "package,4.1.2")
    return version_file


@pytest.fixture
def spec_file(tmp_path, simple_package):
    spec_file = tmp_path / "package_spec.toml"
    spec_file.write_text(f"""
[packages]
[packages.package]
type= "local"
package_dir = "{simple_package}"
""")
    return spec_file


@pytest.fixture
def destination_dir(tmp_path):
    d = tmp_path / "output"
    d.mkdir(parents=True)
    return d


def read_asciidoctor_runner(asciidoctor_mock):
    asciidoctor_mock.assert_called_once()
    runner_path = asciidoctor_mock.call_args[0][0]
    return runner_path.read_text()


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


def test_process_file(asciidoctor_mock, build_dir, spec_file, destination_dir, adoc_data,
                      event_loop):
    in_file = adoc_data / "simple_test.adoc"

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir)
    ])

    output_file = destination_dir / "simple_test.html"
    processed_file = build_dir / "intermediate" / "simple_test.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'html5'" in runner
    assert processed_file.is_file()


def test_process_file_backend_pdf(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                  adoc_data, event_loop):
    in_file = adoc_data / "simple_test.adoc"

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

    output_file = destination_dir / "simple_test.pdf"
    processed_file = build_dir / "intermediate" / "simple_test.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'pdf'" in runner
    assert processed_file.is_file()


def test_process_file_backend_adoc(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                   adoc_data, event_loop):
    in_file = adoc_data / "simple_test.adoc"

    main([
        str(in_file),
        "--spec-file",
        str(spec_file),
        "--destination-dir",
        str(destination_dir),
        "--build-dir",
        str(build_dir),
        "--backend",
        "adoc",
    ])

    asciidoctor_mock.assert_not_called()
    output_file = destination_dir / "simple_test.adoc"
    assert output_file.is_file()


def test_process_custom_file_template_dir(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                          adoc_data, event_loop, tmp_path):
    in_file = adoc_data / "custom_templates.adoc"
    template_dir = tmp_path / "templates"
    (template_dir / "cpp").mkdir(parents=True)
    (template_dir / "cpp" / "class.mako").write_text("Custom class template")
    (template_dir / "cpp" / "myclass.mako").write_text("My class template")

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir), "--backend", "adoc", "--template-dir",
        str(template_dir)
    ])

    asciidoctor_mock.assert_not_called()
    output_file = destination_dir / "custom_templates.adoc"
    assert output_file.is_file()


def test_process_default_cache_dir(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                   adoc_data, event_loop):
    in_file = adoc_data / "simple_test.adoc"

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir)
    ])

    assert (build_dir / "cache" / "templates").is_dir()
    assert (build_dir / "cache" / "templates" / "cpp" / "class.mako.py").is_file()


def test_process_custom_cache_dir(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                  adoc_data, event_loop, tmp_path):
    in_file = adoc_data / "simple_test.adoc"
    cache_dir = tmp_path / "my-cache"

    main([
        str(in_file),
        "--spec-file",
        str(spec_file),
        "--destination-dir",
        str(destination_dir),
        "--build-dir",
        str(build_dir),
        "--cache-dir",
        str(cache_dir),
    ])

    assert (cache_dir / "templates").is_dir()
    assert (cache_dir / "templates" / "cpp" / "class.mako.py").is_file()


def test_all_options(asciidoctor_mock, build_dir, spec_file, version_file, destination_dir,
                     adoc_data, event_loop, tmp_path):
    in_file = adoc_data / "simple_test.adoc"
    image_dir = tmp_path / "images"
    image_dir.mkdir()

    main([
        str(in_file),
        "--base-dir",
        str(in_file.parent),
        "--image-dir",
        str(image_dir),
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

    output_file = destination_dir / "simple_test.html"
    processed_file = build_dir / "intermediate" / "simple_test.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'html5'" in runner
    assert processed_file.is_file()


def test_forward_asciidoctor_options(asciidoctor_mock, build_dir, spec_file, destination_dir,
                                     adoc_data, event_loop):
    in_file = adoc_data / "simple_test.adoc"

    main([
        str(in_file), "--spec-file",
        str(spec_file), "--destination-dir",
        str(destination_dir), "--build-dir",
        str(build_dir), "-a", "specialoption", "-a", "version=12", "-S", "server", "-d", "book",
        "-r", "asciidoctor-diagram"
    ])

    output_file = destination_dir / "simple_test.html"
    processed_file = build_dir / "intermediate" / "simple_test.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'html5'" in runner
    assert "specialoption" in runner
    assert "version=12" in runner
    assert "doctype: 'book'" in runner
    assert "safe: :server" in runner
    assert "require 'asciidoctor-diagram'\n" in runner
    assert processed_file.is_file()


def test_all_short_options(asciidoctor_mock, build_dir, spec_file, version_file, destination_dir,
                           adoc_data, event_loop):
    in_file = adoc_data / "simple_test.adoc"

    main([
        str(in_file),
        "-s",
        str(spec_file),
        "-v",
        str(version_file),
        "-D",
        str(destination_dir),
        "-B",
        str(in_file.parent),
        "-b",
        "html5",
        "-W",
        "--debug",
        "--log",
        "WARNING",
        "--build-dir",
        str(build_dir),
    ])

    output_file = destination_dir / "simple_test.html"
    processed_file = build_dir / "intermediate" / "simple_test.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'html5'" in runner
    assert processed_file.is_file()


def test_no_reference_loaded(asciidoctor_mock, build_dir, destination_dir, adoc_data, event_loop):
    in_file = adoc_data / "no_api_reference.adoc"

    main([str(in_file), "--destination-dir", str(destination_dir), "--build-dir", str(build_dir)])

    output_file = destination_dir / "no_api_reference.html"
    processed_file = build_dir / "intermediate" / "no_api_reference.adoc"
    runner = read_asciidoctor_runner(asciidoctor_mock)
    assert f"to_file: '{output_file}'" in runner
    assert f"convert_file '{processed_file}'" in runner
    assert "backend: 'html5'" in runner
    assert processed_file.is_file()
