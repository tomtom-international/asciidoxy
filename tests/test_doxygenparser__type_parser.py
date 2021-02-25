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
"""General tests for type parsing."""

import pytest
import random
import string

import xml.etree.ElementTree as ET

from typing import List, NamedTuple, Optional
from unittest.mock import MagicMock

from asciidoxy.parser.doxygen.language_traits import LanguageTraits, TokenCategory
from asciidoxy.parser.doxygen.type_parser import Token, TypeParser, find_tokens
from .shared import assert_equal_or_none_if_empty, sub_element


class TestTraits(LanguageTraits):
    TAG = "mylang"

    NESTED_STARTS = "<", "[",
    NESTED_ENDS = ">", "]",
    OPERATORS = "*", "&",
    QUALIFIERS = "const", "volatile", "constexpr", "mutable", "enum", "class",
    ARGS_STARTS = "(",
    ARGS_ENDS = ")",
    SEPARATORS = ",", ";",

    TOKENS = {
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.OPERATOR: OPERATORS,
        TokenCategory.QUALIFIER: QUALIFIERS,
        TokenCategory.ARGS_START: ARGS_STARTS,
        TokenCategory.ARGS_END: ARGS_ENDS,
        TokenCategory.SEPARATOR: SEPARATORS,
    }
    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + OPERATORS + ARGS_STARTS + ARGS_ENDS +
                        SEPARATORS + tuple(string.whitespace))
    SEPARATOR_TOKENS_OVERLAP = True

    ALLOWED_PREFIXES = TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
    ALLOWED_SUFFIXES = TokenCategory.WHITESPACE, TokenCategory.OPERATOR, TokenCategory.QUALIFIER,
    ALLOWED_NAMES = TokenCategory.WHITESPACE, TokenCategory.NAME,

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return type_name.startswith("Builtin")

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        return name.replace('"', "")


class TestParser(TypeParser):
    TRAITS = TestTraits

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        tokens = super().adapt_tokens(tokens, array_tokens)

        for token in tokens:
            if token.text.startswith("arg_"):
                token.category = TokenCategory.ARG_NAME

        return tokens


def whitespace(text: str = " ") -> Token:
    return Token(text, TokenCategory.WHITESPACE)


def qualifier(text: str) -> Token:
    return Token(text, TokenCategory.QUALIFIER)


def operator(text: str) -> Token:
    return Token(text, TokenCategory.OPERATOR)


def name(text: str) -> Token:
    return Token(text, TokenCategory.NAME)


def nested_start(text: str = "<") -> Token:
    return Token(text, TokenCategory.NESTED_START)


def nested_end(text: str = ">") -> Token:
    return Token(text, TokenCategory.NESTED_END)


def nested_sep(text: str = ",") -> Token:
    return Token(text, TokenCategory.NESTED_SEPARATOR)


def ref(text: str, refid: Optional[str] = None, kind: Optional[str] = None) -> Token:
    return Token(text, refid=refid, category=TokenCategory.NAME, kind=kind)


def args_start(text: str = "(") -> Token:
    return Token(text, TokenCategory.ARGS_START)


def args_end(text: str = ")") -> Token:
    return Token(text, TokenCategory.ARGS_END)


def args_sep(text: str = ",") -> Token:
    return Token(text, TokenCategory.ARGS_SEPARATOR)


def arg_name(text: str) -> Token:
    return Token(text, TokenCategory.ARG_NAME)


def sep(text: str = ",") -> Token:
    return Token(text, TokenCategory.SEPARATOR)


def unknown(text: str) -> Token:
    return Token(text, TokenCategory.UNKNOWN)


@pytest.mark.parametrize("text,tokens", [
    ("MyType", [name("MyType")]),
    ("const MyType", [qualifier("const"), whitespace(),
                      name("MyType")]),
    ("MyType<OtherType>",
     [name("MyType"), nested_start(),
      name("OtherType"), nested_end()]),
    ("const MyType<OtherType>&", [
        qualifier("const"),
        whitespace(),
        name("MyType"),
        nested_start(),
        name("OtherType"),
        nested_end(),
        operator("&")
    ]),
    ("const MyType<OtherType> &", [
        qualifier("const"),
        whitespace(),
        name("MyType"),
        nested_start(),
        name("OtherType"),
        nested_end(),
        whitespace(),
        operator("&")
    ]),
    ("const * const MyType", [
        qualifier("const"),
        whitespace(),
        operator("*"),
        whitespace(),
        qualifier("const"),
        whitespace(),
        name("MyType")
    ]),
    ("const* const MyType", [
        qualifier("const"),
        operator("*"),
        whitespace(),
        qualifier("const"),
        whitespace(),
        name("MyType")
    ]),
    ("MyType*", [name("MyType"), operator("*")]),
    ("MyType *", [name("MyType"), whitespace(), operator("*")]),
    ("MyType <OtherType>",
     [name("MyType"), whitespace(),
      nested_start(), name("OtherType"),
      nested_end()]),
    ("MyType < OtherType >", [
        name("MyType"),
        whitespace(),
        nested_start(),
        whitespace(),
        name("OtherType"),
        whitespace(),
        nested_end()
    ]),
    ("MyType  <  OtherType  >", [
        name("MyType"),
        whitespace(),
        nested_start(),
        whitespace(),
        name("OtherType"),
        whitespace(),
        nested_end()
    ]),
    ("const MyType<const OtherType> &", [
        qualifier("const"),
        whitespace(),
        name("MyType"),
        nested_start(),
        qualifier("const"),
        whitespace(),
        name("OtherType"),
        nested_end(),
        whitespace(),
        operator("&")
    ]),
    ("const MyType<const OtherType, YetAnotherType&> &", [
        qualifier("const"),
        whitespace(),
        name("MyType"),
        nested_start(),
        qualifier("const"),
        whitespace(),
        name("OtherType"),
        sep(),
        whitespace(),
        name("YetAnotherType"),
        operator("&"),
        nested_end(),
        whitespace(),
        operator("&")
    ]),
    ("MyType<const OtherType, <YetAnotherType&,const OtherType>> &", [
        name("MyType"),
        nested_start(),
        qualifier("const"),
        whitespace(),
        name("OtherType"),
        sep(),
        whitespace(),
        nested_start(),
        name("YetAnotherType"),
        operator("&"),
        sep(),
        qualifier("const"),
        whitespace(),
        name("OtherType"),
        nested_end(),
        nested_end(),
        whitespace(),
        operator("&")
    ]),
    ("MyType(const RefType&)", [
        name("MyType"),
        args_start(),
        qualifier("const"),
        whitespace(),
        name("RefType"),
        operator("&"),
        args_end()
    ]),
    ("MyType(const RefType&, OtherType*)", [
        name("MyType"),
        args_start(),
        qualifier("const"),
        whitespace(),
        name("RefType"),
        operator("&"),
        sep(),
        whitespace(),
        name("OtherType"),
        operator("*"),
        args_end()
    ]),
])
def test_type_parser__tokenize_text(text, tokens):
    assert TestParser.tokenize_text(text) == tokens


def _generate_whitespace_data():
    whitespace_chars = tuple(string.whitespace)
    return ["".join(random.choices(whitespace_chars, k=random.randrange(1, 10))) for _ in range(20)]


@pytest.mark.parametrize("text", _generate_whitespace_data())
def test_type_parser__tokenize_text__whitespace_only(text):
    assert TestParser.tokenize_text(text) == [whitespace()]


@pytest.mark.parametrize("text,tokens", [
    (" \t\nMyType\n ", [whitespace(), name("MyType"), whitespace()]),
    ("  const  \tMyType",
     [whitespace(), qualifier("const"),
      whitespace(), name("MyType")]),
    ("\nMyType\n\t&", [whitespace(), name("MyType"),
                       whitespace(), operator("&")]),
])
def test_type_parser__tokenize_text__reduce_whitespace(text, tokens):
    assert TestParser.tokenize_text(text) == tokens


def test_type_parser__tokenize_xml__text_only():
    element = ET.Element("type")
    element.text = "const MyType&"
    assert TestParser.tokenize_xml(element) == [
        qualifier("const"), whitespace(),
        name("MyType"), operator("&")
    ]


def test_type_parser__tokenize_xml__simple_element():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound")
    assert TestParser.tokenize_xml(element) == [
        ref("MyType", refid="my_type", kind="compound"),
    ]


def test_type_parser__tokenize_xml__simple_element__kind_is_optional():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type")
    assert TestParser.tokenize_xml(element) == [
        ref("MyType", refid="my_type"),
    ]


def test_type_parser__tokenize_xml__simple_element__name_missing():
    element = ET.Element("type")
    sub_element(element, "ref", text="", refid="my_type")
    assert TestParser.tokenize_xml(element) == []


def test_type_parser__tokenize_xml__simple_element__ref_id_missing():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType")
    assert TestParser.tokenize_xml(element) == [
        ref("MyType"),
    ]


def test_type_parser__tokenize_xml__prefix_suffix():
    element = ET.Element("type")
    element.text = "const "
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound", tail=" *")
    assert TestParser.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(),
        ref("MyType", refid="my_type", kind="compound"),
        whitespace(),
        operator("*"),
    ]


def test_type_parser__tokenize_xml__text_type_with_nested_xml():
    element = ET.Element("type")
    element.text = "const MyType<"
    sub_element(element, "ref", text="OtherType", refid="other_type", kindref="compound", tail=">")
    assert TestParser.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(),
        name("MyType"),
        nested_start(),
        ref("OtherType", refid="other_type", kind="compound"),
        nested_end(),
    ]


def test_type_parser__tokenize_xml__xml_type_with_nested_xml_and_text():
    element = ET.Element("type")
    element.text = "const "
    sub_element(element,
                "ref",
                text="MyType",
                refid="my_type",
                kindref="compound",
                tail="<NestedType, ")
    sub_element(element, "ref", text="OtherType", refid="other_type", kindref="compound", tail=">")
    assert TestParser.tokenize_xml(element) == [
        qualifier("const"),
        whitespace(),
        ref("MyType", refid="my_type", kind="compound"),
        nested_start(),
        name("NestedType"),
        sep(),
        whitespace(),
        ref("OtherType", refid="other_type", kind="compound"),
        nested_end(),
    ]


@pytest.fixture(params=[
    [],
    [qualifier("const"), whitespace()],
    [qualifier("const"), operator("*"), whitespace()],
    [qualifier("const"),
     whitespace(),
     qualifier("const"),
     operator("*"),
     whitespace()],
],
                ids=lambda ps: "".join(p.text for p in ps))
def prefixes(request):
    return request.param


@pytest.fixture(params=[
    [],
    [whitespace(), qualifier("const")],
    [whitespace(), operator("&")],
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
    arg_name: Optional[str] = None


class TypeTestData(NamedTuple):
    tokens: List[Token]
    expected_types: List[ExpectedType] = None


@pytest.fixture(params=[
    TypeTestData([name("MyType")]),
    TypeTestData([name("long")]),
    TypeTestData([name("unsigned"), whitespace(), name("int")]),
    TypeTestData([name("unsigned"),
                  whitespace(),
                  name("long"),
                  whitespace(),
                  name("long")]),
    TypeTestData([ref("MyType", refid="mytype", kind="compound")],
                 [ExpectedType("", "MyType", "", kind="compound", refid="mytype")]),
    TypeTestData([ref("MyType", refid="mytype")], [ExpectedType("", "MyType", "", refid="mytype")]),
    TypeTestData([
        ref("MyType", refid="mytype", kind="compound"),
        whitespace(),
        ref("OtherType", refid="othertype", kind="compound")
    ], [ExpectedType("", "MyType OtherType", "", kind="compound", refid="mytype")]),
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
    TypeTestData(
        [nested_start(), name("NestedType"), nested_end()], [
            ExpectedType("", "NestedType", ""),
        ]),
    TypeTestData([
        nested_start(),
        qualifier("const"),
        whitespace(),
        name("NestedType"),
        operator("*"),
        nested_end()
    ], [
        ExpectedType("const ", "NestedType", "*"),
    ]),
    TypeTestData(
        [nested_start(),
         whitespace(), name("NestedType"),
         whitespace(), nested_end()], [
             ExpectedType("", "NestedType", ""),
         ]),
    TypeTestData([
        nested_start(),
        name("NestedType"),
        nested_sep(),
        ref("OtherType", refid="othertype", kind="compound"),
        nested_end()
    ], [
        ExpectedType("", "NestedType", ""),
        ExpectedType("", "OtherType", "", refid="othertype", kind="compound"),
    ]),
    TypeTestData([
        nested_start(),
        ref("NestedType", refid="nestedtype"),
        whitespace(),
        nested_sep(),
        whitespace(),
        name("OtherType"),
        nested_end(),
    ], [
        ExpectedType("", "NestedType", "", refid="nestedtype"),
        ExpectedType("", "OtherType", ""),
    ]),
    TypeTestData([
        nested_start(),
        name("NestedType"),
        operator("&"),
        nested_sep(),
        whitespace(),
        qualifier("const"),
        whitespace(),
        name("OtherType"),
        nested_end(),
    ], [
        ExpectedType("", "NestedType", "&"),
        ExpectedType("const ", "OtherType", ""),
    ]),
],
                ids=lambda ps: "".join(p.text for p in ps[0]))
def nested_types(request):
    return request.param


@pytest.fixture(params=[
    TypeTestData([], []),
    TypeTestData([
        args_start(),
        qualifier("const"),
        whitespace(),
        name("ArgType"),
        args_sep(),
        whitespace(),
        name("AnotherType"),
        operator("&"),
        args_end(),
    ], [
        ExpectedType("const ", "ArgType", ""),
        ExpectedType("", "AnotherType", "&"),
    ]),
    TypeTestData([
        args_start(),
        qualifier("const"),
        whitespace(),
        name("ArgType"),
        whitespace(),
        arg_name("name"),
        args_sep(),
        whitespace(),
        name("AnotherType"),
        operator("&"),
        whitespace(),
        arg_name("other"),
        args_end(),
    ], [
        ExpectedType("const ", "ArgType", "", arg_name="name"),
        ExpectedType("", "AnotherType", "&", arg_name="other"),
    ]),
],
                ids=lambda ps: "".join(p.text for p in ps[0]))
def arg_types(request):
    return request.param


def _match_expected_type(actual, expected):
    assert_equal_or_none_if_empty(actual.prefix, expected.prefix)
    assert actual.name == expected.name
    assert_equal_or_none_if_empty(actual.suffix, expected.suffix)
    assert actual.kind == expected.kind
    if expected.refid is None:
        assert actual.id is None
    else:
        assert actual.id == f"mylang-{expected.refid}"
    assert not actual.nested
    assert actual.language == "mylang"


def _match_type(actual,
                *,
                name=None,
                prefix=None,
                suffix=None,
                kind=None,
                refid=None,
                nested=None,
                args=None):
    assert_equal_or_none_if_empty(actual.name, name)
    assert_equal_or_none_if_empty(actual.prefix, prefix)
    assert_equal_or_none_if_empty(actual.suffix, suffix)
    assert_equal_or_none_if_empty(actual.kind, kind)

    if refid is None:
        assert actual.id is None
    else:
        assert actual.id == f"mylang-{refid}"

    assert actual.language == "mylang"

    if nested:
        assert len(nested) == len(actual.nested)

        for actual, expected in zip(actual.nested, nested):
            _match_expected_type(actual, expected)
    else:
        assert not actual.nested

    if args:
        assert len(args) == len(actual.args)

        for actual, expected in zip(actual.args, args):
            assert_equal_or_none_if_empty(actual.name, expected.arg_name)
            _match_expected_type(actual.type, expected)
    else:
        assert not actual.args


def test_type_parser__type_from_tokens(prefixes, names, nested_types, arg_types, suffixes):
    driver_mock = MagicMock()
    type_ref = TestParser.type_from_tokens(prefixes + names.tokens + nested_types.tokens +
                                           suffixes + arg_types.tokens,
                                           driver=driver_mock)
    assert type_ref is not None

    if arg_types.expected_types:
        _match_type(type_ref, kind="closure", args=arg_types.expected_types)
        assert type_ref.returns is not None
        _match_type(type_ref.returns,
                    name=names.expected_types[0].name,
                    prefix="".join(p.text for p in prefixes),
                    suffix="".join(s.text for s in suffixes),
                    kind=names.expected_types[0].kind,
                    refid=names.expected_types[0].refid,
                    nested=nested_types.expected_types)

    else:
        _match_type(type_ref,
                    name=names.expected_types[0].name,
                    prefix="".join(p.text for p in prefixes),
                    suffix="".join(s.text for s in suffixes),
                    kind=names.expected_types[0].kind,
                    refid=names.expected_types[0].refid,
                    nested=nested_types.expected_types)

    unresolved_types = []
    if not names.expected_types[0].refid:
        unresolved_types.append(names.expected_types[0].name)
    for expected_type in nested_types.expected_types:
        if not expected_type.refid:
            unresolved_types.append(expected_type.name)
    for expected_type in arg_types.expected_types:
        if not expected_type.refid:
            unresolved_types.append(expected_type.name)
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(unresolved_types))


@pytest.mark.parametrize("tokens,expected_type", [
    ([whitespace(), name("MyType"), whitespace()], ExpectedType("", "MyType", "")),
    ([whitespace(), qualifier("const"),
      whitespace(), name("MyType"),
      whitespace()], ExpectedType("const ", "MyType", "")),
    ([whitespace(), name("MyType"),
      whitespace(), operator("*"),
      whitespace()], ExpectedType("", "MyType", " *")),
])
def test_type_parser__type_from_tokens__strip_whitespace(tokens, expected_type):
    type_ref = TestParser.type_from_tokens(tokens)
    assert type_ref.prefix == expected_type.prefix
    assert type_ref.name == expected_type.name
    assert type_ref.suffix == expected_type.suffix


def test_type_parser__type_from_tokens__deep_nested_type():
    tokens = [
        name("MyType"),
        nested_start(),
        name("NestedType"),
        nested_start(),
        name("OtherType"),
        nested_sep(),
        name("MyType"),
        nested_end(),
        nested_sep(),
        name("OtherType"),
        nested_end()
    ]
    type_ref = TestParser.type_from_tokens(tokens)

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


def test_type_parser__type_from_tokens__namespace():
    tokens = [
        name("MyType"),
        nested_start(),
        name("NestedType"),
        nested_start(),
        name("OtherType"),
        nested_sep(),
        name("MyType"),
        nested_end(),
        nested_sep(),
        name("OtherType"),
        nested_end()
    ]

    type_ref = TestParser.type_from_tokens(tokens, namespace="asciidoxy::test")

    assert type_ref.name == "MyType"
    assert type_ref.namespace == "asciidoxy::test"
    assert len(type_ref.nested) == 2
    assert type_ref.nested[0].name == "NestedType"
    assert type_ref.nested[0].namespace == "asciidoxy::test"
    assert len(type_ref.nested[0].nested) == 2
    assert type_ref.nested[0].nested[0].name == "OtherType"
    assert type_ref.nested[0].nested[0].namespace == "asciidoxy::test"
    assert type_ref.nested[0].nested[1].name == "MyType"
    assert type_ref.nested[0].nested[1].namespace == "asciidoxy::test"
    assert type_ref.nested[1].name == "OtherType"
    assert type_ref.nested[1].namespace == "asciidoxy::test"


def test_type_parser__type_from_tokens__no_namespace():
    tokens = [
        name("MyType"),
        nested_start(),
        name("NestedType"),
        nested_start(),
        name("OtherType"),
        nested_sep(),
        name("MyType"),
        nested_end(),
        nested_sep(),
        name("OtherType"),
        nested_end()
    ]

    type_ref = TestParser.type_from_tokens(tokens, namespace=None)

    assert type_ref.name == "MyType"
    assert type_ref.namespace is None
    assert len(type_ref.nested) == 2
    assert type_ref.nested[0].name == "NestedType"
    assert type_ref.nested[0].namespace is None
    assert len(type_ref.nested[0].nested) == 2
    assert type_ref.nested[0].nested[0].name == "OtherType"
    assert type_ref.nested[0].nested[0].namespace is None
    assert type_ref.nested[0].nested[1].name == "MyType"
    assert type_ref.nested[0].nested[1].namespace is None
    assert type_ref.nested[1].name == "OtherType"
    assert type_ref.nested[1].namespace is None


def test_type_parser__type_from_tokens__do_not_register_builtin_types():
    tokens = [
        name("BuiltinType"),
        nested_start(),
        name("BuiltinType2"),
        nested_start(),
        name("OtherType"),
        nested_sep(),
        name("MyType"),
        nested_end(),
        nested_sep(),
        name("OtherType"),
        nested_end()
    ]

    driver_mock = MagicMock()
    type_ref = TestParser.type_from_tokens(tokens, driver=driver_mock)
    assert type_ref.name == "BuiltinType"
    assert (sorted([args[0].name for args, _ in driver_mock.unresolved_ref.call_args_list
                    ]) == sorted(["OtherType", "MyType", "OtherType"]))


@pytest.mark.parametrize("tokens,expected", [
    ([name("MyType"), nested_end()], ExpectedType("", "MyType", ">")),
    ([name("MyType"), nested_sep(), name("OtherType")], ExpectedType("", "MyType", ",OtherType")),
])
def test_type_parser__type_from_tokens__unexpected_trailing_tokens(tokens, expected):
    type_ref = TestParser.type_from_tokens(tokens)
    _match_expected_type(type_ref, expected)


@pytest.mark.parametrize("tokens,expected", [
    ([nested_sep()], ExpectedType(None, ",", None)),
    ([nested_end()], ExpectedType(None, ">", None)),
    ([qualifier("const")], ExpectedType(None, "const", None)),
    ([operator("*")], ExpectedType(None, "*", None)),
    ([nested_start()], ExpectedType(None, "<", None)),
    ([name("MyType"), nested_start()], ExpectedType(None, "MyType<", None)),
    ([name("MyType"), nested_start(), name("OtherType")
      ], ExpectedType(None, "MyType<OtherType", None)),
    ([name("MyType"), nested_start(),
      name("OtherType"), nested_sep()], ExpectedType(None, "MyType<OtherType,", None)),
])
def test_type_parser__type_from_tokens__invalid_token_sequence(tokens, expected):
    type_ref = TestParser.type_from_tokens(tokens)
    _match_expected_type(type_ref, expected)


def test_type_parser__type_from_tokens__calls_cleanup_name():
    tokens = [
        qualifier('"const"'),
        whitespace(),
        name('"MyType"'),
        whitespace(),
        qualifier('"const"')
    ]
    type_ref = TestParser.type_from_tokens(tokens)
    assert type_ref.prefix == '"const" '
    assert type_ref.name == 'MyType'
    assert type_ref.suffix == ' "const"'


@pytest.mark.parametrize("tokens,expected", [
    ([name("Type")], [name("Type")]),
    ([
        nested_start(),
        name("Type"),
        sep(),
        name("Type2"),
        nested_end(),
    ], [
        nested_start(),
        name("Type"),
        nested_sep(),
        name("Type2"),
        nested_end(),
    ]),
    ([
        args_start(),
        name("Type"),
        sep(),
        name("Type2"),
        args_end(),
    ], [
        args_start(),
        name("Type"),
        args_sep(),
        name("Type2"),
        args_end(),
    ]),
    ([
        nested_start(),
        name("Type"),
        sep(),
        name("Type2"),
        nested_end(),
        args_start(),
        name("Type"),
        nested_start(),
        name("Type"),
        sep(),
        name("Type2"),
        nested_end(),
        sep(),
        name("Type2"),
        args_end(),
    ], [
        nested_start(),
        name("Type"),
        nested_sep(),
        name("Type2"),
        nested_end(),
        args_start(),
        name("Type"),
        nested_start(),
        name("Type"),
        nested_sep(),
        name("Type2"),
        nested_end(),
        args_sep(),
        name("Type2"),
        args_end(),
    ]),
],
                         ids=lambda ps: "".join(p.text for p in ps))
def test_type_parser__adapt_separators(tokens, expected):
    assert TestParser.adapt_separators(tokens) == expected


@pytest.mark.parametrize("tokens,expected", [
    ([
        name("Type"),
        sep(),
        name("SecondType"),
        nested_end(),
    ], [
        name("Type"),
        unknown(","),
        name("SecondType"),
        nested_end(),
    ]),
    ([
        name("Type"),
        sep(),
        name("SecondType"),
        args_end(),
    ], [
        name("Type"),
        unknown(","),
        name("SecondType"),
        args_end(),
    ]),
    ([
        nested_start(),
        name("Type"),
        sep(),
        name("SecondType"),
        nested_end(),
        sep(),
    ], [
        nested_start(),
        name("Type"),
        nested_sep(","),
        name("SecondType"),
        nested_end(),
        unknown(","),
    ]),
    ([
        args_start(),
        name("Type"),
        sep(),
        name("SecondType"),
        args_end(),
        sep(),
    ], [
        args_start(),
        name("Type"),
        args_sep(","),
        name("SecondType"),
        args_end(),
        unknown(","),
    ]),
],
                         ids=lambda ps: "".join(p.text for p in ps))
def test_type_parser__adapt_separators__invalid(tokens, expected):
    assert TestParser.adapt_separators(tokens) == expected


@pytest.mark.parametrize("tokens, expected", [
    ([], (None, [])),
    ([
        whitespace(),
    ], (None, [
        whitespace(),
    ])),
    ([
        args_start(),
        args_end(),
    ], ([], [])),
    ([
        args_start(),
        whitespace(),
        args_end(),
    ], ([], [])),
    ([
        args_start(),
        args_sep(),
        args_end(),
    ], ([], [])),
    ([
        args_start(),
        whitespace(),
        args_sep(),
        whitespace(),
        args_end(),
    ], ([], [])),
],
                         ids=lambda ts: "".join(t.text for t in ts if hasattr(t, "text")))
def test_type_parser__arg_types__empty(tokens, expected):
    assert TestParser.arg_types(tokens) == expected


@pytest.mark.parametrize("tokens, expected", [
    ([], (None, [])),
    ([
        whitespace(),
    ], (None, [
        whitespace(),
    ])),
    ([
        nested_start(),
        nested_end(),
    ], ([], [])),
    ([
        nested_start(),
        whitespace(),
        nested_end(),
    ], ([], [])),
    ([
        nested_start(),
        nested_sep(),
        nested_end(),
    ], ([], [])),
    ([
        nested_start(),
        whitespace(),
        nested_sep(),
        whitespace(),
        nested_end(),
    ], ([], [])),
],
                         ids=lambda ts: "".join(t.text for t in ts if hasattr(t, "text")))
def test_type_parser__nested_types__empty(tokens, expected):
    assert TestParser.nested_types(tokens) == expected


def test_type_parser__parse_xml__simple_element():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound")

    type_ref = TestParser.parse_xml(element)

    assert type_ref is not None
    assert type_ref.name == "MyType"
    assert type_ref.id == "mylang-my_type"
    assert type_ref.kind == "compound"
    assert not type_ref.nested


def test_type_parser__parse_xml__unresolved_ref_with_driver():
    element = ET.Element("type")
    element.text = "MyType"

    driver_mock = MagicMock()
    type_ref = TestParser.parse_xml(element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_called_once_with(type_ref)

    assert type_ref is not None
    assert type_ref.name == "MyType"
    assert not type_ref.id
    assert not type_ref.kind
    assert not type_ref.nested


def test_type_parser__parse_xml__do_not_register_ref_with_id():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound")

    driver_mock = MagicMock()
    type_ref = TestParser.parse_xml(element, driver=driver_mock)
    driver_mock.unresolved_ref.assert_not_called()

    assert type_ref is not None
    assert type_ref.name == "MyType"
    assert type_ref.id == "mylang-my_type"
    assert type_ref.kind == "compound"
    assert not type_ref.nested


def test_type_parser__parse_xml__namespace():
    element = ET.Element("type")
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound")

    driver_mock = MagicMock()
    type_ref = TestParser.parse_xml(element, driver=driver_mock, namespace="asciidoxy::test")
    driver_mock.unresolved_ref.assert_not_called()

    assert type_ref is not None
    assert type_ref.name == "MyType"
    assert type_ref.id == "mylang-my_type"
    assert type_ref.kind == "compound"
    assert type_ref.namespace == "asciidoxy::test"
    assert not type_ref.nested


def test_type_parser__parse_xml__empty_tag():
    element = ET.Element("type")
    assert TestParser.parse_xml(element) is None


def test_type_parser__parse_xml__whitespace_only():
    element = ET.Element("type")
    element.text = "  \n\t  \n  "
    assert TestParser.parse_xml(element) is None


def test_type_parser__parse_xml__nested_types_and_args():
    element = ET.Element("type")
    element.text = "const "
    sub_element(element, "ref", text="MyType", refid="my_type", kindref="compound", tail="<")
    sub_element(element,
                "ref",
                text="NestedType",
                refid="nested_type",
                kindref="compound",
                tail=", OtherNestedType>(const std::string& arg_name, int arg_value)")

    type_ref = TestParser.parse_xml(element)

    assert type_ref is not None
    assert not type_ref.prefix
    assert not type_ref.name
    assert not type_ref.suffix
    assert not type_ref.id
    assert type_ref.kind == "closure"
    assert not type_ref.nested
    assert len(type_ref.args) == 2

    assert type_ref.args[0].name == "arg_name"
    assert type_ref.args[0].type.prefix == "const "
    assert type_ref.args[0].type.name == "std::string"
    assert type_ref.args[0].type.suffix == "&"
    assert not type_ref.args[0].type.id
    assert not type_ref.args[0].type.kind

    assert type_ref.args[1].name == "arg_value"
    assert not type_ref.args[1].type.prefix
    assert type_ref.args[1].type.name == "int"
    assert not type_ref.args[1].type.suffix
    assert not type_ref.args[1].type.id
    assert not type_ref.args[1].type.kind

    assert type_ref.returns is not None
    assert type_ref.returns.prefix == "const "
    assert type_ref.returns.name == "MyType"
    assert not type_ref.returns.suffix
    assert type_ref.returns.id == "mylang-my_type"
    assert type_ref.returns.kind == "compound"
    assert len(type_ref.returns.nested) == 2
    assert not type_ref.returns.args

    assert not type_ref.returns.nested[0].prefix
    assert type_ref.returns.nested[0].name == "NestedType"
    assert not type_ref.returns.nested[0].suffix
    assert type_ref.returns.nested[0].id == "mylang-nested_type"
    assert type_ref.returns.nested[0].kind == "compound"

    assert not type_ref.returns.nested[1].prefix
    assert type_ref.returns.nested[1].name == "OtherNestedType"
    assert not type_ref.returns.nested[1].suffix
    assert not type_ref.returns.nested[1].id
    assert not type_ref.returns.nested[1].kind


@pytest.mark.parametrize("tokens, pattern, expected", [
    ([], [], []),
    ([
        whitespace(),
    ], [
        [TokenCategory.WHITESPACE],
        [TokenCategory.WHITESPACE],
    ], []),
    ([
        name("Type"),
        whitespace(),
        name("Arg"),
    ], [
        [TokenCategory.WHITESPACE],
        [TokenCategory.NAME],
    ], [[
        whitespace(),
        name("Arg"),
    ]]),
    ([
        name("Type"),
        whitespace(),
        name("Arg"),
    ], [
        [TokenCategory.NAME],
        [TokenCategory.NAME],
    ], []),
    ([
        name("Type"),
        whitespace(),
        name("Arg"),
    ], [
        [TokenCategory.WHITESPACE, TokenCategory.NAME],
        [TokenCategory.NAME, TokenCategory.WHITESPACE],
    ], [[
        name("Type"),
        whitespace(),
    ], [
        whitespace(),
        name("Arg"),
    ]]),
    ([
        name("Type"),
        whitespace(),
        name("Arg"),
    ], [
        [TokenCategory.NAME],
        [TokenCategory.WHITESPACE, None],
        [TokenCategory.NAME],
    ], [[
        name("Type"),
        whitespace(),
        name("Arg"),
    ]]),
    ([
        name("Type"),
        name("Arg"),
    ], [
        [TokenCategory.NAME],
        [TokenCategory.WHITESPACE, None],
        [TokenCategory.NAME],
    ], [[
        name("Type"),
        name("Arg"),
    ]]),
])
def test_find_tokens(tokens, pattern, expected):
    assert list(find_tokens(tokens, pattern)) == expected
