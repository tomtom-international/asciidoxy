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
"""Transcoding Java reference into Kotlin."""

from typing import Union

from .base import TranscoderBase
from ..model import ReferableElement, TypeRefBase

_JAVA_TO_KOTLIN_TYPE_MAPPING = {
    # Integral
    "byte": "Byte",
    "Byte": "Byte",
    "short": "Short",
    "Short": "Short",
    "int": "Int",
    "Integer": "Int",
    "long": "Long",
    "Long": "Long",
    # Floating-point
    "float": "Float",
    "Float": "Float",
    "double": "Double",
    "Double": "Double",
    # Other
    "boolean": "Boolean",
    "Boolean": "Boolean",
    "char": "Char",
    "Character": "Char",
}


def _to_kotlin_type(typename: str):
    if typename in _JAVA_TO_KOTLIN_TYPE_MAPPING:
        return _JAVA_TO_KOTLIN_TYPE_MAPPING[typename]
    else:
        return typename


class KotlinTranscoder(TranscoderBase):
    SOURCE = "java"
    TARGET = "kotlin"

    def convert_name(self, source_element: Union[ReferableElement, TypeRefBase]) -> str:
        return _to_kotlin_type(source_element.name)

    def convert_full_name(self, source_element: ReferableElement) -> str:
        return _to_kotlin_type(source_element.full_name)
