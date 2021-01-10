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
"""Base classes for parser drivers."""

from abc import ABC, abstractmethod

from ..api_reference import ApiReference
from ..model import Compound, ReferableElement, TypeRef


class DriverBase(ABC):
    """Base class for drivers."""
    api_reference: ApiReference

    def __init__(self, api_reference: ApiReference):
        self.api_reference = api_reference

    @abstractmethod
    def register(self, element: ReferableElement) -> None:
        """Register a new element."""

    @abstractmethod
    def unresolved_ref(self, ref: TypeRef) -> None:
        """Register an unresolved reference."""

    @abstractmethod
    def inner_type_ref(self, parent: Compound, ref: TypeRef) -> None:
        """Register an inner type reference."""
        pass

    @abstractmethod
    def parse(self, file_or_path) -> bool:
        """Parse all objects in a file and make them available for API reference generation.

        Params:
            file_or_path: File object or path for the file to parse.

        Returns:
            True if file is parsed. False if the file is invalid.
        """
