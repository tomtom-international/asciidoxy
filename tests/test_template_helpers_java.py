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
"""Tests for Java template helpers."""

import pytest

from asciidoxy.templates.java.helpers import JavaTemplateHelper
from asciidoxy.generator.filters import InsertionFilter

from .builders import SimpleClassBuilder


@pytest.fixture
def java_class():
    builder = SimpleClassBuilder("java")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "trash"):
            builder.simple_member(kind=member_type, prot=visibility)

        # adds constructors
        builder.member_function(prot=visibility, name="MyClass", has_return_value=False)
        # add some method
        builder.member_function(prot=visibility, name=visibility.capitalize() + "Method")
        # add static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "StaticMethod",
                                static=True)
        # add simple variable
        builder.member_variable(prot=visibility)
        # add final variable
        builder.member_variable(prot=visibility,
                                name=f"{visibility.capitalize()}Constant",
                                type_prefix="final ")
        # add nested type
        builder.inner_class(prot=visibility, name=f"{visibility.capitalize()}Type")

    return builder.compound


@pytest.fixture
def helper(java_class, empty_context):
    return JavaTemplateHelper(empty_context, java_class, InsertionFilter())


def test_public_constructors__no_filter(helper):
    result = list(helper.public_constructors())
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="MyClass")
    result = list(helper.public_constructors())
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = list(helper.public_constructors())
    assert len(result) == 0


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="PublicMethod")
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_methods()]
    assert len(result) == 0


def test_public_static_methods__no_filter(helper):
    result = [m.name for m in helper.public_static_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_static_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_static_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_static_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_static_methods()]
    assert len(result) == 0


def test_public_constants__no_filter(helper):
    result = [m.name for m in helper.public_constants()]
    assert result == ["PublicConstant"]


def test_public_constants__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_constants()]
    assert result == ["PublicConstant"]


def test_public_constants__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_constants()]
    assert len(result) == 0


def test_public_complex_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert result == ["PublicType", "ProtectedType"]


def test_public_complex_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="Public")
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert result == ["PublicType"]


def test_public_complex_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="NONE")
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert len(result) == 0
