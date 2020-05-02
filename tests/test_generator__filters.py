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
                                         ExceptionFilter, filter_from_strings, InsertionFilter,
                                         combine_specs)
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
    member_filter = MemberFilter.from_spec(["NONE", ".*tedVar.*"])
    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted(["ProtectedVariable"])


def test_member_filter__kind(cpp_class):
    member_filter = MemberFilter.from_spec({"kind": ["NONE", "(enum|class)"]})
    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted([
        "PublicEnum", "ProtectedEnum", "PrivateEnum", "PublicClass", "ProtectedClass",
        "PrivateClass"
    ])


def test_member_filter__prot(cpp_class):
    member_filter = MemberFilter.from_spec({"prot": ["NONE", "protected"]})
    member_names = [m.name for m in cpp_class.members if member_filter(m)]
    assert sorted(member_names) == sorted([
        "ProtectedVariable", "ProtectedEnum", "ProtectedClass", "ProtectedTypedef",
        "ProtectedStruct", "ProtectedTrash", "MyClass", "operator++", "ProtectedMethod",
        "ProtectedStaticMethod"
    ])


def test_member_filter__all(cpp_class):
    member_filter = MemberFilter.from_spec({
        "name": ["NONE", ".*Static.*"],
        "kind": ["NONE", "function"],
        "prot": ["NONE", "public"]
    })
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

    enum_value = EnumValue("cpp")
    enum_value.name = "kGreen"
    cpp_class.enumvalues.append(enum_value)

    enum_value = EnumValue("cpp")
    enum_value.name = "kBlue"
    cpp_class.enumvalues.append(enum_value)

    enum_value = EnumValue("cpp")
    enum_value.name = "kRed"
    cpp_class.enumvalues.append(enum_value)

    return cpp_class


def test_inner_class_filter__name(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter.from_spec(["NONE", ".*Nested.*"])
    inner_class_names = [
        m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)
    ]
    assert sorted(inner_class_names) == sorted(["NestedClass", "NestedStruct"])


def test_inner_class_filter__kind(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter.from_spec({"kind": ["NONE", "struct"]})
    inner_class_names = [
        m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)
    ]
    assert sorted(inner_class_names) == sorted(["NestedStruct", "AnotherStruct"])


def test_inner_class_filter__all(cpp_class_with_inner_classes):
    inner_class_filter = InnerClassFilter.from_spec({
        "name": ["NONE", "Nested.*"],
        "kind": ["NONE", "struct"]
    })
    inner_class_names = [
        m.name for m in cpp_class_with_inner_classes.inner_classes if inner_class_filter(m)
    ]
    assert sorted(inner_class_names) == sorted(["NestedStruct"])


def test_enum_value_filter__name():
    enum_value_1 = EnumValue("cpp")
    enum_value_1.name = "kSomeEnumValue"
    enum_value_2 = EnumValue("cpp")
    enum_value_2.name = "kAnotherEnumValue"

    member_filter = EnumValueFilter.from_spec(["NONE", ".*ome.*"])
    assert member_filter(enum_value_1) is True
    assert member_filter(enum_value_2) is False


def test_exception_filter__name():
    throws_clause_1 = ThrowsClause("cpp")
    throws_clause_1.type.name = "std::runtime_exception"
    throws_clause_2 = ThrowsClause("cpp")
    throws_clause_2.type.name = "NumericError"

    member_filter = ExceptionFilter.from_spec(["ALL", "-std::.*"])
    assert member_filter(throws_clause_1) is False
    assert member_filter(throws_clause_2) is True


@pytest.fixture
def strings_to_filter():
    return [
        "", "Apple", "Banana", "AppleTree", "BananaTree", "Strawberry", "StrawberryDaiquiri",
        "AppleJuice", "BananaJuice"
    ]


def test_filter_from_strings__no_filter(strings_to_filter):
    string_filter = filter_from_strings([])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(strings_to_filter)


def test_filter_from_strings__accept_all(strings_to_filter):
    string_filter = filter_from_strings(["ALL"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(strings_to_filter)


def test_filter_from_strings__accept_none(strings_to_filter):
    string_filter = filter_from_strings(["NONE"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == []


def test_filter_from_strings__explicit_none_explicit_include(strings_to_filter):
    string_filter = filter_from_strings(["NONE", "+.*Tree"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree", "BananaTree"])


def test_filter_from_strings__explicit_none_implicit_include(strings_to_filter):
    string_filter = filter_from_strings(["NONE", ".*Daiquiri"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["StrawberryDaiquiri"])


def test_filter_from_strings__explicit_all_exclude(strings_to_filter):
    string_filter = filter_from_strings(["ALL", "-.*Banana"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(
        ["", "Apple", "AppleJuice", "AppleTree", "Strawberry", "StrawberryDaiquiri"])


def test_filter_from_strings__implicit_none(strings_to_filter):
    string_filter = filter_from_strings(["+.*Tree"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree", "BananaTree"])


def test_filter_from_strings__implicit_all(strings_to_filter):
    string_filter = filter_from_strings(["-Banana"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(
        ["", "Apple", "AppleTree", "AppleJuice", "Strawberry", "StrawberryDaiquiri"])


def test_filter_from_strings__explicit_all_exclude_include(strings_to_filter):
    string_filter = filter_from_strings(["ALL", "-.*Banana", "+.*Juice"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(
        ["", "Apple", "AppleJuice", "AppleTree", "Strawberry", "StrawberryDaiquiri", "BananaJuice"])


def test_filter_from_strings__implicit_all_exclude_include(strings_to_filter):
    string_filter = filter_from_strings(["-.*Banana", "+.*Juice"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(
        ["", "Apple", "AppleJuice", "AppleTree", "Strawberry", "StrawberryDaiquiri", "BananaJuice"])


def test_filter_from_strings__explicit_none_include_exclude(strings_to_filter):
    string_filter = filter_from_strings(["NONE", "+.*Tree", "-Banana"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree"])


def test_filter_from_strings__implicit_none_include_exclude(strings_to_filter):
    string_filter = filter_from_strings(["+.*Tree", "-Banana"])
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree"])


def test_filter_from_strings__single_explicit_include(strings_to_filter):
    string_filter = filter_from_strings("+.*Tree")
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree", "BananaTree"])


def test_filter_from_strings__single_implicit_include(strings_to_filter):
    string_filter = filter_from_strings(".*Tree")
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(["AppleTree", "BananaTree"])


def test_filter_from_strings__single_exclude(strings_to_filter):
    string_filter = filter_from_strings("-Banana")
    filtered = [s for s in strings_to_filter if string_filter(s) == FilterAction.INCLUDE]
    assert sorted(filtered) == sorted(
        ["", "Apple", "AppleTree", "AppleJuice", "Strawberry", "StrawberryDaiquiri"])


def test_insertion_filter__compound__no_filters(cpp_class_with_inner_classes):
    insertion_filter = InsertionFilter()

    member_names = [
        member.name for member in insertion_filter.members(cpp_class_with_inner_classes)
    ]
    assert sorted(member_names) == sorted([
        "PublicVariable", "PublicEnum", "PublicClass", "PublicTypedef", "PublicStruct",
        "PublicTrash", "MyClass", "operator++", "PublicMethod", "PublicStaticMethod",
        "ProtectedVariable", "ProtectedEnum", "ProtectedClass", "ProtectedTypedef",
        "ProtectedStruct", "ProtectedTrash", "MyClass", "operator++", "ProtectedMethod",
        "ProtectedStaticMethod", "PrivateVariable", "PrivateEnum", "PrivateClass", "PrivateTypedef",
        "PrivateStruct", "PrivateTrash", "MyClass", "operator++", "PrivateMethod",
        "PrivateStaticMethod"
    ])

    inner_class_names = [
        inner_class.name
        for inner_class in insertion_filter.inner_classes(cpp_class_with_inner_classes)
    ]
    assert sorted(inner_class_names) == sorted(["NestedClass", "NestedStruct", "AnotherStruct"])

    enum_names = [
        enum_value.name for enum_value in insertion_filter.enum_values(cpp_class_with_inner_classes)
    ]
    assert sorted(enum_names) == sorted(["kRed", "kGreen", "kBlue"])


def test_insertion_filter__compound__filter_members(cpp_class_with_inner_classes):
    insertion_filter = InsertionFilter(members={"kind": "variable"})

    member_names = [
        member.name for member in insertion_filter.members(cpp_class_with_inner_classes)
    ]
    assert sorted(member_names) == sorted([
        "PublicVariable",
        "ProtectedVariable",
        "PrivateVariable",
    ])

    inner_class_names = [
        inner_class.name
        for inner_class in insertion_filter.inner_classes(cpp_class_with_inner_classes)
    ]
    assert sorted(inner_class_names) == sorted(["NestedClass", "NestedStruct", "AnotherStruct"])

    enum_names = [
        enum_value.name for enum_value in insertion_filter.enum_values(cpp_class_with_inner_classes)
    ]
    assert sorted(enum_names) == sorted(["kRed", "kGreen", "kBlue"])


def test_insertion_filter__compound__filter_inner_classes(cpp_class_with_inner_classes):
    insertion_filter = InsertionFilter(inner_classes=".*Struct")

    member_names = [
        member.name for member in insertion_filter.members(cpp_class_with_inner_classes)
    ]
    assert sorted(member_names) == sorted([
        "PublicVariable", "PublicEnum", "PublicClass", "PublicTypedef", "PublicStruct",
        "PublicTrash", "MyClass", "operator++", "PublicMethod", "PublicStaticMethod",
        "ProtectedVariable", "ProtectedEnum", "ProtectedClass", "ProtectedTypedef",
        "ProtectedStruct", "ProtectedTrash", "MyClass", "operator++", "ProtectedMethod",
        "ProtectedStaticMethod", "PrivateVariable", "PrivateEnum", "PrivateClass", "PrivateTypedef",
        "PrivateStruct", "PrivateTrash", "MyClass", "operator++", "PrivateMethod",
        "PrivateStaticMethod"
    ])

    inner_class_names = [
        inner_class.name
        for inner_class in insertion_filter.inner_classes(cpp_class_with_inner_classes)
    ]
    assert sorted(inner_class_names) == sorted(["NestedStruct", "AnotherStruct"])

    enum_names = [
        enum_value.name for enum_value in insertion_filter.enum_values(cpp_class_with_inner_classes)
    ]
    assert sorted(enum_names) == sorted(["kRed", "kGreen", "kBlue"])


def test_insertion_filter__compound__filter_enum_values(cpp_class_with_inner_classes):
    insertion_filter = InsertionFilter(enum_values=".*(Red|Blue)")

    member_names = [
        member.name for member in insertion_filter.members(cpp_class_with_inner_classes)
    ]
    assert sorted(member_names) == sorted([
        "PublicVariable", "PublicEnum", "PublicClass", "PublicTypedef", "PublicStruct",
        "PublicTrash", "MyClass", "operator++", "PublicMethod", "PublicStaticMethod",
        "ProtectedVariable", "ProtectedEnum", "ProtectedClass", "ProtectedTypedef",
        "ProtectedStruct", "ProtectedTrash", "MyClass", "operator++", "ProtectedMethod",
        "ProtectedStaticMethod", "PrivateVariable", "PrivateEnum", "PrivateClass", "PrivateTypedef",
        "PrivateStruct", "PrivateTrash", "MyClass", "operator++", "PrivateMethod",
        "PrivateStaticMethod"
    ])

    inner_class_names = [
        inner_class.name
        for inner_class in insertion_filter.inner_classes(cpp_class_with_inner_classes)
    ]
    assert sorted(inner_class_names) == sorted(["NestedClass", "NestedStruct", "AnotherStruct"])

    enum_names = [
        enum_value.name for enum_value in insertion_filter.enum_values(cpp_class_with_inner_classes)
    ]
    assert sorted(enum_names) == sorted(["kRed", "kBlue"])


def test_insertion_filter__member__enum__no_filters(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::Severity")
    assert member is not None

    insertion_filter = InsertionFilter()

    enum_names = [enum_value.name for enum_value in insertion_filter.enum_values(member)]
    assert sorted(enum_names) == sorted(["Low", "Medium", "High", "Unknown"])


def test_insertion_filter__member__enum__filter_name(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::Severity")
    assert member is not None

    insertion_filter = InsertionFilter(enum_values="High")

    enum_names = [enum_value.name for enum_value in insertion_filter.enum_values(member)]
    assert sorted(enum_names) == sorted(["High"])


def test_insertion_filer__member__exceptions__no_filters(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::CalculateDelay")
    assert member is not None

    insertion_filter = InsertionFilter()

    exception_names = [exception.type.name for exception in insertion_filter.exceptions(member)]
    assert sorted(exception_names) == sorted(["std::runtime_exception"])


def test_insertion_filer__member__exceptions__filter_name(api_reference):
    member = api_reference.find("asciidoxy::traffic::TrafficEvent::CalculateDelay")
    assert member is not None

    insertion_filter = InsertionFilter(exceptions="NONE")

    exception_names = [exception.type.name for exception in insertion_filter.exceptions(member)]
    assert sorted(exception_names) == sorted([])


@pytest.mark.parametrize("first, second, expected", [
    (None, None, None),
    ("Update", None, "Update"),
    (None, "ALL", "ALL"),
    (["NONE", "ALL"], None, ["NONE", "ALL"]),
    (None, ["NONE", "ALL"], ["NONE", "ALL"]),
    ({
        "name": "ALL"
    }, None, {
        "name": "ALL"
    }),
    (None, {
        "name": "ALL"
    }, {
        "name": "ALL"
    }),
    ("NONE", "ALL", ["NONE", "ALL"]),
    ("Alpha", ["Beta", "Gamma"], ["Alpha", "Beta", "Gamma"]),
    (["Alpha", "Beta"], "Gamma", ["Alpha", "Beta", "Gamma"]),
    (["Alpha", "Beta"], ["Gamma", "Delta"], ["Alpha", "Beta", "Gamma", "Delta"]),
    ({
        "name": "Alpha"
    }, {
        "name": "Beta"
    }, {
        "name": ["Alpha", "Beta"]
    }),
    ({
        "name": "Alpha"
    }, {
        "kind": "Beta"
    }, {
        "name": "Alpha",
        "kind": "Beta"
    }),
    ({
        "name": "Alpha"
    }, {
        "name": "Gamma",
        "kind": "Beta"
    }, {
        "name": ["Alpha", "Gamma"],
        "kind": "Beta"
    }),
    ({
        "name": "Gamma",
        "kind": "Beta"
    }, "Alpha", {
        "name": ["Gamma", "Alpha"],
        "kind": "Beta"
    }),
    ({
        "kind": "Beta"
    }, "Alpha", {
        "name": "Alpha",
        "kind": "Beta"
    }),
    ("Alpha", {
        "name": "Gamma",
        "kind": "Beta"
    }, {
        "name": ["Alpha", "Gamma"],
        "kind": "Beta"
    }),
    ("Alpha", {
        "kind": "Beta"
    }, {
        "name": "Alpha",
        "kind": "Beta"
    }),
],
                         ids=lambda x: type(x).__name__)
def test_combine_specs(first, second, expected):
    assert combine_specs(first, second) == expected
