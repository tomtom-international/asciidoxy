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
"""Test Objective C to Kotlin transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.transcoder.kotlin import KotlinTranscoder

from .test_transcoder__base import make_member, make_return_value, make_type_ref


@pytest.fixture
def transcoder():
    return KotlinTranscoder(ApiReference())


@pytest.mark.parametrize("java_type, kotlin_type, kotlin_suffix", [
    ("byte", "Byte", ""),
    ("short", "Short", ""),
    ("int", "Int", ""),
    ("long", "Long", ""),
    ("char", "Char", ""),
    ("float", "Float", ""),
    ("double", "Double", ""),
    ("boolean", "Boolean", ""),
    ("java.lang.Object", "Any", "!"),
    ("java.lang.Cloneable", "Cloneable", "!"),
    ("java.lang.Comparable", "Comparable", "!"),
    ("java.lang.Enum", "Enum", "!"),
    ("java.lang.Annotation", "Annotation", "!"),
    ("java.lang.CharSequence", "CharSequence", "!"),
    ("java.lang.String", "String", "!"),
    ("java.lang.Number", "Number", "!"),
    ("java.lang.Throwable", "Throwable", "!"),
    ("Object", "Any", "!"),
    ("Cloneable", "Cloneable", "!"),
    ("Comparable", "Comparable", "!"),
    ("Enum", "Enum", "!"),
    ("Annotation", "Annotation", "!"),
    ("CharSequence", "CharSequence", "!"),
    ("String", "String", "!"),
    ("Number", "Number", "!"),
    ("Throwable", "Throwable", "!"),
    ("java.lang.Byte", "Byte", "?"),
    ("java.lang.Short", "Short", "?"),
    ("java.lang.Integer", "Int", "?"),
    ("java.lang.Long", "Long", "?"),
    ("java.lang.Character", "Char", "?"),
    ("java.lang.Float", "Float", "?"),
    ("java.lang.Double", "Double", "?"),
    ("java.lang.Boolean", "Boolean", "?"),
    ("Byte", "Byte", "?"),
    ("Short", "Short", "?"),
    ("Integer", "Int", "?"),
    ("Long", "Long", "?"),
    ("Character", "Char", "?"),
    ("Float", "Float", "?"),
    ("Double", "Double", "?"),
    ("Boolean", "Boolean", "?"),
    ("void", "Unit", ""),
])
def test_transcode_type_ref__mapped_types(transcoder, java_type, kotlin_type, kotlin_suffix):
    type_ref = make_type_ref(lang="java", name=java_type, prefix="", suffix="")
    transcoded = transcoder.type_ref(type_ref)
    assert transcoded.name == kotlin_type
    assert not transcoded.prefix
    assert transcoded.suffix == kotlin_suffix


def test_transcode_member__void_return(transcoder):
    member = make_member(lang="java",
                         name="update",
                         returns=make_return_value(
                             make_type_ref(lang="java", name="void", prefix="", suffix="")))
    transcoded = transcoder.member(member)
    assert not transcoded.returns
