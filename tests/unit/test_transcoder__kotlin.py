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
"""Test Objective C to Kotlin transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.transcoder.kotlin import KotlinTranscoder

from .builders import make_compound, make_parameter, make_return_value, make_type_ref


@pytest.fixture
def transcoder():
    return KotlinTranscoder(ApiReference())


def make_java_type_ref(*, prefix="", suffix="", **kwargs):
    return make_type_ref(language="java", prefix=prefix, suffix=suffix, **kwargs)


def make_kotlin_type_ref(*, prefix="", suffix="", **kwargs):
    return make_type_ref(language="kotlin", prefix=prefix, suffix=suffix, **kwargs)


def make_java_compound(**kwargs):
    return make_compound(language="java", **kwargs)


def make_kotlin_compound(**kwargs):
    return make_compound(language="kotlin", **kwargs)


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
    type_ref = make_java_type_ref(name=java_type)
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name=kotlin_type,
                                              suffix=kotlin_suffix,
                                              id=f"kotlin-{java_type.lower()}")
    # TODO: Fix type id


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
    type_ref = make_java_type_ref(name=java_type, prefix="@NonNull ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name=kotlin_type, id=f"kotlin-{java_type.lower()}")
    # TODO: Fix type id


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
    type_ref = make_java_type_ref(name=java_type, prefix="@Nullable ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name=kotlin_type,
                                              suffix="?",
                                              id=f"kotlin-{java_type.lower()}")
    # TODO: Fix type id


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
    type_ref = make_java_type_ref(name="MyClass", prefix=f"{annotation} ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name="MyClass", suffix="?")


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
    type_ref = make_java_type_ref(name="MyClass", prefix=f"{annotation} ")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name="MyClass")


def test_transcode_type_ref__wildcard_generic_extends(transcoder):
    type_ref = make_java_type_ref(name="MyClass")
    type_ref.nested = [make_java_type_ref(name="Base", prefix="? extends ")]
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(
        name="MyClass",
        suffix="!",
        nested=[make_kotlin_type_ref(name="Base", prefix="out ", suffix="!")])


def test_transcode_type_ref__wildcard_generic_super(transcoder):
    type_ref = make_java_type_ref(name="MyClass")
    type_ref.nested = [make_java_type_ref(name="Base", prefix="? super ")]
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(
        name="MyClass",
        suffix="!",
        nested=[make_kotlin_type_ref(name="Base", prefix="in ", suffix="!")])


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
    type_ref = make_java_type_ref(name=java_type, suffix="[]")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded == make_kotlin_type_ref(name=kotlin_type,
                                              suffix="!",
                                              id=f"kotlin-{java_type.lower()}")
    # TODO: Fix type id


def test_transcode_type_ref__array(transcoder):
    type_ref = make_java_type_ref(name="MyClass", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)
    expected = make_kotlin_type_ref(name="Array",
                                    suffix="!",
                                    id=None,
                                    namespace=None,
                                    kind=None,
                                    nested=[make_kotlin_type_ref(name="MyClass", prefix="(out) ")])
    expected.id = None
    assert transcoded == expected


def test_transcode_type_ref__array__prefix(transcoder):
    type_ref = make_java_type_ref(name="MyClass", prefix="final ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)
    expected = make_kotlin_type_ref(name="Array",
                                    prefix="final ",
                                    suffix="!",
                                    id=None,
                                    namespace=None,
                                    kind=None,
                                    nested=[make_kotlin_type_ref(name="MyClass", prefix="(out) ")])
    expected.id = None
    assert transcoded == expected


def test_transcode_type_ref__array__nonnull(transcoder):
    type_ref = make_java_type_ref(name="MyClass", prefix="@NonNull ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)
    expected = make_kotlin_type_ref(name="Array",
                                    id=None,
                                    namespace=None,
                                    kind=None,
                                    nested=[make_kotlin_type_ref(name="MyClass", prefix="(out) ")])
    expected.id = None
    assert transcoded == expected


def test_transcode_type_ref__array__nullable(transcoder):
    type_ref = make_java_type_ref(name="MyClass", prefix="@Nullable ", suffix="[]")
    transcoded = transcoder.type_ref(type_ref)
    expected = make_kotlin_type_ref(name="Array",
                                    suffix="?",
                                    id=None,
                                    namespace=None,
                                    kind=None,
                                    nested=[make_kotlin_type_ref(name="MyClass", prefix="(out) ")])
    expected.id = None
    assert transcoded == expected


def test_transcode_compound__void_return(transcoder):
    compound = make_java_compound(name="update",
                                  returns=make_return_value(type=make_java_type_ref(name="void")))
    transcoded = transcoder.compound(compound)
    assert transcoded == make_kotlin_compound(name="update", returns=None)


def test_transcode_compound__property(transcoder):
    compound = make_java_compound(
        name="MyClass",
        members=[
            make_java_compound(
                name="setName",
                kind="function",
                params=[make_parameter(name="value", type=make_java_type_ref(name="string"))]),
            make_java_compound(name="getName",
                               kind="function",
                               returns=make_return_value(type=make_java_type_ref(name="string")))
        ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_kotlin_compound(
        name="MyClass",
        members=[
            make_kotlin_compound(
                name="name",
                kind="property",
                id="kotlin-getname",
                returns=make_return_value(type=make_kotlin_type_ref(name="string", suffix="!")))
        ])


def test_transcode_compound__boolean_property(transcoder):
    compound = make_java_compound(
        name="MyClass",
        members=[
            make_java_compound(
                name="setReadOnly",
                kind="function",
                params=[make_parameter(name="value", type=make_java_type_ref(name="boolean"))]),
            make_java_compound(name="isReadOnly",
                               kind="function",
                               returns=make_return_value(type=make_java_type_ref(name="boolean")))
        ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_kotlin_compound(
        name="MyClass",
        members=[
            make_kotlin_compound(
                name="isReadOnly",
                kind="property",
                returns=make_return_value(type=make_kotlin_type_ref(name="Boolean")))
        ])

    assert len(transcoded.members) == 1
    prop = transcoded.members[0]
    assert prop.name == "isReadOnly"
    assert not prop.params
    assert prop.returns is not None
    assert prop.returns.type is not None
    assert prop.returns.type.name == "Boolean"


def test_transcode_compound__single_getter_setter_is_no_property(transcoder):
    compound = make_java_compound(
        name="MyClass",
        members=[
            make_java_compound(
                name="setName",
                kind="function",
                params=[make_parameter(name="value", type=make_java_type_ref(name="string"))]),
            make_java_compound(name="getAddress",
                               kind="function",
                               returns=make_return_value(type=make_java_type_ref(name="string"))),
            make_java_compound(name="isReadOnly",
                               kind="function",
                               returns=make_return_value(type=make_java_type_ref(name="boolean")))
        ])
    transcoded = transcoder.compound(compound)
    assert transcoded == make_kotlin_compound(
        name="MyClass",
        members=[
            make_kotlin_compound(name="setName",
                                 kind="function",
                                 params=[
                                     make_parameter(name="value",
                                                    type=make_kotlin_type_ref(name="string",
                                                                              suffix="!"))
                                 ]),
            make_kotlin_compound(
                name="getAddress",
                kind="function",
                returns=make_return_value(type=make_kotlin_type_ref(name="string", suffix="!"))),
            make_kotlin_compound(
                name="isReadOnly",
                kind="function",
                returns=make_return_value(type=make_kotlin_type_ref(name="Boolean")))
        ])


def test_transcode_parameter__vararg(transcoder):
    param = make_parameter(name="values", type=make_java_type_ref(name="Type", suffix="..."))
    transcoded = transcoder.parameter(param)
    assert transcoded == make_parameter(name="values",
                                        prefix="vararg ",
                                        type=make_kotlin_type_ref(name="Type"))


def test_transcode_parameter__vararg__boxed_type(transcoder):
    param = make_parameter(name="values", type=make_java_type_ref(name="Short", suffix="..."))
    transcoded = transcoder.parameter(param)
    assert transcoded == make_parameter(name="values",
                                        prefix="vararg ",
                                        type=make_kotlin_type_ref(name="Short"))
