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
from asciidoxy.model import Compound, Parameter, ReturnValue, ThrowsClause, TypeRef
from asciidoxy.templates.swift.helpers import SwiftTemplateHelper

from .builders import SimpleClassBuilder


@pytest.fixture
def swift_class():
    builder = SimpleClassBuilder("swift")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "internal", "fileprivate", "private"):
        for member_type in ("enum", "trash"):
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

        for inner_type in ("class", "protocol", "struct"):
            builder.inner_class(name=f"{visibility.capitalize()}{inner_type.capitalize()}",
                                prot=visibility)

        builder.member_function(prot=visibility, name="init", has_return_value=False)

    return builder.compound


@pytest.fixture
def helper(empty_generating_api, swift_class):
    return SwiftTemplateHelper(empty_generating_api, swift_class, InsertionFilter())


def test_public_methods(helper):
    result = [m.name for m in helper.methods(prot="public")]
    assert sorted(result) == sorted(["PublicMethod", "PublicMethodNoReturn"])


def test_public_type_methods(helper):
    result = [m.name for m in helper.type_methods(prot="public")]
    assert sorted(result) == sorted(["PublicTypeMethod", "PublicTypeMethodNoReturn"])


def test_public_properties(helper):
    result = [m.name for m in helper.properties(prot="public")]
    assert result == ["PublicProperty"]


def test_private_methods(helper):
    result = [m.name for m in helper.methods(prot="private")]
    assert sorted(result) == sorted(["PrivateMethod", "PrivateMethodNoReturn"])


def test_public_constructors(helper):
    result = [m.name for m in helper.constructors(prot="public")]
    assert sorted(result) == sorted(["init"])


def test_private_constructors(helper):
    result = [m.name for m in helper.constructors(prot="private")]
    assert sorted(result) == sorted(["init"])


def test_public_simple_enclosed_types(helper):
    result = [m.name for m in helper.simple_enclosed_types(prot="public")]
    assert sorted(result) == sorted([
        "PublicEnum",
    ])


def test_private_simple_enclosed_types(helper):
    result = [m.name for m in helper.simple_enclosed_types(prot="private")]
    assert sorted(result) == sorted([
        "PrivateEnum",
    ])


def test_public_complex_enclosed_types(helper):
    result = [m.name for m in helper.complex_enclosed_types(prot="public")]
    assert sorted(result) == sorted([
        "PublicClass",
        "PublicProtocol",
        "PublicStruct",
    ])


def test_private_complex_enclosed_types(helper):
    result = [m.name for m in helper.complex_enclosed_types(prot="private")]
    assert sorted(result) == sorted([
        "PrivateClass",
        "PrivateProtocol",
        "PrivateStruct",
    ])


def test_method_signature__no_params_no_return(helper):
    method = Compound("swift")
    method.name = "start"
    assert helper.method_signature(method) == "func start()"


def test_method_signature__no_params_no_return__throws(helper):
    method = Compound("swift")
    method.name = "start"
    method.exceptions = [ThrowsClause("swift")]
    assert helper.method_signature(method) == "func start() throws"


def test_method_signature__no_params_simple_return(helper):
    method = Compound("swift")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Int")
    assert helper.method_signature(method) == "func start() -> Int"


def test_method_signature__no_params_simple_return__throws(helper):
    method = Compound("swift")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Int")
    method.exceptions = [ThrowsClause("swift")]
    assert helper.method_signature(method) == "func start() throws -> Int"


def test_method_signature__no_params_link_return(helper):
    method = Compound("swift")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")
    method.returns.type.id = "swift-value"
    assert (
        helper.method_signature(method) == "func retrieveValue() -> xref:swift-value[+++Value+++]")


def test_method_signature__no_params_link_return__throws(helper):
    method = Compound("swift")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")
    method.returns.type.id = "swift-value"
    method.exceptions = [ThrowsClause("swift")]
    assert (helper.method_signature(method) ==
            "func retrieveValue() throws -> xref:swift-value[+++Value+++]")


def test_method_signature__one_param(helper):
    method = Compound("swift")
    method.name = "setValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    assert helper.method_signature(method) == "func setValue(arg1: Type1) -> Value"


def test_method_signature__closure_param(helper):
    method = Compound("swift")
    method.name = "setValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("swift", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc")
    param1.type.returns = TypeRef("objc", "Type1")
    param1.type.args = [Parameter()]
    param1.type.args[0].type = TypeRef("objc", "Type2")
    param1.type.args[0].name = "arg2"
    method.params = [param1]

    assert helper.method_signature(method) == "func setValue(arg1: (arg2: Type2) -> Type1) -> Value"


def test_closure_definition__no_params__void_return(helper):
    closure = Compound("swift")
    closure.name = "SuccessClosure"
    closure.returns = ReturnValue()
    closure.returns.type = TypeRef("swift", name="Void")
    closure.returns.type.args = []

    assert helper.closure_definition(closure) == "typealias SuccessClosure = () -> Void"


def test_closure_definition__multiple_params_type_only__void_return(helper):
    closure = Compound("swift")
    closure.name = "SuccessClosure"
    closure.returns = ReturnValue()
    closure.returns.type = TypeRef("swift", name="Void")
    closure.returns.type.args = [Parameter(), Parameter()]
    closure.returns.type.args[0].type = TypeRef("swift", "int")
    closure.returns.type.args[1].type = TypeRef("swift", "Data")
    closure.returns.type.args[1].type.id = "swift-data"

    assert (helper.closure_definition(closure) ==
            "typealias SuccessClosure = (int, xref:swift-data[+++Data+++]) -> Void")


def test_closure_definition__multiple_params_type_and_name__void_return(helper):
    closure = Compound("swift")
    closure.name = "SuccessClosure"
    closure.returns = ReturnValue()
    closure.returns.type = TypeRef("swift", name="Void")
    closure.returns.type.args = [Parameter(), Parameter()]
    closure.returns.type.args[0].type = TypeRef("swift", "int")
    closure.returns.type.args[0].name = "number"
    closure.returns.type.args[1].type = TypeRef("swift", "Data")
    closure.returns.type.args[1].type.id = "swift-data"
    closure.returns.type.args[1].name = "theData"

    assert (helper.closure_definition(closure) ==
            "typealias SuccessClosure = (number: int, theData: xref:swift-data[+++Data+++]) "
            "-> Void")


def test_closure_definition__no_params__return_type(helper):
    closure = Compound("swift")
    closure.name = "SuccessClosure"
    closure.returns = ReturnValue()
    closure.returns.type = TypeRef("swift", name="Data")
    closure.returns.type.id = "swift-data"
    closure.returns.type.args = []

    assert (helper.closure_definition(closure) ==
            "typealias SuccessClosure = () -> xref:swift-data[+++Data+++]")


def test_parameter(helper):
    ref = TypeRef("swift")
    ref.name = "MyType"
    ref.id = "swift-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    assert (helper.parameter(param,
                             default_value=True) == "arg: xref:swift-tomtom_1_MyType[+++MyType+++]"
            " = 12")
