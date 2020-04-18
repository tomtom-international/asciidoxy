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
"""Helper functions for C++ templates."""

from asciidoxy.generator.filters import InsertionFilter


def public_static_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("operator")
                and m.prot == "public" and m.static))


def public_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("operator")
                and m.prot == "public" and not m.static))


def public_constructors(element, insert_filter: InsertionFilter):
    constructor_name = element.name
    return (m for m in insert_filter.members(element)
            if m.kind == "function" and m.name == constructor_name and m.prot == "public")


def public_simple_enclosed_types(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.prot in ("public", "protected", None) and m.kind in ["enum", "typedef"])


def public_complex_enclosed_types(element, insert_filter: InsertionFilter):
    return (m.referred_object for m in insert_filter.inner_classes(element)
            if m.referred_object is not None)


def public_variables(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "variable" and m.prot == "public")
