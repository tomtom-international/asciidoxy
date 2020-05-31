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
"""General tests for type parsing."""

import pytest

import xml.etree.ElementTree as ET

from typing import List, NamedTuple, Optional

from asciidoxy.doxygenparser.type_parser import (Token, Tokenizer, TokenType, TypeProducer,
                                                 TypeParseError)
from .shared import sub_element


def whitespace(text: str) -> Token:
    return Token(text, TokenType.WHITESPACE)


def qualifier(text: str) -> Token:
    return Token(text, TokenType.QUALIFIER)


def operator(text: str) -> Token:
    return Token(text, TokenType.OPERATOR)


def name(text: str) -> Token:
    return Token(text, TokenType.NAME)


def nested_start(text: str) -> Token:
    return Token(text, TokenType.NESTED_START)


def nested_end(text: str) -> Token:
    return Token(text, TokenType.NESTED_END)


def nested_sep(text: str) -> Token:
    return Token(text, TokenType.NESTED_SEPARATOR)


def ref(text: str, refid: str, kind: Optional[str] = None) -> Token:
    return Token(text, refid=refid, type_=TokenType.NAME, kind=kind)


@pytest.mark.parametrize("text,tokens", [
    ("MyType", [name("MyType")]),
    ("const MyType", [qualifier("const"), whitespace(" "),
                      name("MyType")]),
    ("MyType<OtherType>",
     [name("MyType"), nested_start("<"),
      name("OtherType"), nested_end(">")]),
    ("const MyType<OtherType>&", [
        qualifier("const"),
        whitespace(" "),
        name("MyType"),
        nested_start("<"),
        name("OtherType"),
        nested_end(">"),
        operator("&")
    ]),
    ("const MyType<OtherType> &", [
        qualifier("const"),
        whitespace(" "),
        name("MyType"),
        nested_start("<"),
        name("OtherType"),
        nested_end(">"),
        whitespace(" "),
        operator("&")
    ]),
    ("const * const MyType", [
        qualifier("const"),
        whitespace(" "),
        operator("*"),
        whitespace(" "),
        qualifier("const"),
        whitespace(" "),
        name("MyType")
    ]),
    ("const* const MyType", [
        qualifier("const"),
        operator("*"),
        whitespace(" "),
        qualifier("const"),
        whitespace(" "),
        name("MyType")
    ]),
    ("MyType*", [name("MyType"), operator("*")]),
    ("MyType *", [name("MyType"), whitespace(" "), operator("*")]),
    ("MyType <OtherType>",
     [name("MyType"),
      whitespace(" "),
      nested_start("<"),
      name("OtherType"),
      nested_end(">")]),
    ("MyType < OtherType >", [
        name("MyType"),
        whitespace(" "),
        nested_start("<"),
        whitespace(" "),
        name("OtherType"),
        whitespace(" "),
        nested_end(">")
    ]),
    ("MyType  <  OtherType  >", [
        name("MyType"),
        whitespace("  "),
        nested_start("<"),
        whitespace("  "),
        name("OtherType"),
        whitespace("  "),
        nested_end(">")
    ]),
    ("const MyType<const OtherType> &", [
        qualifier("const"),
        whitespace(" "),
        name("MyType"),
        nested_start("<"),
        qualifier("const"),
        whitespace(" "),
        name("OtherType"),
        nested_end(">"),
        whitespace(" "),
        operator("&")
    ]),
    ("const MyType<const OtherType, YetAnotherType&> &", [
        qualifier("const"),
        whitespace(" "),
        name("MyType"),
        nested_start("<"),
        qualifier("const"),
        whitespace(" "),
        name("OtherType"),
        nested_sep(","),
        whitespace(" "),
        name("YetAnotherType"),
        operator("&"),
        nested_end(">"),
        whitespace(" "),
        operator("&")
    ]),
    ("MyType<const OtherType, <YetAnotherType&,const OtherType>> &", [
        name("MyType"),
        nested_start("<"),
        qualifier("const"),
        whitespace(" "),
        name("OtherType"),
        nested_sep(","),
        whitespace(" "),
        nested_start("<"),
        name("YetAnotherType"),
        operator("&"),
        nested_sep(","),
        qualifier("const"),
        whitespace(" "),
        name("OtherType"),
        nested_end(">"),
        nested_end(">"),
        whitespace(" "),
        operator("&")
    ]),
])
def test_tokenizer__tokenize_text(text, tokens):
    assert Tokenizer.tokenize_text(text) == tokens


def test_tokenizer__tokenize_xml__text_only():
    element = ET.Element("type")
    element.text = "const MyType&"
    assert Tokenizer.tokenize_xml(element) == [
        qualifier("const"), whitespace(" "),
        name("MyType"), operator("&")
    ]


def test_tokenizer__tokenize_xml__simple_element():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type", kind="compound")
    assert Tokenizer.tokenize_xml(element) == [
        ref("MyType", refid="my_type", kind="compound"),
    ]


def test_tokenizer__tokenize_xml__simple_element__kind_is_optional():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type")
    assert Tokenizer.tokenize_xml(element) == [
        ref("MyType", refid="my_type"),
    ]


def test_tokenizer__tokenize_xml__prefix_suffix():
    element = ET.Element("type")
    element.text = "const "
    sub_element(element, "ref", text="MyType", refid="my_type", kind="compound", tail=" *")
    assert Tokenizer.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(" "),
        ref("MyType", refid="my_type", kind="compound"),
        whitespace(" "),
        operator("*"),
    ]


def test_tokenizer__tokenize_xml__text_type_with_nested_xml():
    element = ET.Element("type")
    element.text = "const MyType<"
    sub_element(element, "ref", text="OtherType", refid="other_type", kind="compound", tail=">")
    assert Tokenizer.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(" "),
        name("MyType"),
        nested_start("<"),
        ref("OtherType", refid="other_type", kind="compound"),
        nested_end(">"),
    ]


def test_tokenizer__tokenize_xml__xml_type_with_nested_xml_and_text():
    element = ET.Element("type")
    element.text = "const "
    sub_element(element,
                "ref",
                text="MyType",
                refid="my_type",
                kind="compound",
                tail="<NestedType, ")
    sub_element(element, "ref", text="OtherType", refid="other_type", kind="compound", tail=">")
    assert Tokenizer.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(" "),
        ref("MyType", refid="my_type", kind="compound"),
        nested_start("<"),
        name("NestedType"),
        nested_sep(","),
        whitespace(" "),
        ref("OtherType", refid="other_type", kind="compound"),
        nested_end(">"),
    ]


@pytest.fixture(params=[
    [],
    [whitespace(" ")],
    [qualifier("const"), whitespace(" ")],
    [whitespace(" "), qualifier("const"), whitespace(" ")],
    [qualifier("const"), operator("*"), whitespace(" ")],
    [qualifier("const"),
     whitespace(" "),
     qualifier("const"),
     operator("*"),
     whitespace(" ")],
],
                ids=lambda ps: "".join(p.text for p in ps))
def prefixes(request):
    return request.param


@pytest.fixture(params=[
    [],
    [whitespace(" ")],
    [whitespace(" "), qualifier("const")],
    [whitespace(" "), operator("&")],
    [operator("&")],
],
                ids=lambda ps: "".join(p.text for p in ps))
def suffixes(request):
    return request.param


class ExpectedType(NamedTuple):
    prefix: str
    name: str
    suffix: str
    kind: Optional[str] = None
    refid: Optional[str] = None


class TypeTestData(NamedTuple):
    tokens: List[Token]
    expected_types: List[ExpectedType] = None


@pytest.fixture(params=[
    TypeTestData([name("MyType")]),
    TypeTestData([name("long")]),
    TypeTestData([name("unsigned"), whitespace(" "), name("int")]),
    TypeTestData([name("unsigned"),
                  whitespace(" "),
                  name("long"),
                  whitespace(" "),
                  name("long")]),
    TypeTestData([ref("MyType", refid="lang-mytype", kind="compound")],
                 [ExpectedType("", "MyType", "", kind="compound", refid="lang-mytype")]),
    TypeTestData([ref("MyType", refid="lang-mytype")],
                 [ExpectedType("", "MyType", "", refid="lang-mytype")]),
    TypeTestData([
        ref("MyType", refid="lang-mytype", kind="compound"),
        whitespace(" "),
        ref("OtherType", refid="lang-othertype", kind="compound")
    ], [ExpectedType("", "MyType OtherType", "", kind="compound", refid="lang-mytype")]),
],
                ids=lambda ps: "".join(p.text for p in ps[0]))
def names(request):
    test_data = request.param
    if test_data.expected_types is None:
        return TypeTestData(test_data.tokens,
                            [ExpectedType("", "".join(t.text for t in test_data.tokens), "")])
    return test_data


@pytest.fixture(params=[
    TypeTestData([], []),
    TypeTestData([nested_start("<"), name("NestedType"),
                  nested_end(">")], [
                      ExpectedType("", "NestedType", ""),
                  ]),
    TypeTestData([
        nested_start("<"),
        qualifier("const"),
        whitespace(" "),
        name("NestedType"),
        operator("*"),
        nested_end(">")
    ], [
        ExpectedType("const ", "NestedType", "*"),
    ]),
    TypeTestData(
        [nested_start("<"),
         whitespace(" "),
         name("NestedType"),
         whitespace(" "),
         nested_end(">")], [
             ExpectedType(" ", "NestedType", " "),
         ]),
    TypeTestData([
        nested_start("<"),
        name("NestedType"),
        nested_sep(","),
        ref("OtherType", refid="lang-othertype", kind="compound"),
        nested_end(">")
    ], [
        ExpectedType("", "NestedType", ""),
        ExpectedType("", "OtherType", "", refid="lang-othertype", kind="compound"),
    ]),
    TypeTestData([
        nested_start("<"),
        ref("NestedType", refid="lang-nestedtype"),
        whitespace(" "),
        nested_sep(","),
        whitespace(" "),
        name("OtherType"),
        nested_end(">"),
    ], [
        ExpectedType("", "NestedType", " ", refid="lang-nestedtype"),
        ExpectedType(" ", "OtherType", ""),
    ]),
    TypeTestData([
        nested_start("<"),
        name("NestedType"),
        operator("&"),
        nested_sep(","),
        whitespace(" "),
        qualifier("const"),
        whitespace(" "),
        name("OtherType"),
        nested_end(">"),
    ], [
        ExpectedType("", "NestedType", "&"),
        ExpectedType(" const ", "OtherType", ""),
    ]),
],
                ids=lambda ps: "".join(p.text for p in ps[0]))
def nested_types(request):
    return request.param


def test_type_producer__type_from_tokens(prefixes, names, nested_types, suffixes):
    type_ref = TypeProducer.type_from_tokens(prefixes + names.tokens + nested_types.tokens +
                                             suffixes)
    assert type_ref.prefix == "".join(p.text for p in prefixes)
    assert type_ref.name == names.expected_types[0].name
    assert type_ref.kind == names.expected_types[0].kind
    assert type_ref.id == names.expected_types[0].refid
    assert type_ref.suffix == "".join(s.text for s in suffixes)

    if nested_types.expected_types:
        assert len(nested_types.expected_types) == len(type_ref.nested)

        for actual, expected in zip(type_ref.nested, nested_types.expected_types):
            assert actual.prefix == expected.prefix
            assert actual.name == expected.name
            assert actual.suffix == expected.suffix
            assert actual.kind == expected.kind
            assert actual.id == expected.refid
            assert not actual.nested


def test_type_producer__type_from_tokens__deep_nested_type():
    tokens = [
        name("MyType"),
        nested_start("<"),
        name("NestedType"),
        nested_start("<"),
        name("OtherType"),
        nested_sep(","),
        name("MyType"),
        nested_end(">"),
        nested_sep(","),
        name("OtherType"),
        nested_end(">")
    ]
    type_ref = TypeProducer.type_from_tokens(tokens)

    assert type_ref.name == "MyType"
    assert len(type_ref.nested) == 2
    assert type_ref.nested[0].name == "NestedType"
    assert len(type_ref.nested[0].nested) == 2
    assert type_ref.nested[0].nested[0].name == "OtherType"
    assert not type_ref.nested[0].nested[0].nested
    assert type_ref.nested[0].nested[1].name == "MyType"
    assert not type_ref.nested[0].nested[1].nested
    assert type_ref.nested[1].name == "OtherType"
    assert not type_ref.nested[1].nested


@pytest.mark.parametrize("tokens", [
    [],
    [nested_start("<")],
    [nested_sep(",")],
    [nested_end(">")],
    [qualifier("const")],
    [operator("*")],
    [whitespace(" ")],
    [name("MyType"), nested_start("<")],
    [name("MyType"), nested_start("<"), name("OtherType")],
    [name("MyType"), nested_start("<"),
     name("OtherType"), nested_sep(",")],
    [name("MyType"),
     nested_start("<"),
     name("OtherType"),
     nested_sep(","),
     nested_end(">")],
    [name("MyType"), nested_end(">")],
    [name("MyType"), nested_sep(","), name("OtherType")],
],
                         ids=lambda ps: "".join(p.text for p in ps))
def test_type_producer__type_from_tokens__invalid_token_sequence(tokens):
    with pytest.raises(TypeParseError):
        TypeProducer.type_from_tokens(tokens)
