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
"""Helper functions for API reference templates."""

from asciidoxy.generator import Context


def link_from_ref(ref, context: Context, nested_start="&lt;", nested_end="&gt;"):
    if ref is None:
        return ""

    if ref.nested:
        nested = (f"{nested_start}"
                  f"{', '.join(link_from_ref(r, context) for r in ref.nested)}"
                  f"{nested_end}")
    else:
        nested = ""

    if ref.id:
        return (f"{ref.prefix or ''}{context.link_to_element(ref.id, ref.name)}{nested}"
                f"{ref.suffix or ''}").strip()
    else:
        return f"{ref.prefix or ''}{ref.name}{nested}{ref.suffix or ''}".strip()


def print_ref(ref):
    if ref is None:
        return ""

    if ref.nested:
        nested = f"&lt;{', '.join(print_ref(r) for r in ref.nested)}&gt;"
    else:
        nested = ""

    return f"{ref.prefix or ''}{ref.name}{nested}{ref.suffix or ''}".strip()


def argument_list(params, context: Context):
    return f"({', '.join(type_and_name(p, context) for p in params)})"


def type_list(params):
    return f"({', '.join(print_ref(p.type) for p in params)})"


def has(elements):
    return len(list(elements)) > 0


def chain(first_collection, second_collection):
    yield from first_collection
    yield from second_collection


def type_and_name(param, context: Context):
    return f"{link_from_ref(param.type, context)} {param.name}".strip()
