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

from typing import Union

from ..model import ReferableElement, TypeRef
from .base import TranscoderBase


class SwiftTranscoder(TranscoderBase):
    SOURCE = "objc"
    TARGET = "swift"

    def convert_name(self, source_element: Union[ReferableElement, TypeRef]) -> str:
        name = source_element.name
        if ":" in name:
            name = name.split(":", maxsplit=1)[0]
        if name.startswith("initWith"):
            name = "init"
        return name

    def convert_full_name(self, source_element: ReferableElement) -> str:
        full_name = source_element.full_name
        if ":" in full_name:
            full_name = full_name.split(":", maxsplit=1)[0]
        if source_element.name.startswith("initWith"):
            if "." in full_name:
                prefix, _ = full_name.rsplit(".", maxsplit=1)
                full_name = f"{prefix}.init"
            else:
                full_name = "init"
        return full_name
