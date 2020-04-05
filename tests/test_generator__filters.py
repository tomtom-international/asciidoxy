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

from asciidoxy.generator.filters import (AllStringFilter, NoneStringFilter, IncludeStringFilter,
                                         ExcludeStringFilter, ChainedStringFilter, MemberFilter,
                                         FilterAction)


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
