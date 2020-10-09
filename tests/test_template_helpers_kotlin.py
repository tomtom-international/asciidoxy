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
"""Tests for Kotlin template helpers."""

import pytest

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, InnerTypeReference, Member, Parameter, ReturnValue, TypeRef
from asciidoxy.templates.kotlin.helpers import KotlinTemplateHelper


@pytest.fixture
def kotlin_class():
    compound = Compound("kotlin")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("kotlin")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("kotlin")
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
        member_variable.returns.type = TypeRef("kotlin")
        return member_variable

    def generate_property(prot: str) -> Member:
        property = generate_member_function(prot=prot, name=prot.capitalize() + "Property")
        property.kind = "property"
        return property

    def generate_nested_type(kind: str, prot: str) -> InnerTypeReference:
        nested_class = Compound("kotlin")
        nested_class.name = f"{prot.capitalize()}{kind.capitalize()}"
        inner_class_reference = InnerTypeReference(language="kotlin")
        inner_class_reference.name = nested_class.name
        inner_class_reference.referred_object = nested_class
        inner_class_reference.prot = prot
        return inner_class_reference

    # fill class with typical members
    for visibility in ("public", "internal", "protected", "private"):
        for member_type in ("enum", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # add property
        compound.members.append(generate_property(prot=visibility))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add some method without return type
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "MethodNoReturn",
                                     has_return_value=False))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "TypeMethod",
                                     is_static=True))
        # add static method without return type
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "TypeMethodNoReturn",
                                     has_return_value=False,
                                     is_static=True))

        # add final variable
        final_member_variable = generate_member_variable(prot=visibility)
        final_member_variable.name = visibility.capitalize() + "Constant"
        final_member_variable.returns.type.prefix = "final "
        compound.members.append(final_member_variable)

        # add nested type
        compound.inner_classes.append(generate_nested_type("class", visibility))

    compound.members.append(
        generate_member_function(prot="public", name="init", has_return_value=False))

    return compound


@pytest.fixture
def helper(empty_context, kotlin_class):
    return KotlinTemplateHelper(empty_context, kotlin_class, InsertionFilter())


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


def test_parameter(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"

    assert helper.parameter(param) == "arg: xref:kotlin-tomtom_1_MyType[MyType]"


def test_parameter__no_link(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"

    assert helper.parameter(param, link=False) == "arg: MyType"


def test_parameter__default_value(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    assert helper.parameter(param,
                            default_value=True) == "arg: xref:kotlin-tomtom_1_MyType[MyType] = 12"


def test_parameter__ignore_default_value(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    assert helper.parameter(param,
                            default_value=False) == "arg: xref:kotlin-tomtom_1_MyType[MyType]"


def test_parameter__prefix(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.prefix = "vararg "

    assert helper.parameter(param) == "vararg arg: xref:kotlin-tomtom_1_MyType[MyType]"


def test_method_signature__no_params_no_return(helper):
    method = Member("kotlin")
    method.name = "start"
    assert helper.method_signature(method) == "fun start()"


def test_method_signature__no_params_simple_return(helper):
    method = Member("kotlin")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Int")
    assert helper.method_signature(method) == "fun start(): Int"


def test_method_signature__no_params_link_return(helper):
    method = Member("kotlin")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Value")
    method.returns.type.id = "kotlin-value"
    assert helper.method_signature(method) == "fun retrieveValue(): xref:kotlin-value[Value]"


def test_method_signature__one_param(helper):
    method = Member("kotlin")
    method.name = "setValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    assert helper.method_signature(method) == "fun setValue(arg1: Type1): Value"
