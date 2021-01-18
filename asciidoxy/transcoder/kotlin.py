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

from typing import List, Optional, Tuple, Union

from .base import TranscoderBase
from ..model import Compound, Parameter, ReferableElement, TypeRef, TypeRefBase

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

_NONNULL_MAPPED_TYPES = [
    "byte",
    "short",
    "int",
    "long",
    "char",
    "float",
    "double",
    "boolean",
    "void",
]

# https://kotlinlang.org/docs/reference/java-interop.html#nullability-annotations
# https://github.com/JetBrains/kotlin/blob/master/core/compiler.common.jvm/src/org/jetbrains/kotlin/load/java/JvmAnnotationNames.kt
_NULLABLE_ANNOTATIONS = [
    "@Nullable",
    "@CheckForNull",
    "@PossiblyNull",
    "@NullableDecl",
    "@RecentlyNullable",
    "@org.jetbrains.annotations.Nullable",
    "@androidx.annotation.Nullable",
    "@android.support.annotation.Nullable",
    "@android.annotation.Nullable",
    "@com.android.annotations.Nullable",
    "@org.eclipse.jdt.annotation.Nullable",
    "@org.checkerframework.checker.nullness.qual.Nullable",
    "@javax.annotation.Nullable",
    "@javax.annotation.CheckForNull",
    "@edu.umd.cs.findbugs.annotations.CheckForNull",
    "@edu.umd.cs.findbugs.annotations.Nullable",
    "@edu.umd.cs.findbugs.annotations.PossiblyNull",
    "@io.reactivex.annotations.Nullable",
    "@org.checkerframework.checker.nullness.compatqual.NullableDecl",
    "@androidx.annotation.RecentlyNullable",
]

_NONNULL_ANNOTATIONS = [
    "@NotNull",
    "@NonNull",
    "@NonNullDecl",
    "@RecentlyNonNull",
    "@org.jetbrains.annotations.NotNull",
    "@edu.umd.cs.findbugs.annotations.NonNull",
    "@androidx.annotation.NonNull",
    "@android.support.annotation.NonNull",
    "@android.annotation.NonNull",
    "@com.android.annotations.NonNull",
    "@org.eclipse.jdt.annotation.NonNull",
    "@org.checkerframework.checker.nullness.qual.NonNull",
    "@lombok.NonNull",
    "@io.reactivex.annotations.NonNull"
    "@javax.annotation.Nonnull",
    "@org.checkerframework.checker.nullness.compatqual.NonNullDecl",
    "@androidx.annotation.RecentlyNonNull",
]

# https://kotlinlang.org/docs/reference/java-interop.html#java-arrays
_PRIMITIVE_ARRAY_TYPES = [
    "byte",
    "short",
    "int",
    "long",
    "char",
    "float",
    "double",
    "boolean",
]


class KotlinTranscoder(TranscoderBase):
    SOURCE = "java"
    TARGET = "kotlin"

    def convert_name(self, source_element: Union[ReferableElement, TypeRefBase]) -> str:
        return _MAPPED_TYPES.get(source_element.name, source_element.name)

    def convert_full_name(self, source_element: ReferableElement) -> str:
        return _MAPPED_TYPES.get(source_element.full_name, source_element.full_name)

    def _compound(self, compound: Compound) -> Compound:
        transcoded = super()._compound(compound)
        transform_properties(transcoded.members)

        if (transcoded.returns is not None and transcoded.returns.type is not None
                and transcoded.returns.type.name == "Unit"):
            transcoded.returns = None

        return transcoded

    def type_ref(self, type_ref: TypeRef) -> TypeRef:
        transcoded = super().type_ref(type_ref)
        transcoded = transform_array(type_ref, transcoded)
        transcoded = set_nullability(type_ref, transcoded)

        if transcoded.prefix:
            transcoded.prefix = transcoded.prefix.replace("? extends", "out")
            transcoded.prefix = transcoded.prefix.replace("? super", "in")

        return transcoded

    def parameter(self, parameter: Parameter) -> Parameter:
        transcoded = super().parameter(parameter)
        transcoded = transform_vararg(transcoded)
        return transcoded


def transform_properties(members: List[Compound]) -> List[Compound]:
    getters = {
        m.name: m
        for m in members
        if ((m.name.startswith("get") or m.name.startswith("is")) and len(m.params) == 0)
        and m.returns is not None
    }
    setters = {
        m.name: m
        for m in members if (m.name.startswith("set") and len(m.params) == 1) and m.returns is None
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


def set_nullability(type_ref: TypeRef, transcoded: TypeRef) -> TypeRef:
    nullable_prefix, transcoded.prefix = strip_annotations(transcoded.prefix, _NULLABLE_ANNOTATIONS)
    nullable_suffix, transcoded.suffix = strip_annotations(transcoded.suffix, _NULLABLE_ANNOTATIONS)
    nonnull_prefix, transcoded.prefix = strip_annotations(transcoded.prefix, _NONNULL_ANNOTATIONS)
    nonnull_suffix, transcoded.suffix = strip_annotations(transcoded.suffix, _NONNULL_ANNOTATIONS)

    kotlin_nullable = "!"
    if nullable_prefix or nullable_suffix:
        kotlin_nullable = "?"
    elif nonnull_prefix or nonnull_suffix:
        kotlin_nullable = ""
    elif type_ref.name in _NULLABLE_MAPPED_TYPES:
        kotlin_nullable = "?"
    elif type_ref.name in _NONNULL_MAPPED_TYPES:
        kotlin_nullable = ""

    if kotlin_nullable:
        if transcoded.suffix:
            transcoded.suffix = f"{kotlin_nullable}{transcoded.suffix}"
        else:
            transcoded.suffix = kotlin_nullable

    return transcoded


def strip_annotations(text: Optional[str], annotations: List[str]) -> Tuple[bool, Optional[str]]:
    if not text:
        return False, text

    result = " ".join(token for token in text.split(" ") if token not in annotations)
    return len(text) != len(result), result


def transform_array(type_ref: TypeRef, transcoded: TypeRef) -> TypeRef:
    if not transcoded.suffix or "[]" not in transcoded.suffix:
        return transcoded

    if type_ref.name in _PRIMITIVE_ARRAY_TYPES:
        transcoded.name = f"{type_ref.name[0].upper()}{type_ref.name[1:]}Array"
        transcoded.suffix = (type_ref.suffix.replace("[]", "!")
                             if type_ref.suffix is not None else "")
        return transcoded

    array_type = TypeRef("kotlin", "Array")
    array_type.prefix = transcoded.prefix
    array_type.suffix = transcoded.suffix.replace("[]", "")

    transcoded.prefix = "(out) "
    transcoded.suffix = ""
    array_type.nested = [transcoded]

    return array_type


def transform_vararg(param: Parameter) -> Parameter:
    if param.type is None or not param.type.suffix or "..." not in param.type.suffix:
        return param

    param.prefix = "vararg "
    param.type.suffix = param.type.suffix.replace("...", "")
    param.type.suffix = param.type.suffix.replace("?", "")
    param.type.suffix = param.type.suffix.replace("!", "")
    return param
