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
"""Helper functions for API reference templates."""

from typing import Iterator, List, Optional, Sequence

from asciidoxy.generator.asciidoc import Api
from asciidoxy.generator.filters import InsertionFilter
from asciidoxy.model import Compound, Parameter, TypeRef


class TemplateHelper:
    api: Api
    element: Optional[Compound]
    insert_filter: Optional[InsertionFilter]

    NESTED_START: str = "<"
    NESTED_END: str = ">"
    ARGS_START: str = "("
    ARGS_END: str = ")"
    ARGS_BEFORE_TYPE = False
    ARGS_TO_TYPE = ""
    PARAM_NAME_FIRST = False
    PARAM_NAME_SEP = " "
    SIMPLE_ENCLOSED_TYPES = (
        "alias",
        "typedef",
        "enum",
    )
    COMPLEX_ENCLOSED_TYPES = (
        "class",
        "interface",
        "protocol",
        "struct",
    )

    def __init__(self,
                 api: Api,
                 element: Optional[Compound] = None,
                 insert_filter: Optional[InsertionFilter] = None):
        self.api = api
        self.element = element
        self.insert_filter = insert_filter

    def print_ref(self,
                  ref: Optional[TypeRef],
                  *,
                  link: bool = True,
                  skip_args: bool = False) -> str:
        if ref is None:
            return ""

        outer_prefix = ""
        outer_suffix = ""
        inner_ref = ref
        if ref.returns is not None:
            inner_ref = ref.returns

            if ref.prefix or ref.suffix:
                outer_prefix = f"{ref.prefix or ''}("
                outer_suffix = f"){ref.suffix or ''}"

        if inner_ref.nested is not None:
            if len(inner_ref.nested) > 0:
                nested_parts = (self.print_ref(r, link=link, skip_args=skip_args)
                                for r in inner_ref.nested)
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

            if self.ARGS_BEFORE_TYPE:
                args_before = f"{args}{self.ARGS_TO_TYPE}"
                args_after = ""
            else:
                args_before = ""
                args_after = f"{self.ARGS_TO_TYPE}{args}"
        else:
            args_before = args_after = ""

        if link and inner_ref.id:
            return (f"{outer_prefix}{args_before}{inner_ref.prefix or ''}"
                    f"{self.api.link_to_element(inner_ref.id, inner_ref.name)}{nested}"
                    f"{inner_ref.suffix or ''}{args_after}{outer_suffix}").strip()
        else:
            return (f"{outer_prefix}{args_before}{inner_ref.prefix or ''}{inner_ref.name}{nested}"
                    f"{inner_ref.suffix or ''}{args_after}{outer_suffix}".strip())

    def parameter(self, param: Parameter, *, link: bool = True, default_value: bool = False) -> str:
        if default_value and param.default_value:
            defval = f" = {param.default_value}"
        else:
            defval = ""
        prefix = param.prefix or ""

        param_type = self.print_ref(param.type, link=link)
        if not param_type:
            type_and_name = param.name
        else:
            if not param.name:
                type_and_name = self.print_ref(param.type, link=link)
            elif self.PARAM_NAME_FIRST:
                type_and_name = f"{param.name}{self.PARAM_NAME_SEP}{param_type}"
            else:
                type_and_name = f"{param_type}{self.PARAM_NAME_SEP}{param.name}"

        return f"{prefix}{type_and_name}{defval}".strip()

    def argument_list(self,
                      params: Sequence[Parameter],
                      *,
                      link: bool = True,
                      kind: str = "param",
                      start: str = "(",
                      end: str = ")") -> str:
        joined = ', '.join(self.parameter(p, link=link) for p in params if p.kind == kind)
        return f"{start}{joined}{end}"

    def type_list(self,
                  params: Sequence[Parameter],
                  *,
                  link: bool = False,
                  kind: str = "param",
                  start: str = "(",
                  end: str = ")") -> str:
        joined = ', '.join(self.print_ref(p.type, link=link) for p in params if p.kind == kind)
        return f"{start}{joined}{end}"

    def method_signature(self, method: Compound, max_width: int = 80) -> str:
        method_without_params = spaced_join(self._method_prefix(method), method.name)
        suffix = self._method_suffix(method)

        if not method.params:
            return (f"{method_without_params}(){suffix}")

        method_without_params_length = len(
            spaced_join(self._method_prefix(method, link=False).split("\n")[-1], method.name))
        suffix_length = len(self._method_suffix(method, link=False))

        param_sizes = [
            len(self.parameter(p, link=False, default_value=True)) for p in method.params
            if p.kind == "param"
        ]
        indent_size = method_without_params_length + 1
        first_indent = ""

        if any(indent_size + size + 1 + suffix_length > max_width for size in param_sizes):
            indent_size = 4
            first_indent = "\n    "

        param_separator = f",\n{' ' * indent_size}"
        formatted_params = param_separator.join(
            self.parameter(p, default_value=True) for p in method.params if p.kind == "param")

        return (f"{method_without_params}({first_indent}{formatted_params}){suffix}")

    def _method_prefix(self, method: Compound, *, link: bool = True) -> str:
        return_type = self.print_ref(method.returns.type, link=link) if method.returns else ""
        return spaced_join(*self.modifiers("static"), return_type)

    def _method_suffix(self, method: Compound, *, link: bool = True) -> str:
        return suffix_join(*modifiers(method, "const"))

    def modifiers(self, *which: str) -> List[str]:
        if self.element is None:
            return []
        return modifiers(self.element, *which)

    def static_methods(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element) if (
            m.kind == "function" and m.returns and m.prot == prot and "static" in m.modifiers))

    def methods(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element) if (
            m.kind == "function" and m.returns and m.prot == prot and "static" not in m.modifiers))

    def constructors(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        constructor_name = self.element.name
        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "function" and m.name == constructor_name and m.prot == prot)

    def simple_enclosed_types(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.prot == prot and m.kind in self.SIMPLE_ENCLOSED_TYPES)

    def complex_enclosed_types(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.prot == prot and m.kind in self.COMPLEX_ENCLOSED_TYPES)

    def variables(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "variable" and m.prot == prot)

    def properties(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.kind == "property" and m.prot == prot)

    def enum_values(self, prot: str) -> Iterator[Compound]:
        assert self.element is not None
        assert self.insert_filter is not None

        return (m for m in self.insert_filter.members(self.element)
                if m.prot == prot and m.kind == "enumvalue")


def has(elements):
    return any(True for _ in elements)


def has_any(*elements):
    return any(has(e) for e in elements)


def header(level: int, title: str) -> str:
    return f"{'=' * level} {title}"


def h1(leveloffset: int, title: str) -> str:
    return header(leveloffset + 1, title)


def h2(leveloffset: int, title: str) -> str:
    return header(leveloffset + 2, title)


def tc(text: str) -> str:
    """Filter for table cell content."""
    return text.replace("|", "{vbar}")


def param_filter(params: Sequence[Parameter], kind: str = "param") -> Iterator[Parameter]:
    """Return only parameters of a specific kind."""
    return (p for p in params if p.kind == kind)


def modifiers(element: Compound, *which: str) -> List[str]:
    """Return the modifiers applying to the element."""
    return [m for m in element.modifiers if m in which]


def spaced_join(*parts: str) -> str:
    return " ".join(part for part in parts if part).replace("\n ", "\n")


def prefix_join(*parts: str) -> str:
    joined = spaced_join(*parts)
    if joined:
        return f"{joined} "
    else:
        return ""


def suffix_join(*parts: str) -> str:
    joined = spaced_join(*parts)
    if joined:
        return f" {joined}"
    else:
        return ""
