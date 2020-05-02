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

from asciidoxy.templates.cpp.helpers import (public_static_methods, public_methods,
                                             public_constructors, public_simple_enclosed_types,
                                             public_complex_enclosed_types, public_variables)
from asciidoxy.generator.filters import InsertionFilter


def test_public_constructors__no_filter(cpp_class):
    result = list(public_constructors(cpp_class, InsertionFilter()))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_match(cpp_class):
    result = list(public_constructors(cpp_class, InsertionFilter(members="MyClass")))
    assert len(result) == 1
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_no_match(cpp_class):
    result = list(public_constructors(cpp_class, InsertionFilter(members="OtherClass")))
    assert len(result) == 0


def test_public_methods__no_filter(cpp_class):
    result = [m.name for m in public_methods(cpp_class, InsertionFilter())]
    assert result == ["PublicMethod"]


def test_public_methods__filter_match(cpp_class):
    result = [m.name for m in public_methods(cpp_class, InsertionFilter(members="Public.*"))]
    assert result == ["PublicMethod"]


def test_public_methods__filter_no_match(cpp_class):
    result = [m.name for m in public_methods(cpp_class, InsertionFilter(members="PublicThing"))]
    assert len(result) == 0


def test_public_static_methods__no_filter(cpp_class):
    result = [m.name for m in public_static_methods(cpp_class, InsertionFilter())]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_match(cpp_class):
    result = [
        m.name for m in public_static_methods(cpp_class, InsertionFilter(members=".*Static.*"))
    ]
    assert result == ["PublicStaticMethod"]


def test_public_static_methods__filter_no_match(cpp_class):
    result = [
        m.name for m in public_static_methods(cpp_class, InsertionFilter(members="Something"))
    ]
    assert len(result) == 0


def test_public_variables__no_filter(cpp_class):
    result = [m.name for m in public_variables(cpp_class, InsertionFilter())]
    assert result == ["PublicVariable"]


def test_public_variables__filter_match(cpp_class):
    result = [m.name for m in public_variables(cpp_class, InsertionFilter(members=".*Var.*"))]
    assert result == ["PublicVariable"]


def test_public_variables__filter_no_match(cpp_class):
    result = [m.name for m in public_variables(cpp_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_simple_enclosed_types__no_filter(cpp_class):
    simple_enclosed_types = [
        m.name for m in public_simple_enclosed_types(cpp_class, InsertionFilter())
    ]
    assert sorted(simple_enclosed_types) == sorted(
        ["PublicEnum", "PublicTypedef", "ProtectedEnum", "ProtectedTypedef"])


def test_public_simple_enclosed_types__filter_match(cpp_class):
    simple_enclosed_types = [
        m.name
        for m in public_simple_enclosed_types(cpp_class, InsertionFilter(members=".*Typedef"))
    ]
    assert sorted(simple_enclosed_types) == sorted(["PublicTypedef", "ProtectedTypedef"])


def test_public_simple_enclosed_types__filter_no_match(cpp_class):
    simple_enclosed_types = [
        m.name for m in public_simple_enclosed_types(cpp_class, InsertionFilter(members="other"))
    ]
    assert len(simple_enclosed_types) == 0


def test_public_complex_enclosed_types__no_filter(cpp_class):
    result = [m.name for m in public_complex_enclosed_types(cpp_class, InsertionFilter())]
    assert result == ["NestedClass"]


def test_public_complex_enclosed_types__filter_match(cpp_class):
    result = [
        m.name
        for m in public_complex_enclosed_types(cpp_class, InsertionFilter(inner_classes="Nested"))
    ]
    assert result == ["NestedClass"]


def test_public_complex_enclosed_types__filter_no_match(cpp_class):
    result = [
        m.name
        for m in public_complex_enclosed_types(cpp_class, InsertionFilter(inner_classes="NONE"))
    ]
    assert len(result) == 0
