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
"""Parsing of types from strings and XML."""

import string

import xml.etree.ElementTree as ET

from enum import Enum, auto
from typing import List, Optional, Tuple, Type, Union

from .driver_base import DriverBase
from .language_traits import LanguageTraits
from ..model import Compound, Member, TypeRef


def parse_type(traits: Type[LanguageTraits],
               driver: DriverBase,
               type_element: ET.Element,
               parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
    def match_and_extract(regex, text):
        if regex is not None and text:
            match = regex.match(text)
            if match:
                return match.group(0), text[match.end():]

        return None, text

    def extract_type(element_iter, text):
        type_ref = TypeRef(traits.TAG)
        if isinstance(parent, Compound):
            type_ref.namespace = parent.full_name
        elif isinstance(parent, Member):
            type_ref.namespace = parent.namespace

        type_ref.prefix, text = match_and_extract(traits.TYPE_PREFIXES, text)

        if not text:
            try:
                element = next(element_iter)
                type_ref.id = traits.unique_id(element.get("refid"))
                type_ref.kind = element.get("kindref", None)
                type_ref.name = traits.cleanup_name(element.text or "")
                text = element.tail

            except StopIteration:
                pass
        else:
            type_ref.name, text = match_and_extract(traits.TYPE_NAME, text)
            if type_ref.name is not None:
                type_ref.name = traits.cleanup_name(type_ref.name)

        start_nested, text = match_and_extract(traits.TYPE_NESTED_START, text)
        if start_nested:
            while True:
                nested_type_ref, text = extract_type(element_iter, text)
                if nested_type_ref and nested_type_ref.name:
                    type_ref.nested.append(nested_type_ref)
                else:
                    # TODO Error?
                    break

                end_nested, text = match_and_extract(traits.TYPE_NESTED_END, text)
                if end_nested:
                    break

                _, text = match_and_extract(traits.TYPE_NESTED_SEPARATOR, text)

        type_ref.suffix, text = match_and_extract(traits.TYPE_SUFFIXES, text)

        # doxygen inserts empty <type> tag for return value in constructors,
        # this fake types should be filtered out
        if type_ref.name:
            if not type_ref.id and not traits.is_language_standard_type(type_ref.name):
                driver.unresolved_ref(type_ref)

        return type_ref, text

    type_ref, _ = extract_type(type_element.iter("ref"), type_element.text)
    return type_ref


class TokenType(Enum):
    UNKNOWN = auto()
    WHITESPACE = auto()
    QUALIFIER = auto()
    OPERATOR = auto()
    NAME = auto()
    NESTED_START = auto()
    NESTED_END = auto()
    NESTED_SEPARATOR = auto()


class Token:
    type_: TokenType
    refid: Optional[str]
    kind: Optional[str]

    def __init__(self,
                 text: str,
                 type_: TokenType = TokenType.UNKNOWN,
                 refid: Optional[str] = None,
                 kind: Optional[str] = None):
        self.type_ = type_
        self.text = text
        self.refid = refid
        self.kind = kind

    def __eq__(self, other) -> bool:
        return ((self.type_, self.text, self.refid, self.kind) == (other.type_, other.text,
                                                                   other.refid, other.kind))

    def __str__(self) -> str:
        return f"{self.type_}: {repr(self.text)}"

    __repr__ = __str__


class TypeParseError(Exception):
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self) -> str:
        return f"Failed to parse type: {self.msg}"


class Tokenizer:
    NESTED_STARTS = "<", "[",
    NESTED_ENDS = ">", "]",
    NESTED_SEPARATORS = ",", ";",
    OPERATORS = "*", "&",
    BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + OPERATORS +
                  tuple(string.whitespace))

    QUALIFIERS = "const", "volatile", "constexpr", "mutable", "enum", "class",

    @classmethod
    def tokenize_text(cls, text: str) -> List[Token]:
        tokens: List[Token] = []

        def append_token(text: str) -> None:
            # TODO Maybe simplify and do not care about multiple white space tokens?
            token = cls.make_text_token(text)
            if token.type_ == TokenType.WHITESPACE and tokens and tokens[-1].type_ == token.type_:
                tokens[-1].text += text
            else:
                tokens.append(token)

        while text:
            for i, c in enumerate(text):
                if c in cls.BOUNDARIES:
                    if i > 0:
                        append_token(text[:i])
                    append_token(text[i])
                    text = text[i + 1:]
                    break
            else:
                append_token(text)
                text = ""

        return tokens

    @classmethod
    def make_text_token(cls, text: str) -> Token:
        if text.isspace():
            type_ = TokenType.WHITESPACE
        elif text in cls.NESTED_STARTS:
            type_ = TokenType.NESTED_START
        elif text in cls.NESTED_ENDS:
            type_ = TokenType.NESTED_END
        elif text in cls.NESTED_SEPARATORS:
            type_ = TokenType.NESTED_SEPARATOR
        elif text in cls.OPERATORS:
            type_ = TokenType.OPERATOR
        elif text in cls.QUALIFIERS:
            type_ = TokenType.QUALIFIER
        else:
            type_ = TokenType.NAME

        return Token(text, type_)

    @classmethod
    def tokenize_xml(cls, element: ET.Element) -> List[Token]:
        tokens = []

        if element.tag == "ref":
            name = element.text
            refid = element.get("refid", None)
            kind = element.get("kind", None)

            if not name or not refid:
                raise TypeParseError("Encountered reference XML element without name or id.")

            tokens.append(Token(name, refid=refid, kind=kind, type_=TokenType.NAME))

        elif element.text:
            tokens.extend(cls.tokenize_text(element.text))

        for child in element:
            tokens.extend(cls.tokenize_xml(child))
        if element.tail:
            tokens.extend(cls.tokenize_text(element.tail))

        return tokens


class TypeProducer:
    ALLOWED_PREFIXES = TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
    ALLOWED_SUFFIXES = TokenType.WHITESPACE, TokenType.OPERATOR, TokenType.QUALIFIER,
    ALLOWED_NAMES = TokenType.WHITESPACE, TokenType.NAME,

    @classmethod
    def type_from_tokens(cls, tokens: List[Token]) -> TypeRef:
        original_tokens = tokens
        tokens = tokens[:]

        prefixes, tokens = cls.select_tokens(tokens, cls.ALLOWED_PREFIXES)
        names, tokens = cls.select_tokens(tokens, cls.ALLOWED_NAMES)
        tokens[:0] = cls.remove_trailing_whitespace(names)

        if not names:
            raise TypeParseError(f"No name found"
                                 f" in `{''.join(t.text for t in original_tokens)}`")

        nested_types, tokens = cls.nested_types(tokens)
        suffixes, tokens = cls.select_tokens(tokens, cls.ALLOWED_SUFFIXES)

        if tokens:
            raise TypeParseError(f"Unexpected characters `{''.join(t.text for t in tokens)}`"
                                 f" in `{''.join(t.text for t in original_tokens)}`")

        type_ref = TypeRef("lang")
        type_ref.name = "".join(n.text for n in names)
        type_ref.prefix = "".join(p.text for p in prefixes)
        type_ref.suffix = "".join(s.text for s in suffixes)
        type_ref.nested = nested_types or []
        type_ref.id = names[0].refid
        type_ref.kind = names[0].kind
        return type_ref

    @staticmethod
    def select_tokens(tokens, types) -> Tuple[List[Token], List[Token]]:
        for i, t in enumerate(tokens):
            if t.type_ not in types:
                return tokens[:i], tokens[i:]
        return tokens, []

    @staticmethod
    def remove_trailing_whitespace(tokens) -> List[Token]:
        ret = []
        while tokens and tokens[-1].type_ == TokenType.WHITESPACE:
            ret.append(tokens.pop(-1))
        return ret

    @classmethod
    def nested_types(cls, tokens: List[Token]) -> Tuple[Optional[List[TypeRef]], List[Token]]:
        original_tokens = tokens
        tokens = tokens[:]
        nested_types = []

        for i, t in enumerate(tokens):
            if t.type_ == TokenType.WHITESPACE:
                continue
            elif t.type_ == TokenType.NESTED_START:
                tokens = tokens[i + 1:]
                break
            else:
                return None, tokens
        else:
            return None, tokens

        level = 0
        while tokens:
            for i, t in enumerate(tokens):
                if t.type_ == TokenType.NESTED_START:
                    level += 1
                elif level > 0 and t.type_ == TokenType.NESTED_END:
                    level -= 1
                elif level == 0 and t.type_ in (TokenType.NESTED_SEPARATOR, TokenType.NESTED_END):
                    nested_type = cls.type_from_tokens(tokens[:i])
                    nested_types.append(nested_type)
                    tokens = tokens[i + 1:]

                    if t.type_ == TokenType.NESTED_END:
                        return nested_types, tokens
                    else:
                        break
            else:
                break

        raise TypeParseError("Unexpected end of nested types:"
                             f" `{''.join(t.text for t in original_tokens)}`")
