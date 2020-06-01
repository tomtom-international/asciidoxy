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

import xml.etree.ElementTree as ET

from typing import List, Optional, Tuple, Type, Union

from .driver_base import DriverBase
from .language_traits import LanguageTraits, TokenType
from ..model import Compound, Member, TypeRef


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


class TypeParser:
    TRAITS: Type[LanguageTraits]

    @classmethod
    def parse_xml(cls,
                  type_element: ET.Element,
                  driver: Optional[DriverBase] = None,
                  parent: Optional[Union[Compound, Member]] = None):
        tokens = cls.tokenize_xml(type_element)
        return cls.type_from_tokens(tokens, driver, parent)

    @classmethod
    def tokenize_text(cls, text: str) -> List[Token]:
        tokens: List[Token] = []

        def append_token(text: str) -> None:
            token = cls.make_text_token(text)
            if token.type_ == TokenType.WHITESPACE and tokens and tokens[-1].type_ == token.type_:
                pass
            else:
                tokens.append(token)

        while text:
            for i, c in enumerate(text):
                if c in cls.TRAITS.TOKEN_BOUNDARIES:
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
            text = " "
        elif text in cls.TRAITS.NESTED_STARTS:
            type_ = TokenType.NESTED_START
        elif text in cls.TRAITS.NESTED_ENDS:
            type_ = TokenType.NESTED_END
        elif text in cls.TRAITS.NESTED_SEPARATORS:
            type_ = TokenType.NESTED_SEPARATOR
        elif text in cls.TRAITS.OPERATORS:
            type_ = TokenType.OPERATOR
        elif text in cls.TRAITS.QUALIFIERS:
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
            kind = element.get("kindref", None)

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

    @classmethod
    def type_from_tokens(cls,
                         tokens: List[Token],
                         driver: Optional[DriverBase] = None,
                         parent: Optional[Union[Compound, Member]] = None) -> TypeRef:
        original_tokens = tokens
        tokens = tokens[:]

        prefixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_PREFIXES)
        cls.remove_leading_whitespace(prefixes)
        names, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_NAMES)
        tokens[:0] = cls.remove_trailing_whitespace(names)

        if not names:
            raise TypeParseError(f"No name found"
                                 f" in `{''.join(t.text for t in original_tokens)}`")

        nested_types, tokens = cls.nested_types(tokens, driver, parent)
        suffixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_SUFFIXES)
        cls.remove_trailing_whitespace(suffixes)

        if tokens:
            raise TypeParseError(f"Unexpected characters `{''.join(t.text for t in tokens)}`"
                                 f" in `{''.join(t.text for t in original_tokens)}`")

        type_ref = TypeRef(cls.TRAITS.TAG)
        type_ref.name = cls.TRAITS.cleanup_name("".join(n.text for n in names))
        type_ref.prefix = "".join(p.text for p in prefixes)
        type_ref.suffix = "".join(s.text for s in suffixes)
        type_ref.nested = nested_types or []
        type_ref.id = cls.TRAITS.unique_id(names[0].refid)
        type_ref.kind = names[0].kind

        if isinstance(parent, Compound):
            type_ref.namespace = parent.full_name
        elif isinstance(parent, Member):
            type_ref.namespace = parent.namespace

        if (driver is not None and type_ref.name and not type_ref.id
                and not cls.TRAITS.is_language_standard_type(type_ref.name)):
            driver.unresolved_ref(type_ref)

        return type_ref

    @staticmethod
    def select_tokens(tokens, types) -> Tuple[List[Token], List[Token]]:
        for i, t in enumerate(tokens):
            if t.type_ not in types:
                return tokens[:i], tokens[i:]
        return tokens, []

    @classmethod
    def remove_leading_whitespace(cls, tokens) -> List[Token]:
        return cls.remove_whitespace(tokens, 0)

    @classmethod
    def remove_trailing_whitespace(cls, tokens) -> List[Token]:
        return cls.remove_whitespace(tokens, -1)

    @staticmethod
    def remove_whitespace(tokens, location) -> List[Token]:
        ret = []
        while tokens and tokens[location].type_ == TokenType.WHITESPACE:
            ret.append(tokens.pop(location))
        return ret

    @classmethod
    def nested_types(
        cls,
        tokens: List[Token],
        driver: Optional[DriverBase] = None,
        parent: Optional[Union[Compound, Member]] = None
    ) -> Tuple[Optional[List[TypeRef]], List[Token]]:
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
                    nested_type = cls.type_from_tokens(tokens[:i], driver, parent)
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
