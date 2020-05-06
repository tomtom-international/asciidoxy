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
                                         type_and_name, chain)
from asciidoxy.model import Parameter, TypeRef


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
