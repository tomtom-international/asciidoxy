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
"""Base support for parsing documentation for different languages."""

import logging

from abc import ABC
from enum import Enum, auto
from typing import Optional, Sequence

logger = logging.getLogger(__name__)


class TokenType(Enum):
    """Types of tokens in a language grammer.

    Attributes:
        UNKNOWN:          Unidentified token.
        WHITESPACE:       Whitespace between other tokens.
        QUALIFIER:        Type qualifiers.
        OPERATOR:         Operators applied to the type.
        NAME:             Name of the type.
        NESTED_START:     Start of list of nested types.
        NESTED_SEPARATOR: Separator between multiple nested types.
        NESTED_END:       End of list of nested types.
    """
    UNKNOWN = auto()
    WHITESPACE = auto()
    QUALIFIER = auto()
    OPERATOR = auto()
    NAME = auto()
    NESTED_START = auto()
    NESTED_SEPARATOR = auto()
    NESTED_END = auto()


class LanguageTraits(ABC):
    """Traits for specific languages needed to parse their Doxyxen XML files.

    Attributes:
        TAG:                   Tag for identifying the language.
        NESTED_STARTS:         Tokens indicating the start of a list of nested types. Results in
                                   token type NESTED_START.
        NESTED_ENDS:           Tokens indicating the end of a list of nested types. Results in
                                   token type NESTED_END.
        NESTED_SEPARATORS:     Tokens separating multiple nested types. Results in token type
                                   NESTED_SEPARATOR.
        OPERATORS:             Tokens for type operators. Results in token type OPERATOR.
        QUALIFIERS:            Tokens for type qualifiers. Results in token type QUALIFIER.
        TOKEN_BOUNDARIES:      Characters that indicate the boundary between tokens. Token
                                   boundaries are considered tokens themselves as well.
        ALLOWED_PREFIXES:      Token types that are allowed in type prefixes.
        ALLOWED_SUFFIXES:      Token types that are allowed in type suffixes.
        ALLOWED_NAMES:         Token types that are allowed in type names.
    """
    TAG: str

    NESTED_STARTS: Optional[Sequence[str]]
    NESTED_ENDS: Optional[Sequence[str]]
    NESTED_SEPARATORS: Optional[Sequence[str]]
    OPERATORS: Optional[Sequence[str]]
    QUALIFIERS: Optional[Sequence[str]]

    TOKEN_BOUNDARIES: Sequence[str]

    ALLOWED_PREFIXES: Optional[Sequence[TokenType]]
    ALLOWED_SUFFIXES: Optional[Sequence[TokenType]]
    ALLOWED_NAMES: Sequence[TokenType]

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        return False

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        return name

    @classmethod
    def short_name(cls, name: str) -> str:
        return name

    @classmethod
    def full_name(cls, name: str, parent: str = "") -> str:
        return name

    @classmethod
    def namespace(cls, full_name: str) -> Optional[str]:
        return None

    @classmethod
    def is_member_blacklisted(cls, kind: str, name: str) -> bool:
        return False

    @classmethod
    def unique_id(cls, id: Optional[str]) -> Optional[str]:
        if not id:
            return None

        # Workaround a bug in asciidoctor: if there is an occurrence of __ the anchor is not parsed
        # correctly: #2746
        id = id.replace("__", "-")

        return f"{cls.TAG}-{id}"
