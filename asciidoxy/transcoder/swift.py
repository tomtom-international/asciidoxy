# Copyright (C) 2019-2021, TomTom (http://tomtom.com).
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

from ..model import Compound, ReferableElement, ThrowsClause, TypeRef
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

    def convert_name(self, source_element: Union[ReferableElement, TypeRef]) -> str:
        name = source_element.name

        name = self.convert_bridged_type_name(name)

        if ":" in name:
            name = name.split(":", maxsplit=1)[0]

        return name

    def convert_full_name(self, source_element: ReferableElement) -> str:
        full_name = source_element.full_name

        full_name = self.convert_bridged_type_name(full_name)

        if ":" in full_name:
            full_name = full_name.split(":", maxsplit=1)[0]

        return full_name

    def _compound(self, compound: Compound) -> Compound:
        transcoded = super()._compound(compound)
        transcoded = self.remove_with_from_function(transcoded)
        transcoded = self.remove_return_type_from_constructor(transcoded)
        transcoded = self.replace_nserror_with_exception(compound, transcoded)
        transcoded = self.remove_void_return_type(transcoded)
        return transcoded

    @staticmethod
    def remove_with_from_function(transcoded: Compound) -> Compound:
        if transcoded.kind == "function" and "With" in transcoded.name and transcoded.params:
            method_name, _, first_param_name = transcoded.name.partition("With")
            transcoded.name = method_name
            if transcoded.namespace:
                transcoded.full_name = f"{transcoded.namespace}.{method_name}"
            else:
                transcoded.full_name = method_name

            if method_name == "init":
                transcoded.params[0].name = f"{first_param_name[0].lower()}{first_param_name[1:]}"
            else:
                transcoded.params[0].name = f"with{first_param_name}"
        return transcoded

    @staticmethod
    def remove_return_type_from_constructor(transcoded: Compound) -> Compound:
        if transcoded.kind == "function" and transcoded.name == "init":
            transcoded.returns = None
        return transcoded

    @staticmethod
    def remove_void_return_type(transcoded: Compound) -> Compound:
        if (transcoded.kind == "function" and transcoded.returns is not None
                and transcoded.returns.type is not None and transcoded.returns.type.name == "void"):
            transcoded.returns = None
        return transcoded

    @staticmethod
    def replace_nserror_with_exception(original: Compound, transcoded: Compound) -> Compound:
        # https://developer.apple.com/documentation/swift/cocoa_design_patterns/about_imported_cocoa_error_parameters
        if (original.kind == "function" and original.params
                and "NS_SWIFT_NOTHROW" not in original.args):
            for original_param, param in zip(reversed(original.params),
                                             reversed(transcoded.params)):
                if (original_param.type is not None and original_param.type.name == "NSError"
                        and original_param.type.suffix
                        and original_param.type.suffix.count("*") == 2):
                    assert param.type
                    throws_clause = ThrowsClause("swift")
                    throws_clause.type = param.type
                    throws_clause.description = param.description
                    transcoded.exceptions.append(throws_clause)
                    transcoded.params.remove(param)

                    if transcoded.returns is not None and transcoded.returns.type is not None:
                        if transcoded.returns.type.name == "Bool":
                            transcoded.returns = None
                        elif (transcoded.returns.type is not None and transcoded.returns.type.suffix
                              and "?" in transcoded.returns.type.suffix):
                            transcoded.returns.type.suffix = transcoded.returns.type.suffix.replace(
                                "?", "")

                    if not transcoded.params and transcoded.name.endswith("AndReturnError"):
                        transcoded.name = transcoded.name[:-14]
                        transcoded.full_name = transcoded.full_name[:-14]

                    break
                elif param.type is not None and param.type.args:
                    # If there are closures, the NSError does not need to be the last parameter
                    continue
                else:
                    break

        return transcoded

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

        if (type_ref.returns is not None and type_ref.returns.prefix
                and "nullable" in type_ref.returns.prefix):
            transcoded.suffix = f"?{transcoded.suffix or ''}"

            if transcoded.returns is not None and transcoded.returns.suffix:
                transcoded.returns.suffix = transcoded.returns.suffix.replace("?", "").strip()

        return transcoded

    @classmethod
    def convert_bridged_type_name(cls, name: str) -> str:
        if name in cls.BRIDGED_FOUNDATION_TYPES:
            return cls.BRIDGED_FOUNDATION_TYPES[name]
        elif name.startswith("NS") and name not in cls.UNBRIDGED_FOUNDATION_TYPES:
            return name[2:]
        return name
