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
from asciidoxy.templates.helpers import link_from_ref, print_ref


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


def method_signature(element, context: Context, max_width: int = 80):
    method_without_params = f"def {element.name}"
    return_suffix = f" -> {link_from_ref(element.returns.type, context)}" if element.returns else ""

    if not element.params:
        return (f"{method_without_params}(){return_suffix}")

    method_without_params_length = len(method_without_params)
    return_type_no_ref = (f" -> {print_ref(element.returns.type)}" if element.returns else "")
    suffix_length = len(return_type_no_ref)

    param_sizes = [len(f"{p.name}: {print_ref(p.type)}".strip()) for p in element.params]
    indent_size = method_without_params_length + 1
    first_indent = ""

    if any(indent_size + size + 1 + suffix_length > max_width for size in param_sizes):
        indent_size = 4
        first_indent = "\n    "

    param_separator = f",\n{' ' * indent_size}"
    formatted_params = f"{param_separator.join(type_and_name(p, context) for p in element.params)}"

    return (f"{method_without_params}({first_indent}{formatted_params}){return_suffix}")
