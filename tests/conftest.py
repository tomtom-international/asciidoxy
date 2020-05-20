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

from asciidoxy.api_reference import ApiReference
from asciidoxy.doxygenparser import Driver as ParserDriver
from asciidoxy.generator.asciidoc import Api, Context, DocumentTreeNode
from asciidoxy.model import Compound, Member, ReturnValue, InnerTypeReference

_xml_dir = Path(__file__).parent / "xml"


def pytest_addoption(parser):
    parser.addoption(
        "--update-expected-results",
        action="store_true",
        help="Update the expected results for template tests with the current results.")


@pytest.fixture
def update_expected_results(request):
    return request.config.getoption("update_expected_results")


def _doxygen_versions():
    return [str(version.name) for version in _xml_dir.glob("*")]


@pytest.fixture(params=_doxygen_versions())
def doxygen_version(request):
    return request.param


@pytest.fixture
def xml_data(doxygen_version):
    return Path(__file__).parent / "xml" / doxygen_version


@pytest.fixture
def parser_driver_factory(xml_data):
    def factory(*test_dirs, force_language=None):
        parser_driver = ParserDriver(force_language=force_language)

        for test_dir in test_dirs:
            for xml_file in (xml_data / test_dir).glob("**/*.xml"):
                parser_driver.parse(xml_file)

        return parser_driver

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
    return "cpp/default", "java/default", "objc/default", "python/default"


@pytest.fixture
def forced_language():
    """Default value for `force_language` when using the `api_reference` fixture.

    By default the language is not forced. Override this using `pytest.mark.parametrize` to force
    the language.
    """
    return None


@pytest.fixture
def api_reference(parser_driver_factory, api_reference_set, forced_language):
    driver = parser_driver_factory(*api_reference_set, force_language=forced_language)
    driver.resolve_references()
    return driver.api_reference


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


@pytest.fixture
def cpp_class():
    compound = Compound("cpp")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("cpp")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("cpp")
        member.kind = "function"
        member.name = name
        member.prot = prot
        if has_return_value:
            member.returns = ReturnValue()
        if is_static:
            member.static = True
        return member

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("variable", "enum", "class", "typedef", "struct", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # adds constructors
        compound.members.append(
            generate_member_function(prot=visibility, name="MyClass", has_return_value=False))
        # add some operator
        compound.members.append(generate_member_function(prot=visibility, name="operator++"))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "StaticMethod",
                                     is_static=True))

    # insert nested type
    nested_class = Compound("cpp")
    nested_class.name = "NestedClass"
    inner_class_reference = InnerTypeReference(language="cpp")
    inner_class_reference.name = nested_class.name
    inner_class_reference.referred_object = nested_class
    compound.inner_classes.append(inner_class_reference)

    return compound


@pytest.fixture
def warnings_are_errors(context):
    context.warnings_are_errors = True
    return True


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def warnings_are_and_are_not_errors(request, context):
    context.warnings_are_errors = request.param
    return request.param


@pytest.fixture
def multi_page(context):
    context.multi_page = True
    return True


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def single_and_multi_page(request, context):
    context.multi_page = request.param
    return request.param


@pytest.fixture
def empty_context(input_file, build_dir, fragment_dir):
    return Context(base_dir=input_file.parent,
                   build_dir=build_dir,
                   fragment_dir=fragment_dir,
                   reference=ApiReference(),
                   current_document=DocumentTreeNode(input_file))
