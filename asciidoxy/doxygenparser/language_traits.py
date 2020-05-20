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
from typing import Optional, Pattern

logger = logging.getLogger(__name__)


class LanguageTraits(ABC):
    """Traits for specific languages needed to parse their Doxyxen XML files.

    Attributes:
        TAG:                   Tag for identifying the language.
        TYPE_PREFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a prefix to the type.
        TYPE_SUFFIXES:         Pattern matching text that is not part of the type name, but instead
                                   is a suffix to the type.
        TYPE_NESTED_START:     Pattern matching the start of a nested type.
        TYPE_NESTED_SEPARATOR: Pattern matching a separator between multiple nested types.
        TYPE_NESTED_END:       Pattern matching the end of a nested type.
        TYPE_NAME:             Pattern matching a type's name.
    """
    TAG: str

    TYPE_PREFIXES: Optional[Pattern]
    TYPE_SUFFIXES: Optional[Pattern]
    TYPE_NESTED_START: Pattern
    TYPE_NESTED_SEPARATOR: Pattern
    TYPE_NESTED_END: Pattern
    TYPE_NAME: Pattern

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
