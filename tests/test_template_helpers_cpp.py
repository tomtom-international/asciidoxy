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
from asciidoxy.templates.cpp.helpers import CppTemplateHelper


@pytest.fixture
def helper(empty_context, cpp_class):
    return CppTemplateHelper(empty_context, cpp_class, InsertionFilter())


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
    helper.insert_filter = InsertionFilter(members="OtherClass")
    result = list(helper.public_constructors())
    assert len(result) == 0


def test_public_destructors__no_filter(helper):
    result = list(helper.public_destructors())
    assert len(result) == 1
    assert result[0].name == "~MyClass"
    assert result[0].prot == "public"


def test_public_destructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="~MyClass")
    result = list(helper.public_destructors())
    assert len(result) == 1
    assert result[0].name == "~MyClass"
    assert result[0].prot == "public"


def test_public_destructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="OtherClass")
    result = list(helper.public_destructors())
    assert len(result) == 0


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.public_methods()]
    assert result == ["PublicMethod"]


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public.*")
    result = [m.name for m in helper.public_methods()]
    assert result == ["PublicMethod"]


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="PublicThing")
    result = [m.name for m in helper.public_methods()]
    assert len(result) == 0


def test_public_operators__no_filter(helper):
    result = [m.name for m in helper.public_operators()]
    assert result == ["operator++"]


def test_public_operators__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="ALL")
    result = [m.name for m in helper.public_operators()]
    assert result == ["operator++"]


def test_public_operators__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_operators()]
    assert len(result) == 0


def test_public_static_methods__no_filter(helper):
    result = [m.name for m in helper.public_static_methods()]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Static.*")
    result = [m.name for m in helper.public_static_methods()]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="Something")
    result = [m.name for m in helper.public_static_methods()]
    assert len(result) == 0


def test_public_variables__no_filter(helper):
    result = [m.name for m in helper.public_variables()]
    assert result == ["PublicVariable"]


def test_public_variables__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Var.*")
    result = [m.name for m in helper.public_variables()]
    assert result == ["PublicVariable"]


def test_public_variables__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_variables()]
    assert len(result) == 0


def test_public_simple_enclosed_types__no_filter(helper):
    simple_enclosed_types = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(simple_enclosed_types) == sorted(
        ["PublicEnum", "PublicTypedef", "ProtectedEnum", "ProtectedTypedef"])


def test_public_simple_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Typedef")
    simple_enclosed_types = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(simple_enclosed_types) == sorted(["PublicTypedef", "ProtectedTypedef"])


def test_public_simple_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="other")
    simple_enclosed_types = [m.name for m in helper.public_simple_enclosed_types()]
    assert len(simple_enclosed_types) == 0


def test_public_complex_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert result == ["PublicType", "ProtectedType"]


def test_public_complex_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="Protected")
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert result == ["ProtectedType"]


def test_public_complex_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="NONE")
    result = [m.name for m in helper.public_complex_enclosed_types()]
    assert len(result) == 0
