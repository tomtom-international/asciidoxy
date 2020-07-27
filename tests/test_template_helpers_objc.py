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

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Member, ReturnValue, Parameter, TypeRef
from asciidoxy.templates.objc.helpers import ObjcTemplateHelper


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


@pytest.fixture
def helper(empty_context, objc_class):
    return ObjcTemplateHelper(empty_context, objc_class, InsertionFilter())


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["NS_UNAVAILABLE", "PublicMethod"])


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="-NS_")
    result = [m.name for m in helper.public_methods()]
    assert sorted(result) == sorted(["PublicMethod"])


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_methods()]
    assert len(result) == 0


def test_public_class_methods__no_filter(helper):
    result = [m.name for m in helper.public_class_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_class_methods()]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_class_methods()]
    assert len(result) == 0


def test_public_properties__no_filter(helper):
    result = [m.name for m in helper.public_properties()]
    assert result == ["PublicProperty"]


def test_public_properties__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.public_properties()]
    assert result == ["PublicProperty"]


def test_public_properties__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_properties()]
    assert len(result) == 0


def test_public_simple_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(result) == sorted([
        "PublicEnum", "ProtectedEnum", "PrivateEnum", "PublicClass", "ProtectedClass",
        "PrivateClass", "PublicProtocol", "ProtectedProtocol", "PrivateProtocol"
    ])


def test_public_simple_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Enum")
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert sorted(result) == sorted([
        "PublicEnum",
        "ProtectedEnum",
        "PrivateEnum",
    ])


def test_public_simple_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.public_simple_enclosed_types()]
    assert len(result) == 0


def test_objc_method_signature__no_params_simple_return(empty_context):
    method = Member("objc")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    helper = ObjcTemplateHelper(empty_context)
    assert helper.method_signature(method) == "- (void)start"


def test_objc_method_signature__no_params_link_return(empty_context):
    method = Member("objc")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"
    helper = ObjcTemplateHelper(empty_context)
    assert helper.method_signature(method) == "- (xref:objc-value[Value])retrieveValue"


def test_objc_method_signature__one_param(empty_context):
    method = Member("objc")
    method.name = "setValue:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef("objc", "Type1")
    method.params = [param1]

    helper = ObjcTemplateHelper(empty_context)
    assert helper.method_signature(method) == "- (xref:objc-value[Value])setValue:(Type1)arg1"


def test_objc_method_signature__multiple_params_simple_return(empty_context):
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

    helper = ObjcTemplateHelper(empty_context)
    assert (helper.method_signature(method) == """\
- (Value)setValue:(Type1)arg1
         withUnit:(xref:objc-type2[Type2])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__multiple_params_linked_return(empty_context):
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

    helper = ObjcTemplateHelper(empty_context)
    assert (helper.method_signature(method) == """\
- (xref:objc-value[Value])setValue:(Type1)arg1
         withUnit:(xref:objc-type2[Type2])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__class_method(empty_context):
    method = Member("objc")
    method.name = "start"
    method.static = True
    method.returns = ReturnValue()
    method.returns.type = TypeRef("objc", name="void")
    helper = ObjcTemplateHelper(empty_context)
    assert helper.method_signature(method) == "+ (void)start"
