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
Tests for Objective C template helpers.
"""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.generator.asciidoc import Context, DocumentTreeNode
from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Member, ReturnValue, Parameter, TypeRef
from asciidoxy.templates.objc.helpers import (public_methods, public_class_methods,
                                              public_properties, public_simple_enclosed_types,
                                              objc_method_signature)


@pytest.fixture
def context(input_file, build_dir, fragment_dir):
    return Context(base_dir=input_file.parent,
                   build_dir=build_dir,
                   fragment_dir=fragment_dir,
                   reference=ApiReference(),
                   current_document=DocumentTreeNode(input_file))


@pytest.fixture
def objc_class():
    compound = Compound("objc")
    compound.name = "MyClass"

    def generate_member(kind: str, prot: str) -> Member:
        member = Member("objc")
        member.kind = kind
        member.name = prot.capitalize() + kind.capitalize()
        member.prot = prot
        return member

    def generate_member_function(prot: str,
                                 name: str,
                                 has_return_value: bool = True,
                                 is_static: bool = False) -> Member:
        member = Member("objc")
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

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "protocol", "trash"):
            compound.members.append(generate_member(kind=member_type, prot=visibility))

        # add property
        compound.members.append(generate_property(prot=visibility))
        # add some method
        compound.members.append(
            generate_member_function(prot=visibility, name=visibility.capitalize() + "Method"))
        # add static method
        compound.members.append(
            generate_member_function(prot=visibility,
                                     name=visibility.capitalize() + "StaticMethod",
                                     is_static=True))

    # forbidden method
    member = Member("objc")
    member.kind = "function"
    member.name = "NS_UNAVAILABLE"
    member.prot = "public"
    member.returns = ReturnValue()
    compound.members.append(member)

    return compound


def test_public_methods__no_filter(objc_class):
    result = [m.name for m in public_methods(objc_class, InsertionFilter())]
    assert sorted(result) == sorted(["NS_UNAVAILABLE", "PublicMethod"])


def test_public_methods__filter_match(objc_class):
    result = [m.name for m in public_methods(objc_class, InsertionFilter(members="-NS_"))]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_no_match(objc_class):
    result = [m.name for m in public_methods(objc_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_class_methods__no_filter(objc_class):
    result = [m.name for m in public_class_methods(objc_class, InsertionFilter())]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_match(objc_class):
    result = [m.name for m in public_class_methods(objc_class, InsertionFilter(members="Public"))]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_no_match(objc_class):
    result = [m.name for m in public_class_methods(objc_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_properties__no_filter(objc_class):
    result = [m.name for m in public_properties(objc_class, InsertionFilter())]
    assert result == ["PublicProperty"]


def test_public_properties__filter_match(objc_class):
    result = [m.name for m in public_properties(objc_class, InsertionFilter(members="Public"))]
    assert result == ["PublicProperty"]


def test_public_properties__filter_no_match(objc_class):
    result = [m.name for m in public_properties(objc_class, InsertionFilter(members="NONE"))]
    assert len(result) == 0


def test_public_simple_enclosed_types__no_filter(objc_class):
    result = [m.name for m in public_simple_enclosed_types(objc_class, InsertionFilter())]
    assert sorted(result) == sorted([
        "PublicEnum", "ProtectedEnum", "PrivateEnum", "PublicClass", "ProtectedClass",
        "PrivateClass", "PublicProtocol", "ProtectedProtocol", "PrivateProtocol"
    ])


def test_public_simple_enclosed_types__filter_match(objc_class):
    result = [
        m.name for m in public_simple_enclosed_types(objc_class, InsertionFilter(members=".*Enum"))
    ]
    assert sorted(result) == sorted([
        "PublicEnum",
        "ProtectedEnum",
        "PrivateEnum",
    ])


def test_public_simple_enclosed_types__filter_no_match(objc_class):
    result = [
        m.name for m in public_simple_enclosed_types(objc_class, InsertionFilter(members="NONE"))
    ]
    assert len(result) == 0


def test_objc_method_signature__no_params_simple_return(context):
    method = Member("objc")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    assert objc_method_signature(method, context) == "- (void)start"


def test_objc_method_signature__no_params_link_return(context):
    method = Member("objc")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"
    assert objc_method_signature(method, context) == "- (xref:objc-value[Value])retrieveValue"


def test_objc_method_signature__one_param(context):
    method = Member("objc")
    method.name = "setValue:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    assert objc_method_signature(method,
                                 context) == "- (xref:objc-value[Value])setValue:(Type1)arg1"


def test_objc_method_signature__multiple_params_simple_return(context):
    method = Member("objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef("objc", "Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef("objc", "Type3")

    method.params = [param1, param2, param3]

    assert (objc_method_signature(method, context) == "- (Value)setValue:(Type1)arg1\n"
            "         withUnit:(xref:objc-type2[Type2])arg2\n"
            "  andALongerParam:(Type3)arg3")


def test_objc_method_signature__multiple_params_linked_return(context):
    method = Member("objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef("objc", "Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef("objc", "Type3")

    method.params = [param1, param2, param3]

    assert (objc_method_signature(method,
                                  context) == "- (xref:objc-value[Value])setValue:(Type1)arg1\n"
            "         withUnit:(xref:objc-type2[Type2])arg2\n"
            "  andALongerParam:(Type3)arg3")


def test_objc_method_signature__class_method(context):
    method = Member("objc")
    method.name = "start"
    method.static = True
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    assert objc_method_signature(method, context) == "+ (void)start"
