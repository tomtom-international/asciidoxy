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
"""Tests for managing packages."""

from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest
import toml

from asciidoxy.api_reference import ApiReference
from asciidoxy.config import Configuration
from asciidoxy.document import Package
from asciidoxy.packaging.manager import (
    FileCollisionError,
    PackageManager,
    UnknownFileError,
    UnknownPackageError,
)


@pytest.fixture
def package_manager(build_dir):
    return PackageManager(build_dir)


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def warnings_are_and_are_not_errors(request, package_manager):
    package_manager.warnings_are_errors = request.param
    return request.param


def create_package_dir(parent: Path,
                       name: str,
                       xml: bool = True,
                       adoc: bool = True,
                       images: bool = True,
                       contents: bool = True,
                       root_doc: bool = False,
                       python: bool = True) -> Path:
    pkg_dir = parent / name
    pkg_dir.mkdir(parents=True)

    data = {"package": {"name": name}}

    if xml:
        (pkg_dir / "xml").mkdir()
        (pkg_dir / "xml" / f"{name}.xml").touch()

        data["reference"] = {"type": "doxygen", "dir": "xml"}

    if adoc:
        (pkg_dir / "adoc").mkdir()
        (pkg_dir / "adoc" / f"{name}.adoc").touch()

        data["asciidoc"] = {"src_dir": "adoc"}

        if root_doc:
            data["asciidoc"]["root_doc"] = f"{name}.adoc"

        if images:
            (pkg_dir / "images").mkdir()
            (pkg_dir / "images" / f"{name}.png").touch()

            data["asciidoc"]["image_dir"] = "images"

    if python:
        (pkg_dir / "python").mkdir()
        (pkg_dir / "python" / f"{name}.py").touch()

        data["python"] = {"dir": "python"}

    if contents:
        with (pkg_dir / "contents.toml").open("w", encoding="utf-8") as contents_file:
            toml.dump(data, contents_file)

    return pkg_dir


def create_package_spec(parent: Path, *names: str) -> Path:
    data = {
        "sources": {
            "local": {
                "type": "local",
            }
        },
    }

    data["packages"] = {
        name: {
            "source": "local",
            "package_dir": str(parent / name)
        }
        for name in names
    }

    spec_file = parent / "spec.toml"
    with spec_file.open("w", encoding="utf-8") as spec_file_handle:
        toml.dump(data, spec_file_handle)

    return spec_file


def test_collect(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")

    package_manager.collect(spec_file)
    assert len(package_manager.packages) == 2

    packages = package_manager.packages
    assert "a" in packages
    assert "b" in packages

    pkg_a = packages["a"]
    assert pkg_a.reference_dir is not None
    assert pkg_a.reference_dir.is_dir()
    assert pkg_a.adoc_src_dir is not None
    assert pkg_a.adoc_src_dir.is_dir()
    assert pkg_a.adoc_image_dir is not None
    assert pkg_a.adoc_image_dir.is_dir()
    assert pkg_a.python_dir is not None
    assert pkg_a.python_dir.is_dir()

    pkg_b = packages["b"]
    assert pkg_b.reference_dir is not None
    assert pkg_b.reference_dir.is_dir()
    assert pkg_b.adoc_src_dir is not None
    assert pkg_b.adoc_src_dir.is_dir()
    assert pkg_b.adoc_image_dir is not None
    assert pkg_b.adoc_image_dir.is_dir()
    assert pkg_b.python_dir is not None
    assert pkg_b.python_dir.is_dir()


@pytest.fixture
def parser_mock():
    with patch("asciidoxy.packaging.manager.parser_factory") as mock:
        parser_mock = MagicMock()
        mock.return_value = parser_mock
        yield parser_mock


def test_load_reference(package_manager, tmp_path, parser_mock):
    pkg_a_dir = create_package_dir(tmp_path, "a")
    pkg_b_dir = create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    package_manager.load_reference(ApiReference(), Configuration())
    parser_mock.parse.assert_has_calls(
        [call(pkg_a_dir / "xml"), call(pkg_b_dir / "xml")], any_order=True)


def test_prepare_work_directory(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    package_manager.set_input_files(in_file, src_dir)
    doc = package_manager.prepare_work_directory(in_file)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "index.adoc").is_file()
    assert (doc.work_dir / "chapter.adoc").is_file()
    assert (doc.work_dir / "other").is_dir()
    assert (doc.work_dir / "other" / "another.adoc").is_file()

    assert (doc.work_dir / "a.adoc").is_file()
    assert (doc.work_dir / "b.adoc").is_file()
    assert (doc.work_dir / "images").is_dir()
    assert (doc.work_dir / "images" / "a.png").is_file()
    assert (doc.work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__no_include_dir(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    package_manager.set_input_files(in_file)
    doc = package_manager.prepare_work_directory(in_file)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "index.adoc").is_file()
    assert not (doc.work_dir / "chapter.adoc").is_file()
    assert not (doc.work_dir / "other").is_dir()
    assert not (doc.work_dir / "other" / "another.adoc").is_file()

    assert (doc.work_dir / "a.adoc").is_file()
    assert (doc.work_dir / "b.adoc").is_file()
    assert (doc.work_dir / "images").is_dir()
    assert (doc.work_dir / "images" / "a.png").is_file()
    assert (doc.work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__explicit_images(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "image.png").touch()

    package_manager.set_input_files(in_file, None, image_dir)
    doc = package_manager.prepare_work_directory(in_file)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "index.adoc").is_file()
    assert not (doc.work_dir / "chapter.adoc").is_file()
    assert not (doc.work_dir / "other").is_dir()
    assert not (doc.work_dir / "other" / "another.adoc").is_file()

    assert (doc.work_dir / "images").is_dir()
    assert (doc.work_dir / "images" / "image.png").is_file()

    assert (doc.work_dir / "a.adoc").is_file()
    assert (doc.work_dir / "b.adoc").is_file()
    assert (doc.work_dir / "images" / "a.png").is_file()
    assert (doc.work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__implicit_images(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    image_dir = src_dir / "images"
    image_dir.mkdir()
    (image_dir / "image.png").touch()

    package_manager.set_input_files(in_file, None, None)
    doc = package_manager.prepare_work_directory(in_file)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "index.adoc").is_file()
    assert not (doc.work_dir / "chapter.adoc").is_file()
    assert not (doc.work_dir / "other").is_dir()
    assert not (doc.work_dir / "other" / "another.adoc").is_file()

    assert (doc.work_dir / "images").is_dir()
    assert (doc.work_dir / "images" / "image.png").is_file()

    assert (doc.work_dir / "a.adoc").is_file()
    assert (doc.work_dir / "b.adoc").is_file()
    assert (doc.work_dir / "images" / "a.png").is_file()
    assert (doc.work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__file_collision(package_manager, tmp_path, build_dir,
                                                warnings_are_and_are_not_errors):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "a.adoc").touch()

    package_manager.set_input_files(in_file, src_dir)

    if warnings_are_and_are_not_errors:
        with pytest.raises(FileCollisionError) as excinfo:
            package_manager.prepare_work_directory(in_file)
        assert "File a.adoc from package INPUT already exists in package a." in str(excinfo.value)
    else:
        package_manager.prepare_work_directory(in_file)


def test_prepare_work_directory__dir_and_file_collision__file_overwrites_dir_from_input(
        package_manager, tmp_path, build_dir, warnings_are_and_are_not_errors):

    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "a.adoc").mkdir()

    package_manager.set_input_files(in_file, src_dir)
    with pytest.raises(FileCollisionError) as excinfo:
        package_manager.prepare_work_directory(in_file)
    assert ("Package a contains file a.adoc, which is also a directory in package INPUT."
            in str(excinfo.value))


def test_prepare_work_directory__dir_and_file_collision__dir_overwrites_file(
        package_manager, tmp_path, build_dir, warnings_are_and_are_not_errors):

    create_package_dir(tmp_path, "a")
    pkg_b_dir = create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (pkg_b_dir / "adoc" / "a.adoc").mkdir()

    package_manager.set_input_files(in_file, src_dir)
    with pytest.raises(FileCollisionError) as excinfo:
        package_manager.prepare_work_directory(in_file)
    assert ("Package a contains file a.adoc, which is also a directory in package b."
            in str(excinfo.value))


def test_prepare_work_directory__dir_and_file_collision__file_overwrites_dir(
        package_manager, tmp_path, build_dir, warnings_are_and_are_not_errors):

    pkg_a_dir = create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (pkg_a_dir / "adoc" / "b.adoc").mkdir()

    package_manager.set_input_files(in_file, src_dir)
    with pytest.raises(FileCollisionError) as excinfo:
        package_manager.prepare_work_directory(in_file)
    assert "File b.adoc from package b is also a directory in package a." in str(excinfo.value)


def test_prepare_work_directory__same_dir_in_multiple_packages(package_manager, tmp_path,
                                                               build_dir):
    pkg_a_dir = create_package_dir(tmp_path, "a")
    pkg_b_dir = create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()
    (pkg_a_dir / "adoc" / "other").mkdir()
    (pkg_a_dir / "adoc" / "other" / "a_another.adoc").touch()
    (pkg_b_dir / "adoc" / "other").mkdir()
    (pkg_b_dir / "adoc" / "other" / "b_another.adoc").touch()

    package_manager.set_input_files(in_file, src_dir)
    doc = package_manager.prepare_work_directory(in_file)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "other").is_dir()
    assert (doc.work_dir / "other" / "another.adoc").is_file()
    assert (doc.work_dir / "other" / "a_another.adoc").is_file()
    assert (doc.work_dir / "other" / "b_another.adoc").is_file()


@pytest.mark.parametrize("clear", [True, False])
def test_prepare_work_directory__clear_existing(clear, package_manager, tmp_path, build_dir,
                                                work_dir):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    work_dir.mkdir(parents=True, exist_ok=True)
    (work_dir / "existing_file").touch()

    package_manager.set_input_files(in_file, src_dir)
    doc = package_manager.prepare_work_directory(in_file, clear)
    assert doc.work_file.is_file()
    assert doc.work_file.name == "index.adoc"
    assert doc.package is not None
    assert doc.package.is_input_package is True

    assert (doc.work_dir / "index.adoc").is_file()
    assert (doc.work_dir / "chapter.adoc").is_file()
    assert (doc.work_dir / "other").is_dir()
    assert (doc.work_dir / "other" / "another.adoc").is_file()

    assert work_dir == doc.work_dir
    assert (work_dir / "existing_file").exists() is not clear


def test_make_image_directory(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    package_manager.make_image_directory(output_dir)

    assert (output_dir / "images").is_dir()
    assert (output_dir / "images" / "a.png").is_file()
    assert (output_dir / "images" / "b.png").is_file()


def test_make_image_directory__existing_output_dir(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    package_manager.make_image_directory(output_dir)

    assert (output_dir / "images").is_dir()
    assert (output_dir / "images" / "a.png").is_file()
    assert (output_dir / "images" / "b.png").is_file()

    package_manager2 = PackageManager(build_dir)
    package_manager2.collect(spec_file)
    package_manager2.make_image_directory(output_dir)

    assert (output_dir / "images").is_dir()
    assert (output_dir / "images" / "a.png").is_file()
    assert (output_dir / "images" / "b.png").is_file()


def test_make_image_directory__from_input_files(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    image_dir = tmp_path / "images"
    image_dir.mkdir()
    (image_dir / "image.png").touch()

    package_manager.set_input_files(in_file, None, image_dir)
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    package_manager.make_image_directory(output_dir)

    assert (output_dir / "images").is_dir()
    assert (output_dir / "images" / "image.png").is_file()
    assert (output_dir / "images" / "a.png").is_file()
    assert (output_dir / "images" / "b.png").is_file()


def test_make_image_directory__file_collision__file_overwrites_directory(
        package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    (output_dir / "images" / "a.png").mkdir(parents=True)
    with pytest.raises(FileCollisionError) as excinfo:
        package_manager.make_image_directory(output_dir)
    assert ("Unexpected directory a.png, blocking creation of a file from package a."
            in str(excinfo.value))


def test_make_image_directory__file_collision__directory_overwrites_file(
        package_manager, tmp_path, build_dir):
    pkg_a_dir = create_package_dir(tmp_path, "a")
    (pkg_a_dir / "images" / "a_subdir").mkdir(parents=True)
    (pkg_a_dir / "images" / "a_subdir" / "a_subdir_file.png").touch()
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    (output_dir / "images").mkdir(parents=True)
    (output_dir / "images" / "a_subdir").touch()

    with pytest.raises(FileCollisionError) as excinfo:
        package_manager.make_image_directory(output_dir)
    assert ("Unexpected file a_subdir, blocking creation of a directory from package a."
            in str(excinfo.value))


@pytest.mark.parametrize("package_hint", [None, "", "a", "b", Package.INPUT_PACKAGE_NAME])
def test_find_original_file__with_include_dir(package_hint, package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    (src_dir / "chapter.adoc").touch()
    (src_dir / "other").mkdir()
    (src_dir / "other" / "another.adoc").touch()

    package_manager.set_input_files(in_file, src_dir)
    package_manager.prepare_work_directory(in_file)

    assert package_manager.find_original_file(package_manager.work_dir / "index.adoc",
                                              package_hint) == (Package.INPUT_PACKAGE_NAME,
                                                                Path("index.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "chapter.adoc",
                                              package_hint) == (Package.INPUT_PACKAGE_NAME,
                                                                Path("chapter.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "other/another.adoc",
                                              package_hint) == (Package.INPUT_PACKAGE_NAME,
                                                                Path("other/another.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "a.adoc",
                                              package_hint) == ("a", Path("a.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "b.adoc",
                                              package_hint) == ("b", Path("b.adoc"))


@pytest.mark.parametrize("package_hint", [None, "", "a", "b", Package.INPUT_PACKAGE_NAME])
def test_find_original_file__without_include_dir(package_hint, package_manager, tmp_path,
                                                 build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    assert package_manager.find_original_file(package_manager.work_dir / "index.adoc",
                                              package_hint) == (Package.INPUT_PACKAGE_NAME,
                                                                Path("index.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "a.adoc",
                                              package_hint) == ("a", Path("a.adoc"))
    assert package_manager.find_original_file(package_manager.work_dir / "b.adoc",
                                              package_hint) == ("b", Path("b.adoc"))


def test_friendly_filename(package_manager, tmp_path):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)

    assert package_manager.friendly_filename(str(tmp_path / "a/adoc/a.adoc")) == "a:/a.adoc"
    assert package_manager.friendly_filename(str(tmp_path / "b/adoc/b.adoc")) == "b:/b.adoc"
    assert package_manager.friendly_filename(str(in_file)) == "index.adoc"
    assert package_manager.friendly_filename("/other/file.adoc") == "/other/file.adoc"


def test_make_document__input_dir(package_manager, tmp_path, build_dir):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    doc = package_manager.make_document(file_name="index.adoc")
    assert doc is not None
    assert doc.relative_path == Path("index.adoc")
    assert doc.package is not None
    assert doc.package.is_input_package is True


def test_make_document__input_dir__unknown_file(package_manager, tmp_path, build_dir):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.make_document(file_name="unknown.adoc")


def test_make_document__input_file(package_manager, tmp_path, build_dir):
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    doc = package_manager.make_document()
    assert doc is not None
    assert doc.relative_path == Path("index.adoc")
    assert doc.package is not None
    assert doc.package.is_input_package is True


def test_make_document__package_file(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    doc = package_manager.make_document(package_name="a", file_name="a.adoc")
    assert doc is not None
    assert doc.relative_path == Path("a.adoc")
    assert doc.package is not None
    assert doc.package.name == "a"

    doc = package_manager.make_document(package_name="b", file_name="b.adoc")
    assert doc is not None
    assert doc.relative_path == Path("b.adoc")
    assert doc.package is not None
    assert doc.package.name == "b"


def test_make_document__unknown_package(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownPackageError):
        package_manager.make_document(package_name="c", file_name="a.adoc")


def test_make_document__unknown_package_file(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.make_document(package_name="a", file_name="c.adoc")
    with pytest.raises(UnknownFileError):
        package_manager.make_document(package_name="b", file_name="c.adoc")


def test_make_document__wrong_package_file(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()

    package_manager.set_input_files(in_file)
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.make_document(package_name="a", file_name="b.adoc")
    with pytest.raises(UnknownFileError):
        package_manager.make_document(package_name="b", file_name="a.adoc")


def test_python_paths__all_packages(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")

    package_manager.collect(spec_file)
    assert sorted(package_manager.python_paths()) == sorted(
        [tmp_path / "a" / "python", tmp_path / "b" / "python"])


def test_python_paths__some_packages(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a", python=False)
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")

    package_manager.collect(spec_file)
    assert sorted(package_manager.python_paths()) == sorted([tmp_path / "b" / "python"])


def test_python_paths__no_packages(package_manager, tmp_path, build_dir):
    create_package_dir(tmp_path, "a", python=False)
    create_package_dir(tmp_path, "b", python=False)
    spec_file = create_package_spec(tmp_path, "a", "b")

    package_manager.collect(spec_file)
    assert len(package_manager.python_paths()) == 0


def test_python_paths__default_input_file(package_manager, tmp_path, build_dir):
    input_file = tmp_path / "src" / "input.adoc"
    input_file.parent.mkdir(parents=True)
    input_file.touch()

    package_manager.set_input_files(input_file)
    assert sorted(package_manager.python_paths()) == sorted([tmp_path / "src"])


def test_python_paths__separate_include_dir(package_manager, tmp_path, build_dir):
    input_file = tmp_path / "src" / "input.adoc"
    input_file.parent.mkdir(parents=True)
    input_file.touch()

    include_dir = tmp_path / "includes"
    include_dir.mkdir(parents=True)

    package_manager.set_input_files(input_file, include_dir=include_dir)
    assert sorted(package_manager.python_paths()) == sorted([tmp_path / "includes"])


def test_python_paths__separate_python_dir(package_manager, tmp_path, build_dir):
    input_file = tmp_path / "src" / "input.adoc"
    input_file.parent.mkdir(parents=True)
    input_file.touch()

    include_dir = tmp_path / "includes"
    include_dir.mkdir(parents=True)

    python_dir = tmp_path / "python"
    python_dir.mkdir(parents=True)

    package_manager.set_input_files(input_file, include_dir=include_dir, python_dir=python_dir)
    assert sorted(package_manager.python_paths()) == sorted([tmp_path / "python"])


def test_python_paths__python_dir_and_packages(package_manager, tmp_path, build_dir):
    input_file = tmp_path / "src" / "input.adoc"
    input_file.parent.mkdir(parents=True)
    input_file.touch()

    python_dir = tmp_path / "python"
    python_dir.mkdir(parents=True)

    package_manager.set_input_files(input_file, python_dir=python_dir)

    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")

    package_manager.collect(spec_file)
    assert sorted(package_manager.python_paths()) == sorted(
        [tmp_path / "python", tmp_path / "a" / "python", tmp_path / "b" / "python"])
