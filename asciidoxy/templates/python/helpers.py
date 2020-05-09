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
"""Helper functions for python reference templates."""

from asciidoxy.generator import Context
from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.templates.helpers import link_from_ref


def argument_list(params, context: Context):
    return f"({', '.join(type_and_name(p, context) for p in params)})"


def type_and_name(param, context: Context):
    if param.type is None or not param.type.name:
        return param.name
    if param.type.name in ("self", "cls"):
        return param.type.name
    return f"{param.name}: {link_from_ref(param.type, context, '[', ']')}".strip()


def params(element):
    return (param for param in element.params
            if (not param.type or param.type.name not in ("self", "cls")))


def public_static_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("_") and m.static))


def public_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.returns and not m.name.startswith("_") and not m.static))


def public_constructors(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "function" and m.name == "__init__")


def public_enclosed_types(element, insert_filter: InsertionFilter):
    return (m.referred_object for m in insert_filter.inner_classes(element)
            if m.referred_object is not None and not m.name.startswith("_"))


def public_variables(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "variable" and not m.name.startswith("_"))
