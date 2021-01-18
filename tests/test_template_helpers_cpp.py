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

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, ReturnValue, TypeRef
from asciidoxy.templates.cpp.helpers import CppTemplateHelper


@pytest.fixture
def helper(empty_generating_api, cpp_class):
    return CppTemplateHelper(empty_generating_api, cpp_class, InsertionFilter())


def test_public_constructors__no_filter(helper):
    result = list(helper.constructors(prot="public"))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="MyClass")
    result = list(helper.constructors(prot="public"))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="OtherClass")
    result = list(helper.constructors(prot="public"))
    assert len(result) == 0


def test_protected_constructors__no_filter(helper):
    result = list(helper.constructors(prot="protected"))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "protected"


def test_public_destructors__no_filter(helper):
    result = list(helper.destructors(prot="public"))
    assert len(result) == 1
    assert result[0].name == "~MyClass"
    assert result[0].prot == "public"


def test_public_destructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="~MyClass")
    result = list(helper.destructors(prot="public"))
    assert len(result) == 1
    assert result[0].name == "~MyClass"
    assert result[0].prot == "public"


def test_public_destructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="OtherClass")
    result = list(helper.destructors(prot="public"))
    assert len(result) == 0


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.methods(prot="public")]
    assert result == ["PublicMethod"]


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public.*")
    result = [m.name for m in helper.methods(prot="public")]
    assert result == ["PublicMethod"]


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="PublicThing")
    result = [m.name for m in helper.methods(prot="public")]
    assert len(result) == 0


def test_private_methods__no_filter(helper):
    result = [m.name for m in helper.methods(prot="private")]
    assert result == ["PrivateMethod"]


def test_public_operators__no_filter(helper):
    result = [m.name for m in helper.operators(prot="public")]
    assert result == ["operator++"]


def test_public_operators__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = [m.name for m in helper.operators(prot="public")]
    assert result == ["operator++"]


def test_public_operators__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.operators(prot="public")]
    assert len(result) == 0


def test_private_operators__no_filter(helper):
    result = [m.name for m in helper.operators(prot="private")]
    assert result == ["operator++"]


def test_public_static_methods__no_filter(helper):
    result = [m.name for m in helper.static_methods(prot="public")]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Static.*")
    result = [m.name for m in helper.static_methods(prot="public")]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="Something")
    result = [m.name for m in helper.static_methods(prot="public")]
    assert len(result) == 0


def test_private_static_methods__no_filter(helper):
    result = [m.name for m in helper.static_methods(prot="private")]
    assert result == ["PrivateStaticMethod"]


def test_method_signature(helper):
    method = Compound("cpp")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("cpp", "void")

    assert helper.method_signature(method) == "void ShortMethod()"


def test_method_signature__constexpr(helper):
    method = Compound("cpp")
    method.name = "ShortMethod"
    method.constexpr = True

    method.returns = ReturnValue()
    method.returns.type = TypeRef("cpp", "void")

    assert helper.method_signature(method) == "constexpr void ShortMethod()"
