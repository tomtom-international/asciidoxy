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
Tests for the `asciidoxy.model` module.
"""

from asciidoxy.model import (Compound, EnumValue, Member, Parameter, ReturnValue, ThrowsClause,
                             TypeRef, InnerTypeReference)


def test_minimal_constructed_repr():
    assert repr(TypeRef("lang"))
    assert repr(Parameter())
    assert repr(ReturnValue())
    assert repr(ThrowsClause("lang"))
    assert repr(EnumValue("lang"))
    assert repr(Member("lang"))
    assert repr(Compound("lang"))
    assert repr(InnerTypeReference("lang"))


def test_type_ref_to_str():
    assert str(TypeRef("cpp")) == ""
    assert str(TypeRef("cpp", "Type")) == "Type"

    type_ref = TypeRef("cpp", "Type")
    type_ref.id = "12345"
    assert str(type_ref) == "Type"

    type_ref.kind = "class"
    assert str(type_ref) == "Type"

    type_ref.prefix = "const "
    assert str(type_ref) == "const Type"

    type_ref.suffix = " &"
    assert str(type_ref) == "const Type &"

    nested_type_1 = TypeRef("cpp", "Nested1")
    type_ref.nested.append(nested_type_1)
    assert str(type_ref) == "const Type< Nested1 > &"

    nested_type_2 = TypeRef("cpp", "Nested2")
    nested_type_2.prefix = "const "
    nested_type_2.suffix = "*"
    type_ref.nested.append(nested_type_2)
    assert str(type_ref) == "const Type< Nested1, const Nested2* > &"

    nested_type_2.nested.append(nested_type_1)
    assert str(type_ref) == "const Type< Nested1, const Nested2< Nested1 >* > &"
