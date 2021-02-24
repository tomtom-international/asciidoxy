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
"""Parsing of types from strings and XML."""

import logging

import xml.etree.ElementTree as ET

from typing import Iterator, List, Optional, Sequence, Tuple, Type

from .driver_base import DriverBase
from .language_traits import LanguageTraits, TokenCategory
from ...model import Parameter, TypeRef

logger = logging.getLogger(__name__)


class Token:
    """A single token in a language grammar.

    Attributes:
        category: Category of the token in the langugage grammar.
        refid:    If available, a unique identifier for the element the token symbolizes.
        kind:     If available, the kind of element the token symbolizes.
    """
    category: TokenCategory
    refid: Optional[str]
    kind: Optional[str]

    def __init__(self,
                 text: str,
                 category: TokenCategory = TokenCategory.UNKNOWN,
                 refid: Optional[str] = None,
                 kind: Optional[str] = None):
        self.category = category
        self.text = text
        self.refid = refid
        self.kind = kind

    def __eq__(self, other) -> bool:
        return ((self.category, self.text, self.refid, self.kind) == (other.category, other.text,
                                                                      other.refid, other.kind))

    def __str__(self) -> str:
        return f"{self.category}: {repr(self.text)}"

    __repr__ = __str__


class TypeParseError(Exception):
    """Error raised when type parsing fails.

    This exception is still caught internally to trigger fallback to unparsed types.

    Attributes:
        msg: Message explaining the parser error.
    """
    msg: str

    def __init__(self, msg: str):
        self.msg = msg

    def __str__(self) -> str:
        return f"Failed to parse type: {self.msg}"


class TypeParser:
    """Generic type parser from XML and plain text.

    The parser is anemic by design: it has no internal state. Functionality is implemented in class
    and static methods.

    Attributes:
        TRAITS: Specifics for the language grammar to parse.
    """
    TRAITS: Type[LanguageTraits]

    @classmethod
    def parse_xml(cls,
                  type_element: ET.Element,
                  array_element: Optional[ET.Element] = None,
                  driver: Optional[DriverBase] = None,
                  namespace: Optional[str] = None) -> Optional[TypeRef]:
        """Parse a type from an XML element.

        Information from the Doxygen `<type>` and `<array>` elements are combined if needed.

        Arguments:
            type_element:  The `<type>` element from Doxygen.
            array_element: The `<array>` element from Doxygen, if available.
            driver:        Driver to register types without refids with.
            namespace:     Namespace containing the type.
        Returns:
            A `TypeRef` for the type, or None if there is no type information.
        """
        tokens = cls.tokenize_xml(type_element)
        array_tokens = cls.tokenize_xml(array_element) if array_element is not None else []
        tokens = cls.adapt_tokens(tokens, array_tokens)
        if len(tokens) == 0 or all(token.category == TokenCategory.WHITESPACE for token in tokens):
            return None
        return cls.type_from_tokens(tokens, driver, namespace)

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        """Adapt tokens using language specific rules."""
        if cls.TRAITS.SEPARATOR_TOKENS_OVERLAP:
            tokens = cls.adapt_separators(tokens)
        return tokens

    @classmethod
    def adapt_separators(cls, tokens: List[Token]) -> List[Token]:
        """Set the correct category for separator tokens."""
        scope_types = []
        for i, token in enumerate(tokens):
            if token.category in (TokenCategory.NESTED_START, TokenCategory.NESTED_END,
                                  TokenCategory.ARGS_START, TokenCategory.ARGS_END):
                scope_types.append(token.category)

            elif token.category in (TokenCategory.SEPARATOR, TokenCategory.NESTED_SEPARATOR,
                                    TokenCategory.ARGS_SEPARATOR):
                try:
                    token.category = cls._determine_separator_category(scope_types)
                except TypeParseError:
                    logger.warning(f"Cannot determine type of separator of token {i} in"
                                   f"{''.join(t.text for t in tokens)}")
                    token.category = TokenCategory.UNKNOWN
        return tokens

    @staticmethod
    def _determine_separator_category(scope_types: List[TokenCategory]) -> TokenCategory:
        nested_ends = 0
        args_ends = 0
        for scope_type in reversed(scope_types):
            if scope_type == TokenCategory.NESTED_END:
                nested_ends += 1
            elif scope_type == TokenCategory.ARGS_END:
                args_ends += 1
            elif scope_type == TokenCategory.NESTED_START:
                if nested_ends == 0:
                    return TokenCategory.NESTED_SEPARATOR
                else:
                    nested_ends -= 1
            elif scope_type == TokenCategory.ARGS_START:
                if args_ends == 0:
                    return TokenCategory.ARGS_SEPARATOR
                else:
                    args_ends -= 1
        raise TypeParseError("Cannot determine type of separator.")

    @classmethod
    def tokenize_text(cls, text: str) -> List[Token]:
        """Split a text into language grammar tokens."""
        tokens: List[Token] = []

        def append_token(text: str) -> None:
            token = cls.make_text_token(text)
            if token.category == TokenCategory.WHITESPACE and tokens and tokens[
                    -1].category == token.category:
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
        """Determine the token category for a text and create a token for it."""
        if text.isspace():
            category = TokenCategory.WHITESPACE
            text = " "
        else:
            for token_type, tokens in cls.TRAITS.TOKENS.items():
                if text in tokens:
                    category = token_type
                    break
            else:
                category = TokenCategory.NAME

        return Token(text, category)

    @classmethod
    def tokenize_xml(cls, element: ET.Element) -> List[Token]:
        """Split an XML element and its contents into language grammar tokens."""
        tokens = []

        if element.tag == "ref":
            name = element.text
            refid = element.get("refid", None)
            kind = element.get("kindref", None)

            if not name or not refid:
                logger.error(f"Encountered reference XML element without name or id: "
                             f"{ET.tostring(element, encoding='utf-8')}")

            if name:
                tokens.append(Token(name, refid=refid, kind=kind, category=TokenCategory.NAME))

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
                         namespace: Optional[str] = None) -> Optional[TypeRef]:
        """Create a `TypeRef` from a sequence of tokens.

        Returns:
            A `TypeRef` if sufficient tokens are present, or None if all tokens are whitespace.
        """
        if not tokens or all(t.category == TokenCategory.WHITESPACE for t in tokens):
            return None

        original_tokens = tokens
        tokens = tokens[:]

        def fallback():
            return TypeRef(cls.TRAITS.TAG, "".join(t.text for t in original_tokens))

        prefixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_PREFIXES)
        cls.remove_leading_whitespace(prefixes)

        names, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_NAMES)
        cls.remove_leading_whitespace(names)
        tokens[:0] = cls.remove_trailing_whitespace(names)

        nested_types: Optional[List[TypeRef]] = []
        try:
            nested_types, tokens = cls.nested_types(tokens, driver, namespace)
        except TypeParseError as e:
            logger.warning(f"Failed to parse nested types: {e}")
            return fallback()

        suffixes, tokens = cls.select_tokens(tokens, cls.TRAITS.ALLOWED_SUFFIXES)
        tokens[:0] = cls.remove_trailing_whitespace(suffixes)

        arg_types: Optional[List[Parameter]] = []
        try:
            arg_types, tokens = cls.arg_types(tokens, driver, namespace)
        except TypeParseError as e:
            logger.warning(f"Failed to parse args: {e}")
            return fallback()

        if not names:
            logger.warning(f"No name found in `{'`,`'.join(t.text for t in original_tokens)}`")
            return fallback()

        if tokens and any(t.category != TokenCategory.WHITESPACE for t in tokens):
            logger.warning(f"Unexpected trailing token(s) `{'`,`'.join(t.text for t in tokens)}`"
                           f" in `{'`,`'.join(t.text for t in original_tokens)}`")
            suffixes.extend(tokens)

        type_ref = TypeRef(cls.TRAITS.TAG)

        if arg_types is not None:
            type_ref.returns = TypeRef(cls.TRAITS.TAG)
            type_ref.returns.name = cls.TRAITS.cleanup_name("".join(n.text for n in names))
            type_ref.returns.prefix = "".join(p.text for p in prefixes)
            type_ref.returns.suffix = "".join(s.text for s in suffixes)
            type_ref.returns.nested = nested_types
            type_ref.returns.id = cls.TRAITS.unique_id(names[0].refid)
            type_ref.returns.kind = names[0].kind
            type_ref.kind = "closure"

        else:
            type_ref.name = cls.TRAITS.cleanup_name("".join(n.text for n in names))
            type_ref.prefix = "".join(p.text for p in prefixes)
            type_ref.suffix = "".join(s.text for s in suffixes)
            type_ref.nested = nested_types
            type_ref.id = cls.TRAITS.unique_id(names[0].refid)
            type_ref.kind = names[0].kind

        type_ref.args = arg_types
        type_ref.namespace = namespace

        if (driver is not None and type_ref.name and not type_ref.id
                and not cls.TRAITS.is_language_standard_type(type_ref.name)):
            driver.unresolved_ref(type_ref)
        if (driver is not None and type_ref.returns is not None and type_ref.returns.name
                and not type_ref.returns.id
                and not cls.TRAITS.is_language_standard_type(type_ref.returns.name)):
            driver.unresolved_ref(type_ref.returns)

        return type_ref

    @staticmethod
    def select_tokens(
            tokens: List[Token],
            categories: Optional[Sequence[TokenCategory]]) -> Tuple[List[Token], List[Token]]:
        """Select all tokens matching a sequence of categories.

        Picks tokens from the front of `tokens` until a token of another category is encountered.

        Args:
            tokens:     Tokens to select from.
            categories: Categories for which the tokens needs to be selected. Can be None to not
                            select any tokens.
        Returns:
            Tokens matching the categories.
            Tokens left-over after removing the matching tokens.
        """
        if categories:
            for i, t in enumerate(tokens):
                if t.category not in categories:
                    return tokens[:i], tokens[i:]
            return tokens, []
        else:
            return [], tokens

    @classmethod
    def remove_leading_whitespace(cls, tokens) -> List[Token]:
        """Remove leading whitespace from `tokens` and return it."""
        return cls._remove_whitespace(tokens, 0)

    @classmethod
    def remove_trailing_whitespace(cls, tokens) -> List[Token]:
        """Remove trailing whitespace from `tokens` and return it."""
        return cls._remove_whitespace(tokens, -1)

    @staticmethod
    def _remove_whitespace(tokens, location) -> List[Token]:
        ret = []
        while tokens and tokens[location].category == TokenCategory.WHITESPACE:
            ret.append(tokens.pop(location))
        return ret

    @classmethod
    def nested_types(
            cls,
            tokens: List[Token],
            driver: Optional[DriverBase] = None,
            namespace: Optional[str] = None) -> Tuple[Optional[List[TypeRef]], List[Token]]:
        """Parse nested types from tokens if present.

        Returns:
            A list of `TypeRef` for each nested type, an empty list if a nested block is present
                without types, or None if there is no nested block.
        """

        nested_type_tokens, tokens = cls.select_nested_tokens(tokens, TokenCategory.NESTED_START,
                                                              TokenCategory.NESTED_END,
                                                              TokenCategory.NESTED_SEPARATOR)
        if nested_type_tokens is None:
            return None, tokens
        types = (cls.type_from_tokens(ntt, driver, namespace) for ntt in nested_type_tokens)
        return [t for t in types if t is not None], tokens

    @classmethod
    def arg_types(cls,
                  tokens: List[Token],
                  driver: Optional[DriverBase] = None,
                  namespace: Optional[str] = None) -> Tuple[Optional[List[Parameter]], List[Token]]:
        """Parse function argument types from tokens if present.

        Returns:
            A list of `Parameter` for each argument, an empty list if an argument block is present
                without arguments, or None if there is no argument block.
        """

        nested_type_tokens, tokens = cls.select_nested_tokens(tokens, TokenCategory.ARGS_START,
                                                              TokenCategory.ARGS_END,
                                                              TokenCategory.ARGS_SEPARATOR)
        if nested_type_tokens is None:
            return None, tokens

        args = (cls.arg_from_tokens(ntt, driver, namespace) for ntt in nested_type_tokens)
        return [a for a in args if a is not None], tokens

    @classmethod
    def arg_from_tokens(cls,
                        tokens: List[Token],
                        driver: Optional[DriverBase] = None,
                        namespace: Optional[str] = None) -> Optional[Parameter]:
        """Parse an argument definition from a sequence of tokens.

        Returns:
            The argument definition, or None if there is only whitespace.
        """
        if not tokens or all(t.category == TokenCategory.WHITESPACE for t in tokens):
            return None

        name_tokens: List[Token] = []
        while tokens and tokens[-1].category == TokenCategory.ARG_NAME:
            name_tokens.insert(0, tokens.pop(-1))

        arg = Parameter()
        arg.type = cls.type_from_tokens(tokens, driver, namespace)
        arg.name = "".join(t.text for t in name_tokens)
        return arg

    @classmethod
    def select_nested_tokens(
            cls, tokens: List[Token], start_token: TokenCategory, end_token: TokenCategory,
            separator_token: TokenCategory) -> Tuple[Optional[List[List[Token]]], List[Token]]:
        """Find a nested block using specific start, end and separator tokens.

        Returns:
            A sequence of tokens for each entry in a nested block. The separator is used to return
                multiple token sequences per nested block. An empty list if the nested block is
                present but empty. None if no nested block is found.
            Left-over tokens after removing the nested block.
        Raises:
            TypeParseError The nested block is not terminated correctly.
        """
        original_tokens = tokens
        tokens = tokens[:]
        nested_type_tokens = []

        for i, t in enumerate(tokens):
            if t.category == TokenCategory.WHITESPACE:
                continue
            elif t.category == start_token:
                tokens = tokens[i + 1:]
                break
            else:
                return None, tokens
        else:
            return None, tokens

        level = 0
        while tokens:
            for i, t in enumerate(tokens):
                if t.category == start_token:
                    level += 1
                elif level > 0 and t.category == end_token:
                    level -= 1
                elif level == 0 and t.category in (separator_token, end_token):
                    nested_type_tokens.append(tokens[:i])
                    tokens = tokens[i + 1:]

                    if t.category == end_token:
                        return nested_type_tokens, tokens
                    else:
                        break
            else:
                break

        raise TypeParseError("Unexpected end of nested types:"
                             f" `{''.join(t.text for t in original_tokens)}`")


def find_tokens(
        tokens: Sequence[Token],
        search_pattern: Sequence[Sequence[Optional[TokenCategory]]]) -> Iterator[Sequence[Token]]:
    """Find a sequence of tokens matching a sequence of categories.

    The `search_pattern` is a sequence of sequences of categories to match. Tokens need to match at
    least one of the categories in each sequence, in order. If `None` is present in a sequence, it
    means that the sequence is optional and can be skipped.

    Args:
        tokens: Sequence of tokens to search in.
        search_patterns: Pattern of categories to match.
    Returns:
        Iterator over all matches.
    """
    for search_start in range(len(tokens)):
        search_index = search_start

        for categories in search_pattern:
            if search_index >= len(tokens):
                break

            if tokens[search_index].category in categories:
                search_index += 1
            elif None in categories:
                continue
            else:
                break
        else:
            yield tokens[search_start:search_index]

    return None
