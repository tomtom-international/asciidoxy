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
"""Tests for Swift template helpers."""

import pytest

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, InnerTypeReference, Member, Parameter, ReturnValue, TypeRef
from asciidoxy.templates.swift.helpers import SwiftTemplateHelper


@pytest.fixture
def swift_class():
    compound = Compound("swift")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("swift")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("swift")
        member.kind = "function"
        member.name = name
        member.prot = prot
        if has_return_value:
            member.returns = ReturnValue()
        if is_static:
            member.static = True
        return member

    def generate_property(prot: str) -> Member:
        property = generate_member_function(prot=prot, name=prot.capitalize() + "Property")
        property.kind = "property"
        return property

    def generate_nested_type(kind: str) -> InnerTypeReference:
        nested_class = Compound("swift")
        nested_class.name = f"Nested{kind.capitalize()}"
        inner_class_reference = InnerTypeReference(language="swift")
        inner_class_reference.name = nested_class.name
        inner_class_reference.referred_object = nested_class
        return inner_class_reference

    # fill class with typical members
    for visibility in ("public", "internal", "fileprivate", "private"):
        for member_type in ("enum", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # add property
        compound.members.append(generate_property(prot=visibility))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "TypeMethod",
                                     is_static=True))

    for inner_type in ("class", "protocol", "struct"):
        compound.inner_classes.append(generate_nested_type(inner_type))

    return compound


@pytest.fixture
def helper(empty_context, swift_class):
    return SwiftTemplateHelper(empty_context, swift_class, InsertionFilter())


def test_public_methods(helper):
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_type_methods(helper):
    result = [m.name for m in helper.public_type_methods()]
    assert sorted(result) == sorted(["PublicTypeMethod"])


def test_public_properties(helper):
    result = [m.name for m in helper.public_properties()]
    assert result == ["PublicProperty"]


def test_public_simple_enclosed_types(helper):
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(result) == sorted([
        "PublicEnum",
    ])


def test_public_complex_enclosed_types(helper):
     result = [m.name for m in helper.public_complex_enclosed_types()]
     assert sorted(result) == sorted([
         "NestedClass", "NestedProtocol", "NestedStruct",
     ])


def test_method_signature__no_params_no_return(helper):
    method = Member("swift")
    method.name = "start"
    assert helper.method_signature(method) == "func start()"


def test_method_signature__no_params_simple_return(helper):
    method = Member("swift")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Int")
    assert helper.method_signature(method) == "func start() -> Int"


def test_method_signature__no_params_link_return(helper):
    method = Member("swift")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")
    method.returns.type.id = "swift-value"
    assert helper.method_signature(method) == "func retrieveValue() -> xref:swift-value[Value]"


def test_method_signature__one_param(helper):
    method = Member("swift")
    method.name = "setValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    assert helper.method_signature(method) == "func setValue(arg1: Type1) -> Value"
