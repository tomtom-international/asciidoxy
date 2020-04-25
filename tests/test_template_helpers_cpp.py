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
"""
Tests for C++ template helpers.
"""

import pytest

from asciidoxy.model import Compound, Member, ReturnValue, InnerTypeReference
from asciidoxy.templates.cpp.helpers import (public_static_methods, public_methods,
                                             public_constructors, public_simple_enclosed_types,
                                             public_complex_enclosed_types, public_variables)


@pytest.fixture
def cpp_class():
    compound = Compound("cpp")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("cpp")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("cpp")
        member.kind = "function"
        member.name = name
        member.prot = prot
        if has_return_value:
            member.returns = ReturnValue()
        if is_static:
            member.static = True
        return member

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("variable", "enum", "class", "typedef", "struct", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # adds constructors
        compound.members.append(
            generate_member_function(prot=visibility, name="MyClass", has_return_value=False))
        # add some operator
        compound.members.append(generate_member_function(prot=visibility, name="operator++"))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "StaticMethod",
                                     is_static=True))

    # insert nested type
    nested_class = Compound("cpp")
    nested_class.name = "NestedClass"
    inner_class_reference = InnerTypeReference(language="cpp")
    inner_class_reference.name = nested_class.name
    inner_class_reference.referred_object = nested_class
    compound.inner_classes.append(inner_class_reference)

    return compound


def test_public_constructors(cpp_class):
    result = list(public_constructors(cpp_class))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_methods(cpp_class):
    result = [m.name for m in public_methods(cpp_class)]
    assert result == ["PublicMethod"]


def test_public_static_methods(cpp_class):
    result = [m.name for m in public_static_methods(cpp_class)]
    assert result == ["PublicStaticMethod"]


def test_public_variables(cpp_class):
    result = [m.name for m in public_variables(cpp_class)]
    assert result == ["PublicVariable"]


def test_public_simple_enclosed_types(cpp_class):
    simple_enclosed_types = [m.name for m in public_simple_enclosed_types(cpp_class)]
    assert sorted(simple_enclosed_types) == sorted(
        ["PublicEnum", "PublicTypedef", "ProtectedEnum", "ProtectedTypedef"])


def test_public_complex_enclosed_types(cpp_class):
    result = [m.name for m in public_complex_enclosed_types(cpp_class)]
    assert result == ["NestedClass"]
