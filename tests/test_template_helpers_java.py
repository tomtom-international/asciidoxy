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

from asciidoxy.model import Compound, Member, ReturnValue, TypeRef, InnerTypeReference
from asciidoxy.templates.java.helpers import (public_methods, public_static_methods,
                                              public_constructors, public_constants,
                                              public_complex_enclosed_types)
from asciidoxy.generator.filters import InsertionFilter


@pytest.fixture
def java_class():
    compound = Compound("java")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("java")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("java")
        member.kind = "function"
        member.name = name
        member.prot = prot
        if has_return_value:
            member.returns = ReturnValue()
        if is_static:
            member.static = True
        return member

    def generate_member_variable(prot: str) -> Member:
        member_variable = generate_member(kind="variable", prot=visibility)
        member_variable.returns = ReturnValue()
        member_variable.returns.type = TypeRef("java")
        return member_variable

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # adds constructors
        compound.members.append(
            generate_member_function(prot=visibility, name="MyClass", has_return_value=False))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "StaticMethod",
                                     is_static=True))
        # add simple variable
        compound.members.append(generate_member_variable(prot=visibility))

        # add final variable
        final_member_variable = generate_member_variable(prot=visibility)
        final_member_variable.name = visibility.capitalize() + "Constant"
        final_member_variable.returns.type.prefix = "final "
        compound.members.append(final_member_variable)

    # insert nested type
    nested_class = Compound("java")
    nested_class.name = "NestedClass"
    inner_class_reference = InnerTypeReference(language="java")
    inner_class_reference.name = nested_class.name
    inner_class_reference.referred_object = nested_class
    compound.inner_classes.append(inner_class_reference)

    return compound


def test_public_constructors__no_filter(java_class):
    result = list(public_constructors(java_class, InsertionFilter()))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_match(java_class):
    result = list(public_constructors(java_class, InsertionFilter(members="MyClass")))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_no_match(java_class):
    result = list(public_constructors(java_class, InsertionFilter(members="NONE")))
    assert len(result) == 0


def test_public_methods__no_filter(java_class):
    result = [m.name for m in public_methods(java_class, InsertionFilter())]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_match(java_class):
    result = [m.name for m in public_methods(java_class, InsertionFilter(members="PublicMethod"))]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_no_match(java_class):
    result = [m.name for m in public_methods(java_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_static_methods__no_filter(java_class):
    result = [m.name for m in public_static_methods(java_class, InsertionFilter())]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_static_methods__filter_match(java_class):
    result = [m.name for m in public_static_methods(java_class, InsertionFilter(members="Public"))]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_static_methods__filter_no_match(java_class):
    result = [m.name for m in public_static_methods(java_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_constants__no_filter(java_class):
    result = [m.name for m in public_constants(java_class, InsertionFilter())]
    assert result == ["PublicConstant"]


def test_public_constants__filter_match(java_class):
    result = [m.name for m in public_constants(java_class, InsertionFilter(members="Public"))]
    assert result == ["PublicConstant"]


def test_public_constants__filter_no_match(java_class):
    result = [m.name for m in public_constants(java_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_complex_enclosed_types__no_filter(java_class):
    result = [m.name for m in public_complex_enclosed_types(java_class, InsertionFilter())]
    assert result == ["NestedClass"]


def test_public_complex_enclosed_types__filter_match(java_class):
    result = [
        m.name
        for m in public_complex_enclosed_types(java_class, InsertionFilter(inner_classes="Nested"))
    ]
    assert result == ["NestedClass"]


def test_public_complex_enclosed_types__filter_no_match(java_class):
    result = [
        m.name
        for m in public_complex_enclosed_types(java_class, InsertionFilter(inner_classes="NONE"))
    ]
    assert len(result) == 0
