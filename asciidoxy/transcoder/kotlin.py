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

from typing import List, Union

from .base import TranscoderBase
from ..model import Compound, Member, ReferableElement, TypeRef, TypeRefBase

# https://kotlinlang.org/docs/reference/java-interop.html#mapped-types
_MAPPED_TYPES = {
    # Java primitives
    "byte": "Byte",
    "short": "Short",
    "int": "Int",
    "long": "Long",
    "char": "Char",
    "float": "Float",
    "double": "Double",
    "boolean": "Boolean",

    # Java non-primitive built-ins
    "java.lang.Object": "Any",
    "java.lang.Cloneable": "Cloneable",
    "java.lang.Comparable": "Comparable",
    "java.lang.Enum": "Enum",
    "java.lang.Annotation": "Annotation",
    "java.lang.CharSequence": "CharSequence",
    "java.lang.String": "String",
    "java.lang.Number": "Number",
    "java.lang.Throwable": "Throwable",
    "Object": "Any",

    # Java boxed types
    "java.lang.Byte": "Byte",
    "java.lang.Short": "Short",
    "java.lang.Integer": "Int",
    "Integer": "Int",
    "java.lang.Long": "Long",
    "java.lang.Character": "Char",
    "Character": "Char",
    "java.lang.Float": "Float",
    "java.lang.Double": "Double",
    "java.lang.Boolean": "Boolean",

    # Other
    "void": "Unit",
}

_NULLABLE_MAPPED_TYPES = [
    "java.lang.Byte",
    "java.lang.Short",
    "java.lang.Integer",
    "java.lang.Long",
    "java.lang.Character",
    "java.lang.Float",
    "java.lang.Double",
    "java.lang.Boolean",
    "Byte",
    "Short",
    "Integer",
    "Long",
    "Character",
    "Float",
    "Double",
    "Boolean",
]

_NULLABLE_OR_NOT_MAPPED_TYPES = [
    "java.lang.Object",
    "java.lang.Cloneable",
    "java.lang.Comparable",
    "java.lang.Enum",
    "java.lang.Annotation",
    "java.lang.CharSequence",
    "java.lang.String",
    "java.lang.Number",
    "java.lang.Throwable",
    "Object",
    "Cloneable",
    "Comparable",
    "Enum",
    "Annotation",
    "CharSequence",
    "String",
    "Number",
    "Throwable",
]


class KotlinTranscoder(TranscoderBase):
    SOURCE = "java"
    TARGET = "kotlin"

    def convert_name(self, source_element: Union[ReferableElement, TypeRefBase]) -> str:
        return _MAPPED_TYPES.get(source_element.name, source_element.name)

    def convert_full_name(self, source_element: ReferableElement) -> str:
        return _MAPPED_TYPES.get(source_element.full_name, source_element.full_name)

    def _member(self, member: Member) -> Member:
        transcoded = super()._member(member)

        if (transcoded.returns is not None and transcoded.returns.type is not None
                and transcoded.returns.type.name == "Unit"):
            transcoded.returns = None

        return transcoded

    def type_ref(self, type_ref: TypeRef) -> TypeRef:
        transcoded = super().type_ref(type_ref)

        if type_ref.name in _NULLABLE_MAPPED_TYPES:
            if transcoded.suffix:
                if "?" not in transcoded.suffix:
                    transcoded.suffix = f"?{transcoded.suffix}"
            else:
                transcoded.suffix = "?"

        if type_ref.name in _NULLABLE_OR_NOT_MAPPED_TYPES:
            if transcoded.suffix:
                if "!" not in transcoded.suffix:
                    transcoded.suffix = f"!{transcoded.suffix}"
            else:
                transcoded.suffix = "!"

        return transcoded

    def _compound(self, compound: Compound) -> Compound:
        transcoded = super()._compound(compound)
        self.transform_properties(transcoded.members)
        return transcoded

    @staticmethod
    def transform_properties(members: List[Member]) -> List[Member]:
        getters = {
            m.name: m
            for m in members
            if ((m.name.startswith("get") or m.name.startswith("is")) and len(m.params) == 0)
            and m.returns is not None
        }
        setters = {
            m.name: m
            for m in members
            if (m.name.startswith("set") and len(m.params) == 1) and m.returns is None
        }

        for getter_name, getter in getters.items():
            if getter_name.startswith("get"):
                property_name = getter_name[3:]
            else:
                property_name = getter_name[2:]

            setter = setters.get(f"set{property_name}", None)
            if setter is None:
                continue

            if getter.name.startswith("get"):
                getter.name = f"{property_name[0].lower()}{property_name[1:]}"
                if getter.namespace:
                    getter.full_name = f"{getter.namespace}.{getter.name}"
                else:
                    getter.full_name = getter.name
            getter.kind = "property"
            members.remove(setter)

        return members
