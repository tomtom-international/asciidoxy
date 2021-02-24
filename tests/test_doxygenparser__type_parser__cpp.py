# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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
"""Tests for C++ type parsing."""

import pytest

import xml.etree.ElementTree as ET

from unittest.mock import MagicMock

from asciidoxy.parser.doxygen.cpp import CppTypeParser
from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.type_parser import Token
from tests.shared import assert_equal_or_none_if_empty, sub_element
from .test_doxygenparser__type_parser import name, args_start, whitespace, args_end, arg_name


@pytest.fixture(params=[
    "", "const ", "volatile ", "mutable ", "enum ", "class ", "const class ",
    "mutable volatile enum "
])
def cpp_type_prefix(request):
    return request.param


@pytest.fixture(params=["", " *", " &", " **", " * *", " const *", " * const *"])
def cpp_type_suffix(request):
    return request.param


def test_parse_cpp_type_from_text_simple(cpp_type_prefix, cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}double{cpp_type_suffix}"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "cpp"
    assert type_ref.name == "double"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)
    assert not type_ref.nested


def test_parse_cpp_type_from_text_nested_with_prefix_and_suffix(cpp_type_prefix, cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = (f"{cpp_type_prefix}Coordinate< {cpp_type_prefix}Unit{cpp_type_suffix} "
                         f">{cpp_type_suffix}")

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)

    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["Coordinate", "Unit"]))

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id is None
    assert nested_ref.kind is None
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Unit"
    assert_equal_or_none_if_empty(nested_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(nested_ref.suffix, cpp_type_suffix)


def test_parse_cpp_type_from_ref_with_prefix_and_suffix(cpp_type_prefix, cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = cpp_type_prefix
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=cpp_type_suffix)

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # has id, so not unresolved

    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)
    assert not type_ref.nested


def test_parse_cpp_type_from_ref_with_nested_text_type():
    type_element = ET.Element("type")
    type_element.text = "const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail="< const Unit > &")

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    assert (sorted([args[0].name
                    for args, _ in driver_mock.unresolved_ref.call_args_list]) == sorted(["Unit"]))

    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert type_ref.prefix == "const "
    assert type_ref.suffix == " &"

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id is None
    assert nested_ref.kind is None
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Unit"
    assert nested_ref.prefix == "const "
    assert not nested_ref.suffix


def test_parse_cpp_type_from_text_with_nested_ref_type():
    type_element = ET.Element("type")
    type_element.text = "const std::unique_ptr< const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=" & > *")

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # has id, so not unresolved

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == "std::unique_ptr"
    assert type_ref.prefix == "const "
    assert type_ref.suffix == " *"

    assert len(type_ref.nested) == 1
    nested_ref = type_ref.nested[0]
    assert nested_ref is not None
    assert nested_ref.id == "cpp-tomtom_coordinate"
    assert nested_ref.kind == "compound"
    assert nested_ref.language == "cpp"
    assert nested_ref.name == "Coordinate"
    assert nested_ref.prefix == "const "
    assert nested_ref.suffix == " &"


def test_parse_cpp_type_from_multiple_nested_text_and_ref():
    type_element = ET.Element("type")
    type_element.text = "const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=" < std::unique_ptr< ")
    sub_element(type_element,
                "ref",
                refid="tomtom_box",
                kindref="compound",
                text="Box",
                tail=" >, ")
    sub_element(type_element,
                "ref",
                refid="tomtom_point",
                kindref="compound",
                text="Point",
                tail=" < const std::string & > >")

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # has id, so not unresolved

    assert type_ref is not None
    assert type_ref.id == "cpp-tomtom_coordinate"
    assert type_ref.kind == "compound"
    assert type_ref.language == "cpp"
    assert type_ref.name == "Coordinate"
    assert type_ref.prefix == "const "
    assert not type_ref.suffix

    assert len(type_ref.nested) == 2
    nested_1 = type_ref.nested[0]
    assert nested_1 is not None
    assert not nested_1.id
    assert not nested_1.kind
    assert nested_1.language == "cpp"
    assert nested_1.name == "std::unique_ptr"
    assert not nested_1.prefix
    assert not nested_1.suffix

    assert len(nested_1.nested) == 1
    nested_1_1 = nested_1.nested[0]
    assert nested_1_1 is not None
    assert nested_1_1.id == "cpp-tomtom_box"
    assert nested_1_1.kind == "compound"
    assert nested_1_1.language == "cpp"
    assert nested_1_1.name == "Box"
    assert not nested_1_1.prefix
    assert not nested_1_1.suffix

    nested_2 = type_ref.nested[1]
    assert nested_2 is not None
    assert nested_2.id == "cpp-tomtom_point"
    assert nested_2.kind == "compound"
    assert nested_2.language == "cpp"
    assert nested_2.name == "Point"
    assert not nested_2.prefix
    assert not nested_2.suffix

    assert len(nested_2.nested) == 1
    nested_2_1 = nested_2.nested[0]
    assert nested_2_1 is not None
    assert not nested_2_1.id
    assert not nested_2_1.kind
    assert nested_2_1.language == "cpp"
    assert nested_2_1.name == "std::string"
    assert nested_2_1.prefix == "const "
    assert nested_2_1.suffix == " &"


def test_parse_cpp_type_multiple_prefix_and_suffix():
    type_element = ET.Element("type")
    type_element.text = "mutable volatile std::string * const *"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == "std::string"
    assert type_ref.prefix == "mutable volatile "
    assert type_ref.suffix == " * const *"


@pytest.fixture(params=[
    "short int", "signed short", "signed short int", "unsigned short", "unsigned short int",
    "signed int", "signed", "unsigned", "unsigned int", "long int", "signed long",
    "signed long int", "unsigned long", "unsigned long int", "long long", "long long int",
    "signed long long", "signed long long int", "unsigned long long", "unsigned long long int",
    "signed char", "long double"
])
def cpp_type_with_space(request):
    return request.param


def test_parse_cpp_type_with_space(cpp_type_prefix, cpp_type_with_space, cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}{cpp_type_with_space}{cpp_type_suffix}"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == cpp_type_with_space
    assert_equal_or_none_if_empty(type_ref.prefix, cpp_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, cpp_type_suffix)


def test_parse_cpp_type_with_member():
    type_element = ET.Element("type")
    type_element.text = "MyType<NestedType>::member"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["MyType", "NestedType"]))

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "cpp"
    assert type_ref.name == "MyType"
    assert not type_ref.prefix
    assert type_ref.suffix == "::member"
    assert len(type_ref.nested) == 1

    assert type_ref.nested[0].name == "NestedType"
    assert not type_ref.nested[0].prefix
    assert not type_ref.nested[0].suffix
    assert not type_ref.nested[0].nested


def test_parse_cpp_type_with_function_arguments():
    type_element = ET.Element("type")
    type_element.text = "MyType(const Message&, ErrorCode code)"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["MyType", "Message", "ErrorCode"]))

    assert type_ref is not None
    assert not type_ref.id
    assert type_ref.kind == "closure"
    assert type_ref.language == "cpp"
    assert not type_ref.name
    assert not type_ref.prefix
    assert not type_ref.suffix
    assert not type_ref.nested
    assert len(type_ref.args) == 2

    assert type_ref.returns is not None
    assert not type_ref.returns.id
    assert not type_ref.returns.kind
    assert type_ref.returns.language == "cpp"
    assert type_ref.returns.name == "MyType"
    assert not type_ref.returns.prefix
    assert not type_ref.returns.suffix
    assert not type_ref.returns.nested
    assert not type_ref.returns.args

    assert not type_ref.args[0].name
    assert type_ref.args[0].type.name == "Message"
    assert type_ref.args[0].type.prefix == "const "
    assert type_ref.args[0].type.suffix == "&"
    assert not type_ref.args[0].type.nested

    assert type_ref.args[1].name == "code"
    assert type_ref.args[1].type.name == "ErrorCode"
    assert not type_ref.args[1].type.prefix
    assert not type_ref.args[1].type.suffix
    assert not type_ref.args[1].type.nested


def test_parse_cpp_type_with_function_arguments__with_prefix_and_suffix():
    type_element = ET.Element("type")
    type_element.text = "const MyType&(const Message&, ErrorCode code)"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["MyType", "Message", "ErrorCode"]))

    assert type_ref is not None
    assert not type_ref.id
    assert type_ref.kind == "closure"
    assert type_ref.language == "cpp"
    assert not type_ref.name
    assert not type_ref.prefix
    assert not type_ref.suffix
    assert not type_ref.nested
    assert len(type_ref.args) == 2

    assert type_ref.returns is not None
    assert not type_ref.returns.id
    assert not type_ref.returns.kind
    assert type_ref.returns.language == "cpp"
    assert type_ref.returns.name == "MyType"
    assert type_ref.returns.prefix == "const "
    assert type_ref.returns.suffix == "&"
    assert not type_ref.returns.nested
    assert not type_ref.returns.args

    assert not type_ref.args[0].name
    assert type_ref.args[0].type.name == "Message"
    assert type_ref.args[0].type.prefix == "const "
    assert type_ref.args[0].type.suffix == "&"
    assert not type_ref.args[0].type.nested

    assert type_ref.args[1].name == "code"
    assert type_ref.args[1].type.name == "ErrorCode"
    assert not type_ref.args[1].type.prefix
    assert not type_ref.args[1].type.suffix
    assert not type_ref.args[1].type.nested


@pytest.mark.parametrize("arg_name", ["", " value"])
def test_parse_cpp_type_with_function_arguments_with_space_in_type(cpp_type_with_space, arg_name):
    type_element = ET.Element("type")
    type_element.text = f"MyType({cpp_type_with_space}{arg_name})"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["MyType"]))

    assert type_ref is not None
    assert not type_ref.id
    assert type_ref.kind == "closure"
    assert type_ref.language == "cpp"
    assert not type_ref.name
    assert not type_ref.prefix
    assert not type_ref.suffix
    assert not type_ref.nested
    assert len(type_ref.args) == 1

    assert type_ref.returns is not None
    assert type_ref.returns.name == "MyType"
    assert not type_ref.returns.prefix
    assert not type_ref.returns.suffix
    assert not type_ref.returns.nested
    assert not type_ref.returns.args

    assert_equal_or_none_if_empty(type_ref.args[0].name, arg_name.strip())
    assert type_ref.args[0].type.name == cpp_type_with_space
    assert not type_ref.args[0].type.prefix
    assert not type_ref.args[0].type.suffix
    assert not type_ref.args[0].type.nested


def test_parse_cpp_type__remove_constexpr():
    type_element = ET.Element("type")
    type_element.text = "constexpr double"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "cpp"
    assert type_ref.name == "double"
    assert not type_ref.prefix
    assert not type_ref.suffix
    assert not type_ref.nested


def test_parse_cpp_type__remove_constexpr_only():
    type_element = ET.Element("type")
    type_element.text = "constexpr"

    driver_mock = MagicMock()
    type_ref = CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is None


def namespace_sep(text: str = ":") -> Token:
    return Token(text, TokenCategory.NAMESPACE_SEPARATOR)


@pytest.mark.parametrize("tokens, expected", [
    ([], []),
    ([
        name("Type"),
        args_start(),
        name("ArgType"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("ArgType"),
        args_end(),
    ]),
    ([
        name("Type"),
        args_start(),
        name("ArgType"),
        whitespace(),
        name("arg"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("ArgType"),
        whitespace(),
        arg_name("arg"),
        args_end(),
    ]),
    ([
        name("Type"),
        args_start(),
        name("std"),
        namespace_sep(),
        namespace_sep(),
        name("vector"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("std"),
        namespace_sep(),
        namespace_sep(),
        name("vector"),
        args_end(),
    ]),
    ([
        name("Type"),
        args_start(),
        name("std"),
        namespace_sep(),
        namespace_sep(),
        name("vector"),
        whitespace(),
        name("list"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("std"),
        namespace_sep(),
        namespace_sep(),
        name("vector"),
        whitespace(),
        arg_name("list"),
        args_end(),
    ]),
])
def test_cpp_type_parser__adapt_tokens(tokens, expected):
    assert CppTypeParser.adapt_tokens(tokens) == expected
