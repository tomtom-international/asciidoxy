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
"""Support for parsing C++ documentation."""

import re

from typing import Optional

from .language_base import Language


class CppLanguage(Language):
    """Language support for C++."""
    TAG: str = "cpp"

    TYPE_PREFIXES = re.compile(r"((const|volatile|constexpr|mutable|enum|class)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"(\s*(\*|&|const))+")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"((unsigned|signed|short|long)\s+)*(?:(?!\bconst)[a-zA-Z0-9_:])+")

    LANGUAGE_BUILD_IN_TYPES = ("void", "bool", "signed char", "unsigned char", "char", "wchar_t",
                               "char16_t", "char32_t", "char8_t", "float", "double", "long double",
                               "short", "short int", "signed short", "signed short int",
                               "unsigned short", "unsigned short int", "int", "signed",
                               "signed int", "unsigned", "unsigned int", "long", "long int",
                               "signed long", "signed long int", "unsigned long",
                               "unsigned long int", "long long", "long long int",
                               "signed long long", "signed long long int", "unsigned long long",
                               "unsigned long long int")

    def is_language_standard_type(self, type_name: str) -> bool:
        return type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name.startswith("std::")

    def short_name(self, name: str) -> str:
        return name.split("::")[-1]

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}::{name}"

    def namespace(self, full_name: str) -> Optional[str]:
        if "::" in full_name:
            namespace, _ = full_name.rsplit("::", maxsplit=1)
            return namespace
        else:
            return None

    def is_member_blacklisted(self, kind: str, name: str) -> bool:
        return kind == "friend"
