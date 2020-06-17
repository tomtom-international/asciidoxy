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
from asciidoxy.model import Compound, Member, Parameter, ReturnValue, TypeRef, InnerTypeReference
from asciidoxy.templates.python.helpers import (params, public_static_methods, public_methods,
                                                public_constructors, public_enclosed_types,
                                                public_variables, method_signature)


@pytest.fixture
def python_class():
    compound = Compound("python")
    compound.name = "MyClass"

    def generate_member_function(name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("python")
        member.kind = "function"
        member.name = name
        member.prot = "public"
        if has_return_value:
            member.returns = ReturnValue()
        if is_static:
            member.static = True
        return member

    def generate_member_variable(name: str) -> Member:
        member_variable = Member("python")
        member_variable.kind = "variable"
        member_variable.name = name
        member_variable.returns = ReturnValue()
        member_variable.returns.type = TypeRef("python")
        return member_variable

    def generate_inner_class(name: str) -> InnerTypeReference:
        nested_class = Compound("python")
        nested_class.name = name
        inner_class_reference = InnerTypeReference(language="python")
        inner_class_reference.name = nested_class.name
        inner_class_reference.referred_object = nested_class
        return inner_class_reference

    compound.members = [
        generate_member_function("__init__", has_return_value=False, is_static=False),
        generate_member_function("public_static_method", is_static=True),
        generate_member_function("_private_static_method", is_static=True),
        generate_member_function("__mangled_private_static_method", is_static=True),
        generate_member_function("public_method"),
        generate_member_function("_private_method"),
        generate_member_function("__mangled_private_method"),
        generate_member_function("__add__"),
        generate_member_variable("public_variable"),
        generate_member_variable("_private_variable"),
        generate_member_variable("__mangled_private_variable"),
    ]

    compound.inner_classes = [
        generate_inner_class("NestedClass"),
        generate_inner_class("_PrivateNestedClass"),
        generate_inner_class("__MangledPrivateNestedClass"),
    ]

    return compound


def test_params__empty():
    member = Member("lang")
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

    member = Member("lang")
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

    member = Member("lang")
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

    member = Member("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param2]


def test_params__no_type():
    param1 = Parameter()
    param1.type = None
    param1.name = "arg1"

    param2 = Parameter()
    param2.type = None
    param2.name = "arg2"

    member = Member("lang")
    member.params = [param1, param2]

    assert list(params(member)) == [param1, param2]


def test_public_static_methods__no_filter(python_class):
    result = list(m.name for m in public_static_methods(python_class, InsertionFilter()))
    assert sorted(result) == sorted(["public_static_method"])


def test_public_static_methods__filter_match(python_class):
    result = list(m.name
                  for m in public_static_methods(python_class, InsertionFilter(members="ALL")))
    assert sorted(result) == sorted(["public_static_method"])


def test_public_static_methods__filter_no_match(python_class):
    result = list(m.name
                  for m in public_static_methods(python_class, InsertionFilter(members="NONE")))
    assert not result


def test_public_methods__no_filter(python_class):
    result = list(m.name for m in public_methods(python_class, InsertionFilter()))
    assert sorted(result) == sorted(["public_method"])


def test_public_methods__filter_match(python_class):
    result = list(m.name for m in public_methods(python_class, InsertionFilter(members="ALL")))
    assert sorted(result) == sorted(["public_method"])


def test_public_methods__filter_no_match(python_class):
    result = list(m.name for m in public_methods(python_class, InsertionFilter(members="NONE")))
    assert not result


def test_public_constructors__no_filter(python_class):
    result = list(m.name for m in public_constructors(python_class, InsertionFilter()))
    assert sorted(result) == sorted(["__init__"])


def test_public_constructors__filter_match(python_class):
    result = list(m.name for m in public_constructors(python_class, InsertionFilter(members="ALL")))
    assert sorted(result) == sorted(["__init__"])


def test_public_constructors__filter_no_match(python_class):
    result = list(m.name
                  for m in public_constructors(python_class, InsertionFilter(members="NONE")))
    assert not result


def test_public_enclosed_types__no_filter(python_class):
    result = list(m.name for m in public_enclosed_types(python_class, InsertionFilter()))
    assert sorted(result) == sorted(["NestedClass"])


def test_public_enclosed_types__filter_match(python_class):
    result = list(
        m.name for m in public_enclosed_types(python_class, InsertionFilter(inner_classes="ALL")))
    assert sorted(result) == sorted(["NestedClass"])


def test_public_enclosed_types__filter_no_match(python_class):
    result = list(
        m.name for m in public_enclosed_types(python_class, InsertionFilter(inner_classes="NONE")))
    assert not result


def test_public_variables__no_filter(python_class):
    result = list(m.name for m in public_variables(python_class, InsertionFilter()))
    assert sorted(result) == sorted(["public_variable"])


def test_public_variables__filter_match(python_class):
    result = list(m.name for m in public_variables(python_class, InsertionFilter(members="ALL")))
    assert sorted(result) == sorted(["public_variable"])


def test_public_variables__filter_no_match(python_class):
    result = list(m.name for m in public_variables(python_class, InsertionFilter(members="NONE")))
    assert not result


def test_method_signature__no_params(empty_context):
    method = Member("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    assert method_signature(method, empty_context) == "def ShortMethod() -> None"


def test_method_signature__single_param(empty_context):
    method = Member("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "int")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert method_signature(method, empty_context) == "def ShortMethod(value: int) -> int"


def test_method_signature__single_param__too_wide(empty_context):
    method = Member("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "str")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert (method_signature(method, empty_context, max_width=20) == """\
def ShortMethod(
    value: int) -> str""")


def test_method_signature__multiple_params(empty_context):
    method = Member("python")
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

    assert (method_signature(method, empty_context) == """\
def ShortMethod(value: int,
                other_value: float,
                text: str) -> None""")


def test_method_signature__multiple_params__first_param_too_wide(empty_context):
    method = Member("python")
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

    assert (method_signature(method, empty_context, max_width=20) == """\
def ShortMethod(
    value: int,
    other_value: float,
    text: str) -> None""")


def test_method_signature__multiple_params__last_param_too_wide(empty_context):
    method = Member("python")
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

    assert (method_signature(method, empty_context, max_width=40) == f"""\
def ShortMethod(
    value: int,
    other_value: float,
    {"text" * 10}: str) -> Type""")


def test_method_signature__ignore_return_type_xref_length(empty_context):
    method = Member("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "Type")
    method.returns.type.id = "ab" * 80

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")

    assert (method_signature(
        method, empty_context) == f"def ShortMethod(value: int) -> xref:{'ab' * 80}[Type]")


def test_method_signature__ignore_param_type_xref_length(empty_context):
    method = Member("python")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("python", "None")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("python", "int")
    method.params[0].type.id = "ab" * 80

    assert (method_signature(
        method, empty_context) == f"def ShortMethod(value: xref:{'ab' * 80}[int]) -> None")
