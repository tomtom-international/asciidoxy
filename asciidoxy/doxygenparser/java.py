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
"""Support for Java documentation."""

import re

from typing import Optional

from .language_base import Language


class JavaLanguage(Language):
    """Language support for Java."""
    TAG: str = "java"

    TYPE_PREFIXES = re.compile(r"((([\w?]+?\s+extends)|final|synchronized|transient)\s*)+\s+")
    TYPE_SUFFIXES = re.compile(r"")
    TYPE_NESTED_START = re.compile(r"\s*<\s*")
    TYPE_NESTED_SEPARATOR = re.compile(r"\s*,\s*")
    TYPE_NESTED_END = re.compile(r"\s*>")
    TYPE_NAME = re.compile(r"[a-zA-Z0-9_:\.? ]+")

    LANGUAGE_BUILD_IN_TYPES = ("void", "long", "int", "boolean", "byte", "char", "short", "float",
                               "double", "String")
    COMMON_GENERIC_NAMES = ("T", "?", "T ", "? ")

    def is_language_standard_type(self, type_name: str) -> bool:
        return (type_name in self.LANGUAGE_BUILD_IN_TYPES or type_name in self.COMMON_GENERIC_NAMES
                or type_name.startswith("java.") or type_name.startswith("android.")
                or type_name.startswith("native "))

    def cleanup_name(self, name: str) -> str:
        return name.replace("::", ".").strip()

    def short_name(self, name: str) -> str:
        return name.split(".")[-1]

    def full_name(self, name: str, parent: str = "") -> str:
        if name.startswith(parent):
            return name
        return f"{parent}.{name}"

    def namespace(self, full_name: str) -> Optional[str]:
        if "." in full_name:
            namespace, _ = full_name.rsplit(".", maxsplit=1)
            return namespace
        else:
            return None
