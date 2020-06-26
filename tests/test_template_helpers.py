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
Tests for the shared template helpers.
"""

import pytest

from unittest.mock import call, patch

from asciidoxy.templates.helpers import (link_from_ref, print_ref, argument_list, type_list, has,
                                         type_and_name, chain, method_signature)
from asciidoxy.model import Member, Parameter, ReturnValue, TypeRef


@pytest.fixture
def context_mock(empty_context):
    with patch("asciidoxy.generator.asciidoc.Context", wraps=empty_context) as mock:
        yield mock


def test_link_from_ref__empty(context_mock):
    ref = TypeRef("lang")
    assert link_from_ref(ref, context_mock) == ""
    context_mock.assert_not_called()


def test_link_from_ref__none(context_mock):
    assert link_from_ref(None, context_mock) == ""
    context_mock.assert_not_called()


def test_link_from_ref__name_only(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    assert link_from_ref(ref, context_mock) == "MyType"
    context_mock.assert_not_called()


def test_link_from_ref__name_prefix_suffix_no_id(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    assert link_from_ref(ref, context_mock) == "const MyType &"
    context_mock.assert_not_called()


def test_link_from_ref__name_prefix_suffix_with_id(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    assert link_from_ref(ref, context_mock) == "const xref:lang-tomtom_1_MyType[MyType] &"
    context_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_link_from_ref__strip_surrounding_whitespace(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "  const "
    ref.suffix = " &  "
    ref.id = "lang-tomtom_1_MyType"
    assert link_from_ref(ref, context_mock) == "const xref:lang-tomtom_1_MyType[MyType] &"
    context_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_link_from_ref__nested_types(context_mock):
    nested_type_with_id = TypeRef("lang")
    nested_type_with_id.name = "Nested1"
    nested_type_with_id.id = "lang-nested1"

    nested_type_without_id = TypeRef("lang")
    nested_type_without_id.name = "Nested2"

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = [nested_type_with_id, nested_type_without_id]

    assert (link_from_ref(ref, context_mock) ==
            "const xref:lang-tomtom_1_MyType[MyType]&lt;xref:lang-nested1[Nested1], Nested2&gt; &")
    context_mock.link_to_element.assert_has_calls(
        [call(nested_type_with_id.id, nested_type_with_id.name),
         call(ref.id, ref.name)])


def test_link_from_ref__empty_nested_types(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = []

    assert link_from_ref(ref, context_mock) == "const xref:lang-tomtom_1_MyType[MyType]&lt;&gt; &"
    context_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_link_from_ref__args(context_mock):
    arg1_type = TypeRef("lang")
    arg1_type.name = "ArgType1"
    arg1_type.id = "lang-argtype1"

    arg1 = Parameter()
    arg1.type = arg1_type

    arg2_type = TypeRef("lang")
    arg2_type.name = "ArgType2"

    arg2 = Parameter()
    arg2.name = "value"
    arg2.type = arg2_type

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-tomtom_1_MyType"
    ref.args = [arg1, arg2]

    assert (link_from_ref(ref, context_mock) ==
            "xref:lang-tomtom_1_MyType[MyType](xref:lang-argtype1[ArgType1], ArgType2 value)")
    context_mock.link_to_element.assert_has_calls(
        [call(arg1_type.id, arg1_type.name),
         call(ref.id, ref.name)])


def test_link_from_ref__empty_args(context_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.args = []

    assert link_from_ref(ref, context_mock) == "const xref:lang-tomtom_1_MyType[MyType]() &"
    context_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_link_from_ref__nested_and_args_custom_start_and_end(context_mock):
    nested_type = TypeRef("lang")
    nested_type.name = "Nested1"

    arg_type = TypeRef("lang")
    arg_type.name = "ArgType"
    arg_type.id = "lang-argtype"

    arg = Parameter()
    arg.type = arg_type

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = [nested_type]
    ref.args = [arg]

    assert (link_from_ref(ref,
                          context_mock,
                          nested_start="{",
                          nested_end=";",
                          args_start="@",
                          args_end="#") ==
            "const xref:lang-tomtom_1_MyType[MyType]{Nested1;@xref:lang-argtype[ArgType]# &")


def test_print_ref__empty():
    ref = TypeRef("lang")
    assert print_ref(ref) == ""


def test_print_ref__none():
    assert print_ref(None) == ""


def test_print_ref__name_only():
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    assert print_ref(ref) == "MyType"


def test_print_ref__name_prefix_suffix_no_id():
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    ref.prefix = "const "
    ref.suffix = " &"
    assert print_ref(ref) == "const MyType &"


def test_print_ref__strip_surrounding_whitespace():
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    ref.prefix = "\tconst "
    ref.suffix = " &  "
    assert print_ref(ref) == "const MyType &"


def test_print_ref__nested_types():
    nested_type_with_id = TypeRef("lang")
    nested_type_with_id.name = "Nested1"
    nested_type_with_id.id = "lang-nested1"

    nested_type_without_id = TypeRef("lang")
    nested_type_without_id.name = "Nested2"

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = [nested_type_with_id, nested_type_without_id]

    assert print_ref(ref) == "const MyType&lt;Nested1, Nested2&gt; &"


def test_print_ref__empty_nested_types():
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = []

    assert print_ref(ref) == "const MyType&lt;&gt; &"


def test_print_ref__args():
    arg1_type = TypeRef("lang")
    arg1_type.name = "ArgType1"
    arg1_type.id = "lang-argtype1"

    arg1 = Parameter()
    arg1.type = arg1_type

    arg2_type = TypeRef("lang")
    arg2_type.name = "ArgType2"

    arg2 = Parameter()
    arg2.name = "value"
    arg2.type = arg2_type

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-tomtom_1_MyType"
    ref.args = [arg1, arg2]

    assert print_ref(ref) == "MyType(ArgType1, ArgType2 value)"


def test_print_ref__empty_args():
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.args = []

    assert print_ref(ref) == "const MyType() &"


def test_print_ref__nested_and_args_custom_start_and_end():
    nested_type = TypeRef("lang")
    nested_type.name = "Nested1"

    arg_type = TypeRef("lang")
    arg_type.name = "ArgType"
    arg_type.id = "lang-argtype"

    arg = Parameter()
    arg.type = arg_type

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = [nested_type]
    ref.args = [arg]

    assert (print_ref(ref, nested_start="{", nested_end=";", args_start="@",
                      args_end="#") == "const MyType{Nested1;@ArgType# &")


def test_argument_list__empty(empty_context):
    assert argument_list([], empty_context) == "()"


def test_argument_list(empty_context):
    type1 = TypeRef("lang")
    type1.prefix = "const "
    type1.name = "Type1"

    type2 = TypeRef("lang")
    type2.name = "Type2"
    type2.suffix = " &"
    type2.id = "lang-type2"

    type3 = TypeRef("lang")
    type3.name = "Type3"
    type3.nested = [type1, type2]

    param1 = Parameter()
    param1.type = type1

    param2 = Parameter()
    param2.type = type2
    param2.name = "arg2"

    param3 = Parameter()
    param3.type = type3
    param3.name = "arg3"

    assert (argument_list([param1, param2, param3],
                          empty_context) == "(const Type1, xref:lang-type2[Type2] & arg2, "
            "Type3&lt;const Type1, xref:lang-type2[Type2] &&gt; arg3)")


def test_type_list():
    type1 = TypeRef("lang")
    type1.prefix = "const "
    type1.name = "Type1"

    type2 = TypeRef("lang")
    type2.name = "Type2"
    type2.suffix = " &"
    type2.id = "lang-type2"

    type3 = TypeRef("lang")
    type3.name = "Type3"
    type3.nested = [type1, type2]

    param1 = Parameter()
    param1.type = type1
    param1.name = "arg1"

    param2 = Parameter()
    param2.type = type2
    param2.name = "arg2"

    param3 = Parameter()
    param3.type = type3
    param3.name = "arg3"

    assert (type_list([param1, param2,
                       param3]) == "(const Type1, Type2 &, Type3&lt;const Type1, Type2 &&gt;)")


def test_has__list():
    assert has([]) is False
    assert has([1]) is True
    assert has([1, 2]) is True
    assert has([None]) is True


def test_has__generator():
    def empty_gen():
        if False:
            yield 1
        return None

    assert has(empty_gen()) is False

    def single_item_gen():
        yield 1
        return None

    assert has(single_item_gen()) is True

    def multiple_item_gen():
        yield 2
        yield "2"
        yield True
        return None

    assert has(multiple_item_gen()) is True

    def none_gen():
        yield None
        yield None
        return None

    assert has(none_gen()) is True


def test_chain():
    def gen_empty():
        return []

    def gen_one():
        return [1]

    def gen_two():
        return [2, 3]

    def collect_chained(first_gen, second_gen):
        generated_values = []
        for value in chain(first_gen, second_gen):
            generated_values.append(value)
        return generated_values

    assert collect_chained(gen_one(), gen_two()) == [1, 2, 3]
    assert collect_chained(gen_empty(), gen_empty()) == []
    assert collect_chained(gen_empty(), gen_two()) == [2, 3]
    assert collect_chained(gen_one(), gen_empty()) == [1]


def test_type_and_name(empty_context):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"

    assert type_and_name(param, empty_context) == "const xref:lang-tomtom_1_MyType[MyType] & arg"


def test_type_and_name__no_name(empty_context):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = ""

    assert type_and_name(param, empty_context) == "const xref:lang-tomtom_1_MyType[MyType] &"


def test_method_signature__no_params(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    assert method_signature(method, empty_context) == "void ShortMethod()"


def test_method_signature__single_param(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    assert method_signature(method, empty_context) == "void ShortMethod(int value)"


def test_method_signature__single_param__too_wide(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    assert (method_signature(method, empty_context, max_width=20) == """\
void ShortMethod(
    int value)""")


def test_method_signature__multiple_params(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("lang", "double")
    method.params[2].name = "text"
    method.params[2].type = TypeRef("lang", "std::string")

    assert (method_signature(method, empty_context) == """\
void ShortMethod(int value,
                 double other_value,
                 std::string text)""")


def test_method_signature__multiple_params__first_param_too_wide(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("lang", "double")
    method.params[2].name = "text"
    method.params[2].type = TypeRef("lang", "std::string")

    assert (method_signature(method, empty_context, max_width=20) == """\
void ShortMethod(
    int value,
    double other_value,
    std::string text)""")


def test_method_signature__multiple_params__last_param_too_wide(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter(), Parameter(), Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")
    method.params[1].name = "other_value"
    method.params[1].type = TypeRef("lang", "double")
    method.params[2].name = "text" * 10
    method.params[2].type = TypeRef("lang", "std::string")

    assert (method_signature(method, empty_context, max_width=40) == f"""\
void ShortMethod(
    int value,
    double other_value,
    std::string {"text" * 10})""")


def test_method_signature__ignore_return_type_xref_length(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")
    method.returns.type.id = "ab" * 80

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    assert (method_signature(method,
                             empty_context) == f"xref:{'ab' * 80}[void] ShortMethod(int value)")


def test_method_signature__ignore_param_type_xref_length(empty_context):
    method = Member("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")
    method.params[0].type.id = "ab" * 80

    assert (method_signature(method,
                             empty_context) == f"void ShortMethod(xref:{'ab' * 80}[int] value)")
