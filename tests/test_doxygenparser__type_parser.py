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

from collections import namedtuple

from asciidoxy.doxygenparser.type_parser import (TextToken, Tokenizer, TokenType, TypeProducer,
                                                 TypeParseError)


def whitespace(text: str) -> TextToken:
    return TextToken(text, TokenType.WHITESPACE)


def qualifier(text: str) -> TextToken:
    return TextToken(text, TokenType.QUALIFIER)


def operator(text: str) -> TextToken:
    return TextToken(text, TokenType.OPERATOR)


def name(text: str) -> TextToken:
    return TextToken(text, TokenType.NAME)


def nested_start(text: str) -> TextToken:
    return TextToken(text, TokenType.NESTED_START)


def nested_end(text: str) -> TextToken:
    return TextToken(text, TokenType.NESTED_END)


def nested_sep(text: str) -> TextToken:
    return TextToken(text, TokenType.NESTED_SEPARATOR)


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


@pytest.fixture(params=[
    [name("MyType")],
    [name("long")],
    [name("unsigned"), whitespace(" "), name("int")],
    [name("unsigned"),
     whitespace(" "),
     name("long"), whitespace(" "),
     name("long")],
],
                ids=lambda ps: "".join(p.text for p in ps))
def names(request):
    return request.param


NestedTestData = namedtuple("NestedTestData", ["tokens", "expected_types"])
ExpectedType = namedtuple("ExpectedType", ["prefix", "name", "suffix"])


@pytest.fixture(params=[
    NestedTestData([], []),
    NestedTestData([nested_start("<"), name("NestedType"),
                    nested_end(">")], [
                        ExpectedType("", "NestedType", ""),
                    ]),
    NestedTestData([
        nested_start("<"),
        qualifier("const"),
        whitespace(" "),
        name("NestedType"),
        operator("*"),
        nested_end(">")
    ], [
        ExpectedType("const ", "NestedType", "*"),
    ]),
    NestedTestData(
        [nested_start("<"),
         whitespace(" "),
         name("NestedType"),
         whitespace(" "),
         nested_end(">")], [
             ExpectedType(" ", "NestedType", " "),
         ]),
    NestedTestData([
        nested_start("<"),
        name("NestedType"),
        nested_sep(","),
        name("OtherType"),
        nested_end(">")
    ], [
        ExpectedType("", "NestedType", ""),
        ExpectedType("", "OtherType", ""),
    ]),
    NestedTestData([
        nested_start("<"),
        name("NestedType"),
        whitespace(" "),
        nested_sep(","),
        whitespace(" "),
        name("OtherType"),
        nested_end(">"),
    ], [
        ExpectedType("", "NestedType", " "),
        ExpectedType(" ", "OtherType", ""),
    ]),
    NestedTestData([
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
    type_ref = TypeProducer.type_from_tokens(prefixes + names + nested_types.tokens + suffixes)
    assert type_ref.prefix == "".join(p.text for p in prefixes)
    assert type_ref.name == "".join(n.text for n in names)
    assert type_ref.suffix == "".join(s.text for s in suffixes)

    if nested_types.expected_types:
        assert len(nested_types.expected_types) == len(type_ref.nested)

        for actual, expected in zip(type_ref.nested, nested_types.expected_types):
            assert actual.prefix == expected.prefix
            assert actual.name == expected.name
            assert actual.suffix == expected.suffix
            assert not actual.nested


def test_type_producer__deep_nested_type():
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
def test_type_producer__invalid_token_sequence(tokens):
    with pytest.raises(TypeParseError):
        TypeProducer.type_from_tokens(tokens)
