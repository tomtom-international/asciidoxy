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
"""Test filters for generated parts."""

import pytest

from asciidoxy.generator.filters import (AllStringFilter, NoneStringFilter, IncludeStringFilter,
                                         ExcludeStringFilter, ChainedStringFilter, MemberFilter,
                                         FilterAction, InnerClassFilter, EnumValueFilter,
                                         ExceptionFilter)
from asciidoxy.model import Compound, EnumValue, InnerTypeReference, ThrowsClause


def test_all_string_filter():
    all_filter = AllStringFilter()

    assert all_filter("") is FilterAction.INCLUDE
    assert all_filter("any_string") is FilterAction.INCLUDE
    assert all_filter("not_bytes") is FilterAction.INCLUDE


def test_non_string_filter():
    none_filter = NoneStringFilter()

    assert none_filter("") is FilterAction.EXCLUDE
    assert none_filter("any_string") is FilterAction.EXCLUDE
    assert none_filter("not_bytes") is FilterAction.EXCLUDE


def test_include_string_filter():
    include_filter = IncludeStringFilter(r".*str.*")

    assert include_filter("") is FilterAction.NEUTRAL
    assert include_filter("any_string") is FilterAction.INCLUDE
    assert include_filter("not_bytes") is FilterAction.NEUTRAL


def test_exclude_string_filter():
    exclude_filter = ExcludeStringFilter(r".*str.*")

    assert exclude_filter("") is FilterAction.NEUTRAL
    assert exclude_filter("any_string") is FilterAction.EXCLUDE
    assert exclude_filter("not_bytes") is FilterAction.NEUTRAL


def test_chained_string_filter__none_include():
    chained_filter = ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*str.*"))

    assert chained_filter("") is FilterAction.EXCLUDE
    assert chained_filter("any_string") is FilterAction.INCLUDE
    assert chained_filter("not_bytes") is FilterAction.EXCLUDE


def test_chained_string_filter__none_multiple_include():
    chained_filter = ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*str.*"),
                                         IncludeStringFilter(r"not.*"))

    assert chained_filter("") is FilterAction.EXCLUDE
    assert chained_filter("any_string") is FilterAction.INCLUDE
    assert chained_filter("not_bytes") is FilterAction.INCLUDE


def test_chained_string_filter__all_exclude():
    chained_filter = ChainedStringFilter(AllStringFilter(), ExcludeStringFilter(r".*str.*"))

    assert chained_filter("") is FilterAction.INCLUDE
    assert chained_filter("any_string") is FilterAction.EXCLUDE
    assert chained_filter("not_bytes") is FilterAction.INCLUDE


def test_chained_string_filter__all_multiple_exclude():
    chained_filter = ChainedStringFilter(AllStringFilter(), ExcludeStringFilter(r".*str.*"),
                                         ExcludeStringFilter(r"$^"))

    assert chained_filter("") is FilterAction.EXCLUDE
    assert chained_filter("any_string") is FilterAction.EXCLUDE
    assert chained_filter("not_bytes") is FilterAction.INCLUDE


def test_chained_string_filter__all_none():
    chained_filter = ChainedStringFilter(AllStringFilter(), NoneStringFilter())

    assert chained_filter("") is FilterAction.EXCLUDE
    assert chained_filter("any_string") is FilterAction.EXCLUDE
    assert chained_filter("not_bytes") is FilterAction.EXCLUDE


def test_chained_string_filter__none_all():
    chained_filter = ChainedStringFilter(NoneStringFilter(), AllStringFilter())

    assert chained_filter("") is FilterAction.INCLUDE
    assert chained_filter("any_string") is FilterAction.INCLUDE
    assert chained_filter("not_bytes") is FilterAction.INCLUDE


def test_chained_string_filter__none_include_exclude():
    chained_filter = ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*y.*"),
                                         ExcludeStringFilter(r"not.*"))

    assert chained_filter("") is FilterAction.EXCLUDE
    assert chained_filter("any_string") is FilterAction.INCLUDE
    assert chained_filter("not_bytes") is FilterAction.EXCLUDE


def test_member_filter__name(cpp_class):
    member_filter = MemberFilter(
        name_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*tedVar.*")))

    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted(["ProtectedVariable"])


def test_member_filter__kind(cpp_class):
    member_filter = MemberFilter(
        kind_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"(enum|class)")))

    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted(["PublicEnum", "ProtectedEnum", "PrivateEnum",
                                           "PublicClass", "ProtectedClass", "PrivateClass"])


def test_member_filter__prot(cpp_class):
    member_filter = MemberFilter(
        prot_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"protected")))

    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted(["ProtectedVariable", "ProtectedEnum", "ProtectedClass",
                                           "ProtectedTypedef", "ProtectedStruct", "ProtectedTrash",
                                           "MyClass", "operator++", "ProtectedMethod",
                                           "ProtectedStaticMethod"])


def test_member_filter__all(cpp_class):
    member_filter = MemberFilter(
        name_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*Static.*")),
        kind_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"function")),
        prot_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"public"))
    )

    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted(["PublicStaticMethod"])


@pytest.fixture
def cpp_class_with_inner_classes(cpp_class):
    cpp_class.inner_classes[0].referred_object.kind = "class"

    nested_class = Compound("cpp")
    nested_class.name = "NestedStruct"
    nested_class.kind = "struct"
    inner_class_reference = InnerTypeReference(language="cpp")
    inner_class_reference.name = nested_class.name
    inner_class_reference.referred_object = nested_class
    cpp_class.inner_classes.append(inner_class_reference)

    nested_class = Compound("cpp")
    nested_class.name = "AnotherStruct"
    nested_class.kind = "struct"
    inner_class_reference = InnerTypeReference(language="cpp")
    inner_class_reference.name = nested_class.name
    inner_class_reference.referred_object = nested_class
    cpp_class.inner_classes.append(inner_class_reference)

    return cpp_class


def test_inner_class_filter__name(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter(
        name_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*Nested.*")))

    inner_class_names = [m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)]
    assert sorted(inner_class_names) == sorted(["NestedClass", "NestedStruct"])


def test_inner_class_filter__kind(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter(
        kind_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"struct")))

    inner_class_names = [m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)]
    assert sorted(inner_class_names) == sorted(["NestedStruct", "AnotherStruct"])


def test_inner_class_filter__all(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter(
        name_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"Nested.*")),
        kind_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r"struct"))
    )

    inner_class_names = [m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)]
    assert sorted(inner_class_names) == sorted(["NestedStruct"])


def test_enum_value_filter__name():
    enum_value_1 = EnumValue("cpp")
    enum_value_1.name = "kSomeEnumValue"
    enum_value_2 = EnumValue("cpp")
    enum_value_2.name = "kAnotherEnumValue"

    member_filter = EnumValueFilter(
        name_filter=ChainedStringFilter(NoneStringFilter(), IncludeStringFilter(r".*ome.*")))

    assert member_filter(enum_value_1) is True
    assert member_filter(enum_value_2) is False


def test_exception_filter__name():
    throws_clause_1 = ThrowsClause("cpp")
    throws_clause_1.type.name = "std::runtime_exception"
    throws_clause_2 = ThrowsClause("cpp")
    throws_clause_2.type.name = "NumericError"

    member_filter = ExceptionFilter(
        name_filter=ChainedStringFilter(AllStringFilter(), ExcludeStringFilter(r"std::.*")))

    assert member_filter(throws_clause_1) is False
    assert member_filter(throws_clause_2) is True
