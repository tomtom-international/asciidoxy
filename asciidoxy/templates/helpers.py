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


def _arg_name(param):
    if param.name:
        return f" {param.name}"
    else:
        return ""


def link_from_ref(ref,
                  context: Context,
                  nested_start="&lt;",
                  nested_end="&gt;",
                  args_start="(",
                  args_end=")",
                  skip_args=False):
    if ref is None:
        return ""

    if ref.nested is not None:
        if len(ref.nested) > 0:
            nested = (f"{nested_start}"
                      f"{', '.join(link_from_ref(r, context) for r in ref.nested)}"
                      f"{nested_end}")
        else:
            nested = f"{nested_start}{nested_end}"
    else:
        nested = ""

    if not skip_args and ref.args is not None:
        if len(ref.args) > 0:
            arg_parts = [f"{link_from_ref(a.type, context)}{_arg_name(a)}" for a in ref.args]
            args = f"{args_start}{', '.join(arg_parts)}{args_end}"
        else:
            args = f"{args_start}{args_end}"
    else:
        args = ""

    if ref.id:
        return (f"{ref.prefix or ''}{context.link_to_element(ref.id, ref.name)}{nested}{args}"
                f"{ref.suffix or ''}").strip()
    else:
        return f"{ref.prefix or ''}{ref.name}{nested}{args}{ref.suffix or ''}".strip()


def print_ref(ref, nested_start="&lt;", nested_end="&gt;", args_start="(", args_end=")"):
    if ref is None:
        return ""

    if ref.nested is not None:
        if len(ref.nested) > 0:
            nested = f"{nested_start}{', '.join(print_ref(r) for r in ref.nested)}{nested_end}"
        else:
            nested = f"{nested_start}{nested_end}"
    else:
        nested = ""

    if ref.args is not None:
        if len(ref.args) > 0:
            arg_parts = [f"{print_ref(a.type)}{_arg_name(a)}" for a in ref.args]
            args = f"{args_start}{', '.join(arg_parts)}{args_end}"
        else:
            args = f"{args_start}{args_end}"
    else:
        args = ""

    return f"{ref.prefix or ''}{ref.name}{nested}{args}{ref.suffix or ''}".strip()


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


def method_signature(element, context: Context, max_width: int = 80):
    static = "static" if element.static else ""
    return_type = link_from_ref(element.returns.type, context) if element.returns else ""
    method_name = element.name

    method_without_params = " ".join(part for part in (static, return_type, method_name) if part)

    if not element.params:
        return (f"{method_without_params}()")

    return_type_no_ref = print_ref(element.returns.type, context) if element.returns else ""
    method_without_params_length = len(" ".join(part for part in (static, return_type_no_ref,
                                                                  method_name) if part))

    param_sizes = [len(f"{print_ref(p.type)} {p.name}".strip()) for p in element.params]
    indent_size = method_without_params_length + 1
    first_indent = ""

    if any(indent_size + size + 1 > max_width for size in param_sizes):
        indent_size = 4
        first_indent = "\n    "

    param_separator = f",\n{' ' * indent_size}"
    formatted_params = f"{param_separator.join(type_and_name(p, context) for p in element.params)}"

    return (f"{method_without_params}({first_indent}{formatted_params})")
