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
"""Tests for parsing Objective C types."""

import xml.etree.ElementTree as ET

import pytest

from asciidoxy.parser.doxygen.language_traits import TokenCategory
from asciidoxy.parser.doxygen.objc import ObjectiveCTypeParser
from asciidoxy.parser.doxygen.type_parser import Token, TypeParseError
from tests.unit.matchers import IsEmpty, IsNone, m_typeref
from tests.unit.shared import sub_element

from .test_type_parser import (
    arg_name,
    args_end,
    args_sep,
    args_start,
    name,
    operator,
    qualifier,
    sep,
    whitespace,
)


@pytest.fixture(params=[
    "",
    "nullable ",
    "const ",
    "__weak ",
    "__strong ",
    "nullable __weak ",
    "nullable __strong ",
    "_Nonnull ",
    "_Nullable ",
    "__nonnull ",
])
def objc_type_prefix(request):
    return request.param


@pytest.fixture(
    params=["", " *", " **", " * *", " * _Nonnull", " * _Nullable", "*_Nonnull*__autoreleasing"])
def objc_type_suffix(request):
    return request.param


def test_parse_objc_type_from_text_simple(driver_mock, objc_type_prefix, objc_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{objc_type_prefix}NSInteger{objc_type_suffix}"

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="objc",
        name="NSInteger",
        prefix=objc_type_prefix,
        suffix=objc_type_suffix,
        nested=IsEmpty(),
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


@pytest.mark.parametrize("type_with_space", [
    "short int",
    "signed short",
    "signed short int",
    "unsigned short",
    "unsigned short int",
    "signed int",
    "unsigned int",
    "long int",
    "signed long",
    "signed long int",
    "unsigned long",
    "unsigned long int",
    "long long",
    "long long int",
    "signed long long",
    "signed long long int",
    "unsigned long long",
    "unsigned long long int",
    "signed char",
    "long double",
    "unsigned char",
    "signed char",
])
def test_parse_objc_type_with_space(driver_mock, type_with_space):
    type_element = ET.Element("type")
    type_element.text = type_with_space

    m_typeref(
        id=IsNone(),
        kind=IsNone(),
        language="objc",
        name=type_with_space,
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=IsEmpty(),
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()  # built-in type


def test_parse_objc_type__array(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType[]"

    m_typeref(
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_objc_type__array__with_size(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "MyType[16]"

    m_typeref(
        name="MyType",
        prefix=IsEmpty(),
        suffix="[16]",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_objc_type__array__with_prefix_and_suffix(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "const MyType[]*"

    m_typeref(
        name="MyType",
        prefix="const ",
        suffix="[]*",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_objc_type__array__as_nested_type(driver_mock):
    type_element = ET.Element("type")
    type_element.text = "id<MyType[]>"

    m_typeref(
        name="id",
        prefix=IsEmpty(),
        suffix=IsEmpty(),
        nested=[
            m_typeref(
                name="MyType",
                prefix=IsEmpty(),
                suffix="[]",
            ),
        ],
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved("MyType")


def test_parse_objc_type__array__brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[]")
    ET.dump(type_element)

    m_typeref(
        id="objc-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[]",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_objc_type__array__multiple_brackets_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[][]")
    ET.dump(type_element)

    m_typeref(
        id="objc-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[][]",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_objc_type__array__with_size_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType[12]")
    ET.dump(type_element)

    m_typeref(
        id="objc-tomtom_mytype",
        name="MyType",
        prefix=IsEmpty(),
        suffix="[12]",
    ).assert_matches(ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock))
    driver_mock.assert_unresolved()


def test_parse_objc_type__array__end_bracket_without_start_inside_name_element(driver_mock):
    type_element = ET.Element("type")
    sub_element(type_element, "ref", refid="tomtom_mytype", kindref="compound", text="MyType]")
    ET.dump(type_element)

    with pytest.raises(TypeParseError):
        ObjectiveCTypeParser.parse_xml(type_element, driver=driver_mock)
    driver_mock.assert_unresolved()


def block(text: str = "^") -> Token:
    return Token(text, TokenCategory.BLOCK)


@pytest.mark.parametrize("tokens, expected", [
    ([], []),
    ([
        qualifier("nullable"),
        whitespace(),
        name("Type"),
        whitespace(),
        operator("*"),
    ], [
        qualifier("nullable"),
        whitespace(),
        name("Type"),
        whitespace(),
        operator("*"),
    ]),
    ([
        name("Type"),
        whitespace(),
        name("value"),
    ], [
        name("Type"),
        whitespace(),
        name("value"),
    ]),
    ([
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        name("value"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        arg_name("value"),
        args_end(),
    ]),
    ([
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        operator("*"),
        name("value"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        operator("*"),
        arg_name("value"),
        args_end(),
    ]),
    ([
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        operator("*"),
        name("value"),
        sep(),
        name("CoolType"),
        whitespace(),
        qualifier("nullable"),
        whitespace(),
        name("null_value"),
        args_end(),
    ], [
        name("Type"),
        args_start(),
        name("OtherType"),
        whitespace(),
        operator("*"),
        arg_name("value"),
        args_sep(),
        name("CoolType"),
        whitespace(),
        qualifier("nullable"),
        whitespace(),
        arg_name("null_value"),
        args_end(),
    ]),
    ([
        name("void"),
        args_start(),
        block(),
        args_end(),
        args_start(),
        name("NSString"),
        whitespace(),
        operator("*"),
        name("text"),
        args_end(),
    ], [
        name("void"),
        args_start(),
        name("NSString"),
        whitespace(),
        operator("*"),
        arg_name("text"),
        args_end(),
    ]),
],
                         ids=lambda ts: "".join(t.text for t in ts))
def test_objc_type_parser__adapt_tokens(tokens, expected):
    assert ObjectiveCTypeParser.adapt_tokens(tokens) == expected
