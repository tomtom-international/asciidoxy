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

from typing import Optional, Union

from ..model import ReferableElement, TypeRef, TypeRefBase
from .base import TranscoderBase


class SwiftTranscoder(TranscoderBase):
    SOURCE = "objc"
    TARGET = "swift"

    # Bridged types
    # https://developer.apple.com/documentation/swift/imported_c_and_objective-c_apis/working_with_foundation_types
    UNBRIDGED_FOUNDATION_TYPES = [
        "NSObject",
        "NSAutoReleasePool",
        "NSException",
        "NSProxy",
        "NSBackgroundActivity",
        "NSUserNotification",
        "NSXPCConnection",
        "NSNumber",
    ]
    BRIDGED_FOUNDATION_TYPES = {
        "NSDecimalNumber": "Decimal",
        "BOOL": "Bool",
    }

    def convert_kind(self, source_element: Union[ReferableElement, TypeRef]) -> Optional[str]:
        if source_element.kind is None:
            return None
        return {"block": "closure"}.get(source_element.kind, source_element.kind)

    def convert_name(self, source_element: Union[ReferableElement, TypeRefBase]) -> str:
        name = source_element.name

        name = self.convert_bridged_type(name)

        if name.startswith("initWith"):
            name = "init"
        elif ":" in name:
            name = name.split(":", maxsplit=1)[0]

        return name

    def convert_full_name(self, source_element: ReferableElement) -> str:
        full_name = source_element.full_name

        full_name = self.convert_bridged_type(full_name)

        if source_element.name.startswith("initWith"):
            if "." in full_name:
                prefix, _ = full_name.rsplit(".", maxsplit=1)
                full_name = f"{prefix}.init"
            else:
                full_name = "init"
        elif ":" in full_name:
            full_name = full_name.split(":", maxsplit=1)[0]

        return full_name

    def type_ref(self, type_ref: TypeRef) -> TypeRef:
        transcoded = super().type_ref(type_ref)

        if transcoded.prefix and "nullable" in transcoded.prefix:
            transcoded.suffix = f"?{transcoded.suffix or ''}"
            transcoded.prefix = transcoded.prefix.replace("nullable ", "")

        if transcoded.suffix and "*" in transcoded.suffix:
            transcoded.suffix = transcoded.suffix.replace("*", "").rstrip()

        if transcoded.suffix and "_Nullable" in transcoded.suffix:
            suffix = transcoded.suffix.replace(" _Nullable", "")
            transcoded.suffix = f"?{suffix}"

        if transcoded.suffix and "__autoreleasing" in transcoded.suffix:
            transcoded.suffix = transcoded.suffix.replace("__autoreleasing", "").rstrip()

        if transcoded.name == "id":
            if not transcoded.nested:
                transcoded.name = "Any"
            else:
                assert len(transcoded.nested) == 1
                transcoded = transcoded.nested[0]

        return transcoded

    @classmethod
    def convert_bridged_type(cls, name: str) -> str:
        if name in cls.BRIDGED_FOUNDATION_TYPES:
            return cls.BRIDGED_FOUNDATION_TYPES[name]
        elif name.startswith("NS") and name not in cls.UNBRIDGED_FOUNDATION_TYPES:
            return name[2:]
        return name
