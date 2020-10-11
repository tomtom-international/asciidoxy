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
"""Test Objective C to Kotlin transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.transcoder.kotlin import KotlinTranscoder

from .builders import make_compound, make_member, make_parameter, make_return_value, make_type_ref


@pytest.fixture
def transcoder():
    return KotlinTranscoder(ApiReference())


@pytest.mark.parametrize("java_type, kotlin_type, kotlin_suffix", [
    ("byte", "Byte", ""),
    ("short", "Short", ""),
    ("int", "Int", ""),
    ("long", "Long", ""),
    ("char", "Char", ""),
    ("float", "Float", ""),
    ("double", "Double", ""),
    ("boolean", "Boolean", ""),
    ("java.lang.Object", "Any", "!"),
    ("java.lang.Cloneable", "Cloneable", "!"),
    ("java.lang.Comparable", "Comparable", "!"),
    ("java.lang.Enum", "Enum", "!"),
    ("java.lang.Annotation", "Annotation", "!"),
    ("java.lang.CharSequence", "CharSequence", "!"),
    ("java.lang.String", "String", "!"),
    ("java.lang.Number", "Number", "!"),
    ("java.lang.Throwable", "Throwable", "!"),
    ("Object", "Any", "!"),
    ("Cloneable", "Cloneable", "!"),
    ("Comparable", "Comparable", "!"),
    ("Enum", "Enum", "!"),
    ("Annotation", "Annotation", "!"),
    ("CharSequence", "CharSequence", "!"),
    ("String", "String", "!"),
    ("Number", "Number", "!"),
    ("Throwable", "Throwable", "!"),
    ("java.lang.Byte", "Byte", "?"),
    ("java.lang.Short", "Short", "?"),
    ("java.lang.Integer", "Int", "?"),
    ("java.lang.Long", "Long", "?"),
    ("java.lang.Character", "Char", "?"),
    ("java.lang.Float", "Float", "?"),
    ("java.lang.Double", "Double", "?"),
    ("java.lang.Boolean", "Boolean", "?"),
    ("Byte", "Byte", "?"),
    ("Short", "Short", "?"),
    ("Integer", "Int", "?"),
    ("Long", "Long", "?"),
    ("Character", "Char", "?"),
    ("Float", "Float", "?"),
    ("Double", "Double", "?"),
    ("Boolean", "Boolean", "?"),
    ("void", "Unit", ""),
    ("MyClass", "MyClass", "!"),
])
def test_transcode_type_ref__mapped_types(transcoder, java_type, kotlin_type, kotlin_suffix):
    type_ref = make_type_ref(lang="java", name=java_type)
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == kotlin_type
    assert not transcoded.prefix
    assert transcoded.suffix == kotlin_suffix


@pytest.mark.parametrize("java_type, kotlin_type", [
    ("java.lang.Object", "Any"),
    ("java.lang.Cloneable", "Cloneable"),
    ("java.lang.Comparable", "Comparable"),
    ("java.lang.Enum", "Enum"),
    ("java.lang.Annotation", "Annotation"),
    ("java.lang.CharSequence", "CharSequence"),
    ("java.lang.String", "String"),
    ("java.lang.Number", "Number"),
    ("java.lang.Throwable", "Throwable"),
    ("Object", "Any"),
    ("Cloneable", "Cloneable"),
    ("Comparable", "Comparable"),
    ("Enum", "Enum"),
    ("Annotation", "Annotation"),
    ("CharSequence", "CharSequence"),
    ("String", "String"),
    ("Number", "Number"),
    ("Throwable", "Throwable"),
    ("java.lang.Byte", "Byte"),
    ("java.lang.Short", "Short"),
    ("java.lang.Integer", "Int"),
    ("java.lang.Long", "Long"),
    ("java.lang.Character", "Char"),
    ("java.lang.Float", "Float"),
    ("java.lang.Double", "Double"),
    ("java.lang.Boolean", "Boolean"),
    ("Byte", "Byte"),
    ("Short", "Short"),
    ("Integer", "Int"),
    ("Long", "Long"),
    ("Character", "Char"),
    ("Float", "Float"),
    ("Double", "Double"),
    ("Boolean", "Boolean"),
])
def test_transcode_type_ref__nonnull_annotated_types(transcoder, java_type, kotlin_type):
    type_ref = make_type_ref(lang="java", name=java_type, prefix="@NonNull ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == kotlin_type
    assert not transcoded.prefix
    assert not transcoded.suffix


@pytest.mark.parametrize("java_type, kotlin_type", [
    ("java.lang.Object", "Any"),
    ("java.lang.Cloneable", "Cloneable"),
    ("java.lang.Comparable", "Comparable"),
    ("java.lang.Enum", "Enum"),
    ("java.lang.Annotation", "Annotation"),
    ("java.lang.CharSequence", "CharSequence"),
    ("java.lang.String", "String"),
    ("java.lang.Number", "Number"),
    ("java.lang.Throwable", "Throwable"),
    ("Object", "Any"),
    ("Cloneable", "Cloneable"),
    ("Comparable", "Comparable"),
    ("Enum", "Enum"),
    ("Annotation", "Annotation"),
    ("CharSequence", "CharSequence"),
    ("String", "String"),
    ("Number", "Number"),
    ("Throwable", "Throwable"),
    ("java.lang.Byte", "Byte"),
    ("java.lang.Short", "Short"),
    ("java.lang.Integer", "Int"),
    ("java.lang.Long", "Long"),
    ("java.lang.Character", "Char"),
    ("java.lang.Float", "Float"),
    ("java.lang.Double", "Double"),
    ("java.lang.Boolean", "Boolean"),
    ("Byte", "Byte"),
    ("Short", "Short"),
    ("Integer", "Int"),
    ("Long", "Long"),
    ("Character", "Char"),
    ("Float", "Float"),
    ("Double", "Double"),
    ("Boolean", "Boolean"),
])
def test_transcode_type_ref__nullable_annotated_types(transcoder, java_type, kotlin_type):
    type_ref = make_type_ref(lang="java", name=java_type, prefix="@Nullable ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == kotlin_type
    assert not transcoded.prefix
    assert transcoded.suffix == "?"


@pytest.mark.parametrize("annotation", [
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
])
def test_transcode_type_ref__all_nullable_annotations(transcoder, annotation):
    type_ref = make_type_ref(lang="java", name="MyClass", prefix=f"{annotation} ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert transcoded.suffix == "?"


@pytest.mark.parametrize("annotation", [
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
])
def test_transcode_type_ref__all_nonnull_annotations(transcoder, annotation):
    type_ref = make_type_ref(lang="java", name="MyClass", prefix=f"{annotation} ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert not transcoded.suffix


def test_transcode_type_ref__wildcard_generic_extends(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass")
    type_ref.nested = [make_type_ref(lang="java", name="Base", prefix="? extends ")]
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert transcoded.suffix == "!"
    assert len(transcoded.nested) == 1

    assert transcoded.nested[0].name == "Base"
    assert transcoded.nested[0].prefix == "out "
    assert transcoded.nested[0].suffix == "!"


def test_transcode_type_ref__wildcard_generic_super(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass")
    type_ref.nested = [make_type_ref(lang="java", name="Base", prefix="? super ")]
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "MyClass"
    assert not transcoded.prefix
    assert transcoded.suffix == "!"
    assert len(transcoded.nested) == 1

    assert transcoded.nested[0].name == "Base"
    assert transcoded.nested[0].prefix == "in "
    assert transcoded.nested[0].suffix == "!"


@pytest.mark.parametrize("java_type, kotlin_type", [
    ("int", "IntArray"),
    ("byte", "ByteArray"),
    ("short", "ShortArray"),
    ("long", "LongArray"),
    ("char", "CharArray"),
    ("float", "FloatArray"),
    ("double", "DoubleArray"),
    ("boolean", "BooleanArray"),
])
def test_transcode_type_ref__primitive_array(transcoder, java_type, kotlin_type):
    type_ref = make_type_ref(lang="java", name=java_type, suffix="[]")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == kotlin_type
    assert not transcoded.prefix
    assert transcoded.suffix == "!"


def test_transcode_type_ref__array(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "Array"
    assert not transcoded.prefix
    assert transcoded.suffix == "!"

    assert len(transcoded.nested) == 1
    assert transcoded.nested[0].name == "MyClass"
    assert transcoded.nested[0].prefix == "(out) "
    assert not transcoded.nested[0].suffix


def test_transcode_type_ref__array__prefix(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass", prefix="final ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "Array"
    assert transcoded.prefix == "final "
    assert transcoded.suffix == "!"

    assert len(transcoded.nested) == 1
    assert transcoded.nested[0].name == "MyClass"
    assert transcoded.nested[0].prefix == "(out) "
    assert not transcoded.nested[0].suffix


def test_transcode_type_ref__array__nonnull(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass", prefix="@NonNull ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "Array"
    assert not transcoded.prefix
    assert not transcoded.suffix

    assert len(transcoded.nested) == 1
    assert transcoded.nested[0].name == "MyClass"
    assert transcoded.nested[0].prefix == "(out) "
    assert not transcoded.nested[0].suffix


def test_transcode_type_ref__array__nullable(transcoder):
    type_ref = make_type_ref(lang="java", name="MyClass", prefix="@Nullable ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)

    assert transcoded.name == "Array"
    assert not transcoded.prefix
    assert transcoded.suffix == "?"

    assert len(transcoded.nested) == 1
    assert transcoded.nested[0].name == "MyClass"
    assert transcoded.nested[0].prefix == "(out) "
    assert not transcoded.nested[0].suffix


def test_transcode_member__void_return(transcoder):
    member = make_member(lang="java",
                         name="update",
                         returns=make_return_value(make_type_ref(lang="java", name="void")))
    transcoded = transcoder.member(member)
    assert not transcoded.returns


def test_transcode_compound__property(transcoder):
    compound = make_compound(lang="java",
                             name="MyClass",
                             members=[
                                 make_member(lang="java",
                                             name="setName",
                                             params=[
                                                 make_parameter(name="value",
                                                                type_=make_type_ref(lang="java",
                                                                                    name="string"))
                                             ]),
                                 make_member(lang="java",
                                             name="getName",
                                             returns=make_return_value(
                                                 make_type_ref(lang="java", name="string")))
                             ])
    transcoded = transcoder.compound(compound)

    assert len(transcoded.members) == 1
    prop = transcoded.members[0]
    assert prop.name == "name"
    assert not prop.params
    assert prop.returns is not None
    assert prop.returns.type is not None
    assert prop.returns.type.name == "string"


def test_transcode_compound__boolean_property(transcoder):
    compound = make_compound(lang="java",
                             name="MyClass",
                             members=[
                                 make_member(lang="java",
                                             name="setReadOnly",
                                             params=[
                                                 make_parameter(name="value",
                                                                type_=make_type_ref(lang="java",
                                                                                    name="boolean"))
                                             ]),
                                 make_member(lang="java",
                                             name="isReadOnly",
                                             returns=make_return_value(
                                                 make_type_ref(lang="java", name="boolean")))
                             ])
    transcoded = transcoder.compound(compound)

    assert len(transcoded.members) == 1
    prop = transcoded.members[0]
    assert prop.name == "isReadOnly"
    assert not prop.params
    assert prop.returns is not None
    assert prop.returns.type is not None
    assert prop.returns.type.name == "Boolean"


def test_transcode_compound__single_getter_setter_is_no_property(transcoder):
    compound = make_compound(
        lang="java",
        name="MyClass",
        members=[
            make_member(lang="java",
                        name="setName",
                        params=[
                            make_parameter(name="value",
                                           type_=make_type_ref(lang="java", name="string"))
                        ]),
            make_member(lang="java",
                        name="getAddress",
                        returns=make_return_value(make_type_ref(lang="java", name="string"))),
            make_member(lang="java",
                        name="isReadOnly",
                        returns=make_return_value(make_type_ref(lang="java", name="boolean")))
        ])
    transcoded = transcoder.compound(compound)

    member_names = (m.name for m in transcoded.members)
    assert sorted(member_names) == sorted(["setName", "getAddress", "isReadOnly"])


def test_transcode_parameter__vararg(transcoder):
    param = make_parameter(name="values",
                           type_=make_type_ref(lang="java", name="Type", suffix="..."))
    transcoded = transcoder.parameter(param)

    assert transcoded.prefix == "vararg "
    assert transcoded.type is not None
    assert transcoded.type.name == "Type"
    assert not transcoded.type.prefix
    assert not transcoded.type.suffix


def test_transcode_parameter__vararg__boxed_type(transcoder):
    param = make_parameter(name="values",
                           type_=make_type_ref(lang="java", name="Short", suffix="..."))
    transcoded = transcoder.parameter(param)

    assert transcoded.prefix == "vararg "
    assert transcoded.type is not None
    assert transcoded.type.name == "Short"
    assert not transcoded.type.prefix
    assert not transcoded.type.suffix
