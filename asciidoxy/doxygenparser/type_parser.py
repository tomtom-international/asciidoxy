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
"""Parsing of types from strings and XML."""

import xml.etree.ElementTree as ET

from typing import Optional, Type, Union

from .driver_base import DriverBase
from .language_traits import LanguageTraits
from ..model import Compound, Member, TypeRef


def parse_type(traits: Type[LanguageTraits],
               driver: DriverBase,
               type_element: ET.Element,
               parent: Optional[Union[Compound, Member]] = None) -> Optional[TypeRef]:
    def match_and_extract(regex, text):
        if regex is not None and text:
            match = regex.match(text)
            if match:
                return match.group(0), text[match.end():]

        return None, text

    def extract_type(element_iter, text):
        type_ref = TypeRef(traits.TAG)
        if isinstance(parent, Compound):
            type_ref.namespace = parent.full_name
        elif isinstance(parent, Member):
            type_ref.namespace = parent.namespace

        type_ref.prefix, text = match_and_extract(traits.TYPE_PREFIXES, text)

        if not text:
            try:
                element = next(element_iter)
                type_ref.id = traits.unique_id(element.get("refid"))
                type_ref.kind = element.get("kindref", None)
                type_ref.name = traits.cleanup_name(element.text or "")
                text = element.tail

            except StopIteration:
                pass
        else:
            type_ref.name, text = match_and_extract(traits.TYPE_NAME, text)
            if type_ref.name is not None:
                type_ref.name = traits.cleanup_name(type_ref.name)

        start_nested, text = match_and_extract(traits.TYPE_NESTED_START, text)
        if start_nested:
            while True:
                nested_type_ref, text = extract_type(element_iter, text)
                if nested_type_ref and nested_type_ref.name:
                    type_ref.nested.append(nested_type_ref)
                else:
                    # TODO Error?
                    break

                end_nested, text = match_and_extract(traits.TYPE_NESTED_END, text)
                if end_nested:
                    break

                _, text = match_and_extract(traits.TYPE_NESTED_SEPARATOR, text)

        type_ref.suffix, text = match_and_extract(traits.TYPE_SUFFIXES, text)

        # doxygen inserts empty <type> tag for return value in constructors,
        # this fake types should be filtered out
        if type_ref.name:
            if not type_ref.id and not traits.is_language_standard_type(type_ref.name):
                driver.unresolved_ref(type_ref)

        return type_ref, text

    type_ref, _ = extract_type(type_element.iter("ref"), type_element.text)
    return type_ref
