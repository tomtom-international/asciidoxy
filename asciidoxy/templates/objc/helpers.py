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
"""Helper functions for Objective C templates."""

from asciidoxy.generator import Context, InsertionFilter
from asciidoxy.templates.helpers import link_from_ref, print_ref


def objc_method_signature(method, context: Context):
    method_name_parts = method.name.split(":")

    static = "+" if method.static else "-"

    if len(method_name_parts) == 1:
        return f"{static} ({link_from_ref(method.returns.type, context)}){method.name}"

    method_parts = []
    for method_name_part, param in zip(method_name_parts, method.params):
        method_parts.append(
            f"{method_name_part}:({link_from_ref(param.type, context)}){param.name}")

    prefix = f"{static} ({link_from_ref(method.returns.type, context)})"

    if len(method_parts) > 1:
        first_line_text = f"- ({print_ref(method.returns.type)}){method_parts[0]}"
        first_line_colon_position = first_line_text.find(":")
        assert first_line_colon_position > 0

        formatted = [f"{prefix}{method_parts[0]}"]
        for line in method_parts[1:]:
            colon_position = line.find(":")
            if colon_position < first_line_colon_position:
                line = " " * (first_line_colon_position - colon_position) + line
            formatted.append(line)
        method_parts = formatted

        return "\n".join(method_parts)
    else:
        return f"{prefix}{method_parts[0]}"


def public_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.prot == "public" and not m.static))


def public_class_methods(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if (m.kind == "function" and m.prot == "public" and m.static))


def public_properties(element, insert_filter: InsertionFilter):
    return (m for m in insert_filter.members(element)
            if m.kind == "property" and m.prot == "public")


def public_simple_enclosed_types(element, insert_filter: InsertionFilter):
    # For some reason enclosed types are always set to private, so ignore visibility
    return (m for m in insert_filter.members(element) if m.kind in ["enum", "class", "protocol"])
