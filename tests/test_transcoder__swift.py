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
"""Test Objective C to Swift transcoding."""

import pytest

from asciidoxy.api_reference import ApiReference
from asciidoxy.transcoder.swift import SwiftTranscoder

from .test_transcoder__base import make_member, make_parameter


@pytest.fixture
def transcoder():
    return SwiftTranscoder(ApiReference())


def test_transcode_member__no_arguments(transcoder):
    member = make_member("objc", name="update")
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.full_name == "com.asciidoxy.geometry.update"
    assert not transcoded.params


def test_transcode_member__single_argument(transcoder):
    member = make_member("objc", name="updateWithName:", params=[make_parameter("name")])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "updateWithName"
    assert transcoded.full_name == "com.asciidoxy.geometry.updateWithName"
    assert len(transcoded.params) == 1


def test_transcode_member__multiple_arguments(transcoder):
    member = make_member(
        "objc",
        name="updateWithName:andType:andAge:",
        params=[make_parameter("name"),
                make_parameter("type"),
                make_parameter("age")])
    transcoded = transcoder.member(member)

    assert transcoded.language == "swift"
    assert transcoded.name == "updateWithName"
    assert transcoded.full_name == "com.asciidoxy.geometry.updateWithName"
    assert len(transcoded.params) == 3
