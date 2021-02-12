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

from unittest.mock import call, Mock

from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.templates.helpers import has, has_any, TemplateHelper
from asciidoxy.model import Compound, Parameter, ReturnValue, TypeRef


@pytest.fixture
def api_mock(empty_generating_api):
    return Mock(wraps=empty_generating_api)


@pytest.fixture
def helper(empty_generating_api, cpp_class):
    return TemplateHelper(empty_generating_api, cpp_class, InsertionFilter())


def test_print_ref__link__empty(api_mock):
    ref = TypeRef("lang")
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == ""
    api_mock.link_to_element.assert_not_called()


def test_print_ref__link__none(api_mock):
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(None) == ""
    api_mock.link_to_element.assert_not_called()


def test_print_ref__link__name_only(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "MyType"
    api_mock.link_to_element.assert_not_called()


def test_print_ref__link__name_prefix_suffix_no_id(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "const MyType &"
    api_mock.link_to_element.assert_not_called()


def test_print_ref__link__name_prefix_suffix_with_id(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "const xref:lang-tomtom_1_MyType[+++MyType+++] &"
    api_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_print_ref__link__strip_surrounding_whitespace(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "  const "
    ref.suffix = " &  "
    ref.id = "lang-tomtom_1_MyType"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "const xref:lang-tomtom_1_MyType[+++MyType+++] &"
    api_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_print_ref__link__nested_types(api_mock):
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

    helper = TemplateHelper(api_mock)
    assert (helper.print_ref(ref) ==
            "const xref:lang-tomtom_1_MyType[+++MyType+++]&lt;xref:lang-nested1[+++Nested1+++], "
            "Nested2&gt; &")
    api_mock.link_to_element.assert_has_calls(
        [call(nested_type_with_id.id, nested_type_with_id.name),
         call(ref.id, ref.name)])


def test_print_ref__link__empty_nested_types(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = []

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "const xref:lang-tomtom_1_MyType[+++MyType+++]&lt;&gt; &"
    api_mock.link_to_element.assert_called_once_with(ref.id, ref.name)


def test_print_ref__link__closure(api_mock):
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

    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.id = "lang-tomtom_1_MyType"

    ref = TypeRef("lang")
    ref.args = [arg1, arg2]
    ref.returns = return_type

    helper = TemplateHelper(api_mock)
    assert (helper.print_ref(ref) ==
            "xref:lang-tomtom_1_MyType[+++MyType+++](xref:lang-argtype1[+++ArgType1+++], ArgType2 "
            "value)")
    api_mock.link_to_element.assert_has_calls(
        [call(arg1_type.id, arg1_type.name),
         call(return_type.id, return_type.name)])


def test_print_ref__link__complex_closure(api_mock):
    ref = TypeRef("lang")
    ref.name = "std::function"
    ref.nested = [TypeRef("lang")]

    ref.nested[0].returns = TypeRef("lang")
    ref.nested[0].returns.name = "void"
    ref.nested[0].args = [Parameter()]

    ref.nested[0].args[0].type = TypeRef("lang")
    ref.nested[0].args[0].type.name = "std::shared_ptr"
    ref.nested[0].args[0].type.prefix = "const "
    ref.nested[0].args[0].type.suffix = "&"
    ref.nested[0].args[0].type.nested = [TypeRef("lang")]

    ref.nested[0].args[0].type.nested[0].name = "detail::SuccessDescriptor"
    ref.nested[0].args[0].type.nested[0].id = "lang-successdescriptor"

    helper = TemplateHelper(api_mock)
    assert (helper.print_ref(ref) ==
            "std::function&lt;void(const std::shared_ptr&lt;xref:lang-successdescriptor"
            "[+++detail::SuccessDescriptor+++]&gt;&)&gt;")
    api_mock.link_to_element.assert_has_calls(
        [call(ref.nested[0].args[0].type.nested[0].id, ref.nested[0].args[0].type.nested[0].name)])


def test_print_ref__link__empty_closure(api_mock):
    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.prefix = "const "
    return_type.suffix = " &"
    return_type.id = "lang-tomtom_1_MyType"

    ref = TypeRef("lang")
    ref.args = []
    ref.returns = return_type

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref) == "const xref:lang-tomtom_1_MyType[+++MyType+++] &()"
    api_mock.link_to_element.assert_called_once_with(return_type.id, return_type.name)


def test_print_ref__link__closure_with_nested_types__custom_start_and_end(api_mock):
    nested_type = TypeRef("lang")
    nested_type.name = "Nested1"

    arg_type = TypeRef("lang")
    arg_type.name = "ArgType"
    arg_type.id = "lang-argtype"

    arg = Parameter()
    arg.type = arg_type

    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.prefix = "const "
    return_type.suffix = " &"
    return_type.id = "lang-tomtom_1_MyType"
    return_type.nested = [nested_type]

    ref = TypeRef("lang")
    ref.args = [arg]
    ref.returns = return_type

    class TestHelper(TemplateHelper):
        NESTED_START: str = "{"
        NESTED_END: str = ";"
        ARGS_START: str = "@"
        ARGS_END: str = "#"

    helper = TestHelper(api_mock)
    assert (helper.print_ref(ref) == "const xref:lang-tomtom_1_MyType[+++MyType+++]{Nested1; "
            "&@xref:lang-argtype[+++ArgType+++]#")


def test_print_ref__no_link__empty(api_mock):
    ref = TypeRef("lang")
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == ""


def test_print_ref__no_link__none(api_mock):
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(None, link=False) == ""


def test_print_ref__no_link__name_only(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "MyType"


def test_print_ref__no_link__name_prefix_suffix_no_id(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    ref.prefix = "const "
    ref.suffix = " &"
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType &"


def test_print_ref__no_link__strip_surrounding_whitespace(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.id = "lang-mytype"
    ref.prefix = "\tconst "
    ref.suffix = " &  "
    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType &"


def test_print_ref__no_link__nested_types(api_mock):
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

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType&lt;Nested1, Nested2&gt; &"


def test_print_ref__no_link__empty_nested_types(api_mock):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"
    ref.nested = []

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType&lt;&gt; &"


def test_print_ref__no_link__closure(api_mock):
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

    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.id = "lang-tomtom_1_MyType"
    return_type.prefix = "const "
    return_type.suffix = "&"

    ref = TypeRef("lang")
    ref.returns = return_type
    ref.args = [arg1, arg2]

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType&(ArgType1, ArgType2 value)"


def test_print_ref__no_link__empty_closure(api_mock):
    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.prefix = "const "
    return_type.suffix = " &"
    return_type.id = "lang-tomtom_1_MyType"

    ref = TypeRef("lang")
    ref.args = []
    ref.returns = return_type

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "const MyType &()"


def test_print_ref__no_link__closure_with_nested_type__custom_start_and_end(api_mock):
    nested_type = TypeRef("lang")
    nested_type.name = "Nested1"

    arg_type = TypeRef("lang")
    arg_type.name = "ArgType"
    arg_type.id = "lang-argtype"

    arg = Parameter()
    arg.type = arg_type

    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.prefix = "const "
    return_type.suffix = " &"
    return_type.id = "lang-tomtom_1_MyType"
    return_type.nested = [nested_type]

    ref = TypeRef("lang")
    ref.args = [arg]
    ref.returns = return_type

    class TestHelper(TemplateHelper):
        NESTED_START: str = "{"
        NESTED_END: str = ";"
        ARGS_START: str = "@"
        ARGS_END: str = "#"

    helper = TestHelper(api_mock)
    assert (helper.print_ref(ref, link=False) == "const MyType{Nested1; &@ArgType#")


def test_print_ref__no_link__closure_prefix_suffix(api_mock):
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

    return_type = TypeRef("lang")
    return_type.name = "MyType"
    return_type.id = "lang-tomtom_1_MyType"
    return_type.prefix = "const "
    return_type.suffix = "&"

    ref = TypeRef("lang")
    ref.returns = return_type
    ref.args = [arg1, arg2]
    ref.prefix = "final "
    ref.suffix = "*"

    helper = TemplateHelper(api_mock)
    assert helper.print_ref(ref, link=False) == "final (const MyType&(ArgType1, ArgType2 value))*"


def test_argument_list__empty(empty_generating_api):
    helper = TemplateHelper(empty_generating_api)
    assert helper.argument_list([]) == "()"


def test_argument_list(empty_generating_api):
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

    helper = TemplateHelper(empty_generating_api)
    assert (helper.argument_list([param1, param2,
                                  param3]) == "(const Type1, xref:lang-type2[+++Type2+++] & arg2, "
            "Type3&lt;const Type1, xref:lang-type2[+++Type2+++] &&gt; arg3)")


def test_type_list(empty_generating_api):
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

    helper = TemplateHelper(empty_generating_api)
    assert (helper.type_list([param1, param2, param3
                              ]) == "(const Type1, Type2 &, Type3&lt;const Type1, Type2 &&gt;)")


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


def test_has_any__list():
    assert has_any() is False
    assert has_any([]) is False
    assert has_any([], [], []) is False
    assert has_any([1], [], []) is True
    assert has_any([], [2], []) is True
    assert has_any([], [], [3]) is True


def test_has_any__generator():
    def empty_gen():
        if False:
            yield 1
        return None

    def single_item_gen():
        yield 1
        return None

    assert has_any(empty_gen(), empty_gen()) is False
    assert has_any(single_item_gen(), empty_gen()) is True
    assert has_any(empty_gen(), single_item_gen()) is True


def test_has_any__list_and_generator():
    def empty_gen():
        if False:
            yield 1
        return None

    def single_item_gen():
        yield 1
        return None

    assert has_any(empty_gen(), []) is False
    assert has_any([], empty_gen(), []) is False
    assert has_any(single_item_gen(), []) is True
    assert has_any([41], empty_gen()) is True
    assert has_any([], single_item_gen()) is True
    assert has_any(empty_gen(), [42]) is True


def test_parameter(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"

    helper = TemplateHelper(empty_generating_api)
    assert helper.parameter(param) == "const xref:lang-tomtom_1_MyType[+++MyType+++] & arg"


def test_parameter__no_link(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"

    helper = TemplateHelper(empty_generating_api)
    assert helper.parameter(param, link=False) == "const MyType & arg"


def test_parameter__no_name(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = ""

    helper = TemplateHelper(empty_generating_api)
    assert helper.parameter(param) == "const xref:lang-tomtom_1_MyType[+++MyType+++] &"


def test_parameter__default_value(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    helper = TemplateHelper(empty_generating_api)
    assert helper.parameter(
        param, default_value=True) == "const xref:lang-tomtom_1_MyType[+++MyType+++] & arg = 12"


def test_parameter__ignore_default_value(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.default_value = "12"

    helper = TemplateHelper(empty_generating_api)
    assert (helper.parameter(
        param, default_value=False) == "const xref:lang-tomtom_1_MyType[+++MyType+++] "
            "& arg")


def test_parameter__prefix(empty_generating_api):
    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.prefix = "vararg "

    helper = TemplateHelper(empty_generating_api)
    assert helper.parameter(param) == "vararg const xref:lang-tomtom_1_MyType[+++MyType+++] & arg"


def test_parameter__param_name_separator(empty_generating_api):
    class _TemplateHelper(TemplateHelper):
        PARAM_NAME_SEP = "_@_"

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.prefix = "vararg "
    param.default_value = "12"

    helper = _TemplateHelper(empty_generating_api)
    assert (helper.parameter(
        param, default_value=True) == "vararg const xref:lang-tomtom_1_MyType[+++MyType+++] "
            "&_@_arg = 12")


def test_parameter__param_name_first(empty_generating_api):
    class _TemplateHelper(TemplateHelper):
        PARAM_NAME_FIRST = True

    ref = TypeRef("lang")
    ref.name = "MyType"
    ref.prefix = "const "
    ref.suffix = " &"
    ref.id = "lang-tomtom_1_MyType"

    param = Parameter()
    param.type = ref
    param.name = "arg"
    param.prefix = "vararg "
    param.default_value = "12"

    helper = _TemplateHelper(empty_generating_api)
    assert (helper.parameter(
        param, default_value=True) == "vararg arg const xref:lang-tomtom_1_MyType[+++MyType+++] "
            "& = 12")


def test_method_signature__no_params(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    helper = TemplateHelper(empty_generating_api)
    assert helper.method_signature(method) == "void ShortMethod()"


def test_method_signature__const(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"
    method.const = True

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    helper = TemplateHelper(empty_generating_api)
    assert helper.method_signature(method) == "void ShortMethod() const"


def test_method_signature__single_param(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    helper = TemplateHelper(empty_generating_api)
    assert helper.method_signature(method) == "void ShortMethod(int value)"


def test_method_signature__single_param__too_wide(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method, max_width=20) == """\
void ShortMethod(
    int value)""")


def test_method_signature__multiple_params(empty_generating_api):
    method = Compound("lang")
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

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method) == """\
void ShortMethod(int value,
                 double other_value,
                 std::string text)""")


def test_method_signature__multiple_params__first_param_too_wide(empty_generating_api):
    method = Compound("lang")
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

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method, max_width=20) == """\
void ShortMethod(
    int value,
    double other_value,
    std::string text)""")


def test_method_signature__multiple_params__last_param_too_wide(empty_generating_api):
    method = Compound("lang")
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

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method, max_width=40) == f"""\
void ShortMethod(
    int value,
    double other_value,
    std::string {"text" * 10})""")


def test_method_signature__ignore_return_type_xref_length(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")
    method.returns.type.id = "ab" * 80

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method) == f"xref:{'ab' * 80}[+++void+++] ShortMethod(int "
            "value)")


def test_method_signature__ignore_param_type_xref_length(empty_generating_api):
    method = Compound("lang")
    method.name = "ShortMethod"

    method.returns = ReturnValue()
    method.returns.type = TypeRef("lang", "void")

    method.params = [Parameter()]
    method.params[0].name = "value"
    method.params[0].type = TypeRef("lang", "int")
    method.params[0].type.id = "ab" * 80

    helper = TemplateHelper(empty_generating_api)
    assert (helper.method_signature(method) == f"void ShortMethod(xref:{'ab' * 80}[+++int+++] "
            "value)")


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


def test_protected_static_methods__no_filter(helper):
    result = [m.name for m in helper.static_methods(prot="protected")]
    assert result == ["ProtectedStaticMethod"]


def test_private_static_methods__no_filter(helper):
    result = [m.name for m in helper.static_methods(prot="private")]
    assert result == ["PrivateStaticMethod"]


def test_public_methods__no_filter(helper):
    result = [m.name for m in helper.methods(prot="public")]
    assert sorted(result) == sorted(["PublicMethod", "operator=", "operator=", "operator++"])


def test_public_methods__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public.*")
    result = [m.name for m in helper.methods(prot="public")]
    assert result == ["PublicMethod"]


def test_public_methods__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="PublicThing")
    result = [m.name for m in helper.methods(prot="public")]
    assert len(result) == 0


def test_protected_methods__no_filter(helper):
    result = [m.name for m in helper.methods(prot="protected")]
    assert sorted(result) == sorted(["ProtectedMethod", "operator=", "operator=", "operator++"])


def test_private_methods__no_filter(helper):
    result = [m.name for m in helper.methods(prot="private")]
    assert sorted(result) == sorted(["PrivateMethod", "operator=", "operator=", "operator++"])


def test_public_constructors__no_filter(helper):
    result = list(helper.constructors(prot="public"))
    assert len(result) == 3
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="MyClass")
    result = list(helper.constructors(prot="public"))
    assert len(result) == 3
    assert result[0].name == "MyClass"
    assert result[0].prot == "public"


def test_public_constructors__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="OtherClass")
    result = list(helper.constructors(prot="public"))
    assert len(result) == 0


def test_protected_constructors__no_filter(helper):
    result = list(helper.constructors(prot="protected"))
    assert len(result) == 3
    assert result[0].name == "MyClass"
    assert result[0].prot == "protected"


def test_private_constructors__no_filter(helper):
    result = list(helper.constructors(prot="private"))
    assert len(result) == 3
    assert result[0].name == "MyClass"
    assert result[0].prot == "private"


def test_public_simple_enclosed_types__no_filter(helper):
    simple_enclosed_types = [m.name for m in helper.simple_enclosed_types(prot="public")]
    assert sorted(simple_enclosed_types) == sorted(["PublicEnum", "PublicTypedef"])


def test_public_simple_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Typedef")
    simple_enclosed_types = [m.name for m in helper.simple_enclosed_types(prot="public")]
    assert sorted(simple_enclosed_types) == sorted(["PublicTypedef"])


def test_public_simple_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="other")
    simple_enclosed_types = [m.name for m in helper.simple_enclosed_types(prot="public")]
    assert len(simple_enclosed_types) == 0


def test_protected_simple_enclosed_types__no_filter(helper):
    simple_enclosed_types = [m.name for m in helper.simple_enclosed_types(prot="protected")]
    assert sorted(simple_enclosed_types) == sorted(["ProtectedEnum", "ProtectedTypedef"])


def test_private_simple_enclosed_types__no_filter(helper):
    simple_enclosed_types = [m.name for m in helper.simple_enclosed_types(prot="private")]
    assert sorted(simple_enclosed_types) == sorted(["PrivateEnum", "PrivateTypedef"])


def test_public_complex_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.complex_enclosed_types(prot="public")]
    assert result == ["PublicType"]


def test_public_complex_enclosed_types__filter_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes=".*Type")
    result = [m.name for m in helper.complex_enclosed_types(prot="public")]
    assert result == ["PublicType"]


def test_public_complex_enclosed_types__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(inner_classes="NONE")
    result = [m.name for m in helper.complex_enclosed_types(prot="public")]
    assert len(result) == 0


def test_protected_complex_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.complex_enclosed_types(prot="protected")]
    assert result == ["ProtectedType"]


def test_private_complex_enclosed_types__no_filter(helper):
    result = [m.name for m in helper.complex_enclosed_types(prot="private")]
    assert result == ["PrivateType"]


def test_public_variables__no_filter(helper):
    result = [m.name for m in helper.variables(prot="public")]
    assert result == ["PublicVariable"]


def test_public_variables__filter_match(helper):
    helper.insert_filter = InsertionFilter(members=".*Var.*")
    result = [m.name for m in helper.variables(prot="public")]
    assert result == ["PublicVariable"]


def test_public_variables__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.variables(prot="public")]
    assert len(result) == 0


def test_protected_variables__no_filter(helper):
    result = [m.name for m in helper.variables(prot="protected")]
    assert result == ["ProtectedVariable"]


def test_private_variables__no_filter(helper):
    result = [m.name for m in helper.variables(prot="private")]
    assert result == ["PrivateVariable"]
