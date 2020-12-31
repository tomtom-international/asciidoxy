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
"""Tests for Java template helpers."""

import pytest

from asciidoxy.templates.java.helpers import JavaTemplateHelper
from asciidoxy.generator.filters import InsertionFilter

from .builders import SimpleClassBuilder


@pytest.fixture
def java_class():
    builder = SimpleClassBuilder("java")
    builder.name("MyClass")

    # fill class with typical members
    for visibility in ("public", "protected", "private"):
        for member_type in ("enum", "class", "trash"):
            builder.simple_member(kind=member_type, prot=visibility)

        # adds constructors
        builder.member_function(prot=visibility, name="MyClass", has_return_value=False)
        # add some method
        builder.member_function(prot=visibility, name=visibility.capitalize() + "Method")
        # add static method
        builder.member_function(prot=visibility,
                                name=visibility.capitalize() + "StaticMethod",
                                static=True)
        # add simple variable
        builder.member_variable(prot=visibility)
        # add final variable
        builder.member_variable(prot=visibility,
                                name=f"{visibility.capitalize()}Constant",
                                type_prefix="final ")
        # add nested type
        builder.inner_class(prot=visibility, name=f"{visibility.capitalize()}Type")

    return builder.compound


@pytest.fixture
def helper(java_class, empty_generating_api):
    return JavaTemplateHelper(empty_generating_api, java_class, InsertionFilter())


def test_public_constants__no_filter(helper):
    result = [m.name for m in helper.constants(prot="public")]
    assert result == ["PublicConstant"]


def test_public_constants__filter_match(helper):
    helper.insert_filter = InsertionFilter(members="Public")
    result = [m.name for m in helper.constants(prot="public")]
    assert result == ["PublicConstant"]


def test_public_constants__filter_no_match(helper):
    helper.insert_filter = InsertionFilter(members="NONE")
    result = [m.name for m in helper.constants(prot="public")]
    assert len(result) == 0


def test_private_constants__no_filter(helper):
    result = [m.name for m in helper.constants(prot="private")]
    assert result == ["PrivateConstant"]
