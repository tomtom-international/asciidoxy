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
"""Test the template cache implementation."""

from pathlib import PurePosixPath, PureWindowsPath

import pytest

from asciidoxy.generator.cache import DocumentCache, _generate_python_path_code


def test_get_document(document):
    document.original_file.write_text("= My document")

    cache = DocumentCache()
    template = cache.get_document(document)
    assert template is not None
    assert template.source.startswith("= My document")

    assert cache.get_document(document) is template


def test_get_document__not_found(document):
    missing_doc = document.with_relative_path("missing.adoc")

    cache = DocumentCache()
    with pytest.raises(FileNotFoundError):
        cache.get_document(missing_doc)


def test_cache_dir(tmp_path, document):
    document.original_file.write_text("= My document")

    cache_dir = tmp_path / "cache"
    cache = DocumentCache(cache_dir=cache_dir)
    template = cache.get_document(document)
    assert template is not None
    assert template.source.startswith("= My document")
    assert (cache_dir / "documents" /
            str(document.original_file.with_suffix(".adoc.py"))[1:]).is_file()


def test_python_path_code__no_paths():
    assert _generate_python_path_code(None) == []
    assert _generate_python_path_code([]) == []


@pytest.mark.parametrize("path,expected", [
    (PurePosixPath("/home/user/python"), "/home/user/python"),
    (PurePosixPath("/home/user/my python"), "/home/user/my python"),
    (PureWindowsPath(r"C:\Users\user\python"), "C:/Users/user/python"),
    (PureWindowsPath(r"C:\Users\user\my python"), "C:/Users/user/my python"),
])
def test_python_path_code(path, expected):
    code = _generate_python_path_code([path])
    assert code == ["import sys", f"sys.path.insert(1, \"{expected}\")", "del sys"]

    # The generated code must be valid Python that adds the path. Windows paths used to contain
    # backslashes that Python read as escape sequences, like `\U`.
    sys_path = ["first"]
    exec("\n".join(code[1:-1]), {"sys": type("sys", (), {"path": sys_path})})
    assert sys_path == ["first", expected]
