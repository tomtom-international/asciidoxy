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
"""Tests for C++ type parsing."""

import xml.etree.ElementTree as ET

import pytest

from asciidoxy.parser.doxygen.cpp import CppTypeParser
from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.type_parser import Token, TypeParseError
from tests.unit.matchers import IsEmpty, IsNone, m_parameter, m_typeref
from tests.unit.shared import sub_element

from .test_type_parser import arg_name, args_end, args_start, name, whitespace


@pytest.fixture(params=[
    "", "const ", "volatile ", "mutable ", "enum ", "class ", "const class ",
    "mutable volatile enum ", "typename "
])
def cpp_type_prefix(request):
    return request.param


@pytest.fixture(params=["", " *", " &", " **", " * *", " const *", " * const *"])
def cpp_type_suffix(request):
    return request.param


def test_parse_cpp_type_from_text_simple(driver_mock, cpp_type_prefix, cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}double{cpp_type_suffix}"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="cpp",
        name="double",
        prefix=cpp_type_prefix,
        suffix=cpp_type_suffix,
        nested=IsEmpty(),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


def test_parse_cpp_type_from_text_nested_with_prefix_and_suffix(driver_mock, cpp_type_prefix,
                                                                cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = (f"{cpp_type_prefix}Coordinate< {cpp_type_prefix}Unit{cpp_type_suffix} "
                         f">{cpp_type_suffix}")

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="cpp",
        name="Coordinate",
        prefix=cpp_type_prefix,
        suffix=cpp_type_suffix,
        nested=[
            m_typeref(
                id=IsNone(),
                kind=IsNone(),
                language="cpp",
                name="Unit",
                prefix=cpp_type_prefix,
                suffix=cpp_type_suffix,
                nested=IsEmpty(),
            ),
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("Coordinate", "Unit")


def test_parse_cpp_type_from_ref_with_prefix_and_suffix(driver_mock, cpp_type_prefix,
                                                        cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = cpp_type_prefix
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=cpp_type_suffix)

    m_typeref(
        id="cpp-tomtom_coordinate",
        kind="compound",
        language="cpp",
        name="Coordinate",
        prefix=cpp_type_prefix,
        suffix=cpp_type_suffix,
        nested=IsEmpty(),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # has_id, so not unresolved


def test_parse_cpp_type_from_ref_with_nested_text_type(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail="< const Unit > &")

    m_typeref(
        id="cpp-tomtom_coordinate",
        kind="compound",
        language="cpp",
        name="Coordinate",
        prefix="const ",
        suffix=" &",
        nested=[
            m_typeref(
                id=IsNone(),
                kind=IsNone(),
                language="cpp",
                name="Unit",
                prefix="const ",
                suffix=IsEmpty(),
            )
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("Unit")


def test_parse_cpp_type_from_text_with_nested_ref_type(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "const std::unique_ptr< const "
    sub_element(type_element,
                "ref",
                refid="tomtom_coordinate",
                kindref="compound",
                text="Coordinate",
                tail=" & > *")

    m_typeref(
        id=IsEmpty(),
        kind=IsEmpty(),
        language="cpp",
        name="std::unique_ptr",
        prefix="const ",
        suffix=" *",
        nested=[
            m_typeref(
                id="cpp-tomtom_coordinate",
                kind="compound",
                language="cpp",
                name="Coordinate",
                prefix="const ",
                suffix=" &",
            ),
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # has id, so not unresolved


def test_parse_cpp_type_from_multiple_nested_text_and_ref(driver_mock):
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

    m_typeref(
        id="cpp-tomtom_coordinate",
        kind="compound",
        language="cpp",
        name="Coordinate",
        prefix="const ",
        suffix=IsEmpty(),
        nested=[
            m_typeref(
                id=IsEmpty(),
                kind=IsEmpty(),
                language="cpp",
                name="std::unique_ptr",
                prefix=IsEmpty(),
                suffix=IsEmpty(),
                nested=[
                    m_typeref(
                        id="cpp-tomtom_box",
                        kind="compound",
                        language="cpp",
                        name="Box",
                        prefix=IsEmpty(),
                        suffix=IsEmpty(),
                        nested=IsEmpty(),
                    ),
                ],
            ),
            m_typeref(
                id="cpp-tomtom_point",
                kind="compound",
                language="cpp",
                name="Point",
                prefix=IsEmpty(),
                suffix=IsEmpty(),
                nested=[
                    m_typeref(
                        id=IsEmpty(),
                        kind=IsEmpty(),
                        language="cpp",
                        name="std::string",
                        prefix="const ",
                        suffix=" &",
                        nested=IsEmpty(),
                    ),
                ],
            ),
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # has id, so not unresolved


def test_parse_cpp_type_multiple_prefix_and_suffix(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "mutable volatile std::string * const *"

    m_typeref(
        id=IsEmpty(),
        kind=IsEmpty(),
        language="cpp",
        name="std::string",
        prefix="mutable volatile ",
        suffix=" * const *",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


@pytest.fixture(params=[
    "short int", "signed short", "signed short int", "unsigned short", "unsigned short int",
    "signed int", "signed", "unsigned", "unsigned int", "long int", "signed long",
    "signed long int", "unsigned long", "unsigned long int", "long long", "long long int",
    "signed long long", "signed long long int", "unsigned long long", "unsigned long long int",
    "signed char", "long double"
])
def cpp_type_with_space(request):
    return request.param


def test_parse_cpp_type_with_space(driver_mock, cpp_type_prefix, cpp_type_with_space,
                                   cpp_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{cpp_type_prefix}{cpp_type_with_space}{cpp_type_suffix}"

    m_typeref(
        id=IsEmpty(),
        kind=IsEmpty(),
        language="cpp",
        name=cpp_type_with_space,
        prefix=cpp_type_prefix,
        suffix=cpp_type_suffix,
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


def test_parse_cpp_type_with_member(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType<NestedType>::member"

    m_typeref(
        id=IsEmpty(),
        kind=IsEmpty(),
        language="cpp",
        name="MyType",
        prefix=IsEmpty(),
        suffix="::member",
        nested=[
            m_typeref(
                name="NestedType",
                prefix=IsEmpty(),
                suffix=IsEmpty(),
                nested=IsEmpty(),
            ),
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType", "NestedType")


def test_parse_cpp_type_with_function_arguments(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType(const Message&, ErrorCode code)"

    m_typeref(
        id=IsEmpty(),
        kind="closure",
        language="cpp",
        name=IsEmpty(),
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=IsEmpty(),
        args=[
            m_parameter(
                name=IsEmpty(),
                type=m_typeref(
                    name="Message",
                    prefix="const ",
                    suffix="&",
                    nested=IsEmpty(),
                ),
            ),
            m_parameter(
                name="code",
                type=m_typeref(
                    name="ErrorCode",
                    prefix=IsEmpty(),
                    suffix=IsEmpty(),
                    nested=IsEmpty(),
                ),
            ),
        ],
        returns=m_typeref(
            id=IsEmpty(),
            kind=IsEmpty(),
            name="MyType",
            prefix=IsEmpty(),
            suffix=IsEmpty(),
            nested=IsEmpty(),
            args=IsEmpty(),
        ),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType", "Message", "ErrorCode")


def test_parse_cpp_type_with_function_arguments__with_prefix_and_suffix(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "const MyType&(const Message&, ErrorCode code)"

    m_typeref(
        id=IsEmpty(),
        kind="closure",
        language="cpp",
        name=IsEmpty(),
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=IsEmpty(),
        args=[
            m_parameter(
                name=IsEmpty(),
                type=m_typeref(
                    name="Message",
                    prefix="const ",
                    suffix="&",
                    nested=IsEmpty(),
                ),
            ),
            m_parameter(
                name="code",
                type=m_typeref(
                    name="ErrorCode",
                    prefix=IsEmpty(),
                    suffix=IsEmpty(),
                    nested=IsEmpty(),
                ),
            ),
        ],
        returns=m_typeref(
            id=IsEmpty(),
            kind=IsEmpty(),
            language="cpp",
            name="MyType",
            prefix="const ",
            suffix="&",
            nested=IsEmpty(),
            args=IsEmpty(),
        ),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType", "Message", "ErrorCode")


@pytest.mark.parametrize("arg_name", ["", " value"])
def test_parse_cpp_type_with_function_arguments_with_space_in_type(driver_mock, cpp_type_with_space,
                                                                   arg_name):
    type_element = ET.Element("type")
    type_element.text = f"MyType({cpp_type_with_space}{arg_name})"

    m_typeref(
        id=IsEmpty(),
        kind="closure",
        language="cpp",
        name=IsEmpty(),
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=IsEmpty(),
        args=[
            m_parameter(
                name=arg_name.strip(),
                type=m_typeref(
                    name=cpp_type_with_space,
                    prefix=IsEmpty(),
                    suffix=IsEmpty(),
                    nested=IsEmpty(),
                    args=IsEmpty(),
                ),
            ),
        ],
        returns=m_typeref(
            name="MyType",
            prefix=IsEmpty(),
            suffix=IsEmpty(),
            nested=IsEmpty(),
            args=IsEmpty(),
        ),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_cpp_type__remove_constexpr(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "constexpr double"

    m_typeref(
        id=IsEmpty(),
        kind=IsEmpty(),
        language="cpp",
        name="double",
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=IsEmpty(),
        args=IsEmpty(),
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


def test_parse_cpp_type__remove_constexpr_only(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "constexpr"

    assert CppTypeParser.parse_xml(type_element, driver=driver_mock) is None
    driver_mock.assert_unresolved()  # nothing left


def test_parse_cpp_type__array(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType[]"

    m_typeref(
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_cpp_type__array__with_size(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType[16]"

    m_typeref(
        name="MyType",
        prefix=IsEmpty(),
        suffix="[16]",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_cpp_type__array__with_prefix_and_suffix(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "const MyType[]*"

    m_typeref(
        name="MyType",
        prefix="const ",
        suffix="[]*",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_cpp_type__array__as_nested_type(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "std::shared_ptr<MyType[]>"

    m_typeref(
        name="std::shared_ptr",
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=[
            m_typeref(
                name="MyType",
                prefix=IsEmpty(),
                suffix="[]",
            ),
        ],
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_cpp_type__array__brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[]")
    ET.dump(type_element)

    m_typeref(
        id="cpp-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_cpp_type__array__multiple_brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[][]")
    ET.dump(type_element)

    m_typeref(
        id="cpp-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[][]",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_cpp_type__array__with_size_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[12]")
    ET.dump(type_element)

    m_typeref(
        id="cpp-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[12]",
    ).assert_matches(CppTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_cpp_type__array__end_bracket_without_start_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType]")
    ET.dump(type_element)

    with pytest.raises(TypeParseError):
        CppTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.assert_unresolved()


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
