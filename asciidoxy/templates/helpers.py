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


class TemplateHelper:
    context: Context

    NESTED_START: str = "&lt;"
    NESTED_END: str = "&gt;"
    ARGS_START: str = "("
    ARGS_END: str = ")"

    def __init__(self, context: Context):
        self.context = context

    def print_ref(self, ref, *, link: bool = True, skip_args: bool = False):
        if ref is None:
            return ""

        if ref.nested is not None:
            if len(ref.nested) > 0:
                nested_parts = (self.print_ref(r, link=link, skip_args=skip_args)
                                for r in ref.nested)
                nested = (f"{self.NESTED_START}{', '.join(nested_parts)}{self.NESTED_END}")
            else:
                nested = f"{self.NESTED_START}{self.NESTED_END}"
        else:
            nested = ""

        if not skip_args and ref.args is not None:
            if len(ref.args) > 0:
                arg_parts = (f"{self.type_and_name(a, link=link)}" for a in ref.args)
                args = f"{self.ARGS_START}{', '.join(arg_parts)}{self.ARGS_END}"
            else:
                args = f"{self.ARGS_START}{self.ARGS_END}"
        else:
            args = ""

        if link and ref.id:
            return (f"{ref.prefix or ''}"
                    f"{self.context.link_to_element(ref.id, ref.name)}{nested}{args}"
                    f"{ref.suffix or ''}").strip()
        else:
            return f"{ref.prefix or ''}{ref.name}{nested}{args}{ref.suffix or ''}".strip()

    def type_and_name(self, param, *, link: bool = True):
        return f"{self.print_ref(param.type, link=link)} {param.name}".strip()

    def argument_list(self, params, *, link: bool = True):
        return f"({', '.join(self.type_and_name(p, link=link) for p in params)})"

    def type_list(self, params, *, link: bool = False):
        return f"({', '.join(self.print_ref(p.type, link=link) for p in params)})"

    def method_signature(self, method, max_width: int = 80):
        static = "static" if method.static else ""
        return_type = self.print_ref(method.returns.type) if method.returns else ""
        method_name = method.name

        method_without_params = " ".join(part for part in (static, return_type, method_name)
                                         if part)

        if not method.params:
            return (f"{method_without_params}()")

        return_type_no_ref = self.print_ref(method.returns.type,
                                            link=False) if method.returns else ""
        method_without_params_length = len(" ".join(part for part in (static, return_type_no_ref,
                                                                      method_name) if part))

        param_sizes = [
            len(f"{self.print_ref(p.type, link=False)} {p.name}".strip()) for p in method.params
        ]
        indent_size = method_without_params_length + 1
        first_indent = ""

        if any(indent_size + size + 1 > max_width for size in param_sizes):
            indent_size = 4
            first_indent = "\n    "

        param_separator = f",\n{' ' * indent_size}"
        formatted_params = f"{param_separator.join(self.type_and_name(p) for p in method.params)}"

        return (f"{method_without_params}({first_indent}{formatted_params})")


def has(elements):
    return len(list(elements)) > 0


def chain(first_collection, second_collection):
    yield from first_collection
    yield from second_collection
