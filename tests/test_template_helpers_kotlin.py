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
"""Tests for Kotlin template helpers."""

import pytest

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Parameter, ReturnValue, TypeRef
from asciidoxy.templates.kotlin.helpers import KotlinTemplateHelper

from .builders import SimpleClassBuilder


@pytest.fixture
def kotlin_class():
    builder = SimpleClassBuilder("kotlin")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "internal", "protected", "private"):
        for member_type in ("enum", "trash", "class"):
            builder.simple_member(kind=member_type, prot=visibility)

        # add property
        builder.member_property(prot=visibility)
        # add some method
        builder.member_function(prot=visibility, name=visibility.capitalize() + "Method")
        # add some method without return type
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "MethodNoReturn",
                                has_return_value=False)
        # add static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "TypeMethod",
                                static=True)
        # add static method without return type
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "TypeMethodNoReturn",
                                has_return_value=False,
                                static=True)
        # add final variable
        builder.member_variable(prot=visibility,
                                name=f"{visibility.capitalize()}Constant",
                                type_prefix="final ")

    builder.member_function(prot="public", name="init", has_return_value=False)

    return builder.compound


@pytest.fixture
def helper(empty_generating_api, kotlin_class):
    return KotlinTemplateHelper(empty_generating_api, kotlin_class, InsertionFilter())


def test_public_constants__no_filter(helper):
    result = [m.name for m in helper.constants(prot="public")]
    assert result == ["PublicConstant"]


def test_public_constants__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.constants(prot="public")]
    assert result == ["PublicConstant"]


def test_public_constants__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.constants(prot="public")]
    assert len(result) == 0


def test_private_constants__no_filter(helper):
    result = [m.name for m in helper.constants(prot="private")]
    assert result == ["PrivateConstant"]


def test_parameter(helper):
    ref = TypeRef("kotlin")
    ref.name = "MyType"
    ref.id = "kotlin-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    assert (helper.parameter(param, default_value=True) == "arg: xref:kotlin-tomtom_1_MyType"
            "[++MyType++] = 12")


def test_method_signature__no_params_no_return(helper):
    method = Compound("kotlin")
    method.name = "start"
    assert helper.method_signature(method) == "fun start()"


def test_method_signature__no_params_simple_return(helper):
    method = Compound("kotlin")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Int")
    assert helper.method_signature(method) == "fun start(): Int"


def test_method_signature__no_params_link_return(helper):
    method = Compound("kotlin")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Value")
    method.returns.type.id = "kotlin-value"
    assert helper.method_signature(method) == "fun retrieveValue(): xref:kotlin-value[++Value++]"


def test_method_signature__one_param(helper):
    method = Compound("kotlin")
    method.name = "setValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("kotlin", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    assert helper.method_signature(method) == "fun setValue(arg1: Type1): Value"
