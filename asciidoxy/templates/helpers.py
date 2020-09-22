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

from typing import Iterator, Optional, Sequence

from asciidoxy.generator import Context
from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Member, Parameter, TypeRef


class TemplateHelper:
    context: Context
    element: Optional[Compound]
    insert_filter: Optional[InsertionFilter]

    NESTED_START: str = "&lt;"
    NESTED_END: str = "&gt;"
    ARGS_START: str = "("
    ARGS_END: str = ")"

    def __init__(self,
                 context: Context,
                 element: Optional[Compound] = None,
                 insert_filter: Optional[InsertionFilter] = None):
        self.context = context
        self.element = element
        self.insert_filter = insert_filter

    def print_ref(self,
                  ref: Optional[TypeRef],
                  *,
                  link: bool = True,
                  skip_args: bool = False) -> str:
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
                arg_parts = (f"{self.parameter(a, link=link)}" for a in ref.args)
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

    def parameter(self, param: Parameter, *, link: bool = True, default_value: bool = False) -> str:
        if default_value and param.default_value:
            defval = f" = {param.default_value}"
        else:
            defval = ""
        return f"{self.print_ref(param.type, link=link)} {param.name}{defval}".strip()

    def argument_list(self, params: Sequence[Parameter], *, link: bool = True) -> str:
        return f"({', '.join(self.parameter(p, link=link) for p in params)})"

    def type_list(self, params: Sequence[Parameter], *, link: bool = False) -> str:
        return f"({', '.join(self.print_ref(p.type, link=link) for p in params)})"

    def method_signature(self, method: Member, max_width: int = 80) -> str:
        method_without_params = self._method_join(self._method_prefix(method), method.name)
        suffix = self._method_suffix(method)

        if not method.params:
            return (f"{method_without_params}(){suffix}")

        method_without_params_length = len(
            self._method_join(self._method_prefix(method, link=False), method.name))
        suffix_length = len(self._method_suffix(method, link=False))

        param_sizes = [
            len(self.parameter(p, link=False, default_value=True)) for p in method.params
        ]
        indent_size = method_without_params_length + 1
        first_indent = ""

        if any(indent_size + size + 1 + suffix_length > max_width for size in param_sizes):
            indent_size = 4
            first_indent = "\n    "

        param_separator = f",\n{' ' * indent_size}"
        formatted_params = param_separator.join(
            self.parameter(p, default_value=True) for p in method.params)

        return (f"{method_without_params}({first_indent}{formatted_params}){suffix}")

    def _method_prefix(self, method: Member, *, link: bool = True) -> str:
        static = "static" if method.static else ""
        return_type = self.print_ref(method.returns.type, link=link) if method.returns else ""

        return self._method_join(static, return_type)

    def _method_suffix(self, method: Member, *, link: bool = True) -> str:
        if method.const:
            return " const"
        return ""

    @staticmethod
    def _method_join(*parts: str) -> str:
        return " ".join(part for part in parts if part)

    def public_static_methods(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "function" and m.returns and m.prot == "public" and m.static))

    def public_methods(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if (m.kind == "function" and m.returns and m.prot == "public" and not m.static))

    def public_constructors(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        constructor_name = self.element.name
        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "function" and m.name == constructor_name and m.prot == "public")

    def public_simple_enclosed_types(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.prot in ("public", "protected") and m.kind in ("enum", "typedef"))

    def public_complex_enclosed_types(self) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m.referred_object for m in self.insert_filter.inner_classes(self.element)
                if m.referred_object is not None and m.prot in ("public", "protected"))

    def public_variables(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "variable" and m.prot == "public")

    def public_properties(self) -> Iterator[Member]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "property" and m.prot == "public")


def has(elements):
    return any(True for _ in elements)


def has_any(*elements):
    return any(has(e) for e in elements)
