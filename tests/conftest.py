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
from asciidoxy.generator.asciidoc import GeneratingApi, PreprocessingApi
from asciidoxy.generator.context import Context
from asciidoxy.generator.navigation import DocumentTreeNode
from asciidoxy.model import (Compound, EnumValue, InnerTypeReference, Parameter, ReturnValue,
                             ThrowsClause, TypeRef)
from asciidoxy.packaging import Package, PackageManager
from asciidoxy.parser.doxygen import Driver as ParserDriver

from .builders import SimpleClassBuilder

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
def package_manager(build_dir):
    return PackageManager(build_dir)


@pytest.fixture
def work_dir(package_manager):
    wd = package_manager.work_dir
    wd.mkdir(parents=True, exist_ok=True)
    return wd


@pytest.fixture
def input_file(work_dir, package_manager):
    f = work_dir / "input_file.adoc"
    f.touch()
    package_manager.set_input_files(f, include_dir=work_dir)
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
def context(input_file, fragment_dir, api_reference, package_manager):
    c = Context(base_dir=input_file.parent,
                fragment_dir=fragment_dir,
                reference=api_reference,
                package_manager=package_manager,
                current_document=DocumentTreeNode(input_file),
                current_package=Package(PackageManager.INPUT_FILES))
    return c


@pytest.fixture
def preprocessing_api(input_file, context):
    return PreprocessingApi(input_file, context)


@pytest.fixture
def generating_api(input_file, context):
    return GeneratingApi(input_file, context)


@pytest.fixture
def cpp_class():
    builder = SimpleClassBuilder("cpp")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("variable", "enum", "class", "typedef", "struct", "trash"):
            builder.simple_member(kind=member_type, prot=visibility)

        # constructor
        builder.member_function(prot=visibility, name="MyClass", has_return_value=False)
        # default constructor
        builder.member_function(prot=visibility,
                                name="MyClass",
                                has_return_value=False,
                                default=True)
        # deleted constructor
        builder.member_function(prot=visibility,
                                name="MyClass",
                                has_return_value=False,
                                deleted=True)
        # destructor
        builder.member_function(prot=visibility, name="~MyClass", has_return_value=False)

        # operator
        builder.member_function(prot=visibility, name="operator++")
        # default operator
        builder.member_function(prot=visibility, name="operator=", default=True)
        # deleted operator
        builder.member_function(prot=visibility, name="operator=", deleted=True)
        # method
        builder.member_function(prot=visibility, name=f"{visibility.capitalize()}Method")
        # static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "StaticMethod",
                                static=True)
        # nested type
        builder.inner_class(prot=visibility, name=f"{visibility.capitalize()}Type")

    return builder.compound


@pytest.fixture
def warnings_are_errors(context):
    context.warnings_are_errors = True
    return True


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def warnings_are_and_are_not_errors(request, context):
    context.warnings_are_errors = request.param
    return request.param


@pytest.fixture
def multipage(context):
    context.multipage = True
    return True


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def single_and_multipage(request, context):
    context.multipage = request.param
    return request.param


@pytest.fixture
def empty_context(input_file, fragment_dir, package_manager):
    return Context(base_dir=input_file.parent,
                   fragment_dir=fragment_dir,
                   reference=ApiReference(),
                   package_manager=package_manager,
                   current_document=DocumentTreeNode(input_file),
                   current_package=Package(PackageManager.INPUT_FILES))


@pytest.fixture
def empty_preprocessing_api(input_file, empty_context):
    return PreprocessingApi(input_file, empty_context)


@pytest.fixture
def empty_generating_api(input_file, empty_context):
    return GeneratingApi(input_file, empty_context)


_custom_types = {
    Compound: ([
        "id", "name", "full_name", "language", "kind", "include", "namespace", "prot", "definition",
        "args", "brief", "description", "static", "const", "deleted", "default", "constexpr"
    ], ["members", "inner_classes", "enumvalues", "params", "exceptions", "returns"]),
    TypeRef: (["id", "name", "language", "namespace", "kind", "prefix",
               "suffix"], ["nested", "args", "returns"]),
    Parameter: (["name", "description", "default_value", "prefix"], ["type"]),
    ReturnValue: (["description"], ["type"]),
    ThrowsClause: (["description"], ["type"]),
    EnumValue:
    (["id", "name", "full_name", "language", "kind", "initializer", "brief", "description"], []),
    InnerTypeReference: (["id", "name", "language", "namespace", "prot"], ["referred_object"]),
}


def repr_compare_eq(left, right, prefix=""):
    simple_attributes, complex_attributes = _custom_types[type(left)]

    mismatches = [
        f"{prefix}{attr}: `{getattr(left, attr)}` != `{getattr(right, attr)}`"
        for attr in simple_attributes if getattr(left, attr) != getattr(right, attr)
    ]

    for attr in complex_attributes:
        attr_left = getattr(left, attr)
        attr_right = getattr(right, attr)

        if attr_left != attr_right:
            if ((attr_left is None and attr_right is not None)
                    or (attr_left is not None and attr_right is None)):
                mismatches.append(f"{prefix}{attr}: {attr_left} != {attr_right}")
            elif isinstance(attr_left, list):
                assert isinstance(attr_right, list)

                if len(attr_left) != len(attr_right):
                    mismatches.append(f"len({prefix}{attr}): {len(attr_left)} != {len(attr_right)}")
                else:
                    for i, (item_left, item_right) in enumerate(zip(attr_left, attr_right)):
                        mismatches.extend(
                            repr_compare_eq(item_left, item_right, prefix=f"{prefix}{attr}[{i}]."))
            else:
                mismatches.extend(repr_compare_eq(attr_left, attr_right, prefix=f"{prefix}{attr}."))

    return mismatches


def pytest_assertrepr_compare(op, left, right):
    if op == "==" and isinstance(right, left.__class__) and type(left) in _custom_types:
        mismatches = [f"Instances of {type(left)} do not match:"]
        mismatches += repr_compare_eq(left, right)
        return mismatches
