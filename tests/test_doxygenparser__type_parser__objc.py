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
"""Tests for parsing Objective C types."""

import pytest

import xml.etree.ElementTree as ET

from unittest.mock import MagicMock

from asciidoxy.doxygenparser.objc import ObjectiveCTraits
from asciidoxy.doxygenparser.type_parser import parse_type
from .shared import assert_equal_or_none_if_empty


@pytest.fixture(params=[
    "",
    "nullable ",
    "const ",
    "__weak ",
    "__strong ",
    "nullable __weak ",
    "nullable __strong ",
])
def objc_type_prefix(request):
    return request.param


@pytest.fixture(params=["", " *", " **", " * *"])
def objc_type_suffix(request):
    return request.param


def test_parse_objc_type_from_text_simple(objc_type_prefix, objc_type_suffix):
    type_element = ET.Element("type")
    type_element.text = f"{objc_type_prefix}NSInteger{objc_type_suffix}"

    driver_mock = MagicMock()
    type_ref = parse_type(ObjectiveCTraits, driver_mock, type_element)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert type_ref.id is None
    assert type_ref.kind is None
    assert type_ref.language == "objc"
    assert type_ref.name == "NSInteger"
    assert_equal_or_none_if_empty(type_ref.prefix, objc_type_prefix)
    assert_equal_or_none_if_empty(type_ref.suffix, objc_type_suffix)
    assert len(type_ref.nested) == 0


@pytest.mark.parametrize("type_with_space", [
    "short int",
    "signed short",
    "signed short int",
    "unsigned short",
    "unsigned short int",
    "signed int",
    "unsigned int",
    "long int",
    "signed long",
    "signed long int",
    "unsigned long",
    "unsigned long int",
    "long long",
    "long long int",
    "signed long long",
    "signed long long int",
    "unsigned long long",
    "unsigned long long int",
    "signed char",
    "long double",
    "unsigned char",
    "signed char",
])
def test_parse_objc_type_with_space(type_with_space):
    type_element = ET.Element("type")
    type_element.text = type_with_space

    driver_mock = MagicMock()
    type_ref = parse_type(ObjectiveCTraits, driver_mock, type_element)
    driver_mock.unresolved_ref.assert_not_called()  # built-in type

    assert type_ref is not None
    assert not type_ref.id
    assert not type_ref.kind
    assert type_ref.language == "objc"
    assert type_ref.name == type_with_space
    assert type_ref.prefix is None
    assert type_ref.suffix is None
