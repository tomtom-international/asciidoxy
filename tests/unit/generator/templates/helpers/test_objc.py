# Copyright (C) 2019, TomTom (http://tomtom.com).
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
from asciidoxy.generator.templates.objc.helpers import ObjcTemplateHelper
from asciidoxy.model import Compound, Parameter, ReturnValue, TypeRef

from ....builders import SimpleClassBuilder


@pytest.fixture
def objc_class():
    builder = SimpleClassBuilder("objc")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "protocol", "trash"):
            builder.simple_member(kind=member_type, prot=visibility)

        # add property
        builder.member_property(prot=visibility)
        # add some method
        builder.member_function(prot=visibility, name=visibility.capitalize() + "Method")
        # add static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "StaticMethod",
                                modifiers=["static"])

    # forbidden method
    builder.member_function(name="NS_UNAVAILABLE", prot="public")

    return builder.compound


@pytest.fixture
def helper(generating_api, objc_class):
    return ObjcTemplateHelper(generating_api, objc_class, InsertionFilter())


def test_public_class_methods__no_filter(helper):
    result = [m.name for m in helper.class_methods(prot="public")]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.class_methods(prot="public")]
    assert sorted(result) == sorted(["PublicStaticMethod"])


def test_public_class_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.class_methods(prot="public")]
    assert len(result) == 0


def test_private_class_methods__no_filter(helper):
    result = [m.name for m in helper.class_methods(prot="private")]
    assert sorted(result) == sorted(["PrivateStaticMethod"])


def test_public_properties__no_filter(helper):
    result = [m.name for m in helper.properties(prot="public")]
    assert result == ["PublicProperty"]


def test_public_properties__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.properties(prot="public")]
    assert result == ["PublicProperty"]


def test_public_properties__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.properties(prot="public")]
    assert len(result) == 0


def test_private_properties__no_filter(helper):
    result = [m.name for m in helper.properties(prot="private")]
    assert result == ["PrivateProperty"]


def test_objc_method_signature__no_params_simple_return(helper):
    method = Compound(language="objc")
    method.name = "start"
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="void")
    assert helper.method_signature(method) == "- (void)start"


def test_objc_method_signature__no_params_link_return(helper):
    method = Compound(language="objc")
    method.name = "retrieveValue"
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="Value")
    method.returns.type.id = "objc-value"
    assert helper.method_signature(method) == "- (xref:objc-value[++Value++])retrieveValue"


def test_objc_method_signature__one_param(helper):
    method = Compound(language="objc")
    method.name = "setValue:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef(language="objc", name="Type1")
    method.params = [param1]

    assert helper.method_signature(method) == "- (xref:objc-value[++Value++])setValue:(Type1)arg1"


def test_objc_method_signature__multiple_params_simple_return(helper):
    method = Compound(language="objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="Value")

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef(language="objc", name="Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef(language="objc", name="Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef(language="objc", name="Type3")

    method.params = [param1, param2, param3]

    assert (helper.method_signature(method) == """\
- (Value)setValue:(Type1)arg1
         withUnit:(xref:objc-type2[++Type2++])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__multiple_params_linked_return(helper):
    method = Compound(language="objc")
    method.name = "setValue:withUnit:andALongerParam:"
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="Value")
    method.returns.type.id = "objc-value"

    param1 = Parameter()
    param1.name = "arg1"
    param1.type = TypeRef(language="objc", name="Type1")

    param2 = Parameter()
    param2.name = "arg2"
    param2.type = TypeRef(language="objc", name="Type2")
    param2.type.id = "objc-type2"

    param3 = Parameter()
    param3.name = "arg3"
    param3.type = TypeRef(language="objc", name="Type3")

    method.params = [param1, param2, param3]

    assert (helper.method_signature(method) == """\
- (xref:objc-value[++Value++])setValue:(Type1)arg1
         withUnit:(xref:objc-type2[++Type2++])arg2
  andALongerParam:(Type3)arg3""")


def test_objc_method_signature__class_method(helper):
    method = Compound(language="objc")
    method.name = "start"
    method.modifiers = ["static"]
    method.returns = ReturnValue()
    method.returns.type = TypeRef(language="objc", name="void")
    assert helper.method_signature(method) == "+ (void)start"
