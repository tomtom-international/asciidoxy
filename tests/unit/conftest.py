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
"""Fixtures for testing AsciiDoxy."""

from pathlib import Path

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.config import Configuration
from asciidoxy.document import Document, Package
from asciidoxy.generator.asciidoc import GeneratingApi, PreprocessingApi
from asciidoxy.generator.context import Context
from asciidoxy.model import Compound, Parameter, ReturnValue, ThrowsClause, TypeRef
from asciidoxy.packaging import PackageManager
from asciidoxy.parser.doxygen import Driver as ParserDriver

from .builders import SimpleClassBuilder
from .file_builder import FileBuilder

_test_data_dir = Path(__file__).parent.parent / "data"
_xml_dir = _test_data_dir / "generated" / "xml"


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
    return Path(__file__).parent.parent / "data" / "generated" / "xml" / doxygen_version


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
    return _test_data_dir / "adoc"


@pytest.fixture
def test_data():
    return _test_data_dir


@pytest.fixture
def build_dir(tmp_path):
    d = tmp_path / "build"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def package_manager(build_dir):
    mgr = PackageManager(build_dir)
    mgr.work_dir.mkdir(parents=True, exist_ok=True)
    return mgr


@pytest.fixture
def original_dir(tmp_path):
    d = tmp_path / "original"
    d.mkdir(parents=True)
    return d


@pytest.fixture
def original_file(original_dir, package_manager):
    f = original_dir / "input_file.adoc"
    f.touch()
    package_manager.set_input_files(f, include_dir=original_dir)
    return f


@pytest.fixture
def work_dir(package_manager):
    return package_manager.work_dir


@pytest.fixture
def work_file(original_file, work_dir):
    f = work_dir / "input_file.adoc"
    f.touch()
    return f


@pytest.fixture
def document(package_manager, original_file, work_file):
    return Document(Path("input_file.adoc"), package_manager.input_package(),
                    package_manager.work_dir)


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
def default_config(document, build_dir):
    config = Configuration()
    config.input_file = document.original_file
    config.build_dir = build_dir
    config.destination_dir = build_dir / "output"
    config.cache_dir = build_dir / "cache"
    config.backend = "html5"
    config.warnings_are_errors = False
    config.debug = False
    config.log_level = "INFO"
    config.multipage = False
    config.safe_mode = "unsafe"
    config.attribute = []
    config.doctype = None
    config.require = []
    config.failure_level = "FATAL"
    return config


@pytest.fixture
def context(document, api_reference, package_manager, default_config):
    c = Context(reference=api_reference,
                package_manager=package_manager,
                document=document,
                config=default_config)
    return c


@pytest.fixture
def preprocessing_api(context):
    return PreprocessingApi(context)


@pytest.fixture
def generating_api(context):
    return GeneratingApi(context)


@pytest.fixture
def cpp_class():
    builder = SimpleClassBuilder("cpp")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("variable", "enum", "class", "typedef", "struct", "trash", "enumvalue",
                            "alias"):
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

    return builder.compound


@pytest.fixture
def warnings_are_errors(default_config):
    default_config.warnings_are_errors = True
    return True


@pytest.fixture(params=[True, False], ids=["warnings-are-errors", "warnings-are-not-errors"])
def warnings_are_and_are_not_errors(request, default_config):
    default_config.warnings_are_errors = request.param
    return request.param


@pytest.fixture
def multipage(default_config):
    default_config.multipage = True
    return True


@pytest.fixture(params=[True, False], ids=["multi-page", "single-page"])
def single_and_multipage(request, default_config):
    default_config.multipage = request.param
    return request.param


@pytest.fixture
def empty_context(document, package_manager, default_config):
    return Context(reference=ApiReference(),
                   package_manager=package_manager,
                   document=document,
                   config=default_config)


@pytest.fixture
def empty_preprocessing_api(empty_context):
    return PreprocessingApi(empty_context)


@pytest.fixture
def empty_generating_api(empty_context):
    return GeneratingApi(empty_context)


@pytest.fixture
def file_builder(tmp_path, build_dir):
    return FileBuilder(tmp_path, build_dir)


@pytest.fixture
def document_tree(tmp_path):
    # Test tree:
    #
    #       root
    #        /|\
    #       / | \
    #      /  |  \
    #     /   |   \
    #    a    b    c
    #    /\        /\
    #   /  \      /  \
    # a_a  a_b  c_a  c_b
    #      / \
    #     /   \
    #    /     \
    #  a_b_a  a_b_b
    #
    # Special embedded files:
    # a_a_emb -> embedded in a_a
    # c_emb -> embedded in c, c_a, c_b
    # c_emb_emb -> embedded in c_emb
    pkg_dir = tmp_path / "pkg"
    work_dir = tmp_path / "work"
    pkg = Package("my-package")
    pkg.adoc_src_dir = pkg_dir

    root = Document(Path("root.adoc"), pkg, work_dir)
    root.is_root = True
    tree = {"root": root}

    def add(name, included_in=None, embedded_in=None):
        doc = root.with_relative_path(f"{name}.adoc")
        if included_in:
            tree[included_in].include(doc)
        if embedded_in:
            tree[embedded_in].embed(doc)
        tree[name] = doc

    add("a", included_in="root")
    add("b", included_in="root")
    add("c", included_in="root")
    add("a/a_a", included_in="a")
    add("a/a_b", included_in="a")
    add("c/c_a", included_in="c")
    add("c/c_b", included_in="c")
    add("a/b/a_b_a", included_in="a/a_b")
    add("a/b/a_b_b", included_in="a/a_b")

    add("a/a/a_a_emb", embedded_in="a/a_a")
    add("c/c_emb", embedded_in="c")
    tree["c/c_a"].embed(tree["c/c_emb"])
    tree["c/c_b"].embed(tree["c/c_emb"])
    add("c/c_emb_emb", embedded_in="c/c_emb")

    return tree


_custom_types = {
    Compound: ([
        "id",
        "name",
        "full_name",
        "language",
        "kind",
        "include",
        "namespace",
        "prot",
        "definition",
        "args",
        "initializer",
        "brief",
        "description",
        "sections",
        "static",
        "const",
        "deleted",
        "default",
        "constexpr",
    ], ["members", "params", "exceptions", "returns"]),
    TypeRef: (["id", "name", "language", "namespace", "kind", "prefix",
               "suffix"], ["nested", "args", "returns"]),
    Parameter: (["name", "description", "default_value", "prefix"], ["type"]),
    ReturnValue: (["description"], ["type"]),
    ThrowsClause: (["description"], ["type"]),
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
