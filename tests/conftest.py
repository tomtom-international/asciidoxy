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
"""Fixtures for testing AsciiDoxy."""

import pytest

from pathlib import Path

from asciidoxy.asciidoc import Api, Context, DocumentTreeNode
from asciidoxy.doxygen_xml import DoxygenXmlParser

_xml_dir = Path(__file__).parent / "xml"


def _doxygen_versions():
    return [str(version.name) for version in _xml_dir.glob("*")]


@pytest.fixture(params=_doxygen_versions())
def doxygen_version(request):
    return request.param


@pytest.fixture
def xml_data(doxygen_version):
    return Path(__file__).parent / "xml" / doxygen_version


@pytest.fixture
def parser_factory(xml_data):
    def factory(*test_dirs, force_language=None):
        parser = DoxygenXmlParser(force_language=force_language)

        for test_dir in test_dirs:
            for xml_file in (xml_data / test_dir).glob("**/*.xml"):
                parser.parse(xml_file)

        return parser

    return factory


@pytest.fixture
def adoc_data():
    return Path(__file__).parent / "adoc"


@pytest.fixture
def test_data():
    return Path(__file__).parent / "data"


@pytest.fixture
def build_dir(tmp_path):
    d = tmp_path / "build"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def fragment_dir(build_dir):
    d = build_dir / "fragments"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def input_file(tmp_path):
    f = tmp_path / "input_file.adoc"
    f.touch()
    return f


@pytest.fixture
def api_reference_set():
    """Default set of API references to load when using the `api_reference` fixture.

    Override this using `pytest.mark.parametrize` to load other API references.
    """
    return "cpp/default", "java/default", "objc/default"


@pytest.fixture
def forced_language():
    """Default value for `force_language` when using the `api_reference` fixture.

    By default the language is not forced. Override this using `pytest.mark.parametrize` to force
    the language.
    """
    return None


@pytest.fixture
def api_reference(parser_factory, api_reference_set, forced_language):
    parser = parser_factory(*api_reference_set, force_language=forced_language)
    parser.resolve_references()
    return parser.api_reference


@pytest.fixture
def context(input_file, build_dir, fragment_dir, api_reference):
    c = Context(base_dir=input_file.parent,
                build_dir=build_dir,
                fragment_dir=fragment_dir,
                reference=api_reference,
                current_document=DocumentTreeNode(input_file))
    c.preprocessing_run = False
    return c


@pytest.fixture
def api(input_file, context):
    return Api(input_file, context)
