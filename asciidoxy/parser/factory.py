# Copyright (C) 2019, TomTom (http://tomtom.com).
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
"""Factory methods for API reference information parsers."""

from ..api_reference import ApiReference
from ..config import Configuration
from .base import ReferenceParserBase
from .doxygen import Parser as DoxygenParser


class UnsupportedReferenceTypeError(Exception):
    """The requested type of reference is not supported (yet) and cannot be parsed.

    Attributes:
        reference_type: The requested type of reference.
    """
    reference_type: str

    def __init__(self, reference_type: str):
        self.reference_type = reference_type

    def __str__(self) -> str:
        return f"Reference of type {self.reference_type} is not supported."


def parser_factory(reference_type: str, api_reference: ApiReference,
                   config: Configuration) -> ReferenceParserBase:
    """Create a parser for the given type of API reference documentation."""
    if reference_type == "doxygen":
        return DoxygenParser(api_reference)
    else:
        raise UnsupportedReferenceTypeError(reference_type)
