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
"""Tests for managing packages."""

import pytest
import toml

from pathlib import Path
from unittest.mock import MagicMock, call

from asciidoxy.packaging.manager import (FileCollisionError, PackageManager, UnknownFileError,
                                         UnknownPackageError)


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
                       root_doc: bool = False) -> Path:
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

    if contents:
        with (pkg_dir / "contents.toml").open("w", encoding="utf-8") as contents_file:
            toml.dump(data, contents_file)

    return pkg_dir


def create_package_spec(parent: Path, *names: str) -> Path:
    data = {
        "sources": {
            "local": {
                "type": "local",
                "xml_subdir": "xml",
                "include_subdir": "adoc"
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


def test_collect(package_manager, event_loop, tmp_path, build_dir):
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

    pkg_b = packages["b"]
    assert pkg_b.reference_dir is not None
    assert pkg_b.reference_dir.is_dir()
    assert pkg_b.adoc_src_dir is not None
    assert pkg_b.adoc_src_dir.is_dir()
    assert pkg_b.adoc_image_dir is not None
    assert pkg_b.adoc_image_dir.is_dir()


def test_load_reference(package_manager, event_loop, tmp_path, build_dir):
    pkg_a_dir = create_package_dir(tmp_path, "a")
    pkg_b_dir = create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    parser_mock = MagicMock()
    package_manager.load_reference(parser_mock)
    parser_mock.parse.assert_has_calls(
        [call(pkg_a_dir / "xml" / "a.xml"),
         call(pkg_b_dir / "xml" / "b.xml")], any_order=True)


def test_prepare_work_directory(package_manager, event_loop, tmp_path, build_dir):
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
    work_file = package_manager.prepare_work_directory(in_file)
    assert work_file.is_file()
    assert work_file.name == "index.adoc"
    work_dir = work_file.parent

    assert (work_dir / "index.adoc").is_file()
    assert (work_dir / "chapter.adoc").is_file()
    assert (work_dir / "other").is_dir()
    assert (work_dir / "other" / "another.adoc").is_file()

    assert (work_dir / "a.adoc").is_file()
    assert (work_dir / "b.adoc").is_file()
    assert (work_dir / "images").is_dir()
    assert (work_dir / "images" / "a.png").is_file()
    assert (work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__no_include_dir(package_manager, event_loop, tmp_path, build_dir):
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
    work_file = package_manager.prepare_work_directory(in_file)
    assert work_file.is_file()
    assert work_file.name == "index.adoc"
    work_dir = work_file.parent

    assert (work_dir / "index.adoc").is_file()
    assert not (work_dir / "chapter.adoc").is_file()
    assert not (work_dir / "other").is_dir()
    assert not (work_dir / "other" / "another.adoc").is_file()

    assert (work_dir / "a.adoc").is_file()
    assert (work_dir / "b.adoc").is_file()
    assert (work_dir / "images").is_dir()
    assert (work_dir / "images" / "a.png").is_file()
    assert (work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__explicit_images(package_manager, event_loop, tmp_path, build_dir):
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
    work_file = package_manager.prepare_work_directory(in_file)
    assert work_file.is_file()
    assert work_file.name == "index.adoc"
    work_dir = work_file.parent

    assert (work_dir / "index.adoc").is_file()
    assert not (work_dir / "chapter.adoc").is_file()
    assert not (work_dir / "other").is_dir()
    assert not (work_dir / "other" / "another.adoc").is_file()

    assert (work_dir / "images").is_dir()
    assert (work_dir / "images" / "image.png").is_file()

    assert (work_dir / "a.adoc").is_file()
    assert (work_dir / "b.adoc").is_file()
    assert (work_dir / "images" / "a.png").is_file()
    assert (work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__implicit_images(package_manager, event_loop, tmp_path, build_dir):
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
    work_file = package_manager.prepare_work_directory(in_file)
    assert work_file.is_file()
    assert work_file.name == "index.adoc"
    work_dir = work_file.parent

    assert (work_dir / "index.adoc").is_file()
    assert not (work_dir / "chapter.adoc").is_file()
    assert not (work_dir / "other").is_dir()
    assert not (work_dir / "other" / "another.adoc").is_file()

    assert (work_dir / "images").is_dir()
    assert (work_dir / "images" / "image.png").is_file()

    assert (work_dir / "a.adoc").is_file()
    assert (work_dir / "b.adoc").is_file()
    assert (work_dir / "images" / "a.png").is_file()
    assert (work_dir / "images" / "b.png").is_file()


def test_prepare_work_directory__file_collision(package_manager, event_loop, tmp_path, build_dir,
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
        with pytest.raises(FileCollisionError):
            package_manager.prepare_work_directory(in_file)
    else:
        package_manager.prepare_work_directory(in_file)


def test_prepare_work_directory__dir_and_file_collision_1(package_manager, event_loop, tmp_path,
                                                          build_dir,
                                                          warnings_are_and_are_not_errors):
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
    with pytest.raises(FileCollisionError):
        package_manager.prepare_work_directory(in_file)


def test_prepare_work_directory__dir_and_file_collision_2(package_manager, event_loop, tmp_path,
                                                          build_dir,
                                                          warnings_are_and_are_not_errors):
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
    with pytest.raises(FileCollisionError):
        package_manager.prepare_work_directory(in_file)


def test_prepare_work_directory__dir_and_file_collision_3(package_manager, event_loop, tmp_path,
                                                          build_dir,
                                                          warnings_are_and_are_not_errors):
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
    with pytest.raises(FileCollisionError):
        package_manager.prepare_work_directory(in_file)


def test_prepare_work_directory__same_dir_in_multiple_packages(package_manager, event_loop,
                                                               tmp_path, build_dir):
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
    work_file = package_manager.prepare_work_directory(in_file)
    assert work_file.is_file()
    assert work_file.name == "index.adoc"
    work_dir = work_file.parent

    assert (work_dir / "other").is_dir()
    assert (work_dir / "other" / "another.adoc").is_file()
    assert (work_dir / "other" / "a_another.adoc").is_file()
    assert (work_dir / "other" / "b_another.adoc").is_file()


def test_make_image_directory(package_manager, event_loop, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    output_dir = tmp_path / "output"
    package_manager.make_image_directory(output_dir)

    assert (output_dir / "images").is_dir()
    assert (output_dir / "images" / "a.png").is_file()
    assert (output_dir / "images" / "b.png").is_file()


def test_make_image_directory__from_input_files(package_manager, event_loop, tmp_path, build_dir):
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


def test_file_in_work_directory__present(package_manager, event_loop, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    work_file = package_manager.prepare_work_directory(in_file)
    work_dir = work_file.parent

    assert package_manager.file_in_work_directory("a", "a.adoc") == work_dir / "a.adoc"
    assert package_manager.file_in_work_directory("b", "b.adoc") == work_dir / "b.adoc"


def test_file_in_work_directory__default_root_doc(package_manager, event_loop, tmp_path, build_dir):
    create_package_dir(tmp_path, "a", root_doc=True)
    spec_file = create_package_spec(tmp_path, "a")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    work_file = package_manager.prepare_work_directory(in_file)
    work_dir = work_file.parent

    assert package_manager.file_in_work_directory("a", None) == work_dir / "a.adoc"
    assert package_manager.file_in_work_directory("a", "") == work_dir / "a.adoc"


def test_file_in_work_directory__no_root_doc_no_filename(package_manager, event_loop, tmp_path,
                                                         build_dir):
    create_package_dir(tmp_path, "a", root_doc=False)
    spec_file = create_package_spec(tmp_path, "a")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("a", None)
    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("a", "")


def test_file_in_work_directory__unknown_package(package_manager, event_loop, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownPackageError):
        package_manager.file_in_work_directory("c", "a.adoc")


def test_file_in_work_directory__unknown_file(package_manager, event_loop, tmp_path, build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("a", "c.adoc")


def test_file_in_work_directory__package_must_match(package_manager, event_loop, tmp_path,
                                                    build_dir):
    create_package_dir(tmp_path, "a")
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("b", "a.adoc")
    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("a", "b.adoc")


def test_file_in_work_directory__package_without_include_files(package_manager, event_loop,
                                                               tmp_path, build_dir):
    create_package_dir(tmp_path, "a", adoc=False)
    create_package_dir(tmp_path, "b")
    spec_file = create_package_spec(tmp_path, "a", "b")
    package_manager.collect(spec_file)

    src_dir = tmp_path / "src"
    src_dir.mkdir()
    in_file = src_dir / "index.adoc"
    in_file.touch()
    package_manager.prepare_work_directory(in_file)

    with pytest.raises(UnknownFileError):
        package_manager.file_in_work_directory("a", "a.adoc")
