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
"""Transcoding Java reference into Kotlin."""

from ..model import Member
from .base import TranscoderBase


class SwiftTranscoder(TranscoderBase):
    SOURCE = "objc"
    TARGET = "swift"

    def _member(self, member: Member) -> Member:
        transcoded = super()._member(member)

        if ":" in transcoded.name:
            transcoded.name, _ = transcoded.name.split(":", maxsplit=1)
            transcoded.full_name, _ = transcoded.full_name.split(":", maxsplit=1)

        return transcoded
