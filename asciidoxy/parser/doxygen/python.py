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
"""Support for parsing python documentation."""

import string

from typing import List, Optional

from .language_traits import LanguageTraits, TokenCategory
from .parser_base import ParserBase
from .type_parser import Token, TypeParser


class PythonTraits(LanguageTraits):
    """Traits for parsing python documentation."""
    TAG: str = "python"

    NESTED_STARTS = "[",
    NESTED_ENDS = "]",
    NESTED_SEPARATORS = ",",

    TOKENS = {
        TokenCategory.NESTED_START: NESTED_STARTS,
        TokenCategory.NESTED_END: NESTED_ENDS,
        TokenCategory.NESTED_SEPARATOR: NESTED_SEPARATORS,
    }

    TOKEN_BOUNDARIES = (NESTED_STARTS + NESTED_ENDS + NESTED_SEPARATORS + tuple(string.whitespace))

    ALLOWED_PREFIXES = None
    ALLOWED_SUFFIXES = None
    ALLOWED_NAMES = TokenCategory.WHITESPACE, TokenCategory.NAME,

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        return name.replace("::", ".").replace('"', "").strip()

    @classmethod
    def short_name(cls, name: str) -> str:
        return name.split(".")[-1]

    @classmethod
    def full_name(cls, name: str, parent: str = "", kind: Optional[str] = None) -> str:
        if not parent or name.startswith(f"{parent}."):
            return name
        return f"{parent}.{name}"

    @classmethod
    def namespace(cls, full_name: str, kind: Optional[str] = None) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None


class PythonTypeParser(TypeParser):
    """Parser for python types."""
    TRAITS = PythonTraits

    @classmethod
    def adapt_tokens(cls,
                     tokens: List[Token],
                     array_tokens: Optional[List[Token]] = None) -> List[Token]:
        if not tokens:
            return []

        # Nested type hints are stored as arrays in a separate element.
        if array_tokens:
            # There is a bug where the last closing bracket is stored in the type name. We need to
            # insert the nested types in front of that bracket
            if tokens[-1].category == TokenCategory.WHITESPACE:
                tokens.pop(-1)
            if tokens[-1].category == TokenCategory.NESTED_END:
                tokens[-1:-1] = array_tokens
            else:
                tokens.extend(array_tokens)

        # Workaround for Doxygen issue
        tokens = [t for t in tokens if t.text != "def"]

        return tokens


class PythonParser(ParserBase):
    """Parser for python documentation."""
    TRAITS = PythonTraits
    TYPE_PARSER = PythonTypeParser
