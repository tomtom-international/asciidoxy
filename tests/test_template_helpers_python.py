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
"""Tests for python template helpers."""

import pytest

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Parameter, ReturnValue, TypeRef
from asciidoxy.templates.python.helpers import params, PythonTemplateHelper

from .builders import SimpleClassBuilder


@pytest.fixture
def python_class():
    builder = SimpleClassBuilder("python")
    builder.name("MyClass")

    builder.member_function(name="__init__", has_return_value=False, static=False),
    builder.member_function(name="public_static_method", static=True),
    builder.member_function(name="_private_static_method", static=True),
    builder.member_function(name="__mangled_private_static_method", static=True),
    builder.member_function(name="public_method"),
    builder.member_function(name="_private_method"),
    builder.member_function(name="__mangled_private_method"),
    builder.member_function(name="__add__"),
    builder.member_variable(name="public_variable"),
    builder.member_variable(name="_private_variable"),
    builder.member_variable(name="__mangled_private_variable"),
    builder.inner_class(name="NestedClass"),
    builder.inner_class(name="_PrivateNestedClass"),
    builder.inner_class(name="__MangledPrivateNestedClass"),

    return builder.compound


def test_params__empty():
    member = Compound("lang")
    assert list(params(member)) == []


def test_params__normal():
    type1 = TypeRef("lang")
    type1.name = "int"

    type2 = TypeRef("lang")
    type2.name = "float"

    param1 = Parameter()
    param1.type = type1
    param1.name = "arg1"

    param2 = Parameter()
    param2.type = type2
    param2.name = "arg2"

    member = Compound("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param1, param2]


def test_params__self():
    type1 = TypeRef("lang")
    type1.name = "self"

    type2 = TypeRef("lang")
    type2.name = "float"

    param1 = Parameter()
    param1.type = type1

    param2 = Parameter()
    param2.type = type2
    param2.name = "arg2"

    member = Compound("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param2]


def test_params__cls():
    type1 = TypeRef("lang")
    type1.name = "cls"

    type2 = TypeRef("lang")
    type2.name = "float"

    param1 = Parameter()
    param1.type = type1

    param2 = Parameter()
    param2.type = type2
    param2.name = "arg2"

    member = Compound("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param2]


def test_params__no_type():
    param1 = Parameter()
    param1.type = None
    param1.name = "arg1"

    param2 = Parameter()
    param2.type = None
    param2.name = "arg2"

    member = Compound("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param1, param2]


@pytest.fixture
def helper(empty_generating_api, python_class):
    return PythonTemplateHelper(empty_generating_api, python_class, InsertionFilter())


def test_public_static_methods__no_filter(helper):
    result = list(m.name for m in helper.static_methods(prot="public"))
    assert sorted(result) == sorted(["public_static_method"])


def test_public_static_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = list(m.name for m in helper.static_methods(prot="public"))
    assert sorted(result) == sorted(["public_static_method"])


def test_public_static_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = list(m.name for m in helper.static_methods(prot="public"))
    assert not result


def test_public_methods__no_filter(helper):
    result = list(m.name for m in helper.methods(prot="public"))
    assert sorted(result) == sorted(["public_method"])


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = list(m.name for m in helper.methods(prot="public"))
    assert sorted(result) == sorted(["public_method"])


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = list(m.name for m in helper.methods(prot="public"))
    assert not result


def test_public_constructors__no_filter(helper):
    result = list(m.name for m in helper.constructors(prot="public"))
    assert sorted(result) == sorted(["__init__"])


def test_public_constructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = list(m.name for m in helper.constructors(prot="public"))
    assert sorted(result) == sorted(["__init__"])


def test_public_constructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = list(m.name for m in helper.constructors(prot="public"))
    assert not result


def test_public_enclosed_types__no_filter(helper):
    result = list(m.name for m in helper.complex_enclosed_types(prot="public"))
    assert sorted(result) == sorted(["NestedClass"])


def test_public_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="ALL")
    result = list(m.name for m in helper.complex_enclosed_types(prot="public"))
    assert sorted(result) == sorted(["NestedClass"])


def test_public_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="NONE")
    result = list(m.name for m in helper.complex_enclosed_types(prot="public"))
    assert not result


def test_public_variables__no_filter(helper):
    result = list(m.name for m in helper.variables(prot="public"))
    assert sorted(result) == sorted(["public_variable"])


def test_public_variables__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = list(m.name for m in helper.variables(prot="public"))
    assert sorted(result) == sorted(["public_variable"])


def test_public_variables__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = list(m.name for m in helper.variables(prot="public"))
    assert not result


def test_method_signature__no_params(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    assert helper.method_signature(method) == "def ShortMethod() -> None"


def test_method_signature__single_param(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "int")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert helper.method_signature(method) == "def ShortMethod(value: int) -> int"


def test_method_signature__single_param__too_wide(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "str")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert (helper.method_signature(method, max_width=20) == """\
def ShortMethod(
    value: int) -> str""")


def test_method_signature__multiple_params(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("python", "float")
    method.params[2].name = "text"
    method.params[2].type = TypeRef("python", "str")

    assert (helper.method_signature(method) == """\
def ShortMethod(value: int,
                other_value: float,
                text: str) -> None""")


def test_method_signature__multiple_params__first_param_too_wide(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("python", "float")
    method.params[2].name = "text"
    method.params[2].type = TypeRef("python", "str")

    assert (helper.method_signature(method, max_width=20) == """\
def ShortMethod(
    value: int,
    other_value: float,
    text: str) -> None""")


def test_method_signature__multiple_params__last_param_too_wide(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "Type")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("python", "float")
    method.params[2].name = "text" * 10
    method.params[2].type = TypeRef("python", "str")

    assert (helper.method_signature(method, max_width=40) == f"""\
def ShortMethod(
    value: int,
    other_value: float,
    {"text" * 10}: str) -> Type""")


def test_method_signature__ignore_return_type_xref_length(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "Type")
    method.returns.type.id = "ab" * 80

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert (helper.method_signature(method) ==
            f"def ShortMethod(value: int) -> xref:{'ab' * 80}[+++Type+++]")


def test_method_signature__ignore_param_type_xref_length(helper):
    method = Compound("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")
    method.params[0].type.id = "ab" * 80

    assert (helper.method_signature(method) ==
            f"def ShortMethod(value: xref:{'ab' * 80}[+++int+++]) -> None")


def test_parameter(helper):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    assert (helper.parameter(
        param, default_value=True) == "arg: xref:lang-tomtom_1_MyType[+++MyType+++] = 12")


def test_parameter__self(helper):
    param = Parameter()
    param.name = "self"

    assert helper.parameter(param, default_value=False) == "self"


def test_parameter__cls(helper):
    param = Parameter()
    param.name = "cls"

    assert helper.parameter(param, default_value=False) == "cls"
