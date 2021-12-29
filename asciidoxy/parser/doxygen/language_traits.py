# Copyright (C) 2019, TomTom (http://tomtom.com).
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
"""Traits describing how to parse different languages."""

import logging
from abc import ABC
from enum import Enum, auto
from typing import Mapping, Optional, Sequence, Tuple

logger = logging.getLogger(__name__)


class TokenCategory(Enum):
    """Category of tokens in a language grammer.

    Attributes:
        UNKNOWN:             Unidentified token.
        WHITESPACE:          Whitespace between other tokens.
        QUALIFIER:           Type qualifiers.
        OPERATOR:            Operators applied to the type.
        NAME:                Name of the type.
        NESTED_START:        Start of list of nested types.
        NESTED_SEPARATOR:    Separator between multiple nested types.
        NESTED_END:          End of list of nested types.
        WILDCARD:            Type wildcard.
        WILDCARD_BOUNDS:     Bounds limiting a wildcard.
        INVALID:             Invalid tokens. Require a workaround.
        NAMESPACE_SEPARATOR: Separator between namespaces.
        ARGS_START:          Start of a list of argument types.
        ARGS_SEPARATOR:      Separator between multiple argument types.
        ARGS_END:            End of a list of argument types.
        ARG_NAME:            Name of an argument.
        SEPARATOR:           Generic separator. Used if the same character is used for different
                                 kinds of separators. Use `adapt_separators` to select the right
                                 kind.
        BUILT_IN_NAME:       Type name that is built-in in the language.
        BLOCK:               Token indicating a block definition.
        ANNOTATION:          Token indicating an annotation.
    """
    UNKNOWN = auto()
    WHITESPACE = auto()
    QUALIFIER = auto()
    OPERATOR = auto()
    NAME = auto()
    NESTED_START = auto()
    NESTED_SEPARATOR = auto()
    NESTED_END = auto()
    WILDCARD = auto()
    WILDCARD_BOUNDS = auto()
    INVALID = auto()
    NAMESPACE_SEPARATOR = auto()
    ARGS_START = auto()
    ARGS_SEPARATOR = auto()
    ARGS_END = auto()
    ARG_NAME = auto()
    SEPARATOR = auto()
    BUILT_IN_NAME = auto()
    BLOCK = auto()
    ANNOTATION = auto()


class LanguageTraits(ABC):
    """Traits for specific languages needed to parse their Doxyxen XML files.

    Implement this for each language that AsciiDoxy will support.

    Attributes:
        TAG:                      Tag for identifying the language.
        TOKENS:                   The allowed tokens for each supported token type.
        TOKEN_BOUNDARIES:         Characters that indicate the boundary between tokens. Token
                                      boundaries are considered tokens themselves as well.
        SEPARATOR_TOKENS_OVERLAP: Tokens for different separators overlap, and need to be adapted.
        ALLOWED_PREFIXES:         Token types that are allowed in type prefixes.
        ALLOWED_SUFFIXES:         Token types that are allowed in type suffixes.
        ALLOWED_NAMES:            Token types that are allowed in type names.
        NESTING_BOUNDARY:         Character(s) indicating the start of nested types.
        NAMESPACE_SEPARATOR:      Character(s) separating namespaces and names.
        FILE_EXTENSIONS:          Potential file extensions for source code files.
    """
    TAG: str

    TOKENS: Mapping[TokenCategory, Sequence[str]]
    TOKEN_BOUNDARIES: Sequence[str]
    SEPARATOR_TOKENS_OVERLAP: bool = False

    ALLOWED_PREFIXES: Optional[Sequence[TokenCategory]]
    ALLOWED_SUFFIXES: Optional[Sequence[TokenCategory]]
    ALLOWED_NAMES: Sequence[TokenCategory]

    NESTING_BOUNDARY: Optional[str]
    NAMESPACE_SEPARATOR: Optional[str]
    FILE_EXTENSIONS: Optional[Sequence[str]] = None

    @classmethod
    def is_language_standard_type(cls, type_name: str) -> bool:
        """Is the type a built-in type for the language?

        Built-in types do not need to be resolved to other types from Doxygen.

        Args:
            type_name: Type name to check.
        Returns:
            True if the type is built-in.
        """
        return False

    @classmethod
    def names(cls,
              raw_name: str,
              parent_name: str = "",
              kind: Optional[str] = None) -> Tuple[str, str, Optional[str]]:
        """Determine the full name, short name and namespace.

        Args:
            raw_name:    Raw name from the XML file.
            parent_name: Optional name of the parent element.
            kind:        Kind of element the name belongs to.

        Returns:
            Short name.
            Full name.
            Namespace.
        """
        name = cls.cleanup_name(raw_name)
        full_name = cls.full_name(name, parent_name, kind)
        namespace, short_name = cls.namespace_and_name(full_name, kind)
        return short_name, full_name, namespace

    @classmethod
    def cleanup_name(cls, name: str) -> str:
        """Clean up the name according to language rules.

        Doxygen causes some non C++ names to look like C++.

        Args:
            name: Name to clean up.
        Returns:
            Cleaned up version of the name.
        """
        return name

    @classmethod
    def short_name(cls, name: str) -> str:
        """Determine the short version of a type name.

        Removes the namespace to leave only the local name of the type.

        Args:
            name: Long or short version of the name.
        Returns:
            The short version of the name.
        """
        _, name = cls.namespace_and_name(name)
        return name

    @classmethod
    def full_name(cls, name: str, parent: str = "", kind: Optional[str] = None) -> str:
        """Determine the long version of a type name.

        The long name should include the namespace. If needed the namespace is deduced from a parent
        type.

        Args:
            name:   Long or short version of the name.
            parent: Name of a parent. Used to deduce namespace if needed.
            kind:   Kind of element this name applies to.
        Returns:
            Long version of the name.
        """
        if not cls.NAMESPACE_SEPARATOR:
            return name
        if not parent or name.startswith(f"{parent}{cls.NAMESPACE_SEPARATOR}"):
            return name
        if parent and cls.FILE_EXTENSIONS:
            for ext in cls.FILE_EXTENSIONS:
                if parent.endswith(ext):
                    return name
        return f"{parent}{cls.NAMESPACE_SEPARATOR}{name}"

    @classmethod
    def namespace(cls, full_name: str, kind: Optional[str] = None) -> Optional[str]:
        """Determine the namespace part of a type name.

        Args:
            full_name: Long version of a type name.
            kind:      Kind of element this namespace applies to.
        Returns:
            The namespace part of the name, or None if there is no namespace.
        """
        namespace, _ = cls.namespace_and_name(full_name, kind)
        return namespace

    @classmethod
    def namespace_and_name(cls,
                           full_name: str,
                           kind: Optional[str] = None) -> Tuple[Optional[str], str]:
        """Determine the namespace and short name from a fully qualified name.

        Args:
            full_name: Fully qualified name.
            kind:      Kind of element this namespace applies to.
        Returns:
            The namespace part of the name.
            The short name.
        """
        if not cls.NAMESPACE_SEPARATOR:
            return None, full_name
        if cls.NESTING_BOUNDARY:
            name, sep, nested = full_name.partition(cls.NESTING_BOUNDARY)
        else:
            name, sep, nested = full_name, "", ""
        namespace, _, name = name.rpartition(cls.NAMESPACE_SEPARATOR)
        return namespace if namespace else None, f"{name}{sep}{nested}"

    @classmethod
    def is_member_blacklisted(cls, kind: str, name: str) -> bool:
        """Is a member black-listed?

        Doxygen sometimes generates invalid members, that should be ignored.

        Args:
            kind: Kind of member.
            name: Name of the member.
        Returns:
            True if the member is black-listed.
        """
        return False

    @classmethod
    def unique_id(cls, id: Optional[str]) -> Optional[str]:
        """Generate a unique id that can be used to refer to an element.

        The unique id is also unique over multiple different languages.

        Args:
            id: Identifier as reported by Doxygen.
        Returns:
            Unique identifier.
        """
        if not id:
            return None

        # Workaround a bug in asciidoctor: if there is an occurrence of __ the anchor is not parsed
        # correctly: #2746
        id = id.replace("__", "-")

        return f"{cls.TAG}-{id}"
