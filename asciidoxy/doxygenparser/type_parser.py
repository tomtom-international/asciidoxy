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

import logging

import xml.etree.ElementTree as ET

from typing import Iterator, List, Optional, Sequence, Tuple, Type, Union

from .driver_base import DriverBase
from .language_traits import LanguageTraits, TokenType
from ..model import Compound, Member, Parameter, TypeRef

logger = logging.getLogger(__name__)


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
                  array_element: Optional[ET.Element] = None,
                  driver: Optional[DriverBase] = None,
                  parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
        tokens = cls.tokenize_xml(type_element)
        array_tokens = cls.tokenize_xml(array_element) if array_element is not None else []
        tokens = cls.adapt_tokens(tokens, array_tokens)
        if len(tokens) == 0 or all(token.type_ == TokenType.WHITESPACE for token in tokens):
            return None
        return cls.type_from_tokens(tokens, driver, parent)

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        if cls.TRAITS.SEPARATOR_TOKENS_OVERLAP:
            tokens = cls.adapt_separators(tokens)
        return tokens

    @classmethod
    def adapt_separators(cls, tokens: List[Token]) -> List[Token]:
        scope_types = []
        for i, token in enumerate(tokens):
            if token.type_ in (TokenType.NESTED_START, TokenType.NESTED_END, TokenType.ARGS_START,
                               TokenType.ARGS_END):
                scope_types.append(token.type_)

            elif token.type_ in (TokenType.SEPARATOR, TokenType.NESTED_SEPARATOR,
                                 TokenType.ARGS_SEPARATOR):
                try:
                    token.type_ = cls._determine_separator_type(scope_types)
                except TypeParseError:
                    logger.warning(f"Cannot determine type of separator of token {i} in"
                                   f"{''.join(t.text for t in tokens)}")
                    token.type_ = TokenType.UNKNOWN
        return tokens

    @staticmethod
    def _determine_separator_type(scope_types: List[TokenType]) -> TokenType:
        nested_ends = 0
        args_ends = 0
        for scope_type in reversed(scope_types):
            if scope_type == TokenType.NESTED_END:
                nested_ends += 1
            elif scope_type == TokenType.ARGS_END:
                args_ends += 1
            elif scope_type == TokenType.NESTED_START:
                if nested_ends == 0:
                    return TokenType.NESTED_SEPARATOR
                else:
                    nested_ends -= 1
            elif scope_type == TokenType.ARGS_START:
                if args_ends == 0:
                    return TokenType.ARGS_SEPARATOR
                else:
                    args_ends -= 1
        raise TypeParseError("Cannot determine type of separator.")

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
        else:
            for token_type, tokens in cls.TRAITS.TOKENS.items():
                if text in tokens:
                    type_ = token_type
                    break
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
                logger.error(f"Encountered reference XML element without name or id: "
                             f"{ET.tostring(element, encoding='utf-8')}")

            if name:
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
                         parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
        if not tokens or all(t.type_ == TokenType.WHITESPACE for t in tokens):
            return None

        original_tokens = tokens
        tokens = tokens[:]

        prefixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_PREFIXES)
        cls.remove_leading_whitespace(prefixes)

        names, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_NAMES)
        cls.remove_leading_whitespace(names)
        tokens[:0] = cls.remove_trailing_whitespace(names)

        nested_types: Optional[List[TypeRef]] = []
        arg_types: Optional[List[Parameter]] = []
        try:
            nested_types, tokens = cls.nested_types(tokens, driver, parent)
            arg_types, tokens = cls.arg_types(tokens, driver, parent)
        except TypeParseError as e:
            logger.warning(f"Failed to parse nested types or args: {e}")

        suffixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_SUFFIXES)
        cls.remove_trailing_whitespace(suffixes)

        if not names:
            logger.warning(f"No name found in `{'`,`'.join(t.text for t in original_tokens)}`")
            return TypeRef(cls.TRAITS.TAG, "".join(t.text for t in original_tokens))

        if tokens and any(t.type_ != TokenType.WHITESPACE for t in tokens):
            logger.warning(f"Unexpected trailing token(s) `{'`,`'.join(t.text for t in tokens)}`"
                           f" in `{'`,`'.join(t.text for t in original_tokens)}`")
            suffixes.extend(tokens)

        type_ref = TypeRef(cls.TRAITS.TAG)
        type_ref.name = cls.TRAITS.cleanup_name("".join(n.text for n in names))
        type_ref.prefix = "".join(p.text for p in prefixes)
        type_ref.suffix = "".join(s.text for s in suffixes)
        type_ref.nested = nested_types
        type_ref.args = arg_types
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
    def select_tokens(tokens: List[Token],
                      types: Optional[Sequence[TokenType]]) -> Tuple[List[Token], List[Token]]:
        if types:
            for i, t in enumerate(tokens):
                if t.type_ not in types:
                    return tokens[:i], tokens[i:]
            return tokens, []
        else:
            return [], tokens

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

        nested_type_tokens, tokens = cls.select_nested_tokens(tokens, TokenType.NESTED_START,
                                                              TokenType.NESTED_END,
                                                              TokenType.NESTED_SEPARATOR)
        if nested_type_tokens is None:
            return None, tokens
        types = (cls.type_from_tokens(ntt, driver, parent) for ntt in nested_type_tokens)
        return [t for t in types if t is not None], tokens

    @classmethod
    def arg_types(
        cls,
        tokens: List[Token],
        driver: Optional[DriverBase] = None,
        parent: Optional[Union[Compound, Member]] = None
    ) -> Tuple[Optional[List[Parameter]], List[Token]]:

        nested_type_tokens, tokens = cls.select_nested_tokens(tokens, TokenType.ARGS_START,
                                                              TokenType.ARGS_END,
                                                              TokenType.ARGS_SEPARATOR)
        if nested_type_tokens is None:
            return None, tokens

        args = (cls.arg_from_tokens(ntt, driver, parent) for ntt in nested_type_tokens)
        return [a for a in args if a is not None], tokens

    @classmethod
    def arg_from_tokens(cls,
                        tokens: List[Token],
                        driver: Optional[DriverBase] = None,
                        parent: Optional[Union[Compound, Member]] = None) -> Optional[Parameter]:
        if not tokens or all(t.type_ == TokenType.WHITESPACE for t in tokens):
            return None

        name_tokens: List[Token] = []
        while tokens and tokens[-1].type_ == TokenType.ARG_NAME:
            name_tokens.insert(0, tokens.pop(-1))

        arg = Parameter()
        arg.type = cls.type_from_tokens(tokens, driver, parent)
        arg.name = "".join(t.text for t in name_tokens)
        return arg

    @classmethod
    def select_nested_tokens(
            cls, tokens: List[Token], start_token: TokenType, end_token: TokenType,
            separator_token: TokenType) -> Tuple[Optional[List[List[Token]]], List[Token]]:
        original_tokens = tokens
        tokens = tokens[:]
        nested_type_tokens = []

        for i, t in enumerate(tokens):
            if t.type_ == TokenType.WHITESPACE:
                continue
            elif t.type_ == start_token:
                tokens = tokens[i + 1:]
                break
            else:
                return None, tokens
        else:
            return None, tokens

        level = 0
        while tokens:
            for i, t in enumerate(tokens):
                if t.type_ == start_token:
                    level += 1
                elif level > 0 and t.type_ == end_token:
                    level -= 1
                elif level == 0 and t.type_ in (separator_token, end_token):
                    nested_type_tokens.append(tokens[:i])
                    tokens = tokens[i + 1:]

                    if t.type_ == end_token:
                        return nested_type_tokens, tokens
                    else:
                        break
            else:
                break

        raise TypeParseError("Unexpected end of nested types:"
                             f" `{''.join(t.text for t in original_tokens)}`")


def find_tokens(
        tokens: Sequence[Token],
        search_pattern: Sequence[Sequence[Optional[TokenType]]]) -> Iterator[Sequence[Token]]:
    for search_start in range(len(tokens)):
        search_index = search_start

        for types in search_pattern:
            if search_index >= len(tokens):
                break

            if tokens[search_index].type_ in types:
                search_index += 1
            elif None in types:
                continue
            else:
                break
        else:
            yield tokens[search_start:search_index]

    return None
